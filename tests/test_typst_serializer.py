"""
Unit tests for TypstSerializer, html_to_tree, and process_tree_headings_and_toc.
"""

from __future__ import annotations

from pathlib import Path

import markdown

from markpublish.markdown.pattern import PatternChain, compile_pattern
from markpublish.markdown.toc import NumberingContext
from markpublish.markdown.typst_serializer import (
    TypstSerializer,
    escape_typst_text,
    html_to_tree,
    process_tree_headings_and_toc,
    typst_string,
)


def _chain(source="_|1|.1|+"):
    """Das Standard-Pattern: Part ohne Nummer, Kapitel 1, 1.1, 1.1.1."""
    return PatternChain(document=compile_pattern(source, "document"))


def test_escape_typst_text_unit():
    assert escape_typst_text("C# & C++") == "C\\# & C++"
    assert escape_typst_text("Price is $100") == "Price is \\$100"
    assert escape_typst_text("array[0]") == "array\\[0\\]"
    assert escape_typst_text("user@domain.com") == "user\\@domain.com"
    assert escape_typst_text("5 < 10 and 10 > 5") == "5 \\< 10 and 10 \\> 5"
    assert escape_typst_text("formula ~x~") == "formula \\~x\\~"


def test_typst_string_escaping():
    assert typst_string('Hello "World"') == 'Hello \\"World\\"'
    assert typst_string('Path\\to\\file') == 'Path\\\\to\\\\file'
    assert typst_string(None) == ""


def test_serializer_inline_and_headings():
    md = "# First Heading\n\nText with **bold**, *italic*, <del>strikethrough</del> and `inline code`."
    raw_html = markdown.markdown(md, extensions=["tables", "admonition", "def_list"])
    tree = html_to_tree(raw_html)
    ctx = NumberingContext()
    process_tree_headings_and_toc(tree, ctx, patterns=_chain())

    serializer = TypstSerializer()
    typ = serializer.serialize(tree)

    assert '#heading(level: 1, numbering: (..nums) => "1")[First Heading] <first-heading>' in typ
    assert "#strong[bold]" in typ
    assert "#emph[italic]" in typ
    assert "#strike[strikethrough]" in typ
    assert "`inline code`" in typ


def test_serializer_tables():
    md = """
| Header 1 | Header 2 |
| :--- | :--- |
| Val 1 | Val 2 |
"""
    raw_html = markdown.markdown(md, extensions=["tables"])
    tree = html_to_tree(raw_html)
    serializer = TypstSerializer()
    typ = serializer.serialize(tree)

    assert "#table(" in typ
    assert "table.header(" in typ
    assert '[#text(weight: "bold")[Header 1]]' in typ
    assert "[Val 1]" in typ


def test_serializer_admonitions():
    md = """
!!! note "Custom Title"
    This is an admonition body.
"""
    raw_html = markdown.markdown(md, extensions=["admonition"])
    tree = html_to_tree(raw_html)
    serializer = TypstSerializer()
    typ = serializer.serialize(tree)

    assert '#callout(type: "note", title: [Custom Title])' in typ
    assert "This is an admonition body." in typ


def test_serializer_definition_list():
    md = """
Apple
: A fruit that keeps the doctor away.
"""
    raw_html = markdown.markdown(md, extensions=["def_list"])
    tree = html_to_tree(raw_html)
    serializer = TypstSerializer()
    typ = serializer.serialize(tree)

    assert "/ Apple: A fruit that keeps the doctor away." in typ


def test_serializer_math(tmp_path: Path):
    import typst

    from markpublish.markdown.engine import MarkdownEngine

    engine = MarkdownEngine("de")
    md = (
        "Inline: $\\frac{a}{b} + \\sqrt{x+1} + \\top \\to 0$.\n\n"
        "Block:\n\n"
        "$$ \\sum_{i=1}^{n} x_i + \\int_0^1 f(x) dx + \\text{Euro} $$\n"
    )
    html = engine.convert(md)
    tree = html_to_tree(html)
    serializer = TypstSerializer()
    typ = serializer.serialize(tree)

    assert "$(a) / (b) + sqrt(x+1) + top arrow.r 0$" in typ
    assert "sum_(i=1)^(n) x_i + integral_0^1 f(x) dif x + \"Euro\"" in typ

    # Compile with Typst to verify valid syntax
    out_pdf = tmp_path / "math.pdf"
    typ_file = tmp_path / "math.typ"
    typ_file.write_text(typ, encoding="utf-8")
    typst.compile(typ_file, output=out_pdf)
    assert out_pdf.is_file()
    assert out_pdf.stat().st_size > 500


def test_serializer_math_short_relations():
    from markpublish.markdown.engine import MarkdownEngine

    engine = MarkdownEngine("de")
    md = "Vergleich: $x \\ge 1$, $y \\le 2$, $z \\ne 3$."
    html = engine.convert(md)
    tree = html_to_tree(html)
    serializer = TypstSerializer()
    typ = serializer.serialize(tree)
    assert "$x >= 1$" in typ
    assert "$y <= 2$" in typ
    assert "$z != 3$" in typ


def test_serializer_table_pipe_unescape():
    from markpublish.markdown.engine import MarkdownEngine

    engine = MarkdownEngine("de")
    md = "| Header |\n| :--- |\n| a \\| b |"
    html = engine.convert(md)
    tree = html_to_tree(html)
    serializer = TypstSerializer()
    typ = serializer.serialize(tree)
    assert "[a | b]" in typ
    assert "a \\| b" not in typ


def test_serializer_heading_outlined_filtering():
    from markpublish.markdown.engine import MarkdownEngine, process_tree_headings_and_toc
    from markpublish.markdown.toc import NumberingContext

    engine = MarkdownEngine("de")
    md = "# Kap 1\n## Unter 1.1\n## Unter 1.2"
    html = engine.convert(md)
    tree = html_to_tree(html)
    ctx = NumberingContext()
    process_tree_headings_and_toc(tree, ctx, patterns=_chain())

    # Allow only Kap 1 and Unter 1.1 in TOC
    serializer = TypstSerializer(allowed_toc_slugs={"kap-1", "unter-11"})
    typ = serializer.serialize(tree)

    lines = [line for line in typ.splitlines() if line.startswith("#heading")]
    assert "outlined: false" not in lines[0]  # Kap 1
    assert "outlined: false" not in lines[1]  # Unter 1.1
    assert "outlined: false" in lines[2]      # Unter 1.2 gets outlined: false


def test_serialize_tasklist_without_bullet():
    from markpublish.markdown.engine import MarkdownEngine
    from markpublish.markdown.typst_serializer import TypstSerializer, html_to_tree

    engine = MarkdownEngine()
    md = """
- [x] Fertig
- [ ] Offen
- Regulär
"""
    html = engine.convert(md)
    tree = html_to_tree(html)
    serializer = TypstSerializer()
    typst_output = serializer.serialize(tree)

    assert "#task-item(checked: true)[Fertig]" in typst_output
    assert "#task-item(checked: false)[Offen]" in typst_output
    assert "- #task-item" not in typst_output
    assert "- Regulär" in typst_output


def test_tasklist_is_wrapped_in_block():
    """
    Die Aufgabenliste braucht eine Klammer, sonst klebt sie am Absatz davor.

    `#task-item` setzt einen engen Innenabstand, damit die Eintraege dicht
    untereinander stehen. Ohne `#block` ringsum gilt der auch nach aussen: der
    Abstand zum einleitenden Absatz faellt dann kleiner aus als der zwischen
    den Eintraegen, und die erste Zeile liest sich wie Teil des Absatzes.
    """
    from markpublish.markdown.engine import MarkdownEngine
    from markpublish.markdown.typst_serializer import TypstSerializer, html_to_tree

    md = """Einleitender Absatz:

- [x] Fertig
- [ ] Offen

* Normale Liste
* Zweiter Eintrag
"""
    typst_output = TypstSerializer().serialize(html_to_tree(MarkdownEngine().convert(md)))

    assert "#block[\n#task-item(checked: true)[Fertig]" in typst_output
    # Die normale Liste ist eine echte Typst-Liste und bringt ihren
    # Absatzabstand selbst mit -- sie darf keine Klammer bekommen.
    assert "#block[\n- Normale Liste" not in typst_output


def test_anchor_link_becomes_label_reference():
    """
    Ein Anker auf eine Ueberschrift muss ein Sprung sein, keine Adresse.

    `#link("#slug")` gibt Typst eine Zeichenkette; im PDF steht dann eine
    URI-Aktion, und der Betrachter versucht "#slug" zu oeffnen statt zu
    springen. Der Verweis ist tot, ohne dass es auffaellt.
    """
    from markpublish.markdown.engine import MarkdownEngine
    from markpublish.markdown.typst_serializer import TypstSerializer, html_to_tree

    md = """## Ein Abschnitt

[Sprung](#ein-abschnitt) und [extern](https://example.com).
"""
    tree = html_to_tree(MarkdownEngine().convert(md))
    typst_output = TypstSerializer(known_labels={"ein-abschnitt"}).serialize(tree)

    assert '#link(label("ein-abschnitt"))[Sprung]' in typst_output
    # Externe Adressen bleiben Adressen.
    assert '#link("https://example.com")[extern]' in typst_output


def test_unknown_anchor_stays_a_string():
    """
    Ein vertippter Anker darf das Dokument nicht kosten.

    `label()` auf eine Marke, die nirgends gesetzt ist, bricht die
    Typst-Kompilierung ab. Ein Ziel, das es nicht gibt, bleibt deshalb die
    Zeichenkette, die es vorher auch war.
    """
    from markpublish.markdown.engine import MarkdownEngine
    from markpublish.markdown.typst_serializer import TypstSerializer, html_to_tree

    tree = html_to_tree(MarkdownEngine().convert("[Sprung](#gibt-es-nicht)."))
    typst_output = TypstSerializer(known_labels={"ein-abschnitt"}).serialize(tree)

    assert '#link("#gibt-es-nicht")[Sprung]' in typst_output
    assert "label(" not in typst_output

