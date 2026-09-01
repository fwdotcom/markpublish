"""
Tests for PDF and HTML rendering.
"""

import re
from pathlib import Path

import pytest

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


# --------------------------------------------------------------------------
# Deckblatt: leere Felder erscheinen nicht
# --------------------------------------------------------------------------

COVER_YAML = """\

document:
  title: "Deckblatt Test"
{version}
  author: "Test"
  date: "01.09.2026"
  language: "de"
  cover: true
  document_toc: "none"

theme: "default"

parts:
  - title: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "chapters/01.md"
        title: "Kapitel"
"""


def _render_cover_html(tmp_path: Path, version: str = "") -> str:
    chapters = tmp_path / "chapters"
    chapters.mkdir(parents=True, exist_ok=True)
    (chapters / "01.md").write_text("# K\n\nText.\n", encoding="utf-8")
    (tmp_path / "markpublish.yaml").write_text(
        COVER_YAML.format(version=f'  version: "{version}"' if version else ""),
        encoding="utf-8",
    )

    config = load_config(tmp_path / "markpublish.yaml")
    pipeline = MarkdownPipeline(config, base_dir=tmp_path)
    content_items, toc_tree = pipeline.process_document()
    context = DocumentContext(
        config=config,
        content_items=content_items,
        toc_tree=toc_tree,
        template_path=resolve_template_path("html", "default"),
        base_dir=tmp_path,
        target="html",
    )
    out = tmp_path / "cover.html"
    HTMLRenderer().render(context, out)
    return out.read_text(encoding="utf-8")


def test_cover_shows_the_version_when_given(tmp_path: Path):
    html = _render_cover_html(tmp_path, version="2.3.0")
    assert "2.3.0" in html


def test_cover_omits_the_version_field_when_unset(tmp_path: Path):
    """
    Kein Default-Wert im Modell mehr - sonst stuende auf jedem Deckblatt eine
    erfundene "1.0.0", die sich nicht abschalten liesse.
    """
    html = _render_cover_html(tmp_path)

    # Der Titel enthaelt das Wort nicht, also ist jeder Treffer das Label.
    assert "Version" not in html
    assert "1.0.0" not in html


# --------------------------------------------------------------------------
# Trennseiten und Kapitel-TOC: nur im PDF
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


def _render_target(tmp_path: Path, target: str) -> str:
    config = load_config(tmp_path / "markpublish.yaml")
    context = DocumentContext(
        config=config,
        content_items=[],
        toc_tree=[],
        template_path=resolve_template_path(target, "default"),
        base_dir=tmp_path,
        target=target,
    )
    context.content_items, context.toc_tree = MarkdownPipeline(
        config, base_dir=tmp_path, labels=context.labels
    ).process_document()

    renderer = HTMLRenderer() if target == "html" else PDFRenderer()
    out = tmp_path / f"out.{target}"
    renderer.render(context, out)
    return out.read_text(encoding="utf-8") if target == "html" else ""


def _markup_only(html: str) -> str:
    """Ohne das eingebettete Stylesheet - dort stehen die Klassennamen als CSS."""
    return html[html.rindex("</style>"):]


def test_html_theme_renders_no_divider_pages(tmp_path: Path):
    """
    Am Bildschirm gibt es keine Seiten: die Trennseite markiert einen
    Kapitelanfang, den die Seitenleiste ohnehin zeigt, und das Kapitel-TOC
    wiederholt deren Eintraege ein zweites Mal.
    """
    markup = _markup_only(_render_target(_divider_project(tmp_path), "html"))

    assert "chapter-divider" not in markup
    assert "part-divider" not in markup
    assert "local-toc" not in markup


def test_html_keeps_the_part_anchor_the_sidebar_links_to(tmp_path: Path):
    """
    Die <section id="part-..."> bleibt, auch ohne Trennseite - sonst liefe der
    Eintrag der Seitenleiste ins Leere.
    """
    markup = _markup_only(_render_target(_divider_project(tmp_path), "html"))

    targets = set(re.findall(r'id="(part-[^"]+)"', markup))
    links = set(re.findall(r'href="#(part-[^"]+)"', markup))
    assert links, "Kein Part-Eintrag in der Seitenleiste"
    assert links <= targets, f"Sidebar verlinkt ins Leere: {links - targets}"


def test_pdf_theme_still_renders_divider_pages(tmp_path: Path):
    """Gegenprobe: im PDF bleibt beides unveraendert."""
    pytest.importorskip("pypdfium2")
    project = _divider_project(tmp_path)
    _render_target(project, "pdf")

    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(str(project / "out.pdf"))
    text = "\n".join(
        doc[i].get_textpage().get_text_range() for i in range(len(doc))
    )

    # Die Marken stehen im Theme auf text-transform: uppercase.
    assert "KAPITEL 1" in text.upper()
    assert "Zusammenfassung des Kapitels." in text
    assert "Abschnitt A" in text
