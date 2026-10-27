"""Auswertung: Einstellungen, Delegation und Mehrheit, Kennzahlen der Gewichtskonzentration, Tabellen, Verdikte als reine Funktionen (ohne Streamlit) und die festen Reihen."""

import math
from dataclasses import dataclass

import numpy as np

import liq_algorithm as A
import liq_constants as C
import liq_scenario as S


def num(x: float, digits: int = 1) -> str:
    return f"{x:.{digits}f}".replace(".", ",").replace("-", "−")


def pct(x, digits: int = 1) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return f"{100 * x:.{digits}f} %".replace(".", ",").replace("-", "−")


def signed(x: float, digits: int = 1) -> str:
    """Differenz zweier Wahrscheinlichkeiten in Prozentpunkten mit Vorzeichen, ohne Einheit; eine auf null gerundete Differenz hat kein Vorzeichen."""
    text = f"{100 * x:+.{digits}f}"
    if float(text) == 0:
        text = text[1:]
    return text.replace(".", ",").replace("-", "−")


def points(x: float, digits: int = 1) -> str:
    """Differenz zweier Wahrscheinlichkeiten in Prozentpunkten mit Vorzeichen."""
    return f"{signed(x, digits)} Punkte"


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    mean: int = C.DEFAULT_MEAN
    sd: int = C.DEFAULT_SD
    network: str = C.DEFAULT_NETWORK
    alpha: int = C.DEFAULT_ALPHA
    noise: int = C.DEFAULT_NOISE
    rule: str = C.DEFAULT_RULE
    seed: int = C.DEFAULT_SEED
    comp: str = ""


@dataclass
class Analysis:
    settings: Settings
    comp: list
    source: str          # "eingegeben" oder "erzeugt"
    errors: list
    n: int
    adj: list
    perceived: list
    target: list
    weights: list
    chains: list
    direct: float        # Wahrscheinlichkeit, dass die Mehrheit bei Direktwahl richtig liegt
    liquid: float        # … bei Delegation
    conc: dict           # Kennzahlen der Gewichtsverteilung


def analyse(settings: Settings) -> Analysis:
    errors = []
    rows, err = S.parse_competences(settings.comp)
    if err:
        errors.append("Eigene Fähigkeiten: " + err + " Die Eingabe wird ignoriert.")
    if rows is not None:
        comp, source = rows, "eingegeben"
    else:
        comp, source = S.make_competences(settings.mean, settings.sd, settings.n, settings.seed + 1), "erzeugt"
    n = len(comp)
    adj = S.make_network(settings.network, n, settings.seed)
    noise = np.random.default_rng(settings.seed + 2).normal(0.0, settings.noise / 100, size=n) if settings.noise else np.zeros(n)
    perceived = [c + float(e) for c, e in zip(comp, noise)]
    target = A.delegation_targets(adj, comp, perceived, settings.alpha / 100, settings.rule, np.random.default_rng(settings.seed + 3))
    weights = A.guru_weights(target)
    return Analysis(settings=settings, comp=comp, source=source, errors=errors, n=n, adj=adj, perceived=perceived, target=target, weights=weights, chains=A.chain_lengths(target),
                    direct=A.p_correct_direct(comp), liquid=A.p_correct_weighted(comp, weights), conc=A.concentration(weights))


# --- Tabellen und Texte ---------------------------------------------------------------------------------------------------------------------

def summary_rows(a: Analysis) -> list:
    c = a.conc
    return [
        {"": "Direktwahl", "Mehrheit richtig": pct(a.direct), "Wähler mit eigener Stimme": f"{a.n} von {a.n}", "größtes Gewicht": "1", "effektive Zahl der Wähler": num(a.n, 1), "Gini der Gewichte": "0,00"},
        {"": "Delegation", "Mehrheit richtig": pct(a.liquid), "Wähler mit eigener Stimme": f"{c['gurus']} von {a.n}", "größtes Gewicht": f"{c['max']} ({pct(c['max'] / a.n, 0)})",
         "effektive Zahl der Wähler": num(float(c["effective"]), 1), "Gini der Gewichte": num(float(c["gini"]), 2)},
    ]


def guru_rows(a: Analysis, limit: int = 8) -> list:
    """Die Wähler mit dem größten Gewicht: Fähigkeit, Gewicht, Anteil, Zahl der Bekannten."""
    order = sorted((i for i in range(a.n) if a.weights[i] > 0), key=lambda i: (-a.weights[i], i))[:limit]
    return [{"Wähler": f"Wähler {i + 1}", "Fähigkeit": pct(a.comp[i], 1), "Gewicht": a.weights[i], "Anteil der Stimmen": pct(a.weights[i] / a.n, 0), "Bekannte": len(a.adj[i])} for i in order]


def chain_rows(a: Analysis) -> list:
    """Wie viele Wähler delegieren über wie viele Stationen."""
    counts = {}
    for length in a.chains:
        counts[length] = counts.get(length, 0) + 1
    return [{"Stationen bis zum Guru": ("0 (stimmt selbst ab)" if k == 0 else str(k)), "Wähler": counts[k]} for k in sorted(counts)]


# --- Verdikte -------------------------------------------------------------------------------------------------------------------------------

def verdict_state(a: Analysis):
    """Kernfrage: hilft das Delegieren, und was kostet die Konzentration? Rückgabe (st-Methode, Text)."""
    gain = a.liquid - a.direct
    c = a.conc
    if c["gurus"] == a.n:
        return "info", f"Niemand delegiert (kein Nachbar ist um mehr als den Mindestabstand besser): die Mehrheit liegt in {pct(a.direct)} richtig, wie bei der Direktwahl."
    top = max(range(a.n), key=lambda i: (a.weights[i], -i))
    head = f"Delegation: die Mehrheit liegt in {pct(a.liquid)} richtig, bei Direktwahl in {pct(a.direct)} ({points(gain)})."
    tail = (f" Der Wähler mit dem größten Gewicht trägt {c['max']} von {a.n} Stimmen ({pct(c['max'] / a.n, 0)}); {c['gurus']} {'Wähler stimmt' if c['gurus'] == 1 else 'Wähler stimmen'} noch selbst ab (effektiv {num(float(c['effective']), 1)}). "
            f"Liegt dieser eine Wähler (Fähigkeit {pct(a.comp[top], 0)}) falsch, fehlen der Mehrheit {c['max']} Stimmen.")
    if gain > 1e-12:
        return "success", head + tail
    return "warning", head + tail


def verdict_regime(rows):
    """Reihe 1: wann hilft, wann schadet das Delegieren? Rückgabe (st-Methode, Text)."""
    def gap(r):
        return r["liquid"] - r["direct"]

    weak = [r for r in rows if r["mean"] == min(C.SERIES_MEANS)]
    strong = [r for r in rows if r["mean"] == max(C.SERIES_MEANS)]
    hurt = [r for r in rows if gap(r) < 0]
    text = (f"Bei schwacher Direktwahl (mittlere Fähigkeit {min(C.SERIES_MEANS)} %) hebt die Delegation die Mehrheit in jedem Netz um {num(100 * min(map(gap, weak)), 1)} bis {num(100 * max(map(gap, weak)), 1)} Punkte. "
            f"Bei starker Direktwahl ({max(C.SERIES_MEANS)} %, Direktwahl mindestens {pct(min(r['direct'] for r in strong))}) liegt sie im Mittel in jedem Netz darunter (um höchstens {num(-100 * min(map(gap, strong)), 1)} Punkte).")
    if hurt:
        worst = min(hurt, key=gap)
        text += f" Insgesamt schadet sie in {len(hurt)} von {len(rows)} Zeilen im Mittel, am stärksten im Netz „{C.NETWORK_SHORT[worst['network']]}“ bei mittlerer Fähigkeit {worst['mean']} % ({points(gap(worst))})."
    return "warning" if hurt else "info", text


def verdict_alpha(rows):
    """Reihe 2: begrenzt ein Mindestabstand die Konzentration? Rückgabe (st-Methode, Text)."""
    a0 = [r for r in rows if r["alpha"] == 0]
    a10 = [r for r in rows if r["alpha"] == 10]
    text = (f"Im Netz mit Nabenknoten sinkt das größte Gewicht mit dem Mindestabstand von {num(sum(r['max_weight'] for r in a0) / len(a0), 1)} (Abstand 0) auf {num(sum(r['max_weight'] for r in a10) / len(a10), 1)} (Abstand 10 Punkte) "
            f"von {C.SERIES_N} Stimmen; der Anteil der Netze, in denen die Delegation schadet, sinkt von {pct(max(r['worse'] / r['runs'] for r in a0), 0)} auf {pct(max(r['worse'] / r['runs'] for r in a10), 0)} (jeweils der größere Wert beider Fähigkeiten).")
    return "info", text


def verdict_noise(rows):
    """Reihe 3: wie robust ist die Delegation gegen falsch eingeschätzte Fähigkeit? Rückgabe (st-Methode, Text)."""
    low, high = min(C.SERIES_MEANS_FOCUS), max(C.SERIES_MEANS_FOCUS)
    weak = sorted((r for r in rows if r["mean"] == low), key=lambda r: r["noise"])
    strong = sorted((r for r in rows if r["mean"] == high), key=lambda r: r["noise"])
    text = (f"Fehleinschätzung frisst den Gewinn: bei mittlerer Fähigkeit {low} % sinkt er von {signed(weak[0]['gain'])} ohne Rauschen auf {signed(weak[-1]['gain'])} Punkte bei {weak[-1]['noise']} Punkten Rauschen "
            f"(schlechter in {weak[-1]['worse']} von {weak[-1]['runs']} Netzen); bei {high} % geht er von {signed(strong[0]['gain'])} auf {signed(strong[-1]['gain'])} Punkte (schlechter in {strong[-1]['worse']} von {strong[-1]['runs']}).")
    return "warning", text


# --- Feste Reihen ---------------------------------------------------------------------------------------------------------------------------

def _run(network, mean, alpha, noise, seed, rule="best", sd=C.DEFAULT_SD, n=C.SERIES_N):
    a = analyse(Settings(n=n, mean=mean, sd=sd, network=network, alpha=alpha, noise=noise, rule=rule, seed=seed))
    return a


def series_regime() -> list:
    """Je Netzart und mittlerer Fähigkeit: mittlere Wahrscheinlichkeit der richtigen Mehrheit bei Direktwahl und Delegation, Anteil der Netze mit schlechterer Delegation, mittleres größtes Gewicht."""
    rows = []
    for ni, network in enumerate(C.SERIES_NETWORKS):
        for mi, mean in enumerate(C.SERIES_MEANS):
            direct, liquid, worse, mx = [], [], 0, []
            for run in range(C.SERIES_RUNS):
                a = _run(network, mean, 0, 0, C.SERIES_SEED + 10000 * ni + 100 * mi + run)
                direct.append(a.direct)
                liquid.append(a.liquid)
                worse += a.liquid < a.direct - 1e-12
                mx.append(a.conc["max"])
            rows.append({"network": network, "mean": mean, "runs": C.SERIES_RUNS, "direct": float(np.mean(direct)), "liquid": float(np.mean(liquid)), "worse": worse, "max_weight": float(np.mean(mx))})
    return rows


def series_alpha() -> list:
    """Im Netz mit Nabenknoten je Mindestabstand und mittlerer Fähigkeit: mittlerer Gewinn (Delegation minus Direktwahl), Anteil schlechterer Netze, mittleres größtes Gewicht."""
    rows = []
    for mi, mean in enumerate(C.SERIES_MEANS_FOCUS):
        for ai, alpha in enumerate(C.SERIES_ALPHAS):
            gain, worse, mx = [], 0, []
            for run in range(C.SERIES_RUNS):
                a = _run("hub", mean, alpha, 0, C.SERIES_SEED + 100000 + 10000 * mi + 1000 * ai + run)
                gain.append(a.liquid - a.direct)
                worse += a.liquid < a.direct - 1e-12
                mx.append(a.conc["max"])
            rows.append({"mean": mean, "alpha": alpha, "runs": C.SERIES_RUNS, "gain": float(np.mean(gain)), "worse": worse, "max_weight": float(np.mean(mx))})
    return rows


def series_noise() -> list:
    """Im Zufallsnetz je Wahrnehmungsrauschen und mittlerer Fähigkeit: mittlerer Gewinn und Anteil schlechterer Netze."""
    rows = []
    for mi, mean in enumerate(C.SERIES_MEANS_FOCUS):
        for ni, noise in enumerate(C.SERIES_NOISES):
            gain, worse = [], 0
            for run in range(C.SERIES_RUNS):
                a = _run("zufall", mean, 0, noise, C.SERIES_SEED + 200000 + 10000 * mi + 1000 * ni + run)
                gain.append(a.liquid - a.direct)
                worse += a.liquid < a.direct - 1e-12
            rows.append({"mean": mean, "noise": noise, "runs": C.SERIES_RUNS, "gain": float(np.mean(gain)), "worse": worse})
    return rows


def regime_table(rows) -> list:
    return [{"Netz": C.NETWORK_SHORT[r["network"]], "mittlere Fähigkeit": f"{r['mean']} %", "Direktwahl": pct(r["direct"]), "Delegation": pct(r["liquid"]), "Unterschied": points(r["liquid"] - r["direct"]),
             "Delegation schlechter in": f"{r['worse']} von {r['runs']}", "größtes Gewicht (Mittel)": num(r["max_weight"], 1)} for r in rows]


def alpha_table(rows) -> list:
    return [{"mittlere Fähigkeit": f"{r['mean']} %", "Mindestabstand": f"{r['alpha']} Punkte", "Gewinn der Delegation": points(r["gain"]), "Delegation schlechter in": f"{r['worse']} von {r['runs']}",
             "größtes Gewicht (Mittel)": num(r["max_weight"], 1)} for r in rows]


def noise_table(rows) -> list:
    return [{"mittlere Fähigkeit": f"{r['mean']} %", "Rauschen": f"{r['noise']} Punkte", "Gewinn der Delegation": points(r["gain"]), "Delegation schlechter in": f"{r['worse']} von {r['runs']}"} for r in rows]
