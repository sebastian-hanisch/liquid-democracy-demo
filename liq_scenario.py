"""Szenario: Netz und Fähigkeiten der Wähler (erzeugt oder eingegeben). Deterministisch aus (Art, Zahl, Zufalls-Seed)."""

import re

import numpy as np

import liq_constants as C


def make_network(kind: str, n: int, seed: int) -> list:
    """Nachbarlisten (sortiert) eines ungerichteten Netzes mit n Knoten.

    Zufallsnetz: jede Verbindung mit Wahrscheinlichkeit MEAN_DEGREE/(n − 1). Nabenknoten (bevorzugte Anbindung, Barabási–Albert): jeder neue Wähler zieht HUB_LINKS Ziele, mit Wahrscheinlichkeit
    proportional zur Zahl der bisherigen Verbindungen; doppelt gezogene Ziele zählen einmal (mittlerer Grad daher etwa 5,6). Ring: jeder kennt die RING_REACH Nächsten je Seite. Jeder kennt jeden: alle Paare."""
    if kind not in C.NETWORKS:
        raise ValueError(kind)
    rng = np.random.default_rng(seed)
    adj = [set() for _ in range(n)]

    def link(a, b):
        if a != b:
            adj[a].add(b)
            adj[b].add(a)

    if kind == "zufall":
        p = min(1.0, C.MEAN_DEGREE / max(1, n - 1))
        for a in range(n):
            for b in range(a + 1, n):
                if rng.random() < p:
                    link(a, b)
    elif kind == "hub":
        m = min(C.HUB_LINKS, max(1, n - 1))
        targets = list(range(m))
        repeated = []
        for new in range(m, n):
            for t in set(targets):
                link(new, t)
            repeated += list(set(targets)) + [new] * m
            targets = [repeated[int(rng.integers(len(repeated)))] for _ in range(m)]
        for a in range(min(m, n)):                       # die ersten Knoten kennen sich untereinander
            for b in range(a + 1, min(m, n)):
                link(a, b)
    elif kind == "lokal":
        for a in range(n):
            for d in range(1, C.RING_REACH + 1):
                link(a, (a + d) % n)
    else:
        for a in range(n):
            for b in range(a + 1, n):
                link(a, b)
    return [sorted(s) for s in adj]


def make_competences(mean: int, sd: int, n: int, seed: int) -> list:
    """Fähigkeiten (Trefferquoten) der Wähler: Beta-verteilt mit dem Mittel `mean` % und der Standardabweichung `sd` Punkte, auf 1 bis 99 % begrenzt, auf ganze Promille gerundet."""
    m, s = mean / 100, sd / 100
    if not 0 < m < 1 or s <= 0 or s * s >= m * (1 - m):
        raise ValueError("Mittel und Streuung passen nicht zu einer Beta-Verteilung")
    kappa = m * (1 - m) / (s * s) - 1
    rng = np.random.default_rng(seed)
    raw = rng.beta(m * kappa, (1 - m) * kappa, size=n)
    return [min(0.99, max(0.01, round(float(x), 3))) for x in raw]


def parse_competences(text: str):
    """Eingabe: Fähigkeiten in Prozent (ganze Zahlen von 1 bis 99), getrennt durch Komma, Semikolon, Zeilenumbruch oder Leerzeichen. Rückgabe (Liste in 0 bis 1 oder None, Fehlermeldung oder None); leerer Text: (None, None)."""
    text = (text or "").strip()
    if not text:
        return None, None
    parts = [t for t in re.split(r"[,;\s]+", text) if t]
    values = []
    for t in parts:
        if not re.fullmatch(r"\d+", t):
            return None, f"„{t}“ ist keine ganze Zahl (erlaubt: Prozent von 1 bis 99, getrennt durch Komma, Semikolon oder Leerzeichen)."
        values.append(int(t))
    if not C.COMP_TEXT_MIN <= len(values) <= C.COMP_TEXT_MAX:
        return None, f"Es müssen {C.COMP_TEXT_MIN} bis {C.COMP_TEXT_MAX} Wähler sein (eingegeben: {len(values)})."
    if min(values) < 1 or max(values) > 99:
        return None, "Jede Fähigkeit muss zwischen 1 und 99 Prozent liegen."
    return [v / 100 for v in values], None
