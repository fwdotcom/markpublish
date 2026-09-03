"""
Tests for MarkdownToTypstConverter.
"""

from markpublish.markdown.typst_converter import MarkdownToTypstConverter, escape_typst_text, slugify_heading


def test_escape_typst_text():
    assert escape_typst_text("C# & C++") == "C\\# & C++"
    assert escape_typst_text("Price is $100") == "Price is \\$100"
    assert escape_typst_text("array[0]") == "array\\[0\\]"
    assert escape_typst_text("user@domain.com") == "user\\@domain.com"


def test_slugify_heading():
    assert slugify_heading("Einführung & Architektur") == "einfuehrung-architektur"
    assert slugify_heading("1.2 Die Verarbeitungs-Pipeline") == "1-2-die-verarbeitungs-pipeline"
    assert slugify_heading("Über uns / FAQ's") == "ueber-uns-faq-s"


def test_convert_headings():
    conv = MarkdownToTypstConverter()
    md = "# First Heading\n\n## Subheading with `code`\n\n### Deep Section"
    typ = conv.convert(md)
    assert "= First Heading <first-heading>" in typ
    assert "== Subheading with `code` <subheading-with-code>" in typ
    assert "=== Deep Section <deep-section>" in typ
    assert len(conv.extracted_headings) == 3


def test_convert_inline_formatting():
    conv = MarkdownToTypstConverter()
    md = "Text with **bold**, *italic*, ***bold-italic***, ~~strikethrough~~ and `inline code`."
    typ = conv.convert(md)
    assert "#strong[bold]" in typ
    assert "#emph[italic]" in typ
    assert "#strong[#emph[bold-italic]]" in typ
    assert "#strike[strikethrough]" in typ
    assert "`inline code`" in typ


def test_convert_links_and_images():
    conv = MarkdownToTypstConverter()
    md = "Visit [Google](https://google.com) or see ![A Graph](images/graph.png)."
    typ = conv.convert(md)
    assert '#link("https://google.com")[Google]' in typ
    assert '#image("images/graph.png", alt: "A Graph")' in typ


def test_convert_github_callouts():
    labels = {"note": "Hinweis", "warning": "Warnung", "caution": "Achtung"}
    conv = MarkdownToTypstConverter(labels=labels)
    md = """> [!NOTE]
> Dies ist ein mehrzeiliger
> Hinweis mit **Formatierung**.

> [!WARNING] Eigener Warntitel
> Passen Sie hier gut auf!
"""
    typ = conv.convert(md)
    assert '#callout(type: "note", title: [Hinweis])[' in typ
    assert "#strong[Formatierung]" in typ
    assert '#callout(type: "warning", title: [Eigener Warntitel])[' in typ
    assert "Passen Sie hier gut auf!" in typ


def test_convert_fenced_code_block():
    conv = MarkdownToTypstConverter()
    md = """```python
def hello(name: str) -> str:
    # Print greeting
    return f"Hello, {name}!"
```"""
    typ = conv.convert(md)
    assert "```python\ndef hello(name: str) -> str:\n    # Print greeting\n    return f\"Hello, {name}!\"\n```" in typ


def test_convert_tables():
    conv = MarkdownToTypstConverter()
    md = """| Name | Alter | Beruf |
| :--- | :---: | ---: |
| Anna | 28 | Entwicklerin |
| Bob | 34 | Designer |"""
    typ = conv.convert(md)
    assert "#table(" in typ
    assert "columns: (1.2fr, 1.2fr, 2fr)" in typ
    assert "align: (left, center, right)" in typ
    assert "table.header([* Name *], [* Alter *], [* Beruf *])" in typ
    assert "[Anna], [28], [Entwicklerin]" in typ
    assert "[Bob], [34], [Designer]" in typ


def test_convert_task_lists():
    conv = MarkdownToTypstConverter()
    md = """- [ ] Task 1 offen
- [x] Task 2 erledigt
- Normaler Punkt"""
    typ = conv.convert(md)
    assert "#task-item(checked: false)[Task 1 offen]" in typ
    assert "#task-item(checked: true)[Task 2 erledigt]" in typ
    assert "- #task-item" not in typ
    assert "- Normaler Punkt" in typ
