"""Orakel: unabhängige Gegenprobe. Bei wenigen Wählern werden ALLE 2^g Ausgänge der Gurus aufgezählt (exakte Brüche), ohne die Faltung des Kerns; die Delegation wird mit einem einfachen Nachlaufen der Ketten gegengerechnet."""

import itertools
import random
from fractions import Fraction as F

import numpy as np

import liq_algorithm as A
import liq_evaluation as ev


def enumerated(comp, weights):
    """P(mehr als die Hälfte des Gewichts richtig), Gleichstand halb, durch Aufzählen aller Ausgänge der Wähler mit Gewicht."""
    voters = [(q, w) for q, w in zip(comp, weights) if w > 0]
    total = sum(w for _, w in voters)
    result = F(0)
    for outcome in itertools.product((0, 1), repeat=len(voters)):
        prob = F(1)
        right = 0
        for (q, w), hit in zip(voters, outcome):
            prob *= q if hit else 1 - q
            right += w * hit
        if 2 * right > total:
            result += prob
        elif 2 * right == total:
            result += prob / 2
    return result


def test_faltung_gegen_aufzählung_zufällige_gewichte():
    rng = random.Random(11)
    for _ in range(150):
        g = rng.randint(1, 9)
        comp = [F(rng.randint(1, 99), 100) for _ in range(g)]
        weights = [rng.randint(0, 4) for _ in range(g)]
        if sum(weights) == 0:
            continue
        assert A.p_correct_weighted(comp, weights) == enumerated(comp, weights)


def test_direktwahl_gegen_aufzählung():
    rng = random.Random(12)
    for n in range(1, 11):
        comp = [F(rng.randint(1, 99), 100) for _ in range(n)]
        assert A.p_correct_direct(comp) == enumerated(comp, [1] * n)


def follow(target, i):
    while target[i] is not None:
        i = target[i]
    return i


def test_gewichte_gegen_nachlaufen_auf_zufallsnetzen():
    rng = random.Random(13)
    for _ in range(100):
        n = rng.randint(3, 20)
        comp = [rng.random() for _ in range(n)]
        perceived = [c + rng.gauss(0, 0.2) for c in comp]
        adj = [sorted(rng.sample([j for j in range(n) if j != i], rng.randint(1, min(5, n - 1)))) for i in range(n)]
        target = A.delegation_targets(adj, comp, perceived, rng.choice([0.0, 0.05, 0.1]), "best")
        expected = [0] * n
        for i in range(n):
            expected[follow(target, i)] += 1
        assert A.guru_weights(target) == expected


def test_analyse_stimmt_mit_aufzählung_bei_wenigen_wählern():
    for seed in range(8):
        a = ev.analyse(ev.Settings(n=9, mean=60, sd=12, network="zufall", alpha=0, noise=0, seed=seed))
        comp = [F(round(c * 1000), 1000) for c in a.comp]
        assert abs(a.direct - float(enumerated(comp, [1] * 9))) < 1e-12
        assert abs(a.liquid - float(enumerated(comp, a.weights))) < 1e-12


def test_gleichverteilte_fähigkeit_monte_carlo_gegen_exakt():
    """Die Faltung stimmt mit einer Simulation überein (große Gruppe, Aufzählen unmöglich)."""
    rng = np.random.default_rng(3)
    comp = list(rng.uniform(0.45, 0.8, size=41))
    exact = A.p_correct_direct(comp)
    votes = rng.random((40000, 41)) < np.array(comp)
    mc = float(np.mean(votes.sum(axis=1) > 20))
    assert abs(exact - mc) < 0.01
