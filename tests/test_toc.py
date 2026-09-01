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


def test_document_toc_limits_what_a_chapter_adds_to_the_global_toc(tmp_path: Path):
    """
    `document_toc` kuerzt den Beitrag zum globalen Inhaltsverzeichnis, ohne den
    Fliesstext anzutasten: die Zwischenueberschriften stehen weiterhin im
    Kapitel, nur eben nicht im Verzeichnis davor.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        'document:\n  title: "T"\nchapters:\n'
        '  - file: "deep.md"\n    title: "Voll"\n'
        '  - file: "deep.md"\n    title: "Gekuerzt"\n    document_toc: 2\n',
    )

    config = load_config(tmp_path / "markpublish.yaml")
    items, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    titles = _tree_titles(tree)
    assert titles.count((3, "Ebene drei")) == 1, "nur das ungekuerzte Kapitel liefert die dritte Ebene"
    assert titles.count((2, "Ebene zwei")) == 2, "die zweite Ebene bleibt in beiden Kapiteln"

    # Der Text selbst bleibt vollstaendig - gekuerzt wird ausschliesslich das TOC.
    assert "Ebene drei" in items[1].html_content


def test_document_toc_on_a_part_reaches_every_chapter_below_it(tmp_path: Path):
    """
    Der Anwendungsfall, fuer den es die Option gibt: eine Zeile am Anhang-Part
    haelt saemtliche Anhaenge im Inhaltsverzeichnis flach.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        'document:\n  title: "T"\nchapters:\n'
        '  - part: "Anhaenge"\n    document_toc: 1\n    chapters:\n'
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


def test_document_toc_one_keeps_sub_chapters_but_drops_their_headings(tmp_path: Path):
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
        '  - file: "deep.md"\n    title: "Oben"\n    document_toc: 1\n    chapters:\n'
        '      - file: "deep.md"\n        title: "Unten"\n',
    )

    config = load_config(tmp_path / "markpublish.yaml")
    _, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    levels = [lvl for lvl, _ in _tree_titles(tree)]
    assert levels == [1, 2], "Kapitel und Unterkapitel, sonst nichts"


def test_document_toc_defaults_to_the_full_depth(tmp_path: Path):
    """Ohne Angabe gilt volle Tiefe: jede Ueberschrift steht im Verzeichnis."""
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        'document:\n  title: "T"\nchapters:\n  - file: "deep.md"\n    title: "Voll"\n',
    )

    config = load_config(tmp_path / "markpublish.yaml")
    _, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert [lvl for lvl, _ in _tree_titles(tree)] == [1, 2, 3]


def test_document_toc_none_keeps_a_chapter_out_of_the_document_toc(tmp_path: Path):
    """
    'none' ist mehr als Tiefe 0: das Kapitel erscheint gar nicht im vorderen
    Verzeichnis - fuer Vorworte, Kolophone und aehnliches, die im Text stehen
    sollen, aber nicht in der Gliederung.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        'document:\n  title: "T"\nchapters:\n'
        '  - file: "deep.md"\n    title: "Sichtbar"\n'
        '  - file: "deep.md"\n    title: "Versteckt"\n    document_toc: "none"\n',
    )

    config = load_config(tmp_path / "markpublish.yaml")
    items, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert len(_tree_titles(tree)) == 3, "nur der Baum des ersten Kapitels"

    # Der Fliesstext bleibt: ausgeblendet wird das Verzeichnis, nicht das Kapitel.
    assert len(items) == 2
    assert "Ebene zwei" in items[1].html_content


def test_document_toc_full_overrides_what_a_part_handed_down(tmp_path: Path):
    """
    Genau dafuer gibt es das Schluesselwort: ohne 'full' muesste man eine
    willkuerlich grosse Zahl hinschreiben, um das Geerbte aufzuheben.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        'document:\n  title: "T"\nchapters:\n'
        '  - part: "Anhaenge"\n    document_toc: 1\n    chapters:\n'
        '      - file: "deep.md"\n        title: "Flach"\n'
        '      - file: "deep.md"\n        title: "Vollstaendig"\n        document_toc: "full"\n',
    )

    config = load_config(tmp_path / "markpublish.yaml")
    _, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    titles = [t for _, t in _tree_titles(tree)]
    # Das geerbte Kapitel liefert nur seine Ueberschrift, das andere alles.
    assert titles.count("Ebene zwei") == 1
    assert titles.count("Ebene drei") == 1


def test_chapter_toc_full_lists_every_level_below_the_chapter(tmp_path: Path):
    """
    'full' im kleinen Verzeichnis heisst: alles unterhalb der eigenen
    Ueberschrift - die eigene bleibt draussen, sie steht auf der Trennseite
    bereits als Titel darueber.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        'document:\n  title: "T"\nchapters:\n'
        '  - file: "deep.md"\n    title: "Voll"\n    chapter_toc: "full"\n'
        '  - file: "deep.md"\n    title: "Flach"\n    chapter_toc: 2\n',
    )

    config = load_config(tmp_path / "markpublish.yaml")
    items, _ = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert [n.title for n in items[0].local_toc_items] == ["Ebene zwei", "Ebene drei"]
    assert [n.title for n in items[1].local_toc_items] == ["Ebene zwei"]


def test_document_chapter_toc_is_the_root_for_chapters(tmp_path: Path):
    """
    `document.chapter_toc` steht zu `chapters.chapter_toc` wie `autonum_type` zu
    `autonum`: die Vorgabe oben, der Einzelfall unten. Ohne sie wiederholt ein
    Dokument mit zehn Kapiteln zehnmal dieselbe Zeile.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        'document:\n  title: "T"\n  chapter_toc: 2\nchapters:\n'
        '  - file: "deep.md"\n    title: "Erbt"\n'
        '  - file: "deep.md"\n    title: "Voll"\n    chapter_toc: "full"\n'
        '  - file: "deep.md"\n    title: "Keins"\n    chapter_toc: "none"\n',
    )

    config = load_config(tmp_path / "markpublish.yaml")
    items, _ = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert [n.title for n in items[0].local_toc_items] == ["Ebene zwei"]
    assert [n.title for n in items[1].local_toc_items] == ["Ebene zwei", "Ebene drei"]
    assert items[2].local_toc_items == []


def test_document_chapter_toc_defaults_to_none(tmp_path: Path):
    """Ohne Vorgabe bleibt es beim bisherigen Verhalten: keine Kapitel-TOCs."""
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        'document:\n  title: "T"\nchapters:\n  - file: "deep.md"\n    title: "K"\n',
    )

    config = load_config(tmp_path / "markpublish.yaml")
    items, _ = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert items[0].local_toc_items == []


def _tree_numbers(nodes, out=None):
    """[(titel, nummer)] in Dokumentreihenfolge."""
    out = [] if out is None else out
    for n in nodes:
        out.append((n.title, n.number))
        _tree_numbers(n.children, out)
    return out


def test_autonum_none_on_a_part_reaches_every_chapter_below_it(tmp_path: Path):
    """
    Die Angabe steht am Part, die Ueberschriften stehen in den Kapiteldateien -
    ohne Vererbung waere `autonum: "none"` am Anhang-Part wirkungslos und die
    Anhaenge zaehlten den Kapitelzaehler weiter.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        'document:\n  title: "T"\nchapters:\n'
        '  - file: "deep.md"\n    title: "Eins"\n'
        '  - part: "Anhaenge"\n    autonum: "none"\n    chapters:\n'
        '      - file: "deep.md"\n        title: "Anhang A"\n'
        '      - file: "deep.md"\n        title: "Anhang B"\n'
        '  - file: "deep.md"\n    title: "Danach"\n',
    )

    config = load_config(tmp_path / "markpublish.yaml")
    _, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    numbers = _tree_numbers(tree)

    assert numbers[0] == ("Kapitel", "1")

    # Im Anhang traegt nichts eine Nummer - weder Kapitel- noch
    # Zwischenueberschriften. Der Part selbst ist ohnehin unnummeriert.
    part_at = next(i for i, (t, _) in enumerate(numbers) if t == "Anhaenge")
    appendix = numbers[part_at:part_at + 7]
    assert all(num is None for _, num in appendix), appendix

    # Der Zaehler blieb unangetastet: das Kapitel danach ist die 2, nicht die 4.
    assert numbers[part_at + 7] == ("Kapitel", "2")


def test_autonum_none_leaves_the_counter_untouched(tmp_path: Path):
    """
    Kein Neustart bei 1 und kein Sprung: eine unnummerierte Strecke verbraucht
    keine Nummer, das naechste nummerierte Kapitel zaehlt einfach weiter.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        'document:\n  title: "T"\nchapters:\n'
        '  - file: "deep.md"\n    title: "Eins"\n'
        '  - file: "deep.md"\n    title: "Ohne"\n    autonum: "none"\n'
        '  - file: "deep.md"\n    title: "Zwei"\n',
    )

    config = load_config(tmp_path / "markpublish.yaml")
    _, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert [n.number for n in tree] == ["1", None, "2"]


def test_chapters_under_a_part_nest_by_level_in_the_toc(tmp_path: Path):
    """
    Ein Part ist im Inhaltsverzeichnis ein Knoten wie jeder andere: seine
    Kapitel haengen darunter, deren Zwischenueberschriften wiederum darunter.
    Werden die Knoten von Hand an den Part gehaengt statt durch
    build_toc_tree geschickt, liegt der gesamte Anhang flach auf einer Hoehe -
    im PDF sieht das aus, als haette jeder Abschnitt Kapitelrang.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        'document:\n  title: "T"\nchapters:\n'
        '  - part: "Anhaenge"\n    chapters:\n'
        '      - file: "deep.md"\n        title: "Anhang A"\n'
        '      - file: "deep.md"\n        title: "Anhang B"\n',
    )

    config = load_config(tmp_path / "markpublish.yaml")
    _, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert len(tree) == 1
    part = tree[0]
    assert part.is_part

    # Zwei Kapitel unter dem Part - nicht acht Knoten nebeneinander.
    assert len(part.children) == 2

    chapter = part.children[0]
    assert chapter.level == 2
    assert [c.title for c in chapter.children] == ["Ebene zwei"]
    assert [c.title for c in chapter.children[0].children] == ["Ebene drei"]


def test_document_toc_depth_is_the_root_for_chapters(tmp_path: Path):
    """
    `document.toc` gibt nicht nur an/aus, sondern auch die Tiefe - und ist damit
    die Wurzel fuer `chapters.document_toc`. Ohne sie muesste ein Dokument mit
    zwanzig Kapiteln zwanzigmal dieselbe Zeile tragen.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        'document:\n  title: "T"\n  document_toc: 2\nchapters:\n'
        '  - file: "deep.md"\n    title: "Erbt"\n'
        '  - file: "deep.md"\n    title: "Voll"\n    document_toc: "full"\n',
    )

    config = load_config(tmp_path / "markpublish.yaml")
    _, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    titles = [t for _, t in _tree_titles(tree)]
    # Das erbende Kapitel liefert eine Ebene unter sich, das andere alles.
    assert titles.count("Ebene zwei") == 2
    assert titles.count("Ebene drei") == 1


def test_document_toc_none_switches_the_table_off(tmp_path: Path):
    """
    'none' laesst das Verzeichnis ganz weg. Das Template testet `document.toc`
    direkt - ein TocScope muss dort also falsy sein, sonst stuende eine leere
    Verzeichnisseite im PDF.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        'document:\n  title: "T"\n  document_toc: "none"\nchapters:\n'
        '  - file: "deep.md"\n    title: "K"\n',
    )

    config = load_config(tmp_path / "markpublish.yaml")
    assert not config.document.document_toc

    _, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()
    assert _tree_titles(tree) == []


def test_document_toc_defaults_to_full(tmp_path: Path):
    """Ohne Angabe steht jede Ueberschrift im Verzeichnis."""
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        'document:\n  title: "T"\nchapters:\n  - file: "deep.md"\n    title: "K"\n',
    )

    config = load_config(tmp_path / "markpublish.yaml")
    _, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert [lvl for lvl, _ in _tree_titles(tree)] == [1, 2, 3]
