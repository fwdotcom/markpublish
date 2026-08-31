"""
Tests for PDF and HTML rendering.
"""

from pathlib import Path

from markpublish.config.loader import load_config
from markpublish.markdown.engine import MarkdownPipeline
from markpublish.renderers.base import DocumentContext
from markpublish.renderers.html import HTMLRenderer
from markpublish.renderers.pdf import PDFRenderer
from markpublish.templates.resolver import resolve_template_path


def test_full_pipeline_html_and_pdf(tmp_path: Path):
    # Create sample document setup in tmp_path
    chapters_dir = tmp_path / "chapters"
    chapters_dir.mkdir()

    (chapters_dir / "01.md").write_text("# Einleitung\n\nDas ist die Einleitung.", encoding="utf-8")
    (chapters_dir / "02.md").write_text("# Hauptteil\n\n## Detail\n\nInhalt hier.", encoding="utf-8")

    yaml_content = """
document:
  title: "End-to-End Test Document"
  subtitle: "Integration Test"
  author: "Test Runner"
  date: "2026-08-31"
  version: "1.0.0"
  language: "de"
  cover: true
  toc: true
  header: true
  footer: true

theme: "default"

chapters:
  - file: "chapters/01.md"
    title: "Einleitung"
    divider_page: true
    toc: false
  - file: "chapters/02.md"
    title: "Hauptteil"
    divider_page: true
    toc: 2
"""
    config_file = tmp_path / "markpublish.yaml"
    config_file.write_text(yaml_content, encoding="utf-8")

    config = load_config(config_file)
    pipeline = MarkdownPipeline(config, base_dir=tmp_path)
    content_items, toc_tree = pipeline.process_document()

    # 1. Test HTML Renderer
    html_template = resolve_template_path("html", "default")
    html_context = DocumentContext(
        config=config,
        content_items=content_items,
        toc_tree=toc_tree,
        template_path=html_template,
        base_dir=tmp_path,
        target="html",
    )
    html_out = tmp_path / "output.html"
    HTMLRenderer().render(html_context, html_out)
    assert html_out.is_file()
    html_text = html_out.read_text(encoding="utf-8")
    assert "End-to-End Test Document" in html_text
    assert "Einleitung" in html_text
    assert "Hauptteil" in html_text

    # 2. Test PDF Renderer
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

