"""
Tests for TOC extraction and autonumbering.
"""

from markpublish.config.models import AutonumType
from markpublish.markdown.toc import (
    NumberingContext,
    int_to_roman,
    process_html_headings_and_toc,
)


def test_roman_numerals():
    assert int_to_roman(1) == "I"
    assert int_to_roman(4) == "IV"
    assert int_to_roman(9) == "IX"
    assert int_to_roman(10) == "X"


def test_autonumbering_decimal():
    ctx = NumberingContext(default_autonum_type=AutonumType.DECIMAL)

    html = """
<h1>First Chapter</h1>
<h2>First Section</h2>
<h3>Sub Section</h3>
<h2>Second Section</h2>
<h1>Second Chapter</h1>
"""
    processed, nodes = process_html_headings_and_toc(html, ctx)

    assert '<span class="heading-number">1</span>' in processed
    assert '<span class="heading-number">1.1</span>' in processed
    assert '<span class="heading-number">1.1.1</span>' in processed
    assert '<span class="heading-number">1.2</span>' in processed
    assert '<span class="heading-number">2</span>' in processed

    assert len(nodes) == 5
    assert nodes[0].number == "1"
    assert nodes[1].number == "1.1"
    assert nodes[2].number == "1.1.1"
    assert nodes[3].number == "1.2"
    assert nodes[4].number == "2"


def test_autonumbering_none():
    ctx = NumberingContext(default_autonum_type=AutonumType.NONE)
    html = "<h1>Unnumbered Chapter</h1>"
    processed, nodes = process_html_headings_and_toc(html, ctx)
    assert '<span class="heading-number">' not in processed
    assert nodes[0].number is None

