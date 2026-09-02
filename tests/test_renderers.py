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
