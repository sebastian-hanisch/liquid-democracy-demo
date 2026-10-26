"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 3, 201, 101              # Wähler
MEAN_MIN, MEAN_MAX, DEFAULT_MEAN = 50, 80, 62      # mittlere Fähigkeit in %
SD_MIN, SD_MAX, DEFAULT_SD = 5, 20, 15             # Streuung der Fähigkeit in Prozentpunkten
ALPHA_MIN, ALPHA_MAX, DEFAULT_ALPHA = 0, 20, 0     # Mindestabstand für eine Delegation in Punkten
NOISE_MIN, NOISE_MAX, DEFAULT_NOISE = 0, 30, 0     # Wahrnehmungsrauschen der Fähigkeit in Punkten
SEED_MAX, DEFAULT_SEED = 9999, 3
COMP_TEXT_MIN, COMP_TEXT_MAX = 3, 201              # eigene Fähigkeiten: Zahl der Wähler

NETWORKS = {
    "zufall": "Zufallsnetz (jeder kennt im Mittel sechs)",
    "hub": "Netz mit Nabenknoten (einige kennen sehr viele)",
    "lokal": "Ring (jeder kennt die sechs Nächsten)",
    "voll": "Jeder kennt jeden",
}
NETWORK_SHORT = {"zufall": "Zufallsnetz", "hub": "Nabenknoten", "lokal": "Ring", "voll": "Jeder kennt jeden"}
DEFAULT_NETWORK = "zufall"
RING_REACH = 3                                      # Ring: so viele Nachbarn je Seite
HUB_LINKS = 3                                       # Nabennetz: neue Wähler ziehen so viele Ziele (doppelte zählen einmal)
MEAN_DEGREE = 6                                     # Zufallsnetz: mittlerer Grad

RULES = {
    "best": "Zum fähigsten besseren Nachbarn",
    "zufall": "Zu einem zufälligen besseren Nachbarn",
}
RULE_SHORT = {"best": "fähigster Nachbar", "zufall": "zufälliger Nachbar"}
DEFAULT_RULE = "best"

COLOR_DIRECT = "#4c78a8"
COLOR_LIQUID = "#b04a3a"
COLOR_GOOD = "#2F6B65"
COLOR_ALERT = "#c0392b"

# Feste Reihen (Zufallsnetze mit festen Zufalls-Seeds; Wahrscheinlichkeiten exakt gerechnet, Anteile gezählt)
SERIES_SEED = 500000
SERIES_RUNS = 100
SERIES_N = 101
SERIES_MEANS = (52, 55, 58, 62, 66, 70)
SERIES_NETWORKS = ("zufall", "hub", "lokal")
SERIES_ALPHAS = (0, 5, 10, 15, 20)
SERIES_NOISES = (0, 5, 10, 20, 30)
SERIES_MEANS_FOCUS = (55, 62)

NL = chr(10)

PRESETS = {
    "Zufallsnetz, mittlere Fähigkeit 62 %": {"n": 101, "mean": 62, "sd": 15, "network": "zufall", "alpha": 0, "noise": 0, "rule": "best", "seed": 3, "comp": ""},
    "Delegieren hilft": {"n": 101, "mean": 55, "sd": 15, "network": "zufall", "alpha": 0, "noise": 0, "rule": "best", "seed": 3, "comp": ""},
    "Nabenknoten sammeln Stimmen": {"n": 101, "mean": 62, "sd": 15, "network": "hub", "alpha": 0, "noise": 0, "rule": "best", "seed": 32, "comp": ""},
    "Mindestabstand begrenzt den Schaden": {"n": 101, "mean": 62, "sd": 15, "network": "hub", "alpha": 10, "noise": 0, "rule": "best", "seed": 32, "comp": ""},
    "Ein Guru, fünf Stimmen": {"n": 5, "mean": 62, "sd": 15, "network": "voll", "alpha": 0, "noise": 0, "rule": "best", "seed": 3, "comp": "78, 75, 75, 75, 75"},
    "Ein Guru, der hilft": {"n": 5, "mean": 62, "sd": 15, "network": "voll", "alpha": 0, "noise": 0, "rule": "best", "seed": 3, "comp": "90, 60, 60, 60, 60"},
}
PRESET_HELP = {
    "Zufallsnetz, mittlere Fähigkeit 62 %": "Voreinstellung: 101 Wähler in einem Zufallsnetz, im Mittel 62 % Trefferquote; jeder delegiert an den fähigsten besseren Nachbarn. Die Direktwahl liegt schon bei 99,6 %, die Delegation darunter bei 97,6 %: ein Wähler trägt 37 Stimmen.",
    "Delegieren hilft": "Mittlere Fähigkeit 55 %: die Direktwahl liegt bei 88,2 %, die Delegation hebt die Mehrheit auf 93,3 % (+5,1 Punkte).",
    "Nabenknoten sammeln Stimmen": "Im Netz mit Nabenknoten sammelt ein Wähler (Fähigkeit 89 %) 57 von 101 Stimmen: die Mehrheit liegt in 89,2 % richtig statt in 99,0 % bei Direktwahl (−9,8 Punkte).",
    "Mindestabstand begrenzt den Schaden": "Dasselbe Netz, aber wer nur an Nachbarn delegiert, die mindestens zehn Punkte besser sind: das größte Gewicht sinkt von 57 auf 16, die Mehrheit liegt in 99,5 % richtig statt in 99,0 % bei Direktwahl (+0,6 Punkte).",
    "Ein Guru, fünf Stimmen": "Fünf Wähler kennen sich alle; vier haben 75 %, einer 78 %. Alle delegieren an den 78-Prozent-Wähler: die Mehrheit liegt nur noch in 78,0 % richtig statt in 90,3 % bei Direktwahl.",
    "Ein Guru, der hilft": "Vier Wähler mit 60 %, einer mit 90 %: alle delegieren an ihn, die Mehrheit liegt in 90,0 % richtig statt in 78,6 % bei Direktwahl.",
}
