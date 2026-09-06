"""
Gemeinsame Vorbedingungen fuer die Testsuite.

Die eine, die alle betrifft: die Sprache der Programmoberflaeche steht fest.
Ohne sie haengt jede Zusicherung auf einen Meldungstext an der Systemsprache
des Rechners, auf dem die Suite gerade laeuft -- und ein Test, der in Berlin
gruen und in Dublin rot ist, sagt nichts ueber den Code aus.

Englisch, weil es die Fallback-Sprache ist und damit die einzige, die
garantiert jeden Schluessel fuehrt. Wer eine deutsche Meldung pruefen will,
setzt die Sprache im Test ausdruecklich um (siehe test_ui.py).
"""

from __future__ import annotations

import pytest

from markpublish import ui


@pytest.fixture(autouse=True)
def fixed_ui_language(monkeypatch):
    """Nagelt die Oberflaechensprache auf Englisch fest."""
    monkeypatch.setenv(ui.UI_ENV_VAR, "en")
    monkeypatch.setattr(ui, "_language", "en")
    yield
