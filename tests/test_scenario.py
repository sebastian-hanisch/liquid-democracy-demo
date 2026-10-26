"""Szenario: Netze und Fähigkeiten, deterministisch aus dem Zufalls-Seed; Eingabe eigener Fähigkeiten."""

import numpy as np
import pytest

import liq_constants as C
import liq_scenario as S


@pytest.mark.parametrize("kind", list(C.NETWORKS))
@pytest.mark.parametrize("n", [3, 4, 7, 30, 101])
def test_netz_ist_ungerichtet_ohne_schleifen_und_sortiert(kind, n):
    adj = S.make_network(kind, n, 5)
    assert len(adj) == n
    for i, nb in enumerate(adj):
        assert nb == sorted(set(nb)) and i not in nb
        for j in nb:
            assert i in adj[j]


def test_netz_ist_deterministisch_und_der_seed_ändert_es():
    assert S.make_network("hub", 60, 4) == S.make_network("hub", 60, 4)
    assert S.make_network("zufall", 60, 4) != S.make_network("zufall", 60, 5)
    assert S.make_network("hub", 60, 4) != S.make_network("hub", 60, 5)


def test_ring_hat_grad_sechs_und_jeder_kennt_jeden_grad_n_minus_eins():
    assert all(len(nb) == 6 for nb in S.make_network("lokal", 20, 1))
    assert S.make_network("lokal", 20, 1)[0] == [1, 2, 3, 17, 18, 19]
    assert all(len(nb) == 19 for nb in S.make_network("voll", 20, 1))


def test_zufallsnetz_hat_mittleren_grad_um_sechs():
    degs = [np.mean([len(nb) for nb in S.make_network("zufall", 201, s)]) for s in range(10)]
    assert 5.5 < np.mean(degs) < 6.5


def test_nabennetz_hat_höchstens_drei_neue_verbindungen_und_einen_großen_knoten():
    adj = S.make_network("hub", 201, 3)
    degrees = [len(nb) for nb in adj]
    assert min(degrees) >= 2                               # doppelt gezogene Ziele zählen einmal: ein neuer Wähler kennt 1 bis 3 ältere
    assert 5.0 < np.mean(degrees) < 6.0                    # etwas unter 2·3, weil doppelte Ziele entfallen
    assert max(degrees) > 4 * np.mean(degrees)             # einige Nabenknoten kennen sehr viele


def test_nabennetz_ist_zusammenhängend():
    adj = S.make_network("hub", 100, 9)
    seen, stack = {0}, [0]
    while stack:
        for j in adj[stack.pop()]:
            if j not in seen:
                seen.add(j)
                stack.append(j)
    assert len(seen) == 100


def test_unbekanntes_netz_wird_abgelehnt():
    with pytest.raises(ValueError):
        S.make_network("stern", 10, 1)


def test_fähigkeiten_bereich_rundung_und_determinismus():
    comp = S.make_competences(62, 15, 500, 7)
    assert comp == S.make_competences(62, 15, 500, 7)
    assert comp != S.make_competences(62, 15, 500, 8)
    assert all(0.01 <= c <= 0.99 and abs(c * 1000 - round(c * 1000)) < 1e-9 for c in comp)


def test_fähigkeiten_mittel_und_streuung():
    comp = np.array(S.make_competences(62, 15, 5000, 1))
    assert abs(comp.mean() - 0.62) < 0.01
    assert abs(comp.std() - 0.15) < 0.01


@pytest.mark.parametrize("mean, sd", [(50, 60), (62, 0), (0, 5), (100, 5)])
def test_ungültige_beta_parameter(mean, sd):
    with pytest.raises(ValueError):
        S.make_competences(mean, sd, 10, 1)


def test_eingabe_trennzeichen():
    for text in ("78, 75, 75", "78;75;75", "78 75 75", "78\n75\n75", " 78 ,75;  75 "):
        assert S.parse_competences(text) == ([0.78, 0.75, 0.75], None)


def test_eingabe_leer_ist_kein_fehler():
    assert S.parse_competences("") == (None, None)
    assert S.parse_competences("  \n ") == (None, None)
    assert S.parse_competences(None) == (None, None)


@pytest.mark.parametrize("text", ["78, 75", "78, 75, abc", "78, 75, 7.5", "78, 75, 0", "78, 75, 100", "78, 75, -3"])
def test_eingabe_fehler(text):
    values, error = S.parse_competences(text)
    assert values is None and error


def test_eingabe_grenzen_der_wählerzahl():
    assert S.parse_competences(" ".join(["50"] * C.COMP_TEXT_MAX))[0] is not None
    assert S.parse_competences(" ".join(["50"] * (C.COMP_TEXT_MAX + 1)))[0] is None
    assert S.parse_competences(" ".join(["50"] * C.COMP_TEXT_MIN))[0] is not None
