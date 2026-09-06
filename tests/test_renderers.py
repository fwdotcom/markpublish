"""
Tests for PDF rendering.
"""

from pathlib import Path

import pytest

from markpublish.config.loader import load_config
from markpublish.markdown.engine import MarkdownPipeline
from markpublish.renderers.base import DocumentContext
from markpublish.renderers.pdf import PDFRenderer
from markpublish.templates.resolver import resolve_template_path


def test_full_pipeline_pdf(tmp_path: Path):
    # Create sample document setup in tmp_path
    chapters_dir = tmp_path / "chapters"
    chapters_dir.mkdir()

    (chapters_dir / "01.md").write_text("# Einleitung\n\nDas ist die Einleitung.", encoding="utf-8")
    (chapters_dir / "02.md").write_text("# Hauptteil\n\n## Detail\n\nInhalt hier.", encoding="utf-8")

    yaml_content = """\

document:
  title: "End-to-End Test Document"
  subtitle: "Integration Test"
  author: "Test Runner"
  date: "2026-08-31"
  version: "1.0.0"
  language: "de"
  cover: true
  document_toc: "full"
  header: true
  footer: true

theme: "default"

parts:
  - title: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "chapters/01.md"
        title: "Einleitung"
        break_before: "divider"
        chapter_toc: "none"
      - file: "chapters/02.md"
        title: "Hauptteil"
        break_before: "divider"
        chapter_toc: 2
"""
    config_file = tmp_path / "markpublish.yaml"
    config_file.write_text(yaml_content, encoding="utf-8")

    config = load_config(config_file)
    pipeline = MarkdownPipeline(config, base_dir=tmp_path)
    content_items, toc_tree = pipeline.process_document()

    # Test PDF Renderer
    pdf_template = resolve_template_path("pdf", "default")
    pdf_context = DocumentContext(
        config=config,
        content_items=content_items,
        toc_tree=toc_tree,
        template_path=pdf_template,
        base_dir=tmp_path,
        target="pdf",
    )
    pdf_out = tmp_path / "output.pdf"
    PDFRenderer().render(pdf_context, pdf_out)
    assert pdf_out.is_file()
    assert pdf_out.stat().st_size > 1000  # Generated valid PDF


# --------------------------------------------------------------------------
# Trennseiten und Kapitel-TOC im PDF
# --------------------------------------------------------------------------

DIVIDER_YAML = """\

document:
  title: "Trennseiten Test"
  author: "Test"
  date: "01.09.2026"
  language: "de"
  cover: false
  document_toc: "full"

theme: "default"

parts:
  - title: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "chapters/01.md"
        title: "Erstes Kapitel"
        summary: "Zusammenfassung des Kapitels."
        break_before: "divider"
        chapter_toc: 2
  - part: "Anhaenge"
    summary: "Zusammenfassung des Blocks."
    break_before: "divider"
    chapters:
      - file: "chapters/02.md"
        title: "Anhang A"
"""


def _divider_project(tmp_path: Path) -> Path:
    chapters = tmp_path / "chapters"
    chapters.mkdir(parents=True, exist_ok=True)
    (chapters / "01.md").write_text(
        "# Erstes Kapitel\n\n## Abschnitt A\n\nText.\n\n## Abschnitt B\n\nText.\n",
        encoding="utf-8",
    )
    (chapters / "02.md").write_text("# Anhang A\n\nText.\n", encoding="utf-8")
    (tmp_path / "markpublish.yaml").write_text(DIVIDER_YAML, encoding="utf-8")
    return tmp_path


def test_pdf_theme_renders_divider_pages(tmp_path: Path):
    pytest.importorskip("pypdfium2")
    project = _divider_project(tmp_path)
    config = load_config(project / "markpublish.yaml")
    context = DocumentContext(
        config=config,
        content_items=[],
        toc_tree=[],
        template_path=resolve_template_path("pdf", "default"),
        base_dir=project,
        target="pdf",
    )
    context.content_items, context.toc_tree = MarkdownPipeline(
        config, base_dir=project, labels=context.labels
    ).process_document()

    out = project / "out.pdf"
    PDFRenderer().render(context, out)

    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(str(out))
    text = "\n".join(
        doc[i].get_textpage().get_text_range() for i in range(len(doc))
    )

    assert "KAPITEL 1" in text.upper()
    assert "Zusammenfassung des Kapitels." in text
    assert "Abschnitt A" in text


def test_pdf_theme_without_fonts_dir_renders_successfully(tmp_path: Path):
    """Verifies N1: A theme without fonts/ directory does not fail with TypeError."""
    import shutil

    project = _divider_project(tmp_path / "proj")
    config = load_config(project / "markpublish.yaml")

    # Custom theme without fonts/ directory
    theme_dir = tmp_path / "custom_theme" / "pdf"
    theme_dir.mkdir(parents=True)
    orig_template = resolve_template_path("pdf", "default")
    shutil.copy2(orig_template / "template.typ", theme_dir / "template.typ")
    shutil.copy2(orig_template / "i18n.yaml", theme_dir / "i18n.yaml")

    context = DocumentContext(
        config=config,
        content_items=[],
        toc_tree=[],
        template_path=theme_dir,
        base_dir=project,
        target="pdf",
    )
    context.content_items, context.toc_tree = MarkdownPipeline(
        config, base_dir=project, labels=context.labels
    ).process_document()

    out = project / "out_custom.pdf"
    PDFRenderer().render(context, out)
    assert out.is_file()
    assert out.stat().st_size > 1000


def test_pdf_toc_title_and_divider_title_rendering(tmp_path: Path):
    """Verifies that PDF renders toc_title in the TOC and divider_title on the divider page."""
    pytest.importorskip("pypdfium2")
    project = tmp_path / "proj"
    project.mkdir()
    (project / "c1.md").write_text("# Sehr lange Ueberschrift auf der Textseite\n\nFließtext.\n", encoding="utf-8")
    (project / "c2.md").write_text("Text ohne H1.\n", encoding="utf-8")

    (project / "markpublish.yaml").write_text(
        """\
document:
  title: "TOC Test Dokument"
  document_toc: "full"
  cover: true
parts:
  - part: "Hauptabschnitt"
    break_before: "divider"
    divider_title: "Trennseite Hauptabschnitt"
    chapters:
      - file: "c1.md"
        toc_title: "Kurztitel im TOC"
      - file: "c2.md"
        break_before: "divider"
        divider_title: "Trennseite C2"
        toc_title: "Kapitel C2 im TOC"
""",
        encoding="utf-8",
    )

    config = load_config(project / "markpublish.yaml")
    context = DocumentContext(
        config=config,
        content_items=[],
        toc_tree=[],
        template_path=resolve_template_path("pdf", "default"),
        base_dir=project,
        target="pdf",
    )
    context.content_items, context.toc_tree = MarkdownPipeline(
        config, base_dir=project, labels=context.labels
    ).process_document()

    out = project / "test_out.pdf"
    PDFRenderer().render(context, out)
    assert out.is_file()

    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(out))
    full_text = "\n".join(doc[i].get_textpage().get_text_range() for i in range(len(doc)))

    # Trennseiten-Titel vorhanden
    assert "Trennseite Hauptabschnitt" in full_text
    assert "Trennseite C2" in full_text
    # Kurztitel im TOC vorhanden
    assert "Kurztitel im TOC" in full_text
    assert "Kapitel C2 im TOC" in full_text
    # Ausführliche H1 auf Textseite vorhanden
    assert "Sehr lange Ueberschrift auf der Textseite" in full_text

    # TOC-Eintrag fuer Kapitel C2 (ohne H1, aber mit Divider) verweist auf die Dividerseite (5), nicht Textseite (6)
    toc_text = doc[1].get_textpage().get_text_range()
    assert "Kapitel C2 im TOC" in toc_text
    assert "5" in toc_text


def test_pdf_show_title_false_rendering(tmp_path: Path):
    """
    Prueft, dass bei show_title: false die H1 auf der Textseite unterdrueckt wird,
    der Titel auf der Trennseite erscheint und der TOC-Verweis auf die Trennseite zeigt.
    """
    project = tmp_path / "doc"
    project.mkdir()

    (project / "markpublish.yaml").write_text(
        """\
document:
  title: "ShowTitle Test"
  cover: false
  document_toc: "full"
parts:
  - part: "Abschnitt"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "c1.md"
        break_before: "divider"
        show_title: false
""",
        encoding="utf-8",
    )

    (project / "c1.md").write_text(
        "# Kapitel Eins Mit Titel\n\nStart des Inhalts ohne sichtbare H1.\n\n## Unterabschnitt 1",
        encoding="utf-8",
    )

    config = load_config(project / "markpublish.yaml")
    context = DocumentContext(
        config=config,
        content_items=[],
        toc_tree=[],
        template_path=resolve_template_path("pdf", "default"),
        base_dir=project,
        target="pdf",
    )
    context.content_items, context.toc_tree = MarkdownPipeline(
        config, base_dir=project, labels=context.labels
    ).process_document()

    out = project / "out.pdf"
    PDFRenderer().render(context, out)
    assert out.is_file()

    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(out))

    # Seite 1: TOC -> Kapitel Eins Mit Titel verweist auf Seite 2 (Trennseite)
    toc_text = doc[0].get_textpage().get_text_range()
    assert "Kapitel Eins Mit Titel" in toc_text
    assert "2" in toc_text

    # Seite 2: Trennseite -> enthaelt den Titel
    divider_text = doc[1].get_textpage().get_text_range()
    assert "Kapitel Eins Mit Titel" in divider_text

    # Seite 3: Textseite -> enthaelt NICHT die H1, sondern startet direkt mit Inhalt
    content_text = doc[2].get_textpage().get_text_range()
    assert "Start des Inhalts ohne sichtbare H1." in content_text
    assert "Unterabschnitt 1" in content_text
    # Die H1 "Kapitel Eins Mit Titel" darf im Haupttext auf Seite 3 nicht als sichtbare Überschrift erscheinen
    # (ausser in der Kopfzeile oben)
    lines_below_header = content_text.split("\n")[4:]  # Skip header lines
    assert not any("Kapitel Eins Mit Titel" in line for line in lines_below_header)
def test_pdf_part_page_and_chapter_page_do_not_leave_an_empty_page(tmp_path: Path):
    """
    'page' auf Part und Kapitel darf keine leere Seite erzeugen.

    Die Part-Ueberschrift bricht um und steht oben auf der frischen Seite.
    Braeche das erste Kapitel dann ein zweites Mal um, bliebe eine Seite mit
    nichts als der Part-Ueberschrift zurueck - eine Seite, die niemand
    notiert hat und die im Druck bezahlt wird. Der Umbruch haengt deshalb
    daran, ob auf der Seite schon etwas steht, nicht am Schluessel allein.
    """
    pytest.importorskip("pypdfium2")

    (tmp_path / "a.md").write_text("# Kapitel A\n\nText A.\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("# Kapitel B\n\nText B.\n", encoding="utf-8")
    (tmp_path / "markpublish.yaml").write_text(
        """\
document:
  title: "Page Probe"
  language: "de"
  cover: false
  document_toc: "none"
  header: false
  footer: false
parts:
  - part: "Erster Teil"
    break_before: "page"
    chapters:
      - file: "a.md"
        break_before: "page"
      - file: "b.md"
        break_before: "page"
""",
        encoding="utf-8",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    context = DocumentContext(
        config=config,
        content_items=[],
        toc_tree=[],
        template_path=resolve_template_path("pdf", "default"),
        base_dir=tmp_path,
        target="pdf",
    )
    context.content_items, context.toc_tree = MarkdownPipeline(
        config, base_dir=tmp_path, labels=context.labels
    ).process_document()

    out = tmp_path / "probe.pdf"
    PDFRenderer().render(context, out)

    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(str(out))
    pages = [doc[i].get_textpage().get_text_range().strip() for i in range(len(doc))]

    # Zwei Kapitel, zwei Seiten - die Part-Ueberschrift bekommt keine eigene.
    assert len(pages) == 2, pages
    assert "Erster Teil" in pages[0] and "Kapitel A" in pages[0]
    assert "Kapitel B" in pages[1]
    assert all(page for page in pages), "keine Seite darf leer bleiben"
