"""Randfälle: Extremwerte der Regler, Invarianten jeder Analyse, Adresszeile und eigene Fähigkeiten."""

import itertools
import os

import pytest
from streamlit.testing.v1 import AppTest

import liq_constants as C
import liq_evaluation as ev

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
GRID = list(itertools.product(C.NETWORKS, (C.N_MIN, 20, C.N_MAX), (C.MEAN_MIN, C.MEAN_MAX), (C.ALPHA_MIN, C.ALPHA_MAX), (C.NOISE_MIN, C.NOISE_MAX), tuple(C.RULES)))


@pytest.mark.parametrize("network,n,mean,alpha,noise,rule", GRID)
def test_invarianten_an_den_grenzen(network, n, mean, alpha, noise, rule):
    sd = C.SD_MIN if mean == C.MEAN_MAX else C.SD_MAX
    a = ev.analyse(ev.Settings(n=n, mean=mean, sd=sd, network=network, alpha=alpha, noise=noise, rule=rule, seed=3))
    assert a.n == n == len(a.comp) == len(a.weights) and sum(a.weights) == n and a.errors == []
    assert 0 <= a.direct <= 1 and 0 <= a.liquid <= 1
    assert a.conc["max"] == max(a.weights) and 1 <= a.conc["gurus"] <= n and 1 <= float(a.conc["effective"]) <= n + 1e-9
    assert 0 <= float(a.conc["gini"]) < 1
    assert all(t is None or (t != i and t in a.adj[i]) for i, t in enumerate(a.target))          # delegiert wird nur an Bekannte
    assert all(a.weights[i] == 0 for i, t in enumerate(a.target) if t is not None)                # wer delegiert, hat kein Gewicht
    assert ev.verdict_state(a)[1]


def test_drei_wähler_der_kleinste_fall():
    a = ev.analyse(ev.Settings(n=3, network="voll"))
    assert a.n == 3 and sum(a.weights) == 3
    b = ev.analyse(ev.Settings(comp="60 70 80", network="voll"))
    assert b.weights == [0, 0, 3] and b.liquid == pytest.approx(0.8)


def test_alle_gleich_fähig_niemand_delegiert():
    a = ev.analyse(ev.Settings(comp="60 60 60 60 60", network="voll"))
    assert a.weights == [1] * 5 and a.liquid == pytest.approx(a.direct)


def test_gleichstand_bei_gerader_wählerzahl_zählt_halb():
    a = ev.analyse(ev.Settings(comp="50 50 50 50", alpha=20, network="voll"))
    assert a.n == 4 and a.direct == pytest.approx(0.5) and a.liquid == pytest.approx(0.5)      # P(3 oder 4 von 4) = 5/16, Gleichstand 6/16 zählt halb


# --- App: Adresszeile und eigene Fähigkeiten --------------------------------------------------------------------------------------------------


def _run(**params):
    at = AppTest.from_file(APP, default_timeout=180)
    for key, value in params.items():
        at.query_params[key] = value
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_permalink_mit_eigenen_fähigkeiten_füllt_das_feld_und_sperrt_den_erzeuger():
    at = _run(comp="78, 75, 75, 75, 75", network="voll")
    assert at.sidebar.text_area(key="comp_text").value == "78, 75, 75, 75, 75"
    for key in ("n_slider", "mean_slider", "sd_slider"):
        assert at.sidebar.slider(key=key).proto.disabled
    assert at.metric[0].value == "90,3 %" and at.metric[1].value == "78,0 %" and at.metric[2].value == "5 von 5"


def test_permalink_werte_werden_begrenzt_und_schlechte_ignoriert():
    at = _run(n="9999", mean="x", sd="-5", alpha="99", noise="-1", seed="-3", network="stern", rule="los")
    assert at.sidebar.slider(key="n_slider").value == C.N_MAX and at.sidebar.slider(key="mean_slider").value == C.DEFAULT_MEAN
    assert at.sidebar.slider(key="sd_slider").value == C.SD_MIN and at.sidebar.slider(key="alpha_slider").value == C.ALPHA_MAX
    assert at.sidebar.slider(key="noise_slider").value == C.NOISE_MIN and at.sidebar.number_input(key="seed_input").value == 0
    assert at.sidebar.selectbox(key="network_select").value == C.DEFAULT_NETWORK and at.sidebar.selectbox(key="rule_select").value == C.DEFAULT_RULE


def test_zu_langer_text_aus_der_adresszeile_wird_abgeschnitten():
    at = _run(comp="50 " * 2000)
    assert len(at.sidebar.text_area(key="comp_text").value) <= 1500


def test_schlechte_eingabe_zeigt_eine_warnung_und_die_app_läuft_weiter():
    at = _run(comp="78, abc, 75")
    assert any("Eigene Fähigkeiten" in w.value for w in at.warning) and not at.sidebar.slider(key="n_slider").proto.disabled


def test_kein_delegierender_wähler_zeigt_die_info():
    at = _run(comp="60 60 60 60 60", network="voll")
    assert any("Niemand delegiert" in i.value for i in at.info)


def test_regler_ändern_hält_die_app_am_laufen():
    at = _run()
    for key, value in (("n_slider", 3), ("n_slider", 201), ("mean_slider", 80), ("sd_slider", 5), ("alpha_slider", 20), ("noise_slider", 30)):
        at.sidebar.slider(key=key).set_value(value).run()
        assert not at.exception
    for key, value in (("network_select", "hub"), ("rule_select", "zufall")):
        at.sidebar.selectbox(key=key).set_value(value).run()
        assert not at.exception


def test_die_reihen_laufen_auf_klick():
    at = _run()
    for key in ("regime_button", "alpha_button", "noise_button"):
        at.button(key=key).click().run(timeout=180)
        assert not at.exception, [str(e) for e in at.exception]
    assert len(at.table) >= 6
