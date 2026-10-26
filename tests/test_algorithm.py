"""Kern: exakte Mehrheitswahrscheinlichkeit, Kreise, Delegationsregel, Gewichte, Ketten und Konzentration. Jede Einheit an einer Mini-Instanz mit Handrechnung (DEMO-PLAYBOOK §1b)."""

import random
from fractions import Fraction as F

import numpy as np
import pytest

import liq_algorithm as A

# --- Mehrheit --------------------------------------------------------------------------------------------------------------------------------


def test_drei_wähler_mit_60_prozent():
    # P(mindestens 2 von 3) = 3 · 0,6² · 0,4 + 0,6³ = 0,648
    assert A.p_correct_direct([F(3, 5)] * 3) == F(648, 1000)


def test_gleichstand_zählt_halb():
    # zwei Wähler mit 1/2: beide richtig 1/4, genau einer richtig 1/2 (Gleichstand, halb) -> 1/4 + 1/4
    assert A.p_correct_direct([F(1, 2)] * 2) == F(1, 2)


def test_gewichte_zwei_eins_eins_bei_halb():
    # X = 2·B1 + B2 + B3, Gesamtgewicht 4: P(X > 2) = 3/8, P(X = 2) = 2/8 -> 3/8 + 1/8
    assert A.p_correct_weighted([F(1, 2)] * 3, [2, 1, 1]) == F(1, 2)


def test_ein_guru_mit_fünf_stimmen_ist_so_gut_wie_er_selbst():
    assert A.p_correct_weighted([F(78, 100), F(3, 4), F(3, 4), F(3, 4), F(3, 4)], [5, 0, 0, 0, 0]) == F(78, 100)


def test_fünf_wähler_handrechnung_direktwahl():
    # vier Wähler mit 3/4: P(Y=k) = 1, 12, 54, 108, 81 (je /256); Mehrheit = Y >= 3 oder (Y = 2 und der fünfte richtig)
    expected = F(189, 256) + F(78, 100) * F(54, 256)
    assert A.p_correct_direct([F(78, 100), F(3, 4), F(3, 4), F(3, 4), F(3, 4)]) == expected == F(23112, 25600)


def test_fünf_wähler_handrechnung_mit_gutem_guru():
    # vier Wähler mit 0,6: P(Y>=3) = 0,4752, P(Y=2) = 0,3456; dazu der Wähler mit 0,9
    assert A.p_correct_direct([F(9, 10)] + [F(3, 5)] * 4) == F(4752, 10000) + F(9, 10) * F(3456, 10000) == F(78624, 100000)


def test_gewicht_null_wähler_stimmen_nicht_ab():
    assert A.p_correct_weighted([F(9, 10), F(1, 10)], [1, 0]) == F(9, 10)


def test_float_und_bruch_stimmen_überein():
    comp = [0.55, 0.6, 0.7, 0.52, 0.65, 0.58]
    exact = A.p_correct_direct([F(c).limit_denominator(1000) for c in comp])
    assert A.p_correct_direct(comp) == pytest.approx(float(exact), abs=1e-12)


def test_wahrscheinlichkeit_übersteigt_nie_eins():
    # mittlere Fähigkeit 80 %, Streuung 5, 201 Wähler, Zufalls-Seed 3: die Gleitkommafaltung ergibt ohne Kappung 1,0000000000000002
    import liq_scenario as S

    comp = S.make_competences(80, 5, 201, 4)
    assert A.p_correct_direct(comp) <= 1.0
    assert A.p_correct_direct([0.99] * 201) <= 1.0
    assert A.p_correct_direct([F(99, 100)] * 5) < 1


def test_sichere_und_unmögliche_wähler():
    assert A.p_correct_direct([1.0, 1.0, 1.0]) == 1.0
    assert A.p_correct_direct([0.0, 0.0, 0.0]) == 0.0


@pytest.mark.parametrize("comp, weights", [([0.5, 0.5], [1]), ([0.5, 0.5], [1, -1]), ([0.5, 0.5], [0, 0]), ([0.5, 0.5], [1.5, 1])])
def test_ungültige_gewichte_werden_abgelehnt(comp, weights):
    with pytest.raises(ValueError):
        A.p_correct_weighted(comp, weights)


# --- Kreise ----------------------------------------------------------------------------------------------------------------------------------


def test_kreis_aus_zwei_wählern_wird_aufgelöst():
    assert A.break_cycles([1, 0]) == [None, None]


def test_kette_die_in_einen_kreis_läuft_endet_im_kreis():
    # 0 -> 1 -> 2 -> 1 (Kreis aus 1 und 2); 3 -> 0 läuft in den Kreis: 1 und 2 stimmen selbst ab
    assert A.break_cycles([1, 2, 1, 0]) == [1, None, None, 0]


def test_selbstschleife_und_unabhängige_kreise():
    assert A.break_cycles([0]) == [None]
    assert A.break_cycles([1, 0, 3, 2, None]) == [None, None, None, None, None]


def test_ohne_kreis_bleibt_alles_gleich():
    target = [1, 2, None, 2, 3]
    assert A.break_cycles(target) == target


def test_break_cycles_verändert_die_eingabe_nicht():
    target = [1, 0]
    A.break_cycles(target)
    assert target == [1, 0]


# --- Delegationsregel ------------------------------------------------------------------------------------------------------------------------


def test_best_wählt_den_höchsten_wahrgenommenen_nachbarn():
    comp = [F(5, 10), F(6, 10), F(8, 10), F(7, 10)]
    adj = [[1, 2, 3], [0], [0], [0]]
    target = A.delegation_targets(adj, comp, comp, F(0), "best")
    assert target[0] == 2
    assert target[1] is None            # Nachbar 0 ist schlechter: Wähler 1 delegiert nicht


def test_gleichstand_der_besten_geht_an_die_kleinere_nummer():
    comp = [F(5, 10), F(8, 10), F(8, 10)]
    assert A.delegation_targets([[1, 2], [0], [0]], comp, comp, F(0), "best")[0] == 1


def test_mindestabstand_ist_strikt():
    comp = [F(5, 10), F(6, 10)]
    adj = [[1], [0]]
    assert A.delegation_targets(adj, comp, comp, F(1, 10), "best") == [None, None]     # genau 0,1 besser reicht nicht
    assert A.delegation_targets(adj, comp, comp, F(99, 1000), "best") == [1, None]


def test_wahrgenommene_fähigkeit_entscheidet_der_eigene_wert_ist_wahr():
    comp = [F(5, 10), F(4, 10)]
    perceived = [F(3, 10), F(9, 10)]                  # Nachbar 1 wird überschätzt, Nachbar 0 unterschätzt: nur Wähler 0 delegiert
    assert A.delegation_targets([[1], [0]], comp, perceived, F(0), "best") == [1, None]


def test_zufallsregel_wählt_nur_bessere_und_streut():
    comp = [F(1, 10), F(5, 10), F(6, 10), F(2, 100)]
    adj = [[1, 2, 3], [0], [0], [0]]
    seen = set()
    rng = np.random.default_rng(1)
    for _ in range(200):
        seen.add(A.delegation_targets(adj, comp, comp, F(0), "zufall", rng)[0])
    assert seen == {1, 2}


def test_unbekannte_regel_wird_abgelehnt():
    with pytest.raises(ValueError):
        A.delegation_targets([[]], [0.5], [0.5], 0.0, "los")


def test_ohne_bessere_nachbarn_stimmt_jeder_selbst_ab():
    comp = [F(5, 10)] * 3
    assert A.delegation_targets([[1, 2], [0, 2], [0, 1]], comp, comp, F(0), "best") == [None, None, None]


def test_delegation_bildet_nie_einen_kreis():
    rng = random.Random(4)
    for _ in range(200):
        n = rng.randint(3, 12)
        comp = [rng.random() for _ in range(n)]
        perceived = [c + rng.gauss(0, 0.3) for c in comp]            # starkes Rauschen kann Kreise erzeugen
        adj = [sorted(rng.sample([j for j in range(n) if j != i], rng.randint(1, n - 1))) for i in range(n)]
        target = A.delegation_targets(adj, comp, perceived, 0.0, "best")
        for start in range(n):                                       # jede Kette endet nach höchstens n Schritten
            node, steps = start, 0
            while target[node] is not None:
                node, steps = target[node], steps + 1
                assert steps <= n


# --- Gewichte, Ketten, Konzentration ---------------------------------------------------------------------------------------------------------


def test_gewichte_einer_kette():
    # 0 -> 1 -> 2, 3 -> 2, 4 allein
    assert A.guru_weights([1, 2, None, 2, None]) == [0, 0, 4, 0, 1]


def test_gewichte_unabhängig_von_der_reihenfolge_der_kette():
    assert A.guru_weights([None, 0, 1, 2]) == [4, 0, 0, 0]
    assert A.guru_weights([1, 2, 3, None]) == [0, 0, 0, 4]


def test_gewichte_summieren_sich_zur_wählerzahl():
    rng = random.Random(2)
    for _ in range(100):
        n = rng.randint(1, 30)
        target = [rng.choice([None] + [j for j in range(n) if j != i]) if n > 1 else None for i in range(n)]
        w = A.guru_weights(A.break_cycles(target))
        assert sum(w) == n


def test_kettenlängen_handrechnung():
    # 0 -> 1 -> 2 (Guru), 3 -> 2, 4 -> 3
    assert A.chain_lengths([1, 2, None, 2, 3]) == [2, 1, 0, 1, 2]


def test_kettenlängen_gegen_einfaches_nachlaufen():
    rng = random.Random(5)
    for _ in range(100):
        n = rng.randint(2, 25)
        target = A.break_cycles([rng.choice([None] + [j for j in range(n) if j != i]) for i in range(n)])
        expected = []
        for i in range(n):
            node, steps = i, 0
            while target[node] is not None:
                node, steps = target[node], steps + 1
            expected.append(steps)
        assert A.chain_lengths(target) == expected


def test_konzentration_handrechnung():
    c = A.concentration([3, 0, 1, 0])
    assert c["max"] == 3 and c["gurus"] == 2 and c["top5"] == 1
    assert c["effective"] == F(8, 5)                        # 1 / ((3/4)² + (1/4)²) = 16/10
    assert c["gini"] == F(5, 8)                             # Summe der |x_i − x_j| über alle geordneten Paare 20, geteilt durch 2·16·1


def test_konzentration_gleichverteilt_und_ein_halter():
    eq = A.concentration([1, 1, 1, 1])
    assert eq["effective"] == 4 and eq["gini"] == 0 and eq["gurus"] == 4 and eq["max"] == 1
    one = A.concentration([4, 0, 0, 0])
    assert one["effective"] == 1 and one["gini"] == F(3, 4) and one["gurus"] == 1


def test_top5_bei_mehr_als_fünf_gurus():
    assert A.concentration([1] * 10)["top5"] == F(1, 2)


def test_gini_gegen_paarvergleich():
    rng = random.Random(8)
    for _ in range(60):
        n = rng.randint(2, 15)
        w = [rng.randint(0, 6) for _ in range(n)]
        if sum(w) == 0:
            continue
        total = sum(w)
        mean = F(total, n)
        expected = sum(abs(x - y) for x in w for y in w) / (2 * n * n * mean)
        assert A.concentration(w)["gini"] == expected


def test_majority_weight():
    assert A.majority_weight([3, 0, 1, 0]) == F(3, 4)


def test_top5_nimmt_die_fünf_größten_nicht_die_kleinsten():
    assert A.concentration([1, 1, 1, 1, 1, 1, 6])["top5"] == F(10, 12)     # 6 + 4 · 1 von 12


def test_negatives_gewicht_wird_auch_bei_positiver_summe_abgelehnt():
    with pytest.raises(ValueError):
        A.p_correct_weighted([0.5, 0.5], [2, -1])
