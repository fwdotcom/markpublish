"""
Tests fuer Kopf- und Fusszeile des PDF-Themes.

Kopf und Fuss sind Running Elements (`position: running()`, eingesetzt ueber
`content: element()`), nicht eine `content`-Zeichenkette mit `\\A`-Umbruch.
Das ist der Unterschied, um den es hier geht:

  * echtes Markup -> pro Zeile eigene Auszeichnung (Titel fett, Untertitel nicht)
  * Flex-Container -> die rechte Spalte beginnt oben, auch wenn die linke
    mehr Zeilen hat
  * beliebig viele Zeilen -> der Seitenrand wird aus der Zeilenzahl gerechnet

Geprueft wird am Layoutbaum, nicht am Bild: eine Verschiebung um Millimeter
faellt in einem Textvergleich nicht auf, hier schon.

Geometrie, von der Papierkante nach innen:

    Kante -> 12mm -> Zeilen (top-aligned) -> Linie -> 12mm -> Inhalt
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import pytest

from markpublish.config.loader import load_config
from markpublish.markdown.engine import MarkdownPipeline
from markpublish.renderers.base import DocumentContext
from markpublish.templates.resolver import resolve_template_path

pytestmark = pytest.mark.skip(reason="WeasyPrint CSS Paged Media tests replaced by Typst native header/footer engine")

PX_PER_MM = 96 / 25.4

#: Muss zu hf_edge_mm / hf_gap_mm in default/pdf/styles.css passen.
EDGE_MM = 12.0
GAP_MM = 12.0

YAML = """\

document:
  title: "Kopfzeilen Test"
{subtitle}
{version}
  author: "Test"
  copyright: "(c) 2026 Test"
  date: "31.08.2026"
  language: "de"
  cover: false
  document_toc: "none"
  header: true
  footer: true

theme: "default"

parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "chapters/01.md"
      - file: "chapters/02.md"
"""


def build_pages(tmp_path: Path, subtitle: bool = True, version: str = ""):
    """Rendert das Testdokument und gibt die Seitenobjekte von WeasyPrint zurueck."""
    # Nicht importorskip("weasyprint"): der Import allein schlaegt fehl, solange
    # das GTK-Verzeichnis nicht im Suchpfad steht. _load_weasyprint() richtet es
    # ein - denselben Weg nimmt der Renderer.
    from markpublish.renderers.pdf import PDFRenderer, _load_weasyprint

    html_cls, error = _load_weasyprint()
    if html_cls is None:
        pytest.skip(f"WeasyPrint/GTK nicht verfuegbar: {error}")

    chapters = tmp_path / "chapters"
    chapters.mkdir(parents=True, exist_ok=True)
    for name in ("01", "02"):
        (chapters / f"{name}.md").write_text(
            f"# Kapitel {name}\n\n" + ("Fliesstext. " * 60 + "\n\n") * 6,
            encoding="utf-8",
        )

    (tmp_path / "markpublish.yaml").write_text(
        YAML.format(
            subtitle='  subtitle: "Der Untertitel"' if subtitle else "",
            version=f'  version: "{version}"' if version else "",
        ),
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

    # render_template() statt render(): der Layoutbaum wird gebraucht, nicht
    # die fertige Datei.
    html = PDFRenderer().render_template(context, template_name="layout.html")
    return html_cls(string=html, base_url=str(tmp_path)).render().pages


def collect(box, class_name: str, out: List) -> List:
    if type(box).__name__ == class_name:
        out.append(box)
    for child in getattr(box, "all_children", lambda: [])():
        collect(child, class_name, out)
    return out


def margin_box(page, keyword: str):
    for box in collect(page._page_box, "MarginBox", []):
        if box.at_keyword == keyword:
            return box
    return None


def texts(box):
    """[(y_mm, x_mm, fett, Text)], nach Position sortiert."""
    result = [
        (
            round(t.position_y / PX_PER_MM, 2),
            round(t.position_x / PX_PER_MM, 2),
            t.style["font_weight"] >= 700,
            t.text,
        )
        for t in collect(box, "TextBox", [])
    ]
    return sorted(result)


def first_page_with_header(pages):
    for page in pages:
        box = margin_box(page, "@top-left")
        if box is not None and texts(box):
            return page
    raise AssertionError("Keine Seite mit Kopfzeile gefunden")


# --------------------------------------------------------------------------
# Echtes Markup: verschiedene Auszeichnung pro Zeile
# --------------------------------------------------------------------------

def test_header_title_is_bold_and_subtitle_is_not(tmp_path: Path):
    """
    Der Kern der Umstellung. Eine content-Zeichenkette kennt nur EINE
    Formatierung fuer alle ihre Zeilen - fett neben normal ging damit nicht.
    """
    page = first_page_with_header(build_pages(tmp_path))
    lines = texts(margin_box(page, "@top-left"))

    title = [line for line in lines if "Kopfzeilen Test" in line[3]]
    subtitle = [line for line in lines if "Untertitel" in line[3]]
    assert title and subtitle

    assert title[0][2] is True, "Dokumenttitel muss fett sein"
    assert subtitle[0][2] is False, "Untertitel darf nicht fett sein"


# --------------------------------------------------------------------------
# Ungleich lange Spalten: rechts bleibt oben
# --------------------------------------------------------------------------

def test_right_column_is_top_aligned_with_the_left(tmp_path: Path):
    """
    Links zwei Zeilen (Titel + Untertitel), rechts eine (Kapiteltitel). Die
    rechte Zeile muss auf der Hoehe der ERSTEN linken sitzen, nicht mittig und
    nicht unten.
    """
    page = first_page_with_header(build_pages(tmp_path))
    lines = texts(margin_box(page, "@top-left"))

    left = [line for line in lines if line[1] < 100]
    right = [line for line in lines if line[1] >= 100]
    assert len(left) >= 2, f"Erwartet zwei linke Zeilen: {lines}"
    assert len(right) == 1, f"Erwartet eine rechte Zeile: {lines}"

    assert right[0][0] == left[0][0], (
        f"Rechte Spalte nicht top-aligned: rechts y={right[0][0]}, "
        f"links y={left[0][0]}"
    )


def test_footer_columns_start_on_the_same_line(tmp_path: Path):
    """Fusszeile umgekehrt: links eine Zeile, rechts zwei (Datum, Seitenzahl)."""
    page = first_page_with_header(build_pages(tmp_path))
    lines = texts(margin_box(page, "@bottom-left"))

    left = [line for line in lines if line[1] < 100]
    right = [line for line in lines if line[1] >= 100]
    assert len(left) == 1, f"Erwartet eine linke Zeile: {lines}"
    assert len(right) == 2, f"Erwartet zwei rechte Zeilen: {lines}"

    assert left[0][0] == right[0][0]
    assert right[1][0] > right[0][0], "Seitenzahl gehoert unter das Datum"


# --------------------------------------------------------------------------
# Geometrie: Rand zur Kante, Linie am Text, Abstand zum Inhalt
# --------------------------------------------------------------------------

def test_header_keeps_its_margin_to_the_paper_edge(tmp_path: Path):
    page = first_page_with_header(build_pages(tmp_path))
    lines = texts(margin_box(page, "@top-left"))
    assert lines[0][0] == pytest.approx(EDGE_MM, abs=0.05)


def test_rule_sits_directly_below_the_header_text(tmp_path: Path):
    """
    Die Linie gehoert an den Text, der Abstand danach. Mit padding-bottom
    stuende sie am Inhalt und der Abstand ueber ihr - genau andersherum.
    """
    page = first_page_with_header(build_pages(tmp_path))
    box = margin_box(page, "@top-left")

    text_bottom = (box.content_box_y() + box.height) / PX_PER_MM
    rule = (box.border_box_y() + box.border_height()) / PX_PER_MM

    # Nur die Linienstaerke selbst (0.5pt = 0.18mm) darf dazwischen liegen.
    assert rule - text_bottom == pytest.approx(0.0, abs=0.3)


def test_gap_between_rule_and_content(tmp_path: Path):
    pages = build_pages(tmp_path)
    page = first_page_with_header(pages)
    box = margin_box(page, "@top-left")
    rule = (box.border_box_y() + box.border_height()) / PX_PER_MM

    body = collect(page._page_box.children[0], "LineBox", [])
    assert body, "Kein Inhalt auf der Seite"
    first_line = min(line.position_y for line in body) / PX_PER_MM

    assert first_line - rule == pytest.approx(GAP_MM, abs=0.05)


def test_page_margin_follows_the_line_count(tmp_path: Path):
    """
    Eine Margin-Box schiebt den Inhalt nicht - der Seitenrand muss also aus der
    Zeilenzahl gerechnet werden. Faellt der Untertitel weg, ruecken Linie und
    Inhalt genau eine Zeile hoch.
    """
    with_subtitle = first_page_with_header(build_pages(tmp_path / "mit"))
    without = first_page_with_header(build_pages(tmp_path / "ohne", subtitle=False))

    def content_top(page):
        body = collect(page._page_box.children[0], "LineBox", [])
        return min(line.position_y for line in body) / PX_PER_MM

    line_mm = 8 * 1.3 * 25.4 / 72
    delta = content_top(with_subtitle) - content_top(without)
    assert delta == pytest.approx(line_mm, abs=0.1), (
        f"Seitenrand folgt der Zeilenzahl nicht: {delta:.2f}mm statt {line_mm:.2f}mm"
    )

    # Der Abstand zur Papierkante bleibt derselben.
    assert texts(margin_box(without, "@top-left"))[0][0] == pytest.approx(EDGE_MM, abs=0.05)


# --------------------------------------------------------------------------
# Laufende Inhalte
# --------------------------------------------------------------------------

def test_page_counter_runs_inside_the_running_element(tmp_path: Path):
    """counter(page) funktioniert auch im Running Element - sonst staende
    ueberall dieselbe Seitenzahl."""
    pages = build_pages(tmp_path)
    seen = []
    for page in pages:
        box = margin_box(page, "@bottom-left")
        if box is None:
            continue
        seen += [line[3] for line in texts(box) if line[3].startswith("Seite ")]

    assert len(seen) >= 2, f"Zu wenige Fusszeilen: {seen}"
    assert seen[0] != seen[1], f"Seitenzahl aendert sich nicht: {seen[:2]}"
    assert seen[0].endswith(f"von {len(pages)}")


def _footer_meta_line(pages) -> str:
    """Die erste rechte Fusszeilenzeile - Version und/oder Datum."""
    page = first_page_with_header(pages)
    lines = texts(margin_box(page, "@bottom-left"))
    right = [line for line in lines if line[1] >= 100]
    assert right, f"Keine rechte Fusszeilenspalte: {lines}"
    return right[0][3]


def test_footer_prints_the_version_next_to_the_date(tmp_path: Path):
    assert _footer_meta_line(build_pages(tmp_path, version="1.0.0")) == (
        "Version 1.0.0 | 31.08.2026"
    )


def test_footer_drops_the_separator_without_a_version(tmp_path: Path):
    """
    Ohne Version darf kein einsames "| 31.08.2026" stehenbleiben - der Trenner
    gehoert zur Version, nicht zur Zeile.
    """
    line = _footer_meta_line(build_pages(tmp_path))
    assert line == "31.08.2026"
    assert "|" not in line


def test_version_defaults_to_unset(tmp_path: Path):
    """
    Ohne Angabe bleibt die Version leer. Ein erfundener Default liesse sich
    nicht abschalten: jedes Template saehe einen gesetzten Wert und druckte ihn.
    """
    (tmp_path / "chapters").mkdir(parents=True, exist_ok=True)
    (tmp_path / "chapters" / "01.md").write_text("# K\n\nText.\n", encoding="utf-8")
    (tmp_path / "markpublish.yaml").write_text(
        YAML.format(subtitle="", version=""), encoding="utf-8"
    )
    assert load_config(tmp_path / "markpublish.yaml").document.version is None


def test_chapter_title_follows_the_chapter(tmp_path: Path):
    """Der Kapiteltitel kommt aus string(current-section) im Running Element."""
    pages = build_pages(tmp_path)
    titles = []
    for page in pages:
        box = margin_box(page, "@top-left")
        if box is None:
            continue
        right = [line[3] for line in texts(box) if line[1] >= 100]
        titles += right

    assert "Erstes Kapitel" in titles
    assert "Zweites Kapitel" in titles

