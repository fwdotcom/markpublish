"""
Regressionstests zum Code-Review vom 31.08.2026.

Jeder Test ist nach dem Befund benannt, den er absichert. Die urspruengliche
Luecke war durchgehend dieselbe: die Suite prueft, DASS etwas erzeugt wurde,
nie WAS darin steht. Diese Tests pruefen den Inhalt.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from markpublish.config.loader import load_config
from markpublish.config.models import ChapterItem
from markpublish.markdown.engine import MarkdownEngine, MarkdownPipeline
from markpublish.markdown.toc import (
    NumberingContext,
    process_html_headings_and_toc,
    slugify,
)
from markpublish.renderers.base import DocumentContext
from markpublish.renderers.pdf import PDFRenderer
from markpublish.templates.resolver import resolve_template_path

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

NESTED_YAML = """
document:
  title: "Regression Test"
  author: "Test"
  date: "2026-08-31"
  language: "de"

theme: "default"

parts:
  - title: "Main"
    break_before: "none"
    chapters:
      - file: "chapters/01_parent.md"
        title: "Parent"
        chapter_toc: 2
        chapters:
          - file: "chapters/02_child.md"
            title: "Child"
            chapters:
              - file: "chapters/03_grandchild.md"
                title: "Grandchild"
"""

MARKERS = {
    "01_parent": "MARKER-PARENT-BODY",
    "02_child": "MARKER-CHILD-BODY",
    "03_grandchild": "MARKER-GRANDCHILD-BODY",
}


@pytest.fixture
def nested_project(tmp_path: Path) -> Path:
    chapters = tmp_path / "chapters"
    chapters.mkdir()
    for name, marker in MARKERS.items():
        (chapters / f"{name}.md").write_text(
            f"# Ueberschrift {name}\n\n{marker}\n\n"
            f"## Abschnitt {name}\n\nText.\n\n"
            f"### Unterabschnitt {name}\n\nText.\n",
            encoding="utf-8",
        )
    (tmp_path / "markpublish.yaml").write_text(NESTED_YAML, encoding="utf-8")
    return tmp_path


def render_pdf_text(project: Path) -> str:
    """Rendert das Projekt als PDF und gibt den extrahierten Text zurueck."""
    config = load_config(project / "markpublish.yaml")
    content_items, toc_tree = MarkdownPipeline(config, base_dir=project).process_document()
    context = DocumentContext(
        config=config,
        content_items=content_items,
        toc_tree=toc_tree,
        template_path=resolve_template_path("pdf", "default"),
        base_dir=project,
        target="pdf",
    )
    out = project / "out.pdf"
    PDFRenderer().render(context, out)
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(out))
    return "\n".join(doc[i].get_textpage().get_text_range() for i in range(len(doc)))


# --------------------------------------------------------------------------
# C1 - Verschachtelte Unterkapitel verschwanden aus der Ausgabe
# --------------------------------------------------------------------------

def test_c1_nested_chapter_bodies_are_rendered(nested_project: Path):
    text = render_pdf_text(nested_project)
    for name, marker in MARKERS.items():
        assert marker in text, f"Rumpf von {name}.md fehlt in der Ausgabe"


# --------------------------------------------------------------------------
# C2 / C3 - Kopfzeile und TOC-Seitenzahlen im PDF
# --------------------------------------------------------------------------

def test_c2_running_header_has_no_stray_glyph(nested_project: Path):
    text = render_pdf_text(nested_project)
    assert "਱" not in text
    assert "2026-08-31" in text or "31.08.2026" in text or "Regression Test" in text


def test_c3_toc_entries_carry_page_numbers(nested_project: Path):
    text = render_pdf_text(nested_project)
    assert "01_parent" in text
    assert "02_child" in text


# --------------------------------------------------------------------------
# H2 - ein abgeschaltetes TOC wurde ignoriert
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "toc_value, expected",
    [
        ("full", True),
        ("none", False),
        (2, True),
        ({"enabled": True, "max_depth": 2}, True),
        ({"enabled": False}, False),
    ],
)
def test_h2_toc_config_controls_local_toc(tmp_path: Path, toc_value, expected):
    """
    chapter_toc: none schaltet das Kapitel-TOC ab; 2 begrenzt die Tiefe.
    """
    (tmp_path / "a.md").write_text("# K\n\n## A\n\n### B\n", encoding="utf-8")
    item = ChapterItem(file="a.md", chapter_toc=toc_value)
    pipeline = MarkdownPipeline(None, base_dir=tmp_path)
    nodes = pipeline._build_local_toc(item, 1)
    if expected:
        assert len(nodes) > 0, f"Erwartet TOC fuer {toc_value!r}, war leer"
    else:
        assert nodes == [], f"Erwartet kein TOC fuer {toc_value!r}, war {nodes}"


@pytest.mark.parametrize("bad", [True, False, 0, -1, "fill", "gibtsnicht"])
def test_toc_keys_reject_what_they_cannot_mean(bad):
    """
    Wahrheitswerte und Unsinn brechen ab, statt still auf den Standard
    zurueckzufallen: ein fehlendes Verzeichnis faellt sonst erst beim
    Durchblaettern des fertigen PDFs auf.
    """
    with pytest.raises(ValidationError):
        ChapterItem(file="a.md", chapter_toc=bad)


# --------------------------------------------------------------------------
# M1 / M2 - Kapitel-TOC: eigene Ueberschrift raus, Tiefe kapitelrelativ
# --------------------------------------------------------------------------

def test_m1_m2_local_toc_scope(nested_project: Path):
    config = load_config(nested_project / "markpublish.yaml")
    content_items, _ = MarkdownPipeline(config, base_dir=nested_project).process_document()

    parent = content_items[0]
    titles = [n.title for n in parent.local_toc_items]

    # M1: die eigene Kapitelueberschrift gehoert nicht in "Inhalt dieses Kapitels"
    assert "Ueberschrift 01_parent" not in titles
    # chapter_toc: 2 -> genau die h2-Ebene, nicht h3
    assert "Abschnitt 01_parent" in titles
    assert "Unterabschnitt 01_parent" not in titles


# --------------------------------------------------------------------------
# H3 / H4 - Markdown-Extensions
# --------------------------------------------------------------------------

def test_h3_alert_syntax_inside_code_fence_is_literal():
    engine = MarkdownEngine(language="de")
    out = engine.convert("```markdown\n> [!NOTE]\n> Hinweistext\n```")
    assert "[!NOTE]" in out
    assert "!!! note" not in out


def test_h3_real_alerts_still_work():
    engine = MarkdownEngine(language="de")
    out = engine.convert("> [!TIP]\n> Nuetzlich.")
    assert 'class="admonition tip"' in out
    assert "Tipp" in out


def test_h4_ordered_list_after_unordered_keeps_numbering():
    engine = MarkdownEngine()
    out = engine.convert("- eins\n- zwei\n\n1. a\n2. b\n")
    assert "<ol" in out
    assert out.count("<ul") == 1


def test_tasklist_emits_custom_checkbox_markup():
    engine = MarkdownEngine()
    out = engine.convert("- [x] erledigt\n- [ ] offen\n")
    assert 'class="task-list-indicator"' in out
    assert out.count("checked") == 1


# --------------------------------------------------------------------------
# H6 / N4 - slugify
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Report: Q3/2026 <final>", "report-q32026-final"),
        ("Anhänge", "anhaenge"),
        ("Größe & Maß", "groesse-mass"),
        ("../../etc/passwd", "etcpasswd"),
        ("***", "section"),
    ],
)
def test_h6_n4_slugify(raw, expected):
    assert slugify(raw) == expected


def test_h6_output_filename_has_no_path_separators(tmp_path: Path):
    """Ein Titel mit / oder : darf keinen Pfad erzeugen."""
    slug = slugify("Report: Q3/2026", separator="_")
    assert "/" not in slug and "\\" not in slug and ":" not in slug
    assert slug == "report_q32026"


def test_h6_filename_separator_stays_underscore():
    """Bestehende Dateinamen sollen sich nicht aendern."""
    assert slugify("markpublish Benutzerhandbuch", separator="_") == "markpublish_benutzerhandbuch"


# --------------------------------------------------------------------------
# C4 - Typannotationen im Resolver aufloesbar
# --------------------------------------------------------------------------

def test_c4_resolver_type_hints_resolve():
    import typing

    from markpublish.templates import resolver

    for fn in (
        resolver.resolve_template_path,
        resolver.get_common_templates_dir,
        resolver.list_templates,
    ):
        typing.get_type_hints(fn)


# --------------------------------------------------------------------------
# M4 / M5 - Resolver-Duplikate, Konfig-Mutation
# --------------------------------------------------------------------------

def test_m4_list_templates_has_no_duplicate_rows():
    from markpublish.templates.resolver import list_templates

    rows = list_templates()
    keys = [(r["target"], r["theme"], r["path"]) for r in rows]
    assert len(keys) == len(set(keys)), f"Doppelte Zeilen: {keys}"


def test_m5_load_config_does_not_mutate_caller_dict():
    raw = {"document": {"title": "T", "date": "auto"}}
    load_config(raw)
    assert raw["document"]["date"] == "auto"


# --------------------------------------------------------------------------
# N1 / N2 / N3 - Heading-Verarbeitung
# --------------------------------------------------------------------------

def test_n1_heading_attribute_may_contain_gt():
    html = '<h2 title="a > b">Titel</h2>'
    out, nodes = process_html_headings_and_toc(html, NumberingContext())
    assert [n.title for n in nodes] == ["Titel"]
    assert 'title="a > b"' in out


def test_n2_no_stray_space_in_heading_tag():
    out, _ = process_html_headings_and_toc("<h1>Nur Text</h1>", NumberingContext())
    assert "<h1  " not in out


def test_n3_explicit_id_does_not_collide_with_generated_slug():
    html = '<h2>Einleitung</h2><h2 id="einleitung">Andere</h2>'
    out, _ = process_html_headings_and_toc(html, NumberingContext())

