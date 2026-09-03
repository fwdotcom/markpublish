"""
Unit tests for TypstSerializer, html_to_tree, and process_tree_headings_and_toc.
"""

from __future__ import annotations

from pathlib import Path

import markdown

from markpublish.markdown.toc import NumberingContext
from markpublish.markdown.typst_serializer import (
    TypstSerializer,
    escape_typst_text,
    html_to_tree,
    process_tree_headings_and_toc,
    typst_string,
)


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
    process_tree_headings_and_toc(tree, ctx)

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
    process_tree_headings_and_toc(tree, ctx)

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

