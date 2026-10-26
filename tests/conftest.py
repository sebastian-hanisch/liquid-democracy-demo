"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def five():
    """Fünf Wähler, die sich alle kennen: Fähigkeiten 78, 75, 75, 75, 75 %. Handrechnung: bei Direktwahl liegt die Mehrheit in 0,90 (siehe test_algorithm), wenn alle an Wähler 0 delegieren, in 0,78."""
    comp = [0.78, 0.75, 0.75, 0.75, 0.75]
    adj = [[j for j in range(5) if j != i] for i in range(5)]
    return comp, adj
