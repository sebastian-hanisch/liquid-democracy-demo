"""Abbildungen: Zahl und Art der Spuren, gesperrte Achsen, Werte aus der Analyse und den Reihen."""

import math

import liq_constants as C
import liq_evaluation as ev
import liq_visualization as V


def _locked(fig):
    return fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_positionen_liegen_auf_dem_einheitskreis():
    pos = V.positions(8)
    assert pos[0] == (0.0, 1.0)
    assert all(abs(math.hypot(x, y) - 1) < 1e-12 for x, y in pos)
    assert len({(round(x, 9), round(y, 9)) for x, y in pos}) == 8


def test_netzabbildung():
    a = ev.analyse(ev.Settings(n=31))
    fig = V.build_network(a)
    assert _locked(fig) and len(fig.data) == 2
    edges = fig.data[0]
    assert sum(1 for v in edges.x if v is None) == sum(1 for t in a.target if t is not None)
    nodes = fig.data[1]
    assert len(nodes.x) == a.n and list(nodes.marker.color) == a.comp
    sizes = list(nodes.marker.size)
    top = max(range(a.n), key=lambda i: a.weights[i])
    assert sizes[top] == max(sizes)
    assert [i for i, c in enumerate(nodes.marker.line.color) if c == "#222"] == [i for i, w in enumerate(a.weights) if w]


def test_gewichtsabbildung_sortiert_und_färbt_nach_hälfte():
    a = ev.analyse(ev.Settings(comp="90, 60, 60, 60, 60", network="voll"))
    fig = V.build_weights(a)
    assert _locked(fig) and list(fig.data[0].y) == [5] and fig.data[0].marker.color[0] == C.COLOR_LIQUID
    b = ev.analyse(ev.Settings())
    ys = list(V.build_weights(b).data[0].y)
    assert ys == sorted(ys, reverse=True) and len(ys) <= 20 and ys[0] == b.conc["max"]


def test_gewichtsabbildung_ohne_delegation_zeigt_nur_begrenzte_zahl():
    a = ev.analyse(ev.Settings(n=21, sd=5, alpha=20))
    fig = V.build_weights(a, limit=5)
    assert list(fig.data[0].y) == [1] * 5
    assert fig.data[0].marker.color[0] == C.COLOR_DIRECT


def _rows(kind):
    if kind == "regime":
        return [{"network": n, "mean": m, "direct": 0.5, "liquid": 0.6, "runs": 100, "worse": 1, "max_weight": 9.0} for n in C.SERIES_NETWORKS for m in C.SERIES_MEANS]
    if kind == "alpha":
        return [{"mean": m, "alpha": al, "gain": 0.01, "runs": 100, "worse": 1, "max_weight": 9.0} for m in C.SERIES_MEANS_FOCUS for al in C.SERIES_ALPHAS]
    return [{"mean": m, "noise": no, "gain": 0.01, "runs": 100, "worse": 1} for m in C.SERIES_MEANS_FOCUS for no in C.SERIES_NOISES]


def test_reihenabbildungen():
    regime = V.build_regime_series(_rows("regime"))
    assert _locked(regime) and len(regime.data) == len(C.SERIES_NETWORKS)
    assert all(len(t.x) == len(C.SERIES_MEANS) and abs(t.y[0] - 10) < 1e-9 for t in regime.data)
    alpha = V.build_alpha_series(_rows("alpha"))
    assert _locked(alpha) and len(alpha.data) == 1 + len(C.SERIES_MEANS_FOCUS)
    assert alpha.data[0].yaxis == "y2" and alpha.data[1].yaxis == "y" and list(alpha.data[0].y) == [9.0] * len(C.SERIES_ALPHAS)
    noise = V.build_noise_series(_rows("noise"))
    assert _locked(noise) and len(noise.data) == len(C.SERIES_MEANS_FOCUS)
    assert [t.x[-1] for t in noise.data] == [f"{C.SERIES_NOISES[-1]} Punkte"] * 2
