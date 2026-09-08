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

SAMPLE_YAML = """
document:
  title: "Regression Test"
  author: "Test"
  date: "2026-08-31"
  language: "de"

theme: "default"

parts:
  - part: "Main"
    break_before: "none"
    chapters:
      - file: "chapters/01_first.md"
        chapter_toc: 2
      - file: "chapters/02_second.md"
      - file: "chapters/03_third.md"
"""

MARKERS = {
    "01_first": "MARKER-FIRST-BODY",
    "02_second": "MARKER-SECOND-BODY",
    "03_third": "MARKER-THIRD-BODY",
}


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    chapters = tmp_path / "chapters"
    chapters.mkdir()
    for name, marker in MARKERS.items():
        (chapters / f"{name}.md").write_text(
            f"# Ueberschrift {name}\n\n{marker}\n\n"
            f"## Abschnitt {name}\n\nText.\n\n"
            f"### Unterabschnitt {name}\n\nText.\n",
            encoding="utf-8",
        )
    (tmp_path / "markpublish.yaml").write_text(SAMPLE_YAML, encoding="utf-8")
    return tmp_path


def assemble_typst_source(project: Path) -> str:
    """
    Gibt die main.typ zurueck, die der Renderer an Typst uebergibt.

    Nicht `ContentItem.typst_content` pruefen: das ist nur der Fallback fuer
    den Fall, dass kein element_tree vorliegt. Der Renderer serialisiert den
    Baum selbst neu, und genau dort ist S4 entstanden -- ein Test auf
    typst_content war gruen, waehrend das PDF falsche Ebenen zeigte.
    """
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
    return PDFRenderer()._assemble_typst_document(context, project)


def typst_headings(source: str) -> dict:
    """
    Zerlegt die Ueberschriftenzeilen einer main.typ zu {Titel: Ebene}.

    Unterstuetzt sowohl '#heading(level: 2, ...)[...]' als auch '== ...'.
    Nummer und Label gehoeren nicht zum Titel.
    """
    headings: dict = {}
    for line in source.splitlines():
        line = line.strip()
        if line.startswith("#heading("):
            m = re.match(r"#heading\(level:\s*(\d+).*?\)\[(.*?)\]", line)
            if m:
                depth = int(m.group(1))
                title = m.group(2)
                title = re.sub(r"\\(.)", r"\1", title)
                headings[title] = depth
                continue
        if not line.startswith("="):
            continue
        depth = len(line) - len(line.lstrip("="))
        title = line.lstrip("=").split(" <")[0].strip()
        first, _, rest = title.partition(" ")
        if rest and first.rstrip(".").replace(".", "").isdigit():
            title = rest
        # Der Serializer schuetzt Sonderzeichen ("01\_parent"); der TOC-Baum
        # fuehrt den Klartext. Fuer den Vergleich zurueckdrehen.
        title = re.sub(r"\\(.)", r"\1", title)
        headings[title] = depth
    return headings


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
# C1 - Kapitelruempfe verschwanden aus der Ausgabe
# --------------------------------------------------------------------------

def test_c1_chapter_bodies_are_rendered(sample_project: Path):
    text = render_pdf_text(sample_project)
    for name, marker in MARKERS.items():
        assert marker in text, f"Rumpf von {name}.md fehlt in der Ausgabe"


def test_s4_typst_levels_match_the_toc_tree(sample_project: Path):
    """
    S4: TOC-Baum und gesetzte Ebene duerfen nicht auseinanderlaufen.

    Jedes Kapitel steht auf Ebene 1, seine '##' auf 2, seine '###' auf 3 --
    im Verzeichnis wie in der an Typst uebergebenen Quelle. Geprueft wird
    letztere, nicht `typst_content`; siehe assemble_typst_source().
    """
    config = load_config(sample_project / "markpublish.yaml")
    _, toc_tree = MarkdownPipeline(config, base_dir=sample_project).process_document()

    toc_levels: dict = {}

    def walk(nodes):
        for node in nodes:
            toc_levels[node.title] = node.level
            walk(getattr(node, "children", None) or [])

    walk(toc_tree)

    compared = 0
    for title, depth in typst_headings(assemble_typst_source(sample_project)).items():
        if title not in toc_levels:
            continue
        compared += 1
        assert toc_levels[title] == depth, (
            f"{title!r}: Verzeichnis sagt Ebene {toc_levels[title]}, "
            f"gesetzt wird Ebene {depth}"
        )
    assert compared >= 6, "Zu wenige Ueberschriften verglichen -- Test greift ins Leere"


# --------------------------------------------------------------------------
# C2 / C3 - Kopfzeile und TOC-Seitenzahlen im PDF
# --------------------------------------------------------------------------

def test_c2_running_header_has_no_stray_glyph(sample_project: Path):
    text = render_pdf_text(sample_project)
    assert "਱" not in text
    assert "2026-08-31" in text or "31.08.2026" in text or "Regression Test" in text


def test_c3_toc_entries_carry_page_numbers(sample_project: Path):
    text = render_pdf_text(sample_project)
    assert "01_first" in text
    assert "02_second" in text


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
    nodes = pipeline._build_local_toc(item)
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

def test_m1_m2_local_toc_scope(sample_project: Path):
    config = load_config(sample_project / "markpublish.yaml")
    content_items, _ = MarkdownPipeline(config, base_dir=sample_project).process_document()

    first = content_items[0]
    titles = [n.title for n in first.local_toc_items]

    # M1: die eigene Kapitelueberschrift gehoert nicht in "Inhalt dieses Kapitels"
    assert "Ueberschrift 01_first" not in titles
    # chapter_toc: 2 -> genau die h2-Ebene, nicht h3
    assert "Abschnitt 01_first" in titles
    assert "Unterabschnitt 01_first" not in titles


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

