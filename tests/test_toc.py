"""
Tests for TOC extraction and autonumbering.
"""

from pathlib import Path

from markpublish.config.loader import load_config
from markpublish.markdown.engine import MarkdownPipeline
from markpublish.markdown.pattern import PatternChain, compile_pattern
from markpublish.markdown.toc import (
    NumberingContext,
    int_to_roman,
    process_html_headings_and_toc,
)


def _chain(source, scope="document"):
    return PatternChain(document=compile_pattern(source, scope))


def test_roman_numerals():
    assert int_to_roman(1) == "I"
    assert int_to_roman(4) == "IV"
    assert int_to_roman(9) == "IX"
    assert int_to_roman(10) == "X"


def test_autonumbering_decimal():
    ctx = NumberingContext()

    html = """
<h1>First Chapter</h1>
<h2>First Section</h2>
<h3>Sub Section</h3>
<h2>Second Section</h2>
<h1>Second Chapter</h1>
"""
    processed, nodes = process_html_headings_and_toc(html, ctx, _chain("_|1|.1|+"))

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
    ctx = NumberingContext()
    html = "<h1>Unnumbered Chapter</h1>"
    processed, nodes = process_html_headings_and_toc(html, ctx, _chain("none"))
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
        """\
document:
  title: "T"
parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "deep.md"
      - file: "deep.md"
        document_toc: 2
""",
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
        """\
document:
  title: "T"
parts:
  - part: "Anhaenge"
    document_toc: 1
    chapters:
      - file: "deep.md"
      - file: "deep.md"
""",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    _, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    titles = [t for _, t in _tree_titles(tree)]
    assert "Anhaenge" in titles
    assert titles.count("Kapitel") == 2, "beide Anhaenge stehen mit ihrer Ueberschrift im TOC"
    assert "Ebene zwei" not in titles
    assert "Ebene drei" not in titles


def test_document_toc_one_includes_only_chapter_title(tmp_path: Path):
    """
    document_toc: 1 liefert nur die Kapitelueberschrift (Ebene 1),
    saemtliche Zwischenueberschriften (h2, h3) fallen heraus.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        """\
document:
  title: "T"
parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "deep.md"
        document_toc: 1
""",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    _, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    levels = [lvl for lvl, _ in _tree_titles(tree)]
    assert levels == [1], "Nur die Hauptueberschrift, keine Zwischenueberschriften"


def test_document_toc_defaults_to_the_full_depth(tmp_path: Path):
    """Ohne Angabe gilt volle Tiefe: jede Ueberschrift steht im Verzeichnis."""
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        """\
document:
  title: "T"
parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "deep.md"
""",
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
        """\
document:
  title: "T"
parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "deep.md"
      - file: "deep.md"
        document_toc: "none"
""",
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
        """\
document:
  title: "T"
parts:
  - part: "Anhaenge"
    document_toc: 1
    chapters:
      - file: "deep.md"
      - file: "deep.md"
        document_toc: "full"
""",
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
        """\
document:
  title: "T"
parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "deep.md"
        chapter_toc: "full"
      - file: "deep.md"
        chapter_toc: 2
""",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    items, _ = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert [n.title for n in items[0].local_toc_items] == ["Ebene zwei", "Ebene drei"]
    assert [n.title for n in items[1].local_toc_items] == ["Ebene zwei"]


def test_document_chapter_toc_is_the_root_for_chapters(tmp_path: Path):
    """
    `document.chapter_toc` steht zu `chapters.chapter_toc` wie `document.autonum_pattern` zu
    `parts.autonum_pattern`: die Vorgabe oben, der Einzelfall unten. Ohne sie wiederholt ein
    Dokument mit zehn Kapiteln zehnmal dieselbe Zeile.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        """\
document:
  title: "T"
  chapter_toc: 2
parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "deep.md"
      - file: "deep.md"
        chapter_toc: "full"
      - file: "deep.md"
        chapter_toc: "none"
""",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    items, _ = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert [n.title for n in items[0].local_toc_items] == ["Ebene zwei"]
    assert [n.title for n in items[1].local_toc_items] == ["Ebene zwei", "Ebene drei"]
    assert items[2].local_toc_items == []


def test_document_chapter_toc_defaults_to_full(tmp_path: Path):
    """Ohne Vorgabe gilt der Standard 'full': Unterueberschriften werden erfasst."""
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        """\
document:
  title: "T"
parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "deep.md"
""",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    items, _ = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert [n.title for n in items[0].local_toc_items] == ["Ebene zwei", "Ebene drei"]


def test_document_chapter_toc_can_be_disabled(tmp_path: Path):
    """Mit chapter_toc: 'none' wird das lokale Kapitel-TOC deaktiviert."""
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        """\
document:
  title: "T"
  chapter_toc: "none"
parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "deep.md"
""",
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
    ohne Vererbung waere `autonum_pattern: none` am Anhang-Part wirkungslos und die
    Anhaenge zaehlten den Kapitelzaehler weiter.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        """\
document:
  title: "T"
parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "deep.md"
  - part: "Anhaenge"
    autonum_pattern: none
    chapters:
      - file: "deep.md"
      - file: "deep.md"
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "deep.md"
""",
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


def test_autonum_none_on_a_chapter_leaves_its_own_number_alone(tmp_path: Path):
    """
    Ein Kapitel-Pattern beschreibt, was *in* dem Kapitel steht, nicht das
    Kapitel selbst -- Slot 1 ist dort die h2. `none` schaltet deshalb nur die
    Ueberschriften darin ab; die Kapitelnummer kommt weiter von oben und die
    Zaehlung laeuft ohne Luecke durch.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        """\
document:
  title: "T"
parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "deep.md"
      - file: "deep.md"
        autonum_pattern: none
      - file: "deep.md"
""",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    _, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert [n.number for n in tree] == ["1", "2", "3"]
    assert [c.number for c in tree[1].children] == [None]
    assert tree[1].children[0].children[0].number is None
    assert tree[0].children[0].number == "1.1"


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
        """\
document:
  title: "T"
parts:
  - part: "Anhaenge"
    chapters:
      - file: "deep.md"
      - file: "deep.md"
""",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    _, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert len(tree) == 1
    part = tree[0]
    assert part.is_part

    # Zwei Kapitel unter dem Part - nicht acht Knoten nebeneinander.
    assert len(part.children) == 2

    chapter = part.children[0]
    assert chapter.level == 1
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
        """\
document:
  title: "T"
  document_toc: 2
parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "deep.md"
      - file: "deep.md"
        document_toc: "full"
""",
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
        """\
document:
  title: "T"
  document_toc: "none"
parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "deep.md"
""",
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
        """\
document:
  title: "T"
parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "deep.md"
""",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    _, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert [lvl for lvl, _ in _tree_titles(tree)] == [1, 2, 3]


def test_a_skipped_chapter_slot_numbers_h2_from_one(tmp_path: Path):
    """
    `"_|1|.1|+"` am Part laesst die Kapitelueberschrift unnummeriert und faengt
    bei der h2 mit 1 an; die h3 wird relativ dazu 1.1.
    """
    _write(tmp_path, "appendix.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        """\
document:
  title: "T"
parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    autonum_pattern: "_|1|.1|+"
    chapters:
      - file: "appendix.md"
""",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    items, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert items[0].number_prefix is None, "h1 (Anhang A) erhaelt keine Nummer"
    assert '<span class="heading-number">1</span> Ebene zwei' in items[0].html_content
    assert '<span class="heading-number">1.1</span> Ebene drei' in items[0].html_content

    # Auch im Baum / TOC korrekt nummeriert
    tocs = _tree_titles(tree)
    assert tocs[0][1] == "Kapitel"
    assert tree[0].number is None
    assert tree[0].children[0].number == "1"
    assert tree[0].children[0].children[0].number == "1.1"


def test_a_leading_literal_prefixes_every_number(tmp_path: Path):
    """
    Ein fuehrendes Literal in Slot 1 steht vor jeder Nummer, die der Slot traegt
    -- und vor allem, was sich daraus zusammensetzt: A.1, A.1.1.
    """
    _write(tmp_path, "appendix.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        """\
document:
  title: "T"
parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    autonum_pattern: "_|1|.1|+"
    chapters:
      - file: "appendix.md"
        autonum_pattern: "'A.'1|.1|+"
""",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    items, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert '<span class="heading-number">A.1</span> Ebene zwei' in items[0].html_content
    assert '<span class="heading-number">A.1.1</span> Ebene drei' in items[0].html_content
    assert tree[0].children[0].number == "A.1"
    assert tree[0].children[0].children[0].number == "A.1.1"


def test_autonum_reset_restarts_each_chapter_under_a_skipped_level(tmp_path: Path):
    """
    Ist die Kapitelebene uebersprungen, rueckt beim Kapitelwechsel kein Zaehler
    vor -- die h2 des zweiten Anhangs waere sonst B.2. `autonum_reset` ist genau
    fuer diesen Fall da und laesst jedes Kapitel wieder bei eins anfangen.
    """
    _write(tmp_path, "app_a.md", DEEP_MD)
    _write(tmp_path, "app_b.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        """\
document:
  title: "T"
parts:
  - part: "Anhaenge"
    break_before: "divider"
    autonum_pattern: "_|1|.1|+"
    autonum_reset: true
    chapters:
      - file: "app_a.md"
        autonum_pattern: "'A.'1|.1|+"
      - file: "app_b.md"
        autonum_pattern: "'B.'1|.1|+"
""",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    items, _ = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    # items = [part_divider, app_a, app_b]
    app_a = items[1]
    app_b = items[2]

    assert '<span class="heading-number">A.1</span> Ebene zwei' in app_a.html_content
    assert '<span class="heading-number">B.1</span> Ebene zwei' in app_b.html_content


def test_chapter_document_toc_none_and_depth_limits(tmp_path: Path):
    (tmp_path / "c1.md").write_text("# Kap 1\n## Unter 1.1\n### Detail 1.1.1\n", encoding="utf-8")
    (tmp_path / "c2.md").write_text("# Kap 2\n## Unter 2.1\n", encoding="utf-8")
    (tmp_path / "markpublish.yaml").write_text(
        """\
document:
  title: "T"
parts:
  - part: "P"
    break_before: "none"
    chapters:
      - file: "c1.md"
        document_toc: 1
      - file: "c2.md"
        document_toc: "none"
""",
        encoding="utf-8",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    items, toc = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    # c1 has document_toc: 1 -> H1 is in outline, H2 and H3 have outlined: false
    c1 = items[0]
    lines_c1 = [line for line in c1.typst_content.splitlines() if line.startswith("#heading")]
    assert "outlined: false" not in lines_c1[0]  # Kap 1
    assert "outlined: false" in lines_c1[1]      # Unter 1.1
    assert "outlined: false" in lines_c1[2]      # Detail 1.1.1

    # c2 has document_toc: "none" -> All headings have outlined: false
    c2 = items[1]
    lines_c2 = [line for line in c2.typst_content.splitlines() if line.startswith("#heading")]
    assert "outlined: false" in lines_c2[0]      # Kap 2
    assert "outlined: false" in lines_c2[1]      # Unter 2.1


def test_chapter_title_from_file_h1_with_toc_and_divider_overrides(tmp_path: Path):
    """
    Stellt sicher, dass:
    1. Die H1 aus der Markdown-Datei standardmaessig den Titel fuer Seite, TOC und Divider liefert.
    2. toc_title gezielt den Verzeichniseintrag ueberschreibt, waehrend die H1 auf der Seite bleibt.
    3. divider_title gezielt den Trennseitentitel steuert.
    """
    (tmp_path / "c1.md").write_text("# Sehr lange Ueberschrift auf der Textseite\n\nText 1", encoding="utf-8")
    (tmp_path / "c2.md").write_text("# Normales Kapitel\n\nText 2", encoding="utf-8")

    (tmp_path / "markpublish.yaml").write_text(
        """\
document:
  title: "Doc"
parts:
  - part: "Hauptabschnitt"
    break_before: "divider"
    chapters:
      - file: "c1.md"
        toc_title: "Kurztitel im TOC"
        divider_title: "Trennseiten-Titel"
        break_before: "divider"
      - file: "c2.md"
""",
        encoding="utf-8",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    items, toc = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    # Part
    assert items[0].is_part is True
    assert items[0].display_title == "Hauptabschnitt"

    # c1: Textseite hat originale H1, TOC hat Kurztitel, Divider hat Trennseiten-Titel
    assert items[1].display_title == "Kurztitel im TOC"
    assert items[1].toc_title == "Kurztitel im TOC"
    assert items[1].divider_title == "Trennseiten-Titel"
    assert "Sehr lange Ueberschrift auf der Textseite" in items[1].typst_content
    # Im TOC steht der Kurztitel
    assert items[1].local_toc_items == []  # Keine Unterebenen
    assert toc[0].children[0].title == "Kurztitel im TOC"

    # c2: erbt alles aus Datei-H1
    assert items[2].display_title == "Normales Kapitel"
    assert items[2].toc_title == "Normales Kapitel"
    assert items[2].divider_title == "Normales Kapitel"
    assert "Normales Kapitel" in items[2].typst_content


def test_h1_less_chapter_with_titles(tmp_path: Path):
    """
    Ein Kapitel ohne '#' in der Datei ist gueltig, wenn toc_title und divider_title gesetzt sind:
    - Textseite enthaelt absolut keine Ueberschrift.
    - TOC und Divider erhalten die definierten Titel.
    """
    (tmp_path / "dedication.md").write_text("Fuer meine Familie.\n\nReiner Text ohne H1.", encoding="utf-8")

    (tmp_path / "markpublish.yaml").write_text(
        """\
document:
  title: "Doc"
parts:
  - part: "Vorspann"
    break_before: "none"
    chapters:
      - file: "dedication.md"
        toc_title: "Widmung"
        divider_title: "Widmungsblatt"
        break_before: "divider"
""",
        encoding="utf-8",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    items, toc = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    # Da part break_before: none hat, gibt es kein Part-Item, items[0] ist das Kapitel
    assert len(items) == 1
    ch = items[0]
    assert ch.toc_title == "Widmung"
    assert ch.divider_title == "Widmungsblatt"
    assert ch.display_title == "Widmung"
    # Keine Ueberschrift im typst_content
    assert "#heading" not in ch.typst_content
    # Aber synthetischer Eintrag im TOC vorhanden
    assert len(toc[0].children) == 1
    assert toc[0].children[0].title == "Widmung"


def test_validation_error_missing_divider_title(tmp_path: Path):
    """
    Wenn break_before: 'divider' gefordert ist, die Datei aber kein '#' hat und kein divider_title
    konfiguriert ist, bricht der Build mit ConfigurationError ab.
    """
    from markpublish.config.models import ConfigurationError

    (tmp_path / "empty_heading.md").write_text("Nur Fließtext ohne Ueberschrift", encoding="utf-8")

    (tmp_path / "markpublish.yaml").write_text(
        """\
document:
  title: "Doc"
parts:
  - part: "Abschnitt"
    chapters:
      - file: "empty_heading.md"
        break_before: "divider"
        toc_title: "TOC Titel Vorhanden"
""",
        encoding="utf-8",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    import pytest
    with pytest.raises(ConfigurationError) as exc_info:
        MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert "requires a divider page" in str(exc_info.value)
    assert "divider_title" in str(exc_info.value)


def test_validation_error_missing_toc_title(tmp_path: Path):
    """
    Wenn ein Kapitel im Inhaltsverzeichnis gelistet werden soll, die Datei aber kein '#' hat
    und kein toc_title konfiguriert ist, bricht der Build mit ConfigurationError ab.
    """
    from markpublish.config.models import ConfigurationError

    (tmp_path / "no_h1.md").write_text("Nur Fließtext ohne Ueberschrift", encoding="utf-8")

    (tmp_path / "markpublish.yaml").write_text(
        """\
document:
  title: "Doc"
parts:
  - part: "Abschnitt"
    chapters:
      - file: "no_h1.md"
""",
        encoding="utf-8",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    import pytest
    with pytest.raises(ConfigurationError) as exc_info:
        MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert "table of contents" in str(exc_info.value)
    assert "toc_title" in str(exc_info.value)


def test_h1_less_chapter_excluded_from_toc_and_divider_is_valid(tmp_path: Path):
    """
    Eine Datei ohne '#' darf existieren, wenn sie weder Trennseite noch Verzeichniseintrag verlangt.
    """
    (tmp_path / "notes.md").write_text("Reine Notizen, nirgends gelistet.", encoding="utf-8")

    (tmp_path / "markpublish.yaml").write_text(
        """\
document:
  title: "Doc"
parts:
  - part: "Abschnitt"
    break_before: "none"
    part_toc: "none"
    chapters:
      - file: "notes.md"
        break_before: "none"
        document_toc: "none"
""",
        encoding="utf-8",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    items, toc = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()
    assert len(items) == 1
    assert "#heading" not in items[0].typst_content


def test_validation_error_missing_toc_title_with_part_toc(tmp_path: Path):
    """
    Auch wenn document_toc 'none' ist, aber part_toc auf der Part-Trennseite aktiv ist,
    muss ein Kapitel ohne '#' ein toc_title besitzen, da es sonst ohne Titel im Part-TOC stuende.
    """
    import pytest

    from markpublish.config.models import ConfigurationError

    (tmp_path / "no_h1.md").write_text("Nur Fließtext ohne Ueberschrift", encoding="utf-8")

    (tmp_path / "markpublish.yaml").write_text(
        """\
document:
  title: "Doc"
  document_toc: "none"
parts:
  - part: "Abschnitt"
    break_before: "divider"
    part_toc: "full"
    chapters:
      - file: "no_h1.md"
""",
        encoding="utf-8",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    with pytest.raises(ConfigurationError) as exc_info:
        MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert "table of contents" in str(exc_info.value)
    assert "toc_title" in str(exc_info.value)


def test_show_title_false_suppresses_h1_in_content_but_keeps_toc_node(tmp_path: Path):
    """
    show_title: false unterdrueckt die H1 im Textinhalt (weder im HTML noch im Typst),
    erhaelt aber den TOCNode im Inhaltsverzeichnis und setzt needs_synthetic_toc_heading.
    """
    (tmp_path / "chapter.md").write_text("# Mein Kapitel\n\nDies ist der Inhalt.", encoding="utf-8")
    (tmp_path / "markpublish.yaml").write_text(
        """\
document:
  title: "Doc"
parts:
  - part: "Hauptteil"
    break_before: "divider"
    chapters:
      - file: "chapter.md"
        show_title: false
""",
        encoding="utf-8",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    items, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    assert len(tree) == 1
    # Part Node -> Child ist das Kapitel mit Titel "Mein Kapitel"
    assert tree[0].children[0].title == "Mein Kapitel"

    # items enthaelt den Part (items[0]) und das Kapitel (items[1])
    assert len(items) == 2
    assert items[0].is_part is True
    ch = items[1]
    assert ch.is_part is False
    assert ch.show_title is False
    assert ch.needs_synthetic_toc_heading is True
    assert "<h1>" not in ch.html_content
    assert "#heading(level: 1" not in ch.typst_content
    assert "Dies ist der Inhalt." in ch.html_content
    assert "Dies ist der Inhalt." in ch.typst_content


def test_a_numbered_part_keeps_its_number_out_of_the_chapter_numbers(tmp_path: Path):
    """
    Slot 1 des document-Patterns nummeriert den Part und sonst nichts: die
    Kapitel zaehlen ueber die Partgrenze hinweg durch.

    Traege die Part-Nummer nach unten, haette dieselbe Konfiguration je nach
    Sichtbarkeit des Parts andere Kapitelnummern -- eine entfernte Trennseite
    verschoebe stillschweigend jeden Querverweis.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        """\
document:
  title: "T"
  autonum_pattern: "I|1|.1|+"
parts:
  - part: "Grundlagen"
    break_before: "divider"
    chapters:
      - file: "deep.md"
      - file: "deep.md"
  - part: "Praxis"
    break_before: "divider"
    chapters:
      - file: "deep.md"
""",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    items, tree = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    parts = [i for i in items if i.is_part]
    assert [p.number_prefix for p in parts] == ["I", "II"]

    chapters = [i for i in items if not i.is_part]
    assert [c.number_prefix for c in chapters] == ["1", "2", "3"]

    # Und dasselbe im Verzeichnis, damit Baum und Satz nicht auseinanderlaufen.
    assert [n.number for n in tree] == ["I", "II"]
    assert [c.number for c in tree[0].children] == ["1", "2"]
    assert tree[0].children[0].children[0].number == "1.1"


def test_a_hidden_part_gets_no_number_and_consumes_none(tmp_path: Path):
    """
    `document_toc: "none"` ist die Klammer, die der Aufbau verlangt und die
    niemand sehen soll. Zaehlte sie mit, hiesse der erste sichtbare Abschnitt
    "II" und "I" kaeme im ganzen Dokument nicht vor.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(
        tmp_path,
        "markpublish.yaml",
        """\
document:
  title: "T"
  autonum_pattern: "I|1|.1|+"
parts:
  - part: "Klammer"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "deep.md"
  - part: "Anhaenge"
    break_before: "divider"
    chapters:
      - file: "deep.md"
""",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    items, _ = MarkdownPipeline(config, base_dir=tmp_path, labels={}).process_document()

    visible = [i for i in items if i.is_part]
    assert [p.display_title for p in visible] == ["Anhaenge"]
    assert visible[0].number_prefix == "I"


LABEL_YAML = """\
document:
  title: "T"
  autonum_pattern: "_|1|.1|+"
  chapter_label: "Kapitel"
parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "deep.md"
  - part: "Anhaenge"
    break_before: "divider"
    autonum_pattern: "A|.1|+"
    autonum_reset: true
    chapter_label: "Anhang"
    chapters:
      - file: "deep.md"
      - file: "deep.md"
        label: "Exkurs"
"""


def test_a_label_stands_before_the_number_but_not_in_the_ones_below(tmp_path: Path):
    """
    Der Anzeigename gehoert zur Ueberschrift, nicht zur Nummer. Stuende er im
    Pattern, truege ihn jede Unterueberschrift mit -- 'Anhang A.1'.
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(tmp_path, "markpublish.yaml", LABEL_YAML)

    config = load_config(tmp_path / "markpublish.yaml")
    items, tree = MarkdownPipeline(
        config, base_dir=tmp_path, labels={"label_separator": ": "}
    ).process_document()

    appendix = [n for n in tree if n.title == "Anhaenge"][0]
    assert [c.number for c in appendix.children] == ["Anhang A: ", "Exkurs B: "]
    assert appendix.children[0].children[0].number == "A.1"


def test_the_bare_number_stays_on_the_item_for_the_divider_page(tmp_path: Path):
    """
    Die Trennseite setzt ihr Wort selbst vor die Nummer ("KAPITEL 5"). Bekaeme
    sie die schon beschriftete Nummer, stuende dort "ANHANG Anhang A:".
    """
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(tmp_path, "markpublish.yaml", LABEL_YAML)

    config = load_config(tmp_path / "markpublish.yaml")
    items, _ = MarkdownPipeline(
        config, base_dir=tmp_path, labels={"label_separator": ": "}
    ).process_document()

    chapters = [i for i in items if not i.is_part]
    assert [c.number_prefix for c in chapters] == ["1", "A", "B"]
    assert [c.display_number for c in chapters] == ["Kapitel 1: ", "Anhang A: ", "Exkurs B: "]
    assert [c.label for c in chapters] == ["Kapitel", "Anhang", "Exkurs"]


def test_the_innermost_label_wins(tmp_path: Path):
    """document.chapter_label -> parts[].chapter_label -> chapters[].label."""
    _write(tmp_path, "deep.md", DEEP_MD)
    _write(tmp_path, "markpublish.yaml", LABEL_YAML)

    config = load_config(tmp_path / "markpublish.yaml")
    items, _ = MarkdownPipeline(
        config, base_dir=tmp_path, labels={"label_separator": ": "}
    ).process_document()

    labels = [i.label for i in items if not i.is_part]
    assert labels == ["Kapitel", "Anhang", "Exkurs"]
