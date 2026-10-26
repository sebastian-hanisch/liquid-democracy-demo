"""Einmalige Messung der README-Zahlen (nicht Teil der App): feste Pläne, Ausgabe auf stdout. Alle Wahrscheinlichkeiten der richtigen Mehrheit sind exakt gerechnet (Faltung); die Reihen mitteln über Zufallsnetze mit festen Zufalls-Seeds."""

import sys
import time

sys.path.insert(0, ".")
import liq_constants as C
import liq_evaluation as ev

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

t0 = time.time()
print("PRESETS")
for name, p in C.PRESETS.items():
    a = ev.analyse(ev.Settings(**p))
    print(name, a.n, p["network"], p["alpha"], p["seed"])
    print("   ", ev.verdict_state(a))
    for r in ev.summary_rows(a):
        print("   ", r)

rows = ev.series_regime()
print("REIHE 1 (Delegation gegen Direktwahl je Netz und mittlerer Fähigkeit)")
for r in ev.regime_table(rows):
    print("   ", r)
print("   ", ev.verdict_regime(rows))
rows = ev.series_alpha()
print("REIHE 2 (Mindestabstand im Netz mit Nabenknoten)")
for r in ev.alpha_table(rows):
    print("   ", r)
print("   ", ev.verdict_alpha(rows))
rows = ev.series_noise()
print("REIHE 3 (Wahrnehmungsrauschen im Zufallsnetz)")
for r in ev.noise_table(rows):
    print("   ", r)
print("   ", ev.verdict_noise(rows))
print("sec", round(time.time() - t0, 1))
