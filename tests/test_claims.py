"""Befunde der festen Reihen: jede Aussage der README und der Verdikte steht hier als Prüfung. Die Reihen rechnen mit festen Zufalls-Seeds; geprüft werden Richtungen und grobe Bänder, nicht die letzte Stelle
(die Zufallsströme von numpy können sich zwischen Versionen unterscheiden)."""

import pytest

import liq_constants as C
import liq_evaluation as ev


@pytest.fixture(scope="module")
def regime():
    return ev.series_regime()


@pytest.fixture(scope="module")
def alpha():
    return ev.series_alpha()


@pytest.fixture(scope="module")
def noise():
    return ev.series_noise()


def pick(rows, **kw):
    found = [r for r in rows if all(r[k] == v for k, v in kw.items())]
    assert len(found) == 1
    return found[0]


def gain(r):
    return r["liquid"] - r["direct"] if "direct" in r else r["gain"]


# --- Reihe 1 ----------------------------------------------------------------------------------------------------------------------------------


def test_reihe_1_aufbau(regime):
    assert len(regime) == len(C.SERIES_NETWORKS) * len(C.SERIES_MEANS) == 18
    assert all(r["runs"] == C.SERIES_RUNS for r in regime)
    assert ev.regime_table(regime)[0]["Netz"] == "Zufallsnetz"


def test_schwache_gruppe_gewinnt_in_jedem_netz_stark(regime):
    for network in C.SERIES_NETWORKS:
        r = pick(regime, network=network, mean=52)
        assert gain(r) > 0.20 and r["worse"] <= 2           # README: +26 bis +31 Punkte, in keinem/fast keinem Netz schlechter
        assert r["direct"] < 0.70


def test_starke_gruppe_verliert_in_jedem_netz(regime):
    for network in C.SERIES_NETWORKS:
        r = pick(regime, network=network, mean=70)
        assert r["direct"] > 0.999 and gain(r) <= 1e-9 and r["worse"] >= 95
    assert gain(pick(regime, network="hub", mean=70)) < -0.005             # im Nabennetz sichtbar (README: −0,9 Punkte)


def test_nabennetz_ist_bei_62_prozent_am_schädlichsten_der_ring_hilft_noch(regime):
    hub, zufall, ring = (gain(pick(regime, network=n, mean=62)) for n in ("hub", "zufall", "lokal"))
    assert hub < zufall < ring
    assert hub < -0.01 and ring > 0                                        # README: −1,8 gegen +0,3 Punkte


def test_ring_hat_das_kleinste_größte_gewicht(regime):
    for mean in C.SERIES_MEANS:
        ring = pick(regime, network="lokal", mean=mean)["max_weight"]
        assert ring < pick(regime, network="zufall", mean=mean)["max_weight"] < pick(regime, network="hub", mean=mean)["max_weight"]


def test_der_gewinn_fällt_mit_der_fähigkeit(regime):
    for network in C.SERIES_NETWORKS:
        gains = [gain(pick(regime, network=network, mean=m)) for m in C.SERIES_MEANS]
        assert gains[0] > gains[1] > gains[2] > gains[3] and gains[0] == max(gains)


def test_verdikt_reihe_1(regime):
    kind, text = ev.verdict_regime(regime)
    assert kind == "warning" and "Nabenknoten" in text and "8 von 18 Zeilen" in text and "−0,0" not in text


# --- Reihe 2 ----------------------------------------------------------------------------------------------------------------------------------


def test_reihe_2_aufbau(alpha):
    assert len(alpha) == len(C.SERIES_MEANS_FOCUS) * len(C.SERIES_ALPHAS) == 10
    assert ev.alpha_table(alpha)[0]["Mindestabstand"] == "0 Punkte"


def test_mindestabstand_senkt_das_größte_gewicht(alpha):
    for mean in C.SERIES_MEANS_FOCUS:
        weights = [pick(alpha, mean=mean, alpha=a)["max_weight"] for a in C.SERIES_ALPHAS]
        assert weights == sorted(weights, reverse=True)
        assert weights[0] > 2 * weights[-1]                                # README: 28 gegen 9–10 Stimmen


def test_bei_62_prozent_kippt_der_gewinn_mit_dem_mindestabstand(alpha):
    assert pick(alpha, mean=62, alpha=0)["gain"] < -0.005
    assert pick(alpha, mean=62, alpha=20)["gain"] > 0
    shares = [pick(alpha, mean=62, alpha=a)["worse"] for a in C.SERIES_ALPHAS]
    assert shares == sorted(shares, reverse=True) and shares[0] >= 60 and shares[-1] <= 10


def test_bei_55_prozent_hilft_ein_mittlerer_abstand_am_meisten(alpha):
    gains = {a: pick(alpha, mean=55, alpha=a)["gain"] for a in C.SERIES_ALPHAS}
    assert gains[15] > gains[0] + 0.03 and all(g > 0.09 for g in gains.values())


def test_verdikt_reihe_2(alpha):
    kind, text = ev.verdict_alpha(alpha)
    assert kind == "info" and "Abstand 10 Punkte" in text


# --- Reihe 3 ----------------------------------------------------------------------------------------------------------------------------------


def test_reihe_3_aufbau(noise):
    assert len(noise) == len(C.SERIES_MEANS_FOCUS) * len(C.SERIES_NOISES) == 10
    assert ev.noise_table(noise)[0]["Rauschen"] == "0 Punkte"


def test_rauschen_frisst_den_gewinn_bei_55_prozent(noise):
    g = [pick(noise, mean=55, noise=x)["gain"] for x in C.SERIES_NOISES]
    assert g[0] > 0.10 and g[0] - g[-1] > 0.10 and g[-1] > -0.02            # README: +13,1 auf +0,3 Punkte
    assert pick(noise, mean=55, noise=30)["worse"] > 30


def test_rauschen_vertieft_den_verlust_bei_62_prozent(noise):
    g = [pick(noise, mean=62, noise=x)["gain"] for x in C.SERIES_NOISES]
    assert g[0] < 0 and g[-1] < g[0] - 0.05 and g[-1] < -0.05                # README: −0,5 auf −7,2 Punkte
    assert pick(noise, mean=62, noise=30)["worse"] >= 95


def test_verdikt_reihe_3(noise):
    kind, text = ev.verdict_noise(noise)
    assert kind == "warning" and "Fehleinschätzung frisst den Gewinn" in text and "−0,0" not in text
