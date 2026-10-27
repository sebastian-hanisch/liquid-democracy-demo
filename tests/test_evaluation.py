"""Auswertung: Formatierung, Analyse, Tabellen, Verdikte und die Zahlen in den Hilfetexten der Presets."""

import re
from fractions import Fraction as F

import pytest

import liq_constants as C
import liq_evaluation as ev
from liq_evaluation import Settings, analyse


def test_formatierung():
    assert ev.num(1234.567, 1) == "1234,6"
    assert ev.num(-0.5, 1) == "−0,5"
    assert ev.pct(0.9876) == "98,8 %"
    assert ev.pct(None) == "–" and ev.pct(float("nan")) == "–"
    assert ev.pct(F(1, 2), 0) == "50 %"
    assert ev.points(0.051) == "+5,1 Punkte"
    assert ev.points(-0.098) == "−9,8 Punkte"
    assert ev.signed(0.051) == "+5,1" and ev.signed(-0.098) == "−9,8"


def test_auf_null_gerundete_differenz_hat_kein_vorzeichen():
    assert ev.points(-0.00003) == "0,0 Punkte"
    assert ev.points(0.00003) == "0,0 Punkte"
    assert ev.signed(-0.0004) == "0,0"
    assert ev.points(-0.0006) == "−0,1 Punkte"


def test_analyse_ist_deterministisch_und_konsistent():
    s = Settings()
    a, b = analyse(s), analyse(s)
    assert a.comp == b.comp and a.target == b.target and a.liquid == b.liquid
    assert a.n == C.DEFAULT_N == len(a.comp) == len(a.weights) == len(a.adj)
    assert sum(a.weights) == a.n
    assert 0 <= a.direct <= 1 and 0 <= a.liquid <= 1
    assert a.source == "erzeugt" and a.errors == []
    assert a.conc["max"] == max(a.weights) and a.conc["gurus"] == sum(1 for w in a.weights if w)


def test_ohne_rauschen_ist_die_wahrnehmung_wahr_mit_rauschen_nicht():
    a = analyse(Settings(noise=0))
    assert a.perceived == a.comp
    b = analyse(Settings(noise=10))
    assert b.perceived != b.comp and b.comp == a.comp


def test_mindestabstand_macht_delegation_seltener():
    low = analyse(Settings(alpha=0))
    high = analyse(Settings(alpha=20))
    assert sum(1 for t in high.target if t is not None) < sum(1 for t in low.target if t is not None)


def test_ohne_delegation_gleich_direktwahl():
    a = analyse(Settings(n=21, sd=5, alpha=20))
    assert all(t is None for t in a.target)
    assert a.liquid == pytest.approx(a.direct, abs=1e-12)
    assert a.conc["gurus"] == a.n and a.conc["max"] == 1


def test_eigene_fähigkeiten_bestimmen_die_wählerzahl():
    a = analyse(Settings(n=101, comp="78, 75, 75, 75, 75", network="voll"))
    assert a.n == 5 and a.source == "eingegeben" and a.comp == [0.78, 0.75, 0.75, 0.75, 0.75]


def test_ungültige_eingabe_wird_gemeldet_und_ignoriert():
    a = analyse(Settings(n=31, comp="78, abc, 75"))
    assert a.source == "erzeugt" and a.n == 31
    assert len(a.errors) == 1 and a.errors[0].startswith("Eigene Fähigkeiten:") and "abc" in a.errors[0]


def test_handbeispiele_mit_exakten_werten():
    bad = analyse(Settings(comp="78, 75, 75, 75, 75", network="voll"))
    assert bad.weights == [5, 0, 0, 0, 0]
    assert bad.liquid == pytest.approx(0.78, abs=1e-12) and bad.direct == pytest.approx(0.9028125, abs=1e-12)
    good = analyse(Settings(comp="90, 60, 60, 60, 60", network="voll"))
    assert good.weights == [5, 0, 0, 0, 0]
    assert good.liquid == pytest.approx(0.9, abs=1e-12) and good.direct == pytest.approx(0.78624, abs=1e-12)


def test_regel_zufall_hat_im_nabennetz_mit_seed_32_ein_kleineres_groesstes_gewicht():  # nur dieser Einzelfall, kein allgemeiner Befund
    best = analyse(Settings(network="hub", rule="best", seed=32))
    rnd = analyse(Settings(network="hub", rule="zufall", seed=32))
    assert rnd.conc["max"] < best.conc["max"]


# --- Tabellen ---------------------------------------------------------------------------------------------------------------------------------


def test_tabellen_der_analyse():
    a = analyse(Settings())
    rows = ev.summary_rows(a)
    assert [r[""] for r in rows] == ["Direktwahl", "Delegation"]
    assert rows[0]["Wähler mit eigener Stimme"] == f"{a.n} von {a.n}" and rows[0]["größtes Gewicht"] == "1"
    assert rows[1]["Mehrheit richtig"] == ev.pct(a.liquid)
    guru = ev.guru_rows(a)
    assert len(guru) == 8 and [g["Gewicht"] for g in guru] == sorted((w for w in a.weights if w), reverse=True)[:8]
    assert guru[0]["Gewicht"] == a.conc["max"]
    chains = ev.chain_rows(a)
    assert sum(r["Wähler"] for r in chains) == a.n
    assert chains[0]["Stationen bis zum Guru"] == "0 (stimmt selbst ab)" and chains[0]["Wähler"] == a.conc["gurus"]


# --- Verdikte ---------------------------------------------------------------------------------------------------------------------------------


def test_verdikt_niemand_delegiert():
    kind, text = ev.verdict_state(analyse(Settings(n=21, sd=5, alpha=20)))
    assert kind == "info" and "Niemand delegiert" in text


def test_verdikt_ein_guru_steht_im_singular():
    kind, text = ev.verdict_state(analyse(Settings(comp="90, 60, 60, 60, 60", network="voll")))
    assert kind == "success" and "1 Wähler stimmt noch selbst ab" in text and "5 von 5 Stimmen" in text


def test_verdikt_schaden_ist_eine_warnung_nutzen_ein_erfolg():
    assert ev.verdict_state(analyse(Settings(comp="78, 75, 75, 75, 75", network="voll")))[0] == "warning"
    assert ev.verdict_state(analyse(Settings(mean=55)))[0] == "success"


def _row(**kw):
    base = {"runs": 100, "worse": 0}
    base.update(kw)
    return base


def test_verdikt_regime_mit_und_ohne_schaden():
    rows = [_row(network=n, mean=m, direct=d, liquid=lq, max_weight=10.0) for n in C.SERIES_NETWORKS for m, d, lq in ((min(C.SERIES_MEANS), 0.6, 0.9), (max(C.SERIES_MEANS), 0.999, 0.99))]
    kind, text = ev.verdict_regime(rows)
    assert kind == "warning" and "9 von 18" not in text and "in 3 von 6 Zeilen" in text and "um höchstens 0,9 Punkte" in text
    nobody_hurt = [_row(network=n, mean=m, direct=d, liquid=d + 0.01, max_weight=10.0) for n in C.SERIES_NETWORKS for m, d in ((min(C.SERIES_MEANS), 0.6), (max(C.SERIES_MEANS), 0.9))]
    assert ev.verdict_regime(nobody_hurt)[0] == "info"


def test_verdikt_alpha_und_noise_nennen_ihre_zahlen():
    rows = [_row(mean=m, alpha=al, gain=0.0, worse=w, max_weight=mw) for m in C.SERIES_MEANS_FOCUS for al, w, mw in ((0, 80, 30.0), (10, 20, 15.0))]
    kind, text = ev.verdict_alpha(rows)
    assert kind == "info" and "30,0" in text and "15,0" in text and "80 %" in text and "20 %" in text
    noise_rows = [_row(mean=m, noise=no, gain=g, worse=w) for m in C.SERIES_MEANS_FOCUS for no, g, w in ((0, 0.1, 0), (30, -0.05, 60))]
    kind, text = ev.verdict_noise(noise_rows)
    assert kind == "warning" and "+10,0 auf −5,0 Punkte" in text and "60 von 100" in text


# --- Presets: jede Zahl im Hilfetext stimmt ---------------------------------------------------------------------------------------------------


EXPECTED = {
    "Zufallsnetz, mittlere Fähigkeit 62 %": {"direct": "99,6 %", "liquid": "97,6 %", "max": 37},
    "Delegieren hilft": {"direct": "88,2 %", "liquid": "93,3 %", "max": 38, "diff": "+5,1"},
    "Nabenknoten sammeln Stimmen": {"direct": "99,0 %", "liquid": "89,2 %", "max": 57, "diff": "−9,8", "top": "89 %"},
    "Mindestabstand begrenzt den Schaden": {"direct": "99,0 %", "liquid": "99,5 %", "max": 16, "diff": "+0,6"},
    "Ein Guru, fünf Stimmen": {"direct": "90,3 %", "liquid": "78,0 %", "max": 5},
    "Ein Guru, der hilft": {"direct": "78,6 %", "liquid": "90,0 %", "max": 5},
}


NENNT_GEWICHT = ("Zufallsnetz, mittlere Fähigkeit 62 %", "Nabenknoten sammeln Stimmen", "Mindestabstand begrenzt den Schaden")  # Hilfetexte, die das größte Gewicht nennen


def test_jedes_preset_hat_einen_hilfetext_und_erwartete_werte():
    assert set(C.PRESETS) == set(C.PRESET_HELP) == set(EXPECTED)


@pytest.mark.parametrize("name", list(EXPECTED))
def test_hilfetext_des_presets_stimmt_mit_der_rechnung(name):
    a = analyse(Settings(**C.PRESETS[name]))
    exp, help_text = EXPECTED[name], C.PRESET_HELP[name]
    assert ev.pct(a.direct) == exp["direct"] and ev.pct(a.liquid) == exp["liquid"] and a.conc["max"] == exp["max"]
    assert exp["direct"].replace(" %", "") in help_text and exp["liquid"].replace(" %", "") in help_text
    if "diff" in exp:
        assert ev.signed(a.liquid - a.direct) == exp["diff"] and exp["diff"].lstrip("+") in help_text
    if "top" in exp:
        top = max(range(a.n), key=lambda i: (a.weights[i], -i))
        assert ev.pct(a.comp[top], 0) == exp["top"] and f"Fähigkeit {exp['top'].replace(' %', '')} %" in help_text
    if name in NENNT_GEWICHT:
        assert re.search(rf"\b{exp['max']}\b", help_text)


def test_hub_presets_vorher_nachher():
    harm = analyse(Settings(**C.PRESETS["Nabenknoten sammeln Stimmen"]))
    fix = analyse(Settings(**C.PRESETS["Mindestabstand begrenzt den Schaden"]))
    assert harm.conc["max"] == 57 and fix.conc["max"] == 16
    assert harm.liquid < harm.direct < fix.liquid
    assert harm.comp == fix.comp and harm.adj == fix.adj          # nur der Mindestabstand unterscheidet beide


# --- Lücken aus der Mutationsprüfung ---------------------------------------------------------------------------------------------------------


def test_rauschen_hat_die_eingestellte_standardabweichung_und_vorzeichen():
    import numpy as np

    a = ev.analyse(ev.Settings(noise=10, seed=7))
    err = np.array(a.perceived) - np.array(a.comp)
    assert np.allclose(err, np.random.default_rng(9).normal(0.0, 0.10, size=a.n))     # Zufalls-Seed + 2, Standardabweichung 10 Punkte


def test_mindestabstand_wird_in_punkten_gelesen():
    for seed in range(6):
        a = ev.analyse(ev.Settings(alpha=10, seed=seed))
        delegating = [(i, t) for i, t in enumerate(a.target) if t is not None]
        assert delegating
        assert all(a.perceived[t] > a.comp[i] + 0.10 for i, t in delegating)


def test_guru_zeilen_nehmen_auch_den_letzten_wähler_und_nur_gurus():
    a = ev.analyse(ev.Settings(comp="60 70 80", network="voll"))
    assert [r["Wähler"] for r in ev.guru_rows(a)] == ["Wähler 3"]              # Gewicht 3; die anderen zwei haben 0
    b = ev.analyse(ev.Settings(comp="60 60 60 60 60", network="voll"))
    assert len(ev.guru_rows(b)) == 5 and all(r["Gewicht"] == 1 for r in ev.guru_rows(b))   # Gewicht 1 zählt als Guru


def test_verdikt_nennt_die_fähigkeit_des_gurus_mit_dem_größten_gewicht():
    assert "Fähigkeit 90 %" in ev.verdict_state(ev.analyse(ev.Settings(comp="90, 60, 60, 60, 60", network="voll")))[1]
    assert "Fähigkeit 80 %" in ev.verdict_state(ev.analyse(ev.Settings(comp="60 70 80", network="voll")))[1]


def test_regime_tabelle_zeigt_das_vorzeichen_des_unterschieds():
    row = _row(network="hub", mean=62, direct=0.5, liquid=0.6, max_weight=9.0)
    assert ev.regime_table([row])[0]["Unterschied"] == "+10,0 Punkte"
    assert ev.regime_table([dict(row, liquid=0.4)])[0]["Unterschied"] == "−10,0 Punkte"


def test_verdikt_regime_gleichstand_ist_kein_schaden_und_schwach_stark_getrennt():
    low, high = min(C.SERIES_MEANS), max(C.SERIES_MEANS)
    rows = [_row(network="zufall", mean=m, direct=0.6, liquid=0.6, max_weight=1.0) for m in (low, high)]
    assert ev.verdict_regime(rows)[0] == "info"
    rows = [_row(network="zufall", mean=low, direct=0.60, liquid=0.70, max_weight=1.0), _row(network="hub", mean=low, direct=0.60, liquid=0.80, max_weight=1.0),
            _row(network="zufall", mean=high, direct=0.999, liquid=0.99, max_weight=1.0), _row(network="hub", mean=high, direct=0.999, liquid=0.97, max_weight=1.0)]
    text = ev.verdict_regime(rows)[1]
    assert "um 10,0 bis 20,0 Punkte" in text and "um höchstens 2,9 Punkte" in text and "(mittlere Fähigkeit 52 %)" in text


def test_verdikt_noise_trennt_schwache_und_starke_gruppe_und_ordnet_nach_rauschen():
    low, high = min(C.SERIES_MEANS_FOCUS), max(C.SERIES_MEANS_FOCUS)
    rows = [_row(mean=low, noise=30, gain=0.003, worse=46), _row(mean=high, noise=30, gain=-0.072, worse=99),
            _row(mean=high, noise=0, gain=-0.005, worse=60), _row(mean=low, noise=0, gain=0.130, worse=0)]           # absichtlich unsortiert
    text = ev.verdict_noise(rows)[1]
    assert f"bei mittlerer Fähigkeit {low} % sinkt er von +13,0 ohne Rauschen auf +0,3 Punkte bei 30 Punkten" in text
    assert "46 von 100 Netzen" in text and f"bei {high} % geht er von −0,5 auf −7,2 Punkte (schlechter in 99 von 100)" in text


def _fake_run(calls):
    from types import SimpleNamespace

    def fake(*args, **kwargs):
        calls.append(args)
        return SimpleNamespace(direct=0.5, liquid=0.5, conc={"max": 3})
    return fake


def test_reihen_rechnen_alle_netze_und_zählen_gleichstände_nicht_als_schaden(monkeypatch):
    calls = []
    monkeypatch.setattr(ev, "_run", _fake_run(calls))
    rows = ev.series_regime()
    assert len(calls) == len(C.SERIES_NETWORKS) * len(C.SERIES_MEANS) * C.SERIES_RUNS and len({c[4] for c in calls}) == len(calls)   # jeder Lauf ein eigener Zufalls-Seed
    assert all(r["worse"] == 0 and r["direct"] == r["liquid"] == 0.5 and r["max_weight"] == 3 for r in rows)
    calls.clear()
    rows = ev.series_alpha()
    assert len(calls) == len(C.SERIES_MEANS_FOCUS) * len(C.SERIES_ALPHAS) * C.SERIES_RUNS and len({c[4] for c in calls}) == len(calls)
    assert all(r["worse"] == 0 and r["gain"] == 0 for r in rows)
    calls.clear()
    rows = ev.series_noise()
    assert len(calls) == len(C.SERIES_MEANS_FOCUS) * len(C.SERIES_NOISES) * C.SERIES_RUNS and len({c[4] for c in calls}) == len(calls)
    assert all(r["worse"] == 0 and r["gain"] == 0 for r in rows)


def test_delegation_der_analyse_folgt_genau_dem_mindestabstand_in_punkten():
    import numpy as np

    import liq_algorithm as A

    for seed in range(25):
        a = ev.analyse(ev.Settings(alpha=10, seed=seed))
        assert a.target == A.delegation_targets(a.adj, a.comp, a.perceived, 0.10, "best", np.random.default_rng(seed + 3))
