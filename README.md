# Liquid Democracy: wann hilft Delegieren? – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-liquid-democracy-demo.streamlit.app/)** -->

Gelber Kandidat der Linie **Abstimmen und Fair Teilen** (Konzepte-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“). Verwandt: [mehrheitsurteil-demo](https://github.com/sebastian-hanisch/mehrheitsurteil-demo) (Mehrheit ohne Delegation, Jury-Satz, verschieden gute Gutachter), [wahlregeln-demo](https://github.com/sebastian-hanisch/wahlregeln-demo) (Regeln für Präferenzen) und [zufallsgremium-demo](https://github.com/sebastian-hanisch/zufallsgremium-demo) (Gremien per Los).
Die Demo fragt: **Eine Gruppe entscheidet über eine Frage mit einer richtigen Antwort. Jeder Wähler liegt mit seiner Fähigkeit richtig, unabhängig von den anderen, und darf seine Stimme an einen besseren Bekannten übertragen, der sie weiterreichen kann („Liquid Democracy“). Wann hebt das die Mehrheit, wann senkt es sie, und wie viele Stimmen sammeln sich bei wenigen Wählern?** Die Wahrscheinlichkeit, dass die Mehrheit richtig liegt, ist **exakt** gerechnet (Faltung der unabhängigen Stimmen); gemessen wird zusätzlich die **Gewichtskonzentration** (größtes Gewicht, effektive Zahl der Wähler, Gini-Koeffizient der Gewichte).

Der Kern ist eigener Code (`numpy` für Zufallsnetze und Fähigkeiten, die Mehrheit in Python mit Zahlen jeder Art). Unabhängige Orakel in den Tests: die **Aufzählung aller 2^g Ausgänge** der abstimmenden Wähler mit exakten Brüchen gegen die Faltung, das **einfache Nachlaufen der Delegationsketten** gegen die Gewichte, eine **Simulation** gegen die Faltung bei großer Gruppe.

## Warum dieses Problem

Die Delegation klingt nach „die Besseren entscheiden“, und bei einer schwachen Gruppe stimmt das auch: bei mittlerer Fähigkeit 52 % hebt sie die Mehrheit in drei Netzarten um **26 bis 31 Punkte** (Direktwahl 65 bis 66 %, Delegation 93 bis 96 %). Bei einer **starken** Gruppe kippt es: bei mittlerer Fähigkeit 62 % (Direktwahl 99 % und mehr) liegt die Delegation im Mittel im Netz mit Nabenknoten (−1,8 Punkte) und knapp im Zufallsnetz (−0,3) **darunter**, im Ring nicht (+0,3); bei 66 und 70 % liegt sie in allen drei Netzarten darunter oder gleichauf. Dazu passt, dass sich die Stimmen bei wenigen Wählern sammeln (die Ursache ist nicht isoliert gemessen): im Netz mit Nabenknoten trägt der größte Wähler im Mittel **28,5 von 101 Stimmen**, und liegt er falsch, fehlen der Mehrheit so viele Stimmen. Ein **Mindestabstand** von 10 Punkten (nur an deutlich bessere Bekannte delegieren) senkt im Netz mit Nabenknoten das größte Gewicht auf 16 und macht aus −1,7 im Mittel +0,3 Punkte (in 17 von 100 Netzen bleibt die Delegation schlechter). Schätzt man die Fähigkeit der Bekannten sehr ungenau ein (Rauschen doppelt so groß wie die Streuung), geht der Gewinn der schwachen Gruppe im Zufallsnetz fast verloren; bei Rauschen von 10 Punkten bleiben +10,7 von +13,1 Punkten.

## Modell

**Wähler.** n Wähler, Wähler i liegt unabhängig mit der Wahrscheinlichkeit p_i richtig (Fähigkeit). Erzeugt werden die p_i aus einer Beta-Verteilung mit der eingestellten Mitte und Streuung (auf 1 bis 99 % begrenzt, auf Promille gerundet) oder von Hand eingegeben.
**Netz.** Wer wen kennt: **Zufallsnetz** (jedes Paar mit Wahrscheinlichkeit 6/(n−1), im Mittel sechs Bekannte), **Nabenknoten** (bevorzugte Anbindung: jeder neue Wähler zieht drei Ziele mit Wahrscheinlichkeit proportional zu deren Verbindungen; doppelt gezogene Ziele zählen einmal, mittlerer Grad daher etwa 5,6), **Ring** (die sechs Nächsten) und **jeder kennt jeden**.
**Delegation.** Wähler i überträgt seine Stimme an einen Bekannten j mit eingeschätzter Fähigkeit p̃_j > p_i + α (Mindestabstand α); Regel „fähigster“: das j mit dem größten p̃_j (Gleichstand: kleinere Nummer), Regel „zufällig“: ein zufälliger solcher Bekannter. Die Einschätzung ist p̃_j = p_j + ε_j mit einem Rauschen ε_j je Wähler (für alle Bekannten gleich, wie ein Ruf).
**Ketten und Gewichte.** Die Stimme wandert weiter, bis sie bei einem Wähler ankommt, der nicht delegiert (dem **Guru**); Kreise werden aufgelöst (die Wähler auf dem Kreis stimmen selbst ab). Das Gewicht w_g eines Gurus ist die Zahl der Wähler, deren Kette bei ihm endet.
**Mehrheit.** Jeder Guru hat mit seiner **wahren** Fähigkeit recht, unabhängig von den anderen; die Mehrheit liegt richtig, wenn mehr als die Hälfte des Gewichts richtig liegt (bei genau der Hälfte zählt der Gleichstand halb). Formeln und Lesehilfe stehen im 📐-Expander der App.

## Methodik

- **Kern** (`liq_algorithm.py`): exakte Mehrheitswahrscheinlichkeit durch Faltung (für Gleitkommazahlen und Brüche), Kreise auflösen, Delegationsregel, Gewichte, Kettenlängen, Konzentrationsmaße.
- **Szenario und Auswertung** (`liq_scenario.py`, `liq_evaluation.py`): Netze und Fähigkeiten aus dem Zufalls-Seed, Texteingabe mit Prüfung, Tabellen, drei feste Reihen, alle Verdikte als reine Funktionen.
- **Oberfläche** (`app.py`): sechs Schnellstart-Szenarien (zwei von Hand nachgerechnet), Regler für Wähler, Fähigkeit, Streuung, Netz, Regel, Mindestabstand, Rauschen und Zufalls-Seed, Textfeld für eigene Fähigkeiten, das Netz der Delegationen, die größten Gewichte, Kernfrage, drei Reiter mit festen Reihen, Annahmen und Formeln.

## Befunde (gemessen, keine Behauptungen)

Alle Wahrscheinlichkeiten der richtigen Mehrheit sind **exakt** gerechnet. Die Reihen laufen auf **100 Zufallsnetzen** je Zeile mit **101 Wählern**, Streuung 15 Punkte und Delegation zum fähigsten besseren Bekannten, mit festen Zufalls-Seeds; die Zeilen zeigen Mittelwerte und gezählte Anteile. Die Reihen sind **voneinander unabhängige Stichproben**: dieselbe Einstellung kann in zwei Reihen um einige Zehntel bis etwa einen Punkt abweichen (Zufallsnetz, 62 %: −0,3 in Reihe 1 gegen −0,5 in Reihe 3; Nabenknoten, 55 %: +11,5 gegen +10,5).

| Frage | Befund | Test |
|---|---|---|
| Stimmt der Kern? | Die Faltung gleicht der **Aufzählung aller Ausgänge** mit exakten Brüchen auf 150 Zufallsfällen (bis 9 abstimmende Wähler, Gewichte 0 bis 4) und auf der ganzen Analyse bei 9 Wählern; die Gewichte gleichen dem einfachen Nachlaufen der Ketten auf 100 Zufallsnetzen; bei 41 Wählern weicht die Faltung von einer Simulation (40.000 Wiederholungen) um weniger als einen Punkt ab. | `test_oracle_liquid_democracy.py` |
| Von Hand: Ein Guru, fünf Stimmen | Vier Wähler mit 75 %, einer mit 78 %, alle kennen sich: Direktwahl **90,28125 %** (= 23112/25600), alle delegieren an den 78-Prozent-Wähler: **78 %**. | `test_algorithm.py::test_fünf_wähler_handrechnung_direktwahl`, `test_evaluation.py::test_handbeispiele_mit_exakten_werten` |
| Von Hand: Ein Guru, der hilft | Vier Wähler mit 60 %, einer mit 90 %: Direktwahl **78,624 %**, mit Delegation **90 %**. | `test_algorithm.py::test_fünf_wähler_handrechnung_mit_gutem_guru` |
| Wann hilft Delegieren? | Delegation gegen Direktwahl in Punkten (Zufallsnetz / Nabenknoten / Ring), mittlere Fähigkeit 52 %: **+30,2 / +26,4 / +31,1**; 55 %: +12,0 / +11,5 / +14,3; 58 %: +2,5 / +0,9 / +3,6; 62 %: **−0,3 / −1,8 / +0,3**; 66 %: −0,5 / −1,4 / −0,1; 70 %: −0,2 / −0,9 / 0,0. Insgesamt ist sie in **8 von 18** Zeilen im Mittel schlechter, in einer davon (Ring, 70 %) um weniger als 0,05 Punkte. Bei 70 % ist die Delegation in 100 von 100 Netzen schlechter (Zufallsnetz, Nabenknoten und Ring), im Ring allerdings nur um durchschnittlich 0,03 Punkte. | `test_claims.py::test_schwache_gruppe_gewinnt_in_jedem_netz_stark`, `…::test_starke_gruppe_verliert_in_jedem_netz`, `…::test_nabennetz_ist_bei_62_prozent_am_schädlichsten_der_ring_hilft_noch`, `…::test_verdikt_reihe_1` |
| Wie stark ist die Konzentration? | Mittleres größtes Gewicht von 101 Stimmen: Zufallsnetz **21,2 bis 23,1**, Nabenknoten **26,1 bis 30,0**, Ring **12,2 bis 13,0** (je nach mittlerer Fähigkeit). Der Ring hat in jeder Zeile das kleinste Gewicht, das Netz mit Nabenknoten das größte. | `test_claims.py::test_ring_hat_das_kleinste_größte_gewicht` |
| Hilft ein Mindestabstand? | Im Netz mit Nabenknoten sinkt das größte Gewicht mit dem Mindestabstand 0 / 5 / 10 / 15 / 20 Punkte von **28,5 / 19,8 / 16,0 / 11,9 / 9,0** (mittlere Fähigkeit 62 %); der Gewinn geht von **−1,7** auf **+0,7 Punkte**, der Anteil der Netze mit schlechterer Delegation von **79** auf **1 von 100**. Bei 55 % steigt der Gewinn von +10,5 auf +15,0 Punkte (Abstand 15) und fällt bei 20 Punkten leicht auf +14,7. | `test_claims.py::test_mindestabstand_senkt_das_größte_gewicht`, `…::test_bei_62_prozent_kippt_der_gewinn_mit_dem_mindestabstand`, `…::test_bei_55_prozent_hilft_ein_mittlerer_abstand_am_meisten` |
| Und bei falscher Einschätzung? | Im Zufallsnetz mit Rauschen 0 / 5 / 10 / 20 / 30 Punkte: bei mittlerer Fähigkeit 55 % sinkt der Gewinn von **+13,1** auf **+0,3 Punkte** (schlechter in 46 von 100 Netzen); bei 62 % geht er von **−0,5** auf **−7,2 Punkte** (schlechter in 99 von 100). | `test_claims.py::test_rauschen_frisst_den_gewinn_bei_55_prozent`, `…::test_rauschen_vertieft_den_verlust_bei_62_prozent` |
| Schnellstart-Szenarien | Voreinstellung (Zufallsnetz, 62 %, Seed 3): Direktwahl 99,6 %, Delegation 97,6 %, ein Wähler trägt 37 Stimmen. Delegieren hilft (55 %): 88,2 → 93,3 % (+5,1). Nabenknoten (Seed 32): 99,0 → **89,2 %** (−9,8), ein Wähler mit Fähigkeit 89 % trägt **57 von 101 Stimmen**. Dasselbe Netz mit Mindestabstand 10: größtes Gewicht **16**, Mehrheit 99,5 % (+0,6). Zwei Handbeispiele (90,3 → 78,0 und 78,6 → 90,0 %). | `test_evaluation.py::test_hilfetext_des_presets_stimmt_mit_der_rechnung`, `…::test_hub_presets_vorher_nachher` |
| Vormessung | Eine Vormessung vor dem Bau (300 Netze je Zeile, Wegwerfskript) zeigte denselben Sinn; **keine Zahl daraus** steht hier, alle Zahlen sind die der festen Reihen der Demo. | – |

## Ehrliche Grenzen

- **Es gibt eine richtige Antwort.** Bei Wertfragen („was wollen wir?“) gibt es keine Trefferquote; die Rechnung betrifft nur Wissensfragen mit überprüfbarem Ergebnis.
- **Die Wähler irren unabhängig.** Teilen sie Quellen oder Vorurteile, ist auch die Direktwahl schlechter, als hier gerechnet (siehe `mehrheitsurteil-demo`).
- **Der Guru irrt unabhängig von seinen Delegierenden.** In der Praxis überzeugen Gurus ihre Anhänger oft von ihrer Sicht, was Fehler verstärken würde.
- **Eine Fähigkeit je Wähler, eine Frage.** Echte Wähler sind bei einer Frage gut, bei einer anderen schlecht.
- **Delegiert wird nach einer festen Regel** (fähigster oder zufälliger besserer Bekannter); echte Wähler delegieren aus Sympathie, Bequemlichkeit oder Loyalität.
- **Das Rauschen ist ein Ruf je Wähler**, mittelwertfrei und für alle Bekannten gleich; ein Ruf, der unabhängig von der Leistung besteht, ist nicht modelliert.
- **Standardnetze, keine empirischen.** Zufallsnetz, Nabenknoten und Ring; echte Netze und der Zusammenhang zwischen Bekanntheit und Fähigkeit können anders aussehen.
- **Die Fähigkeit der Bekannten ist (verrauscht) beobachtbar.** Das ist die stärkste Annahme: ohne sie lässt sich nicht an „bessere“ delegieren.
- **Keine Obergrenze für Gewichte, kein Wählen über mehrere Wege.** Verfahren mit Gewichtsgrenze oder nicht-lokale Mechanismen sind nicht umgesetzt.
- **Reihen mit 100 Netzen je Zeile** und festen Zufalls-Seeds; Unterschiede von wenigen Zehntel Punkten liegen im Rahmen der Stichprobe.
- **Literatur** (aus dem Gedächtnis, nicht im Original geprüft): Kahng, Mackenzie, Procaccia, „Liquid Democracy: An Algorithmic Perspective“, AAAI 2018 und Journal of Artificial Intelligence Research 2021; Caragiannis und Micha, IJCAI 2019.

## Befunde und Korrekturen gegenüber dem Plan

- **Port:** 9200, Präfix `liq_`.
- **Plan:** „Liquid Democracy mit Gewichtskonzentration“; umgesetzt: Delegation im Netz, exakte Mehrheit, Konzentrationsmaße, drei Reihen (Wann hilft es? Hilft ein Mindestabstand? Und bei falscher Einschätzung?).
- **Die Vormessung meldete, Wahrnehmungsrauschen von 10 bis 20 Punkten kehre das Bild nicht um.** Die Demo rechnet es als **Ruf je Wähler** und misst: es kehrt das Bild bei 55 % tatsächlich nicht um (+0,3 Punkte bei 30 Punkten Rauschen, ein Gleichstand ist nicht auszuschließen), frisst aber den Gewinn fast ganz auf und vertieft bei 62 % den Verlust auf −7,2 Punkte.
- **Die Presets mit Nabenknoten** brauchen Zufalls-Seed 32: mit Seed 3 hilft die Delegation im selben Netz (ein Einzelfall); der gewählte Seed zeigt den häufigeren Ausgang, aber einen besonders deutlichen Fall (Mittel der Reihe im Netz mit Nabenknoten bei 62 %: −1,8 Punkte, 28,5 Stimmen); wie oft er eintritt, zeigen die Reihen.
- **Nabennetz:** ein neuer Wähler zieht drei Ziele; doppelt gezogene zählen einmal (mittlerer Grad etwa 5,6 statt 6). Das ist so im Test festgehalten.
- **Kappung:** die Gleitkommafaltung ergab bei großen, sehr starken Gruppen 1,0000000000000002; der Kern kappt auf 1.
- **Reglerspanne:** Wähler 3 bis 201, mittlere Fähigkeit 50 bis 80 %, Streuung 5 bis 20 Punkte, Mindestabstand 0 bis 20, Rauschen 0 bis 30 Punkte.

## Verifikation

- **Umfang:** 366 Tests.
- **Kern:** jede Einheit an Mini-Fällen von Hand (Wahrscheinlichkeiten 0,648; Gleichstand halb; Gewichte 2/1/1; Kreise, Ketten, Gini 5/8 von Hand und gegen den Paarvergleich).
- **Orakel:** Aufzählung aller Ausgänge, Nachlaufen der Ketten, Simulation (siehe Befunde).
- **Reihen und Texte:** jede Zahl dieser README in `tests/test_claims.py` (Richtungen und Bänder, nicht die letzte Stelle: die Zufallsströme von numpy können sich zwischen Versionen unterscheiden) und `tests/test_evaluation.py` (Hilfetexte der Presets, Verdikte und Tabellen als reine Funktionen), Randfälle und Adresszeile in `tests/test_edge_cases.py`.
- **Presets, Layout, Oberfläche:** wie in allen Demos (Presets vollständig und im Regelbereich, Schnellstart oben, aktives Preset hervorgehoben, AppTest jeder Button und jeder Regler an den Rändern, Footer, Laufzeit-Importe).
- **Mutationsprüfung** (`tools/mutate_demo.py`): 168 Stellen in Kern und Auswertung (`liq_algorithm.py`, `liq_evaluation.py`), **138 gefangen** (3 davon über wortgleiche Zeilen in Nachbar-Demos), **26 als äquivalent festgehalten**, **4 Mutanten mit Zeitüberschreitung** (Endlosschleife der Kreissuche in `break_cycles`; zählt nicht als gefangen). Äquivalent sind **25 Stellen der Zufalls-Seed-Rechnung der drei Reihen** (ein anderer fester Seed ist eine andere, ebenso gültige Stichprobe; die Tests prüfen Richtungen und Bänder, dazu, dass jeder Lauf einen eigenen Seed hat) und die **Nullprüfung der Gewichte** (ein Wähler ohne Gewicht ändert die Faltung nicht). Der erste Lauf (160 Stellen) ließ 38 überleben; **echte Lücken** waren: die Rangfolge der fünf größten Gewichte, ein negatives Gewicht bei positiver Summe, Vorzeichen und Größe des Rauschens, die Umrechnung des Mindestabstands von Punkten, die Zeilen der Wähler mit größtem Gewicht, das Vorzeichen in der Reihentabelle, mehrere Schwellen und Zahlen der Verdikte (an handgesetzten Zeilen) und die Zahl der Läufe je Reihe (je ein neuer Test).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `liq_algorithm.py` | Kern: Mehrheit (Faltung), Kreise, Delegation, Gewichte, Konzentration |
| `liq_constants.py` | Regler-Grenzen, feste Reihen, Farben, Presets |
| `liq_evaluation.py` | Analyse, Tabellen, Verdikte, drei feste Reihen |
| `liq_layout.py` | Fester Kopf (Stylesheet) |
| `liq_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `liq_scenario.py` | Netze, Fähigkeiten, Texteingabe |
| `liq_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `messen.py` | Einmalige Messung der Zahlen in dieser README (nicht Teil der App) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Kern, Orakel, Reihen und Claims, Auswertung und Presets, Randfälle, Szenario, Abbildungen, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Quadratisches Wählen** (Stimmen kosten quadratisch viel Guthaben): eigenes Thema mit eigener Rechnung.
- **Nicht-lokale Verfahren** (Kahng u. a.: ein Mechanismus, der Delegation begrenzt oder Wähler gezielt zuweist) und **Gewichtsgrenzen**: würden die Konzentration beheben, aber hier ist die Frage, was die einfache Delegation tut.
- **Abhängige Irrtümer der Wähler**, **mehrere Fragen**, **Delegation nach Themen**: die Rechnung würde dann nicht mehr exakt gefaltet.
- **Verhaltensmodelle** (Sympathie, Loyalität) und **empirische Netze**: keine Daten.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und NumPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
