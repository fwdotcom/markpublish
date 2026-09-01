"""
Tests for TOC extraction and autonumbering.
"""

from pathlib import Path

from markpublish.config.loader import load_config
from markpublish.config.models import AutonumType
from markpublish.markdown.engine import MarkdownPipeline
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



def _write(tmp_path, name, body):
    (tmp_path / name).write_text(body, encoding="utf-8")


DEEP_MD = "# Kapitel\n\nText.\n\n## Ebene zwei\n\nText.\n\n### Ebene drei\n\nText.\n"


def _tree_titles(nodes, out=None):
    """Flache Liste aus (level, titel) - fuer Zusicherungen ueber das globale TOC."""
    out = [] if out is None else out
    for n in nodes:
        out.append((n.level, n.title))
        _tree_titles(n.children, out)
    return out


def test_toc_depth_limits_what_a_chapter_adds_to_the_global_toc(tmp_path: Path):
    """
    `toc_depth` kuerzt den Beitrag zum globalen Inhaltsverzeichnis, ohne den
    Fliesstext anzutasten: die Zwischenueberschriften stehen weiterhin im
    Kapitel, nur eben nicht mehr im Verzeichnis davor.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        'document:\n  title: "T"\nchapters:\n'
        '  - file: "deep.md"\n    title: "Voll"\n'
        '  - file: "deep.md"\n    title: "Gekuerzt"\n    toc_depth: 2\n',
    )

    config = load_config(tmp_path / "markpublish.yaml")
    items, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    titles = _tree_titles(tree)
    assert titles.count((3, "Ebene drei")) == 1, "nur das ungekuerzte Kapitel liefert die dritte Ebene"
    assert titles.count((2, "Ebene zwei")) == 2, "die zweite Ebene bleibt in beiden Kapiteln"

    # Der Text selbst bleibt vollstaendig - gekuerzt wird ausschliesslich das TOC.
    assert "Ebene drei" in items[1].html_content


def test_toc_depth_on_a_part_reaches_every_chapter_below_it(tmp_path: Path):
    """
    Der Anwendungsfall, fuer den es die Option gibt: eine Zeile am Anhang-Part
    haelt saemtliche Anhaenge im Inhaltsverzeichnis flach.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        'document:\n  title: "T"\nchapters:\n'
        '  - part: "Anhaenge"\n    toc_depth: 1\n    chapters:\n'
        '      - file: "deep.md"\n        title: "Anhang A"\n'
        '      - file: "deep.md"\n        title: "Anhang B"\n',
    )

    config = load_config(tmp_path / "markpublish.yaml")
    _, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    titles = [t for _, t in _tree_titles(tree)]
    assert "Anhaenge" in titles
    assert titles.count("Kapitel") == 2, "beide Anhaenge stehen mit ihrer Ueberschrift im TOC"
    assert "Ebene zwei" not in titles
    assert "Ebene drei" not in titles


def test_toc_depth_one_keeps_sub_chapters_but_drops_their_headings(tmp_path: Path):
    """
    Vererbung gilt pro Kapitel, nicht ueber die zusammengelegte Liste: ein
    Unterkapitel behaelt seinen eigenen Eintrag, verliert aber die Ebenen
    darunter. Wuerde ueber die Gesamtliste gefiltert, fiele das Unterkapitel
    selbst mit heraus.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        'document:\n  title: "T"\nchapters:\n'
        '  - file: "deep.md"\n    title: "Oben"\n    toc_depth: 1\n    chapters:\n'
        '      - file: "deep.md"\n        title: "Unten"\n',
    )

    config = load_config(tmp_path / "markpublish.yaml")
    _, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    levels = [lvl for lvl, _ in _tree_titles(tree)]
    assert levels == [1, 2], "Kapitel und Unterkapitel, sonst nichts"


def test_toc_depth_defaults_to_the_full_depth(tmp_path: Path):
    """Ohne Angabe aendert sich nichts - das ist das bisherige Verhalten."""
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        'document:\n  title: "T"\nchapters:\n  - file: "deep.md"\n    title: "Voll"\n',
    )

    config = load_config(tmp_path / "markpublish.yaml")
    _, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert [lvl for lvl, _ in _tree_titles(tree)] == [1, 2, 3]
