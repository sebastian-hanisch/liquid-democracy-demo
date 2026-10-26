"""Kern: Liquid Democracy. n Wähler entscheiden über eine Frage mit einer richtigen Antwort; jeder Wähler liegt mit seiner Fähigkeit (Trefferquote) richtig, unabhängig von den anderen. Direktwahl: jeder stimmt selbst ab, die Mehrheit
entscheidet. Delegation: jeder Wähler kann seine Stimme einem Nachbarn im Netz übertragen, der besser ist; Ketten werden bis zu einem Wähler verfolgt, der selbst abstimmt (dem „Guru“), dessen Stimme dann das Gewicht der
übertragenen Stimmen trägt. Die Wahrscheinlichkeit, dass die Mehrheit richtig liegt, wird EXAKT gerechnet (Faltung der unabhängigen Stimmen); alle Funktionen arbeiten mit Zahlen jeder Art (float oder Fraction)."""

from fractions import Fraction


def p_correct_weighted(comp, weights):
    """Wahrscheinlichkeit, dass das richtige Ergebnis mehr als die Hälfte des Gesamtgewichts erhält (bei genau der Hälfte zählt der Gleichstand halb). `weights[i]` ist das Gewicht des Wählers i (0: er stimmt nicht selbst ab);
    die Stimmen der Wähler mit Gewicht sind unabhängig und richtig mit der Wahrscheinlichkeit `comp[i]`."""
    if len(comp) != len(weights):
        raise ValueError("Fähigkeiten und Gewichte brauchen gleich viele Einträge")
    total = sum(weights)
    if total <= 0 or any(w < 0 or int(w) != w for w in weights):
        raise ValueError("Gewichte müssen nichtnegative ganze Zahlen mit positiver Summe sein")
    one = comp[0] * 0 + 1
    dist = [one] + [comp[0] * 0] * total
    for q, w in zip(comp, weights):
        if w == 0:
            continue
        new = [d * (1 - q) for d in dist]
        for k in range(total - w + 1):
            new[k + w] += dist[k] * q
        dist = new
    correct = sum(dist[k] for k in range(total + 1) if 2 * k > total)
    if total % 2 == 0:
        correct += dist[total // 2] * Fraction(1, 2) if isinstance(one, Fraction) else dist[total // 2] * 0.5
    return min(correct, one)          # Rundungsfehler der Gleitkommafaltung können knapp über 1 liegen


def p_correct_direct(comp):
    """Direktwahl: jeder Wähler hat das Gewicht 1."""
    return p_correct_weighted(comp, [1] * len(comp))


def break_cycles(target) -> list:
    """Wähler auf einem Kreis von Delegationen (A zu B zu A) stimmen selbst ab; die Ketten, die in den Kreis laufen, enden bei ihnen."""
    n = len(target)
    out = list(target)
    state = [0] * n          # 0 unbesucht, 1 auf dem aktuellen Weg, 2 fertig
    for start in range(n):
        if state[start]:
            continue
        path, node = [], start
        while node is not None and state[node] == 0:
            state[node] = 1
            path.append(node)
            node = out[node]
        if node is not None and state[node] == 1:                # Kreis gefunden: ab `node` im Weg
            for v in path[path.index(node):]:
                out[v] = None
        for v in path:
            state[v] = 2
    return out


def delegation_targets(adj, comp, perceived, alpha, rule, rng=None) -> list:
    """Ziel der Delegation je Wähler (None: stimmt selbst ab). Wähler i überträgt seine Stimme an einen Nachbarn j, dessen wahrgenommene Fähigkeit `perceived[j]` größer ist als die eigene wahre Fähigkeit plus `alpha`;
    Regel „best“: der Nachbar mit der größten wahrgenommenen Fähigkeit (Gleichstand: kleinere Nummer), Regel „zufall“: ein zufälliger solcher Nachbar (braucht `rng`)."""
    if rule not in ("best", "zufall"):
        raise ValueError(rule)
    target = [None] * len(comp)
    for i, neighbours in enumerate(adj):
        better = [j for j in neighbours if perceived[j] > comp[i] + alpha]
        if not better:
            continue
        if rule == "best":
            target[i] = max(better, key=lambda j: (perceived[j], -j))
        else:
            target[i] = better[int(rng.integers(len(better)))]
    return break_cycles(target)


def guru_weights(target) -> list:
    """Gewicht je Wähler: Zahl der Wähler (er selbst eingeschlossen), deren Delegationskette bei ihm endet; 0 für alle, die delegieren."""
    n = len(target)
    guru = [None] * n

    def find(i):
        path = []
        while guru[i] is None and target[i] is not None:
            path.append(i)
            i = target[i]
        root = guru[i] if guru[i] is not None else i
        for v in path:
            guru[v] = root
        guru[i] = root
        return root

    weight = [0] * n
    for i in range(n):
        weight[find(i)] += 1
    return weight


def chain_lengths(target) -> list:
    """Länge der Delegationskette je Wähler (0: stimmt selbst ab)."""
    n = len(target)
    length = [None] * n

    def find(i):
        path = []
        while length[i] is None and target[i] is not None:
            path.append(i)
            i = target[i]
        base = length[i] if length[i] is not None else 0
        length[i] = base
        for v in reversed(path):
            base += 1
            length[v] = base
        return length[path[0]] if path else length[i]

    return [find(i) for i in range(n)]


def concentration(weights) -> dict:
    """Wie ungleich die Stimmen verteilt sind: größtes Gewicht, Zahl der Gurus, Anteil der fünf größten Gewichte, effektive Zahl der Wähler (1 / Σ (w/n)²) und Gini-Koeffizient über alle Wähler."""
    n = sum(weights)
    ordered = sorted(weights)
    gurus = sum(1 for w in weights if w > 0)
    sq = sum(Fraction(w, n) ** 2 for w in weights)
    cum = sum((i + 1) * w for i, w in enumerate(ordered))
    gini = Fraction(2 * cum, len(weights) * n) - Fraction(len(weights) + 1, len(weights))
    return {"max": max(weights), "gurus": gurus, "top5": Fraction(sum(sorted(weights, reverse=True)[:5]), n), "effective": 1 / sq, "gini": gini}


def majority_weight(weights) -> Fraction:
    """Anteil des größten Gewichts am Gesamtgewicht."""
    return Fraction(max(weights), sum(weights))
