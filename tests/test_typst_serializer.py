"""
Unit tests for TypstSerializer, html_to_tree, and process_tree_headings_and_toc.
"""

from __future__ import annotations

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

    assert "= 1 First Heading <first-heading>" in typ
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
    assert "table.header([#text(weight: \"bold\")[Header 1]])" in typ
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
