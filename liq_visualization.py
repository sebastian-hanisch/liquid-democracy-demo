"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import math

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import liq_constants as C
import liq_evaluation as ev


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.28), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def positions(n: int) -> list:
    """Die Wähler gleichmäßig auf einem Kreis (Wähler 1 oben, im Uhrzeigersinn)."""
    return [(math.sin(2 * math.pi * i / n), math.cos(2 * math.pi * i / n)) for i in range(n)]


def build_network(a):
    """Die Delegationen: jeder Pfeil führt von einem Wähler zu dem, an den er seine Stimme überträgt. Die Fläche eines Punkts wächst mit dem Gewicht, die Farbe zeigt die Fähigkeit; Wähler mit eigener Stimme haben einen dunklen Rand."""
    pos = positions(a.n)
    fig = go.Figure()
    ex, ey = [], []
    for i, t in enumerate(a.target):
        if t is not None:
            ex += [pos[i][0], pos[t][0], None]
            ey += [pos[i][1], pos[t][1], None]
    fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines", line=dict(color="rgba(128,128,128,0.35)", width=1), hoverinfo="skip", showlegend=False))
    sizes = [7 + 5 * math.sqrt(w) if w else 7 for w in a.weights]
    fig.add_trace(go.Scatter(
        x=[p[0] for p in pos], y=[p[1] for p in pos], mode="markers", showlegend=False,
        marker=dict(size=sizes, color=a.comp, colorscale="Blues", cmin=0.3, cmax=1.0, colorbar=dict(title="Fähigkeit", tickformat=".0%", thickness=12),
                    line=dict(color=["#222" if w else "rgba(0,0,0,0)" for w in a.weights], width=2)),
        text=[f"Wähler {i + 1}: Fähigkeit {ev.pct(a.comp[i], 1)}, Gewicht {a.weights[i]}, {len(a.adj[i])} Bekannte" for i in range(a.n)], hovertemplate="%{text}<extra></extra>"))
    fig.update_xaxes(visible=False, range=[-1.25, 1.25], constrain="domain")
    fig.update_yaxes(visible=False, range=[-1.25, 1.25], scaleanchor="x", scaleratio=1, constrain="domain")
    return _base(fig, height=460)


def build_weights(a, limit: int = 20):
    """Die größten Gewichte, absteigend; die gestrichelte Linie ist die Hälfte aller Stimmen: ein Gewicht darüber entscheidet allein."""
    order = sorted((i for i in range(a.n) if a.weights[i] > 0), key=lambda i: (-a.weights[i], i))[:limit]
    fig = go.Figure(go.Bar(x=[f"Wähler {i + 1}" for i in order], y=[a.weights[i] for i in order], marker_color=[C.COLOR_LIQUID if a.weights[i] * 2 > a.n else C.COLOR_DIRECT for i in order],
                           customdata=[ev.pct(a.comp[i], 0) for i in order], hovertemplate="%{x}: Gewicht %{y} (Fähigkeit %{customdata})<extra></extra>"))
    fig.add_hline(y=a.n / 2, line_color=C.COLOR_ALERT, line_dash="dash", annotation_text="Hälfte aller Stimmen", annotation_position="top right")
    fig.update_yaxes(title_text="Gewicht (Stimmen)", rangemode="tozero")
    fig.update_xaxes(type="category")
    return _base(fig, height=320)


def build_regime_series(rows):
    """Unterschied der Richtigkeit (Delegation minus Direktwahl, Prozentpunkte) über der mittleren Fähigkeit, eine Linie je Netz; die Null-Linie trennt Nutzen von Schaden."""
    fig = go.Figure()
    colors = {"zufall": "#4c78a8", "hub": "#b04a3a", "lokal": "#2F6B65"}
    for network in C.SERIES_NETWORKS:
        sel = [r for r in rows if r["network"] == network]
        fig.add_trace(go.Scatter(x=[f"{r['mean']} %" for r in sel], y=[100 * (r["liquid"] - r["direct"]) for r in sel], mode="lines+markers", name=C.NETWORK_SHORT[network], line=dict(color=colors[network], width=2.5),
                                 hovertemplate="%{x}: %{y:+.1f} Punkte<extra>" + C.NETWORK_SHORT[network] + "</extra>"))
    fig.add_hline(y=0, line_color="rgba(128,128,128,0.8)", line_dash="dot")
    fig.update_yaxes(title_text="Delegation minus Direktwahl (Punkte)")
    fig.update_xaxes(title_text="Mittlere Fähigkeit eines Wählers", type="category")
    return _base(fig, height=360)


def build_alpha_series(rows):
    """Oben der mittlere Gewinn der Delegation (Punkte), unten das mittlere größte Gewicht (Stimmen), beide über dem Mindestabstand im Netz mit Nabenknoten."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.6, 0.4])
    colors = {C.SERIES_MEANS_FOCUS[0]: "#4c78a8", C.SERIES_MEANS_FOCUS[1]: "#b04a3a"}
    sel0 = [r for r in rows if r["mean"] == C.SERIES_MEANS_FOCUS[0]]
    xs = [f"{r['alpha']} Punkte" for r in sel0]
    fig.add_trace(go.Bar(x=xs, y=[r["max_weight"] for r in sel0], name=f"größtes Gewicht (bei {C.SERIES_MEANS_FOCUS[0]} %)", marker_color="rgba(128,128,128,0.45)", hovertemplate="%{x}: %{y:.1f} Stimmen<extra>größtes Gewicht</extra>"), row=2, col=1)
    for mean in C.SERIES_MEANS_FOCUS:
        sel = [r for r in rows if r["mean"] == mean]
        fig.add_trace(go.Scatter(x=xs, y=[100 * r["gain"] for r in sel], mode="lines+markers", name=f"Gewinn bei mittlerer Fähigkeit {mean} %", line=dict(color=colors[mean], width=2.5),
                                 hovertemplate="%{x}: %{y:+.1f} Punkte<extra>" + f"{mean} %" + "</extra>"), row=1, col=1)
    fig.add_hline(y=0, line_color="rgba(128,128,128,0.8)", line_dash="dot", row=1, col=1)
    fig.update_yaxes(title_text="Gewinn (Punkte)", row=1, col=1)
    fig.update_yaxes(title_text="größtes Gewicht", rangemode="tozero", row=2, col=1)
    fig.update_xaxes(title_text="Mindestabstand für eine Delegation", type="category", row=2, col=1)
    return _base(fig, height=460)


def build_noise_series(rows):
    """Mittlerer Gewinn der Delegation über dem Wahrnehmungsrauschen im Zufallsnetz, eine Linie je mittlerer Fähigkeit."""
    fig = go.Figure()
    colors = {C.SERIES_MEANS_FOCUS[0]: "#4c78a8", C.SERIES_MEANS_FOCUS[1]: "#b04a3a"}
    for mean in C.SERIES_MEANS_FOCUS:
        sel = [r for r in rows if r["mean"] == mean]
        fig.add_trace(go.Scatter(x=[f"{r['noise']} Punkte" for r in sel], y=[100 * r["gain"] for r in sel], mode="lines+markers", name=f"mittlere Fähigkeit {mean} %", line=dict(color=colors[mean], width=2.5),
                                 hovertemplate="%{x}: %{y:+.1f} Punkte<extra>" + f"{mean} %" + "</extra>"))
    fig.add_hline(y=0, line_color="rgba(128,128,128,0.8)", line_dash="dot")
    fig.update_yaxes(title_text="Gewinn der Delegation (Punkte)")
    fig.update_xaxes(title_text="Wahrnehmungsrauschen der Fähigkeit", type="category")
    return _base(fig, height=340)
