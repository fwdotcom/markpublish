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

from markpublish.config.loader import load_config
from markpublish.config.models import ChapterItem
from markpublish.markdown.engine import MarkdownEngine, MarkdownPipeline
from markpublish.markdown.toc import (
    NumberingContext,
    process_html_headings_and_toc,
    slugify,
)
from markpublish.renderers.base import DocumentContext, css_string
from markpublish.renderers.html import HTMLRenderer
from markpublish.renderers.pdf import PDFRenderer
from markpublish.templates.resolver import resolve_template_path

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

NESTED_YAML = """
document:
  title: "Verschachtelungs Test"
  author: "Test"
  date: "31.08.2026"
  version: "1.0.0"
  language: "de"
  cover: false
  toc: true
  header: true
  footer: true

theme: "default"

chapters:
  - file: "chapters/parent.md"
    title: "Elternkapitel"
    divider_page: true
    toc: 2
    chapters:
      - file: "chapters/child.md"
        title: "Kindkapitel"
      - file: "chapters/grandchild_host.md"
        title: "Zweites Kind"
        chapters:
          - file: "chapters/grandchild.md"
            title: "Enkelkapitel"

  - part: "Anhaenge"
    divider_page: true
    chapters:
      - file: "chapters/appendix.md"
        title: "Anhang A"
"""

MARKERS = {
    "parent": "MARKER-ELTERN-RUMPF",
    "child": "MARKER-KIND-RUMPF",
    "grandchild_host": "MARKER-KIND2-RUMPF",
    "grandchild": "MARKER-ENKEL-RUMPF",
    "appendix": "MARKER-ANHANG-RUMPF",
}


@pytest.fixture
def nested_project(tmp_path: Path) -> Path:
    """Ein Dokument mit Unterkapiteln, Enkelkapiteln und einem Part."""
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


def render(project: Path, target: str) -> str:
    """Rendert das Projekt und gibt bei HTML den Quelltext zurueck."""
    config = load_config(project / "markpublish.yaml")
    content_items, toc_tree = MarkdownPipeline(config, base_dir=project).process_document()
    context = DocumentContext(
        config=config,
        content_items=content_items,
        toc_tree=toc_tree,
        template_path=resolve_template_path(target, "default"),
        base_dir=project,
        target=target,
    )
    out = project / f"out.{target}"
    if target == "html":
        HTMLRenderer().render(context, out)
        return out.read_text(encoding="utf-8")
    PDFRenderer().render(context, out)
    return ""


# --------------------------------------------------------------------------
# C1 - Verschachtelte Unterkapitel verschwanden aus der Ausgabe
# --------------------------------------------------------------------------

def test_c1_nested_chapter_bodies_are_rendered(nested_project: Path):
    html = render(nested_project, "html")
    for name, marker in MARKERS.items():
        assert marker in html, f"Rumpf von {name}.md fehlt in der Ausgabe"


def test_c1_every_toc_link_has_a_target(nested_project: Path):
    """Anker-Integritaet: kein TOC-Eintrag darf ins Leere zeigen."""
    html = render(nested_project, "html")
    ids = set(re.findall(r'\bid="([^"]+)"', html))
    targets = set(re.findall(r'href="#([^"]+)"', html))
    assert targets, "Test greift nicht - es gibt keine Fragment-Links"
    assert targets <= ids, f"Tote Anker: {sorted(targets - ids)}"


# --------------------------------------------------------------------------
# H5 - Doppelte id-Attribute
# --------------------------------------------------------------------------

def test_h5_ids_are_unique(nested_project: Path):
    html = render(nested_project, "html")
    ids = re.findall(r'\bid="([^"]+)"', html)
    duplicates = {i for i in ids if ids.count(i) > 1}
    assert not duplicates, f"Doppelte ids: {sorted(duplicates)}"


# --------------------------------------------------------------------------
# C2 / C3 - Kopfzeile und TOC-Seitenzahlen im PDF
# --------------------------------------------------------------------------

def _pdf_text(pdf_path: Path) -> str:
    pdfium = pytest.importorskip("pypdfium2")
    doc = pdfium.PdfDocument(str(pdf_path))
    return "\n".join(doc[i].get_textpage().get_text_range() for i in range(len(doc)))


def test_c2_running_header_has_no_stray_glyph(nested_project: Path):
    """`\\A31` wurde als Hex-Escape U+0A31 gelesen statt als Zeilenumbruch."""
    render(nested_project, "pdf")
    text = _pdf_text(nested_project / "out.pdf")
    assert "਱" not in text, "CSS-Escape \\A frisst wieder die Folgeziffern"
    assert "31.08.2026" in text


def test_c3_toc_entries_carry_page_numbers(nested_project: Path):
    render(nested_project, "pdf")
    text = _pdf_text(nested_project / "out.pdf")
    toc_lines = [
        line for line in text.splitlines()
        if "Ueberschrift parent" in line or "Ueberschrift child" in line
    ]
    assert toc_lines, "TOC-Zeilen nicht gefunden"
    assert any(re.search(r"\d+\s*$", line) for line in toc_lines), (
        f"Keine Seitenzahl am Zeilenende: {toc_lines}"
    )


# --------------------------------------------------------------------------
# H2 - toc: {enabled: false} wurde ignoriert
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "toc_value, expected",
    [
        (True, True),
        (False, False),
        (2, True),
        (0, False),
        ({"enabled": True, "max_depth": 2}, True),
        ({"enabled": False, "max_depth": 3}, False),
    ],
)
def test_h2_toc_truthiness(toc_value, expected):
    item = ChapterItem(file="a.md", title="A", toc=toc_value)
    assert bool(item.toc) is expected


# --------------------------------------------------------------------------
# M1 / M2 - Kapitel-TOC: eigene Ueberschrift raus, Tiefe kapitelrelativ
# --------------------------------------------------------------------------

def test_m1_m2_local_toc_scope(nested_project: Path):
    config = load_config(nested_project / "markpublish.yaml")
    content_items, _ = MarkdownPipeline(config, base_dir=nested_project).process_document()

    parent = content_items[0]
    titles = [n.title for n in parent.local_toc_items]

    # M1: die eigene Kapitelueberschrift gehoert nicht in "Inhalt dieses Kapitels"
    assert "Ueberschrift parent" not in titles
    # toc: 2 -> genau die h2-Ebene, nicht h3
    assert "Abschnitt parent" in titles
    assert "Unterabschnitt parent" not in titles


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
    ids = re.findall(r'id="([^"]+)"', out)
    assert len(ids) == len(set(ids)), f"Doppelte ids: {ids}"


# --------------------------------------------------------------------------
# css_string - Apostroph in Ueberschriften bricht die string-set-Deklaration
# --------------------------------------------------------------------------

def test_css_string_escapes_quotes_and_backslashes():
    assert css_string("Frank's Guide") == "Frank\\'s Guide"
    assert css_string("a\\b") == "a\\\\b"
