"""Liquid Democracy: wann hilft Delegieren? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Gelber Kandidat der Linie „Abstimmen und Fair Teilen“: Wähler mit unterschiedlicher Fähigkeit entscheiden über eine Frage mit einer richtigen Antwort und dürfen ihre Stimme an einen besseren Bekannten übertragen. Gemessen wird,
wie oft die Mehrheit richtig liegt (exakt gerechnet) und wie stark sich die Stimmen bei wenigen Wählern („Gurus“) sammeln. Der Kern liegt in liq_algorithm.py.

Lauffähig mit: streamlit run app.py
"""

import time

import streamlit as st

import liq_constants as C
import liq_evaluation as ev
from liq_evaluation import Settings, analyse, num
from liq_layout import dunkles_design, kopf_css
from liq_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from liq_scenario import parse_competences
from liq_visualization import build_alpha_series, build_network, build_noise_series, build_regime_series, build_weights

st.set_page_config(page_title="Liquid Democracy – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _series_regime():
    return ev.series_regime()


@st.cache_data(show_spinner=False)
def _series_alpha():
    return ev.series_alpha()


@st.cache_data(show_spinner=False)
def _series_noise():
    return ev.series_noise()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in liq_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("💧 Liquid Democracy: wann hilft Delegieren?")
st.markdown(
    """
Eine Gruppe entscheidet über eine Frage mit **einer richtigen Antwort**. Jeder Wähler liegt mit seiner **Fähigkeit** richtig (zum Beispiel in 62 von 100 Fällen), unabhängig von den anderen. Bei der **Direktwahl** stimmt jeder selbst ab; bei der **Delegation** („Liquid Democracy“) darf jeder seine Stimme an einen **besseren Bekannten** übertragen, der sie weiterreichen kann, bis die Kette bei einem Wähler endet, der selbst abstimmt, dem **Guru**.
Das kann die Mehrheit **verbessern**, wenn die Gruppe schwach ist, und sie **verschlechtern**, wenn sich viele Stimmen bei wenigen Wählern **sammeln**: dann entscheidet fast nur noch deren Zufall. Die Demo rechnet die Wahrscheinlichkeit, dass die Mehrheit richtig liegt, **exakt** (Faltung der unabhängigen Stimmen) und misst die **Gewichtskonzentration**.
Verwandt: `mehrheitsurteil-demo` (Abstimmen ohne Delegation, Jury-Satz), `wahlregeln-demo` (Regeln für Präferenzen) und `zufallsgremium-demo` (Gremien per Los).

Weiter unten: die **Kernfrage**, der Abschnitt **🔬 Feste Reihen** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So wird gerechnet", expanded=True):
    st.markdown(
        """
1. **Wähler und Fähigkeit.** Die Fähigkeiten werden aus einer Beta-Verteilung mit der eingestellten Mitte und Streuung gezogen (auf ganze Promille gerundet) oder von Hand eingegeben.
2. **Netz.** Wer wen kennt, legt das Netz fest: ein Zufallsnetz (im Mittel sechs Bekannte), ein Netz mit **Nabenknoten** (neue Wähler knüpfen ihre Kontakte bevorzugt zu schon gut Vernetzten), ein Ring (die sechs Nächsten) oder „jeder kennt jeden“.
3. **Delegation.** Wer einen Bekannten hat, dessen **eingeschätzte** Fähigkeit um mehr als den **Mindestabstand** über der eigenen liegt, überträgt die Stimme (an den fähigsten oder an einen zufälligen solchen Bekannten). Die Einschätzung ist die wahre Fähigkeit plus ein **Rauschen**, das für jeden Wähler gleich ist (ein guter Ruf wirkt auf alle Bekannten gleich).
4. **Ketten.** Eine Stimme wandert weiter, bis sie bei einem Wähler ankommt, der nicht delegiert. Läuft eine Kette im Kreis, stimmen die Wähler auf dem Kreis selbst ab. Das **Gewicht** eines Gurus ist die Zahl der Wähler, deren Kette bei ihm endet.
5. **Mehrheit.** Jeder Guru hat mit seiner wahren Fähigkeit recht, unabhängig von den anderen; seine Stimme zählt so oft wie sein Gewicht. Die Wahrscheinlichkeit, dass mehr als die Hälfte des Gewichts richtig liegt, wird exakt gerechnet (bei genau der Hälfte zählt der Gleichstand halb).
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

_comp_valid, _ = parse_competences(st.session_state["comp_text"])
custom = _comp_valid is not None
with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Wähler**")
    n = st.slider("Zahl der Wähler", *bounds("n_slider"), key="n_slider", disabled=custom, help="Wie viele Wähler abstimmen. Bei eigenen Fähigkeiten bestimmt deren Zahl den Wert. Bei gerader Zahl zählt ein Gleichstand halb.")
    mean = st.slider("Mittlere Fähigkeit (%)", *bounds("mean_slider"), key="mean_slider", disabled=custom, help="Wie oft ein Wähler im Mittel richtig liegt. Ab etwa 60 % ist die Direktwahl bei 100 Wählern schon fast sicher.")
    sd = st.slider("Streuung der Fähigkeit (Punkte)", *bounds("sd_slider"), key="sd_slider", disabled=custom, help="Wie verschieden die Wähler sind. Bei kleiner Streuung und Mindestabstand gibt es kaum bessere Bekannte, an die sich delegieren lässt.")
    st.markdown("**Netz und Delegation**")
    network = st.selectbox("Wer kennt wen", list(C.NETWORKS), format_func=C.NETWORKS.get, key="network_select", help="Bestimmt, an wen ein Wähler überhaupt delegieren kann. Im Netz mit Nabenknoten kennen einige Wähler sehr viele.")
    rule = st.selectbox("An wen wird delegiert", list(C.RULES), format_func=C.RULES.get, key="rule_select", help="Auch bei einem zufälligen besseren Bekannten laufen die Ketten zu den fähigsten Wählern der Umgebung; die Konzentration ist ähnlich hoch wie beim fähigsten Bekannten.")
    alpha = st.slider("Mindestabstand (Punkte)", *bounds("alpha_slider"), key="alpha_slider", help="Ein Bekannter muss um mehr als diesen Abstand besser eingeschätzt werden, damit delegiert wird. 0 = schon ein kleiner Vorsprung genügt.")
    noise = st.slider("Wahrnehmungsrauschen (Punkte)", *bounds("noise_slider"), key="noise_slider", help="Wie ungenau die Fähigkeit der Bekannten eingeschätzt wird (Standardabweichung der Fehleinschätzung, je Wähler fest).")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1, help="Legt Netz, Fähigkeiten, Einschätzung und die zufällige Delegationsregel fest.")
    st.button("🎲 Neues Szenario erzeugen", width="stretch", on_click=randomize_seed)
    st.markdown("**Eigene Fähigkeiten (optional)**")
    comp_text = st.text_area("Fähigkeit je Wähler in Prozent", key="comp_text", height=100, placeholder="z. B. 78, 75, 75, 75, 75",
                             help=f"Ganze Prozent von 1 bis 99, getrennt durch Komma, Semikolon oder Leerzeichen; {C.COMP_TEXT_MIN} bis {C.COMP_TEXT_MAX} Werte. Leer lassen, um die Fähigkeiten erzeugen zu lassen. Netz und Delegation gelten weiter.")

sync_query_params({"n_slider": int(n), "mean_slider": int(mean), "sd_slider": int(sd), "network_select": network, "rule_select": rule, "alpha_slider": int(alpha), "noise_slider": int(noise), "seed_input": int(seed), "comp_text": comp_text})

settings = Settings(n=int(n), mean=int(mean), sd=int(sd), network=network, alpha=int(alpha), noise=int(noise), rule=rule, seed=int(seed), comp=comp_text)
a = _analysis(settings)
for message in a.errors:
    st.warning(message)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

c = a.conc
st.markdown("## 🎯 Ergebnis")
m1, m2, m3 = st.columns(3)
m1.metric("Mehrheit richtig (Direktwahl)", ev.pct(a.direct), delta=f"{a.n} Wähler mit je einer Stimme", delta_color="off")
m2.metric("Mehrheit richtig (Delegation)", ev.pct(a.liquid), delta=f"{ev.points(a.liquid - a.direct).replace('−', '-')} gegen Direktwahl")  # ASCII-Minus: nur daran erkennt Streamlit einen negativen Wert (rote Farbe, Pfeil nach unten)
m3.metric("Größtes Gewicht", f"{c['max']} von {a.n}", delta=f"{ev.pct(c['max'] / a.n, 0)} aller Stimmen", delta_color="off")
if a.source == "eingegeben":
    st.caption(f"Die eigenen Fähigkeiten bestimmen die Zahl der Wähler ({a.n}); Mittel und Streuung haben keine Wirkung; das Netz entsteht aus der gewählten Netzart und dem Zufalls-Seed.")
st.markdown("**Das Netz der Delegationen**")
st.plotly_chart(build_network(a), width="stretch", key="network_chart")
st.caption("Jeder Punkt ist ein Wähler (hell: weniger fähig, dunkel: fähiger); die Fläche wächst mit dem Gewicht, ein dunkler Rand kennzeichnet Wähler, die selbst abstimmen. Die Linien führen von jedem delegierenden Wähler zu seinem nächsten Glied der Kette.")
st.markdown("**Wer trägt die Stimmen?**")
st.plotly_chart(build_weights(a), width="stretch", key="weights_chart")
st.caption("Die größten Gewichte, absteigend. Rot: ein Gewicht über der Hälfte aller Stimmen (entscheidet allein).")
st.table(ev.summary_rows(a))
with st.expander("Die Wähler mit dem größten Gewicht und die Länge der Ketten"):
    st.table(ev.guru_rows(a))
    st.table(ev.chain_rows(a))

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Hilft das Delegieren, und was kostet die Konzentration?")
kind, text = ev.verdict_state(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Reihen --------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Feste Reihen")
st.caption(
    f"Feste Programme, unabhängig von den Reglern: je Zeile {C.SERIES_RUNS} Zufallsnetze mit festen Zufalls-Seeds ({C.SERIES_N} Wähler, Streuung {C.DEFAULT_SD} Punkte, Delegation zum fähigsten besseren Bekannten); "
    "die Wahrscheinlichkeit der richtigen Mehrheit ist je Netz exakt gerechnet, die Zeilen zeigen Mittelwerte und gezählte Anteile. Jede Reihe rechnet auf Klick einige Sekunden."
)
tab1, tab2, tab3 = st.tabs(["Wann hilft Delegieren?", "Hilft ein Mindestabstand?", "Und bei falscher Einschätzung?"])
with tab1:
    st.markdown("**Delegation gegen Direktwahl** bei steigender mittlerer Fähigkeit in drei Netzen: wo die Linie unter der Null liegt, schadet die Delegation im Mittel.")
    if st.button("Reihe rechnen", key="regime_button"):
        t0 = time.perf_counter()
        with st.spinner("Rechne die Reihe …"):
            _series_regime()
        st.session_state["regime_done"] = time.perf_counter() - t0
    if "regime_done" in st.session_state:
        rows = _series_regime()
        st.plotly_chart(build_regime_series(rows), width="stretch", key="regime_chart")
        st.table(ev.regime_table(rows))
        kind, text = ev.verdict_regime(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {num(st.session_state['regime_done'], 1)} s (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")
with tab2:
    st.markdown("**Mindestabstand im Netz mit Nabenknoten.** Wer nur an deutlich bessere Bekannte delegiert, macht Ketten kürzer und Gewichte kleiner; oben der Gewinn der Delegation, unten das mittlere größte Gewicht (bei mittlerer Fähigkeit 55 %).")
    if st.button("Reihe rechnen", key="alpha_button"):
        t0 = time.perf_counter()
        with st.spinner("Rechne die Reihe …"):
            _series_alpha()
        st.session_state["alpha_done"] = time.perf_counter() - t0
    if "alpha_done" in st.session_state:
        rows = _series_alpha()
        st.plotly_chart(build_alpha_series(rows), width="stretch", key="alpha_chart")
        st.table(ev.alpha_table(rows))
        kind, text = ev.verdict_alpha(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {num(st.session_state['alpha_done'], 1)} s (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")
with tab3:
    st.markdown("**Wahrnehmungsrauschen im Zufallsnetz.** Wer die Fähigkeit der Bekannten falsch einschätzt, delegiert auch an schlechtere; hier mit steigendem Rauschen bei zwei mittleren Fähigkeiten.")
    if st.button("Reihe rechnen", key="noise_button"):
        t0 = time.perf_counter()
        with st.spinner("Rechne die Reihe …"):
            _series_noise()
        st.session_state["noise_done"] = time.perf_counter() - t0
    if "noise_done" in st.session_state:
        rows = _series_noise()
        st.plotly_chart(build_noise_series(rows), width="stretch", key="noise_chart")
        st.table(ev.noise_table(rows))
        kind, text = ev.verdict_noise(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {num(st.session_state['noise_done'], 1)} s (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Es gibt eine richtige Antwort** | Bei Wertfragen („was wollen wir?“) gibt es keine Trefferquote; die Rechnung betrifft nur Wissensfragen mit überprüfbarem Ergebnis. | – |
| **Die Wähler irren unabhängig** | Teilen die Wähler dieselben Quellen oder Vorurteile, ist auch die Direktwahl schlechter, als hier gerechnet; dann kann ein fähiger Guru mehr bringen. | `mehrheitsurteil-demo` (Abhängigkeit bei der Mehrheit) |
| **Der Guru irrt unabhängig von seinen Delegierenden** | Hier hat der Guru seine eigene Trefferquote; in der Praxis überzeugen Gurus ihre Anhänger oft von ihrer Sicht, was Fehler verstärkt. | – |
| **Fähigkeit ist eine Zahl** | Echte Wähler sind bei einer Frage gut, bei einer anderen schlecht; die Demo kennt nur eine Frage und eine Fähigkeit je Wähler. | – |
| **Die Wähler delegieren nach einer festen Regel** | Echte Wähler delegieren aus Sympathie, Bequemlichkeit oder Loyalität, nicht nur an den Fähigsten. | diese Demo (Regel „zufälliger besserer Bekannter“) |
| **Eine Schätzung ist unverzerrt** | Das Rauschen ist je Wähler fest und mittelwertfrei; bleibt ein guter Ruf auch ohne Leistung bestehen, entsteht Konzentration ohne Nutzen. | diese Demo (Reihe „Und bei falscher Einschätzung?“) |
| **Netz und Fähigkeit sind zufällig, nicht empirisch** | Die Netze sind Standardmodelle (Zufallsnetz, Nabenknoten, Ring); echte Netze und die Verbindung zwischen Bekanntheit und Fähigkeit können anders aussehen. | – |
| **Keine Obergrenze für Gewichte** | Verfahren mit Gewichtsgrenze oder mehreren Delegationswegen sind hier nicht umgesetzt. | – |
| **Modell, kein Befund über Abstimmungsplattformen** | Die Zahlen sagen, was die Rechnung für erzeugte oder eingegebene Szenarien liefert, nicht, wie eine bestimmte Plattform arbeitet. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Direktwahl.** Wähler $i \in \{1,\dots,n\}$ liegt unabhängig mit der Wahrscheinlichkeit $p_i$ richtig. Bei Gewichten $w_i \in \mathbb{N}_0$ mit $W = \sum_i w_i$ ist $X = \sum_i w_i B_i$ mit unabhängigen $B_i \sim \mathrm{Bernoulli}(p_i)$ das richtige Gewicht. Die Direktwahl hat $w_i = 1$.

**Richtige Mehrheit.**
$$P_{\text{richtig}} = \Pr[X > W/2] + \tfrac12 \Pr[X = W/2].$$
Die Verteilung von $X$ entsteht durch Faltung: $f_0 = 1$ und $f_{j}(x) = (1 - p_j)\, f_{j-1}(x) + p_j\, f_{j-1}(x - w_j)$.

**Delegation.** Wähler $i$ überträgt seine Stimme an $\tau(i)$, einen Bekannten mit $\tilde p_{\tau(i)} > p_i + \alpha$, wobei $\tilde p_j = p_j + \varepsilon_j$ die eingeschätzte Fähigkeit ist; Regel „fähigster“: das $j$ mit dem größten $\tilde p_j$. Kreise von Delegationen werden aufgelöst (die Wähler auf dem Kreis stimmen selbst ab). Das Gewicht $w_g$ eines Gurus $g$ ist die Zahl der Wähler, deren Kette bei $g$ endet, mit $\sum_g w_g = n$.

**Konzentration.** Größtes Gewicht $\max_g w_g$; effektive Zahl der Wähler $n_{\text{eff}} = 1 / \sum_i (w_i / n)^2$ (gleich $n$ bei Direktwahl, gleich $1$, wenn ein Wähler alle Stimmen trägt); Gini-Koeffizient der Gewichte über alle $n$ Wähler.

**Ein Guru allein.** Trägt ein Wähler mehr als die Hälfte der Stimmen, entscheidet er allein, und die Mehrheit liegt genau mit der Wahrscheinlichkeit $p_g$ richtig.

**Literatur** (aus dem Gedächtnis, nicht im Original geprüft): Kahng, Mackenzie, Procaccia, „Liquid Democracy: An Algorithmic Perspective“, AAAI 2018 und Journal of Artificial Intelligence Research 2021; Caragiannis und Micha, „Contribution Games in Social Networks“ und „A Contribution to the Critique of Liquid Democracy“, IJCAI 2019.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
