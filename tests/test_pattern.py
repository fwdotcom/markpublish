"""
Tests fuer die Pattern-Sprache: Grammatik, Ebenenzuordnung, Zurueckweisungen.
"""

from __future__ import annotations

import pytest

from markpublish.markdown.pattern import (
    LEVEL_CHAPTER,
    LEVEL_PART,
    NumSlot,
    PatternChain,
    PatternError,
    SkipSlot,
    compile_pattern,
    int_to_alpha,
    int_to_roman,
)


def _numbers(source: str, scope: str, upto: int = 3) -> list:
    """Nummern der Ebenen ab der Basis, jede Ebene einmal betreten."""
    pattern = compile_pattern(source, scope)
    counters: dict = {}
    out = []
    for level in range(pattern.base_level, pattern.base_level + upto):
        counters[level] = counters.get(level, 0) + 1
        out.append(pattern.render(level, counters))
    return out


# ---------------------------------------------------------------------------
# Symbole
# ---------------------------------------------------------------------------

def test_roman_numerals():
    assert int_to_roman(1) == "I"
    assert int_to_roman(4) == "IV"
    assert int_to_roman(9) == "IX"
    assert int_to_roman(2026) == "MMXXVI"


def test_alpha_runs_past_z():
    assert int_to_alpha(1) == "a"
    assert int_to_alpha(26) == "z"
    assert int_to_alpha(27) == "aa"


@pytest.mark.parametrize(
    "source, expected",
    [
        ("1|.1|+", ["1", "1.1", "1.1.1"]),
        ("1.|1.|+", ["1.", "1.1.", "1.1.1."]),
        ("I|.1|+", ["I", "I.1", "I.1.1"]),
        ("I|.1|.a", ["I", "I.1", "I.1.a"]),
        ("01|.01|+", ["01", "01.01", "01.01.01"]),
        ("_|1|.1|+", [None, "1", "1.1"]),
        ("'Kapitel '1", ["Kapitel 1", None, None]),
    ],
)
def test_patterns_from_the_spec(source, expected):
    """Die Beispieltabelle der Spezifikation, im `parts`-Block notiert."""
    assert _numbers(source, "part") == expected


def test_quoted_literals_keep_reserved_characters():
    """`A` und `i` sind Symbole - woertlich gemeint gehoeren sie in Hochkommas."""
    assert _numbers("'Artikel '1|' ('1')'", "part", upto=2) == [
        "Artikel 1",
        "Artikel 1 (1)",
    ]


def test_a_doubled_quote_is_one_apostrophe():
    assert _numbers("'''s '1", "part", upto=1) == ["'s 1"]


# ---------------------------------------------------------------------------
# Ebenen
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "scope, base",
    [("document", LEVEL_PART), ("part", LEVEL_CHAPTER), ("chapter", LEVEL_CHAPTER + 1)],
)
def test_slot_one_sits_below_the_place_the_pattern_stands(scope, base):
    assert compile_pattern("1|.1", scope).base_level == base


def test_the_part_number_stays_out_of_everything_below_it():
    """
    Slot 1 eines document-Patterns zaehlt fuer sich: die Kapitelnummer traegt
    ihn nicht, sonst haetten Kapitel je nach Sichtbarkeit ihres Parts andere
    Nummern.
    """
    assert _numbers("I|1|.1|+", "document") == ["I", "1", "1.1"]


def test_a_continuation_fills_every_deeper_level():
    pattern = compile_pattern("1|.1|+", "part")
    assert pattern.last_level == 6
    assert isinstance(pattern.slot_for(6), NumSlot)


def test_a_skipped_level_holds_no_counter():
    pattern = compile_pattern("_|1|.1|+", "part")
    assert isinstance(pattern.slot_for(LEVEL_CHAPTER), SkipSlot)
    assert not pattern.numbers(LEVEL_CHAPTER)


def test_levels_beyond_the_last_slot_get_nothing():
    pattern = compile_pattern("1|.1", "part")
    assert pattern.slot_for(4) is None
    assert pattern.render(4, {1: 1, 2: 1, 3: 1, 4: 1}) is None


# ---------------------------------------------------------------------------
# Kaskade
# ---------------------------------------------------------------------------

def test_the_innermost_place_that_notes_something_wins():
    chain = PatternChain(
        document=compile_pattern("I|1|.1|+", "document"),
        part=compile_pattern("A|.1|+", "part"),
    )
    assert chain.for_level(LEVEL_PART).base_level == LEVEL_PART
    assert chain.for_level(LEVEL_CHAPTER).base_level == LEVEL_CHAPTER


def test_a_chapter_cannot_switch_off_its_own_number():
    """
    `none` am Kapitel schaltet ab, was das Kapitel beschreibt - also h2 und
    tiefer. Seine eigene Nummer kommt aus dem Part und bleibt.
    """
    chain = PatternChain(
        document=compile_pattern("_|1|.1|+", "document"),
        chapter=None,
    )
    assert chain.for_level(LEVEL_CHAPTER) is not None
    assert chain.for_level(LEVEL_CHAPTER + 1) is None


def test_a_place_that_notes_nothing_is_skipped():
    chain = PatternChain(document=compile_pattern("_|1|.1|+", "document"))
    assert chain.for_level(4) is not None


# ---------------------------------------------------------------------------
# Zurueckweisungen
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "source, scope, reason",
    [
        ("1||.1", "part", "empty slot"),
        ("1|'x", "part", "never closed"),
        ("1|..", "part", "no symbol"),
        ("1|.1a", "part", "more than one symbol"),
        ("1|.0", "part", "not a valid decimal"),
        ("+|1", "part", "first slot"),
        ("1|+|.1", "part", "must be the last slot"),
        ("_|+", "part", "follows '_'"),
        ("1|_", "part", "redundant"),
        ("I|+", "document", "follows the part slot"),
        ("1|.1|.1|.1|.1|.1", "chapter", "at most 5"),
        ("1|.1|.1|.1|.1|.1|.1|.1", "document", "at most 7"),
    ],
)
def test_a_broken_pattern_aborts_with_its_reason(source, scope, reason):
    """
    Kein stiller Rueckfall auf einen Standardwert: ein Tippfehler nummerierte
    sonst unbemerkt das ganze Dokument falsch.
    """
    with pytest.raises(PatternError, match=reason):
        compile_pattern(source, scope)


@pytest.mark.parametrize("source", [None, "", "none", "NONE"])
def test_no_pattern_means_no_numbers(source):
    assert compile_pattern(source, "document") is None
