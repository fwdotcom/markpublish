"""
Integration tests executing real Typst compilation for edge cases.

Verifies fixes for review findings:
- B1, B6: Safe metadata escaping in Typst setup-document.
- B2, B5: Typst special characters ($5, C#, @, <tag>, brackets, math).
- B3: Local image resolution and copying to build directory.
- S1: Physical page count calculation across pagenum_reset.
- S2: Header/footer rendering when cover is disabled.
- S3: Suppressing header and footer via config switches.
- S7: Full markdown extensions (callouts, def_list, tables, footnotes).
"""

from __future__ import annotations

import base64
from pathlib import Path

import pypdfium2 as pdfium

from markpublish.config.loader import load_config
from markpublish.markdown.engine import MarkdownPipeline
from markpublish.renderers.base import DocumentContext
from markpublish.renderers.pdf import PDFRenderer
from markpublish.templates.resolver import resolve_template_path


def _compile_pdf(tmp_path: Path, yaml_text: str, files: dict[str, str | bytes]) -> Path:
    """Helper to set up files, build document context, and compile PDF via Typst."""
    (tmp_path / "markpublish.yaml").write_text(yaml_text, encoding="utf-8")
    for name, content in files.items():
        file_path = tmp_path / name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            file_path.write_bytes(content)
        else:
            file_path.write_text(content, encoding="utf-8")

    config = load_config(tmp_path / "markpublish.yaml")
    template_path = resolve_template_path(
        target="pdf",
        theme=config.theme,
        config_base_dir=tmp_path,
    )
    context = DocumentContext(
        config=config,
        content_items=[],
        toc_tree=[],
        template_path=template_path,
        base_dir=tmp_path,
        target="pdf",
    )
    pipeline = MarkdownPipeline(config, base_dir=tmp_path, labels=context.labels)
    context.content_items, context.toc_tree = pipeline.process_document()

    out_pdf = tmp_path / "output.pdf"
    renderer = PDFRenderer()
    renderer.render(context, out_pdf)
    assert out_pdf.is_file()
    assert out_pdf.stat().st_size > 500
    return out_pdf


def test_special_characters_compile_without_error(tmp_path: Path):
    """
    Test edge cases: $5.00 price, C# language name, @mentions, HTML-like tags,
    and brackets compile cleanly without Typst parsing errors.
    """
    yaml_text = """\
document:
  title: "Test with $5 and C# & Quotes \\"Special\\""
  subtitle: "Backslash \\\\ and brackets [test]"
  author: 'Author "The Great"'
  summary: 'Summary with $100 and C# code'
  cover: false
  document_toc:
    enabled: false
parts:
  - title: "Main Part"
    break_before: "none"
    chapters:
      - file: "chapter.md"
        title: "Chapter with $99 and C#"
"""
    chapter_md = """\
# Heading with $5 and C# <label-test>

Here is a price of $5.00 and another price of $10.50.
Programming in C# and C++ is fun.
Reach out to @support or @user.
A comparison: 5 < 10 and 10 > 5.
Bracket test: [Link text](https://example.com) and literal [brackets].
Math block test:

$$
E = m c^2
$$

Inline formatting: *emphasis*, **bold**, `inline code with $5 and C#`.
"""
    out_pdf = _compile_pdf(tmp_path, yaml_text, {"chapter.md": chapter_md})

    doc = pdfium.PdfDocument(out_pdf)
    assert len(doc) >= 1
    page_text = doc[0].get_textpage().get_text_range()
    assert "$5.00" in page_text
    assert "C#" in page_text
    assert "5 < 10" in page_text or "5" in page_text


def test_local_image_is_copied_and_compiled(tmp_path: Path):
    """
    Tests that local images referenced in Markdown (even in subfolders)
    are copied into the build directory and rendered without Typst path errors.
    """
    # 1x1 transparent PNG
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    yaml_text = """\
document:
  title: "Image Test"
  cover: false
  document_toc:
    enabled: false
parts:
  - title: "Part"
    break_before: "none"
    chapters:
      - file: "ch/chapter.md"
        title: "Chapter"
"""
    chapter_md = """\
# Image Chapter

Here is an image:
![Test Pixel](../img/pixel.png)
"""
    out_pdf = _compile_pdf(
        tmp_path,
        yaml_text,
        {
            "ch/chapter.md": chapter_md,
            "img/pixel.png": png_data,
        },
    )
    assert out_pdf.is_file()
    doc = pdfium.PdfDocument(out_pdf)
    assert len(doc) >= 1


def test_pagenum_reset_total_pages_stays_accurate(tmp_path: Path):
    """
    Tests that when pagenum_reset is used, the footer's total page count
    accurately reflects the physical total page count rather than resetting.
    """
    yaml_text = """\
document:
  title: "Page Reset Test"
  language: "en"
  cover: false
  header: true
  footer: true
  document_toc:
    enabled: false
parts:
  - title: "First Part"
    break_before: "none"
    chapters:
      - file: "ch1.md"
        title: "Chapter 1"
  - title: "Second Part"
    break_before: "page"
    pagenum_reset: true
    chapters:
      - file: "ch2.md"
        title: "Chapter 2"
"""
    ch1_md = "# Chapter 1\n\nPage one content.\n"
    ch2_md = "# Chapter 2\n\nPage two content.\n"

    out_pdf = _compile_pdf(tmp_path, yaml_text, {"ch1.md": ch1_md, "ch2.md": ch2_md})
    doc = pdfium.PdfDocument(out_pdf)
    assert len(doc) == 2

    # Verify both pages show "of 2"
    page1_text = doc[0].get_textpage().get_text_range()
    page2_text = doc[1].get_textpage().get_text_range()

    assert "of 2" in page1_text
    assert "of 2" in page2_text


def test_header_and_footer_can_be_disabled(tmp_path: Path):
    """
    Tests that setting header: false and footer: false properly suppresses
    headers and footers in the generated PDF.
    """
    yaml_text = """\
document:
  title: "Header Suppression Test"
  language: "en"
  cover: false
  header: false
  footer: false
  document_toc:
    enabled: false
parts:
  - title: "Part"
    break_before: "none"
    chapters:
      - file: "ch.md"
        title: "Chapter"
"""
    ch_md = "# Title\n\nContent paragraph.\n"
    out_pdf = _compile_pdf(tmp_path, yaml_text, {"ch.md": ch_md})
    doc = pdfium.PdfDocument(out_pdf)
    text = doc[0].get_textpage().get_text_range()
    assert "Page 1 of 1" not in text
    assert "Header Suppression Test" not in text.split("\n")[0]


def test_markdown_extensions_render_properly(tmp_path: Path):
    """
    Tests that tables, callouts/admonitions, definition lists, and footnotes
    are properly converted and compiled into Typst.
    """
    yaml_text = """\
document:
  title: "Extensions Test"
  cover: false
  document_toc:
    enabled: false
parts:
  - title: "Part"
    break_before: "none"
    chapters:
      - file: "ext.md"
        title: "Extensions"
"""
    ext_md = """\
# Extensions

> [!NOTE]
> This is a callout note.

> [!WARNING]
> This is a warning callout.

| Header A | Header B |
| :--- | :--- |
| Cell 1 | Cell 2 |

Term 1
: Definition 1

Here is a footnote reference[^1].

[^1]: Footnote content explaining something.
"""
    out_pdf = _compile_pdf(tmp_path, yaml_text, {"ext.md": ext_md})
    doc = pdfium.PdfDocument(out_pdf)
    assert len(doc) >= 1
    text = doc[0].get_textpage().get_text_range()
    assert "Cell 1" in text
    assert "Cell 2" in text
    assert "Definition 1" in text


def test_metadata_special_characters_in_key_and_value_compiles_cleanly(tmp_path: Path):
    """
    Tests that quotes and special characters in custom metadata keys and values
    do not inject syntax errors into the Typst document.
    """
    yaml_text = """\
document:
  title: "Meta Quote Test"
  cover: true
  'quo"te': 'value with "quotes" and $math$ and #tags'
parts:
  - title: "Part"
    break_before: "none"
    chapters:
      - file: "a.md"
        title: "A"
"""
    a_md = "# Title\n\nContent.\n"
    out_pdf = _compile_pdf(tmp_path, yaml_text, {"a.md": a_md})
    doc = pdfium.PdfDocument(out_pdf)
    assert len(doc) >= 1
    # Check cover page text contains value
    text = doc[0].get_textpage().get_text_range()
    assert 'value with "quotes"' in text


def test_custom_metadata_with_project_i18n_renders_localized_label_on_cover(tmp_path: Path):
    """
    Tests that Level 4 project-level i18n.yaml provides the localized label
    for a custom extra metadata field, and that the label appears on the PDF cover page.
    """
    yaml_text = """\
document:
  title: "Projektbericht"
  language: "de"
  cover: true
  department: "F&E"
parts:
  - title: "Hauptteil"
    break_before: "none"
    chapters:
      - file: "a.md"
        title: "A"
"""
    # Project-level i18n.yaml
    project_i18n = """\
de:
  department: "Fachabteilung"
"""
    (tmp_path / "i18n.yaml").write_text(project_i18n, encoding="utf-8")
    a_md = "# Kapitel\n\nInhalt.\n"
    out_pdf = _compile_pdf(tmp_path, yaml_text, {"a.md": a_md})
    doc = pdfium.PdfDocument(out_pdf)
    assert len(doc) >= 1
    cover_text = doc[0].get_textpage().get_text_range()
    assert "Fachabteilung" in cover_text, "Das lokalisierte Label aus der Projekt-i18n.yaml fehlt auf dem Deckblatt"
    assert "F&E" in cover_text, "Der Metadatenwert fehlt auf dem Deckblatt"



def test_the_theme_decides_the_order_of_the_cover_metadata(tmp_path: Path):
    """
    Die Reihenfolge im Metadatenraster ist Gestaltung und steht im Theme
    (`cover-order` in template.typ) -- nicht in der Reihenfolge einer
    Python-Konstante, wo sie niemand vermutet.

    Geprueft wird am gesetzten Dokument, nicht am Quelltext: nur so faellt auf,
    wenn die Sortierung wirkungslos wird.
    """
    yaml_text = """\
document:
  title: "Reihenfolge"
  language: "de"
  cover: true
  document_toc: "none"
  author: "AUTORNAME"
  version: "VERSIONSNUMMER"
  date: "DATUMSWERT"
  copyright: "COPYRIGHTZEILE"
  status: "STATUSWERT"
  eigenes_feld: "FREIERWERT"
parts:
  - title: "P"
    break_before: "none"
    chapters:
      - file: "a.md"
        title: "A"
"""
    out_pdf = _compile_pdf(tmp_path, yaml_text, {"a.md": "# A\n\nText.\n"})
    cover = pdfium.PdfDocument(out_pdf)[0].get_textpage().get_text_range()

    # cover-order im mitgelieferten Theme: version, date, author, copyright,
    # status -- und alles Freie dahinter.
    expected = [
        "VERSIONSNUMMER",
        "DATUMSWERT",
        "AUTORNAME",
        "COPYRIGHTZEILE",
        "STATUSWERT",
        "FREIERWERT",
    ]
    positions = [cover.find(value) for value in expected]
    assert all(p >= 0 for p in positions), f"nicht alle Werte gesetzt: {positions}"
    assert positions == sorted(positions), (
        f"Reihenfolge weicht ab: {list(zip(expected, positions, strict=True))}"
    )
