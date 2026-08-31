"""
Tests fuer das Satzbild des Default-PDF-Themes.

Zwei Dinge, die ein Textvergleich nicht sieht und die trotzdem sofort auffallen,
sobald sie kippen:

  * das Inhaltsverzeichnis laeuft auf einem festen Zeilenraster. Vorher hatte
    jede Gliederungsebene eigene Schriftgroesse UND eigene Abstaende - vier
    Zeilenhoehen uebereinander, ohne dass die Gliederung dadurch klarer wurde.
  * die Schriften kommen aus einer Stelle (:root), nicht aus fuenf verstreuten
    font-family-Deklarationen.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import pytest

from markpublish.config.loader import load_config
from markpublish.markdown.engine import MarkdownPipeline
from markpublish.renderers.base import DocumentContext
from markpublish.templates.resolver import resolve_template_path

PX_PER_MM = 96 / 25.4

#: Muss zu --toc-line in default/pdf/styles.css passen.
TOC_LINE_MM = 6.0

YAML = """
document:
  title: "Raster Test"
  author: "Test"
  date: "01.09.2026"
  language: "de"
  cover: false
  toc: true

theme: "default"

chapters:
  - file: "chapters/01.md"
    title: "Erstes Kapitel"
  - file: "chapters/02.md"
    title: "Zweites Kapitel"
  - part: "Anhaenge"
    chapters:
      - file: "chapters/03.md"
        title: "Anhang A"
"""

CHAPTER_MD = """# {title}

Text.

## Abschnitt eins

Text.

### Unterabschnitt

Text.

## Abschnitt zwei

Text.
"""


def build_pages(tmp_path: Path):
    from markpublish.renderers.pdf import PDFRenderer, _load_weasyprint

    html_cls, error = _load_weasyprint()
    if html_cls is None:
        pytest.skip(f"WeasyPrint/GTK nicht verfuegbar: {error}")

    chapters = tmp_path / "chapters"
    chapters.mkdir(parents=True, exist_ok=True)
    for name, title in (("01", "Eins"), ("02", "Zwei"), ("03", "Anhang A")):
        (chapters / f"{name}.md").write_text(
            CHAPTER_MD.format(title=title), encoding="utf-8"
        )
    (tmp_path / "markpublish.yaml").write_text(YAML, encoding="utf-8")

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

    html = PDFRenderer().render_template(context, template_name="layout.html")
    return html_cls(string=html, base_url=str(tmp_path)).render().pages


def walk(box, out: List) -> List:
    out.append(box)
    for child in getattr(box, "all_children", lambda: [])():
        walk(child, out)
    return out


def toc_rows(page):
    """(y_mm, {css_klassen}) je Rasterzeile.

    Ein <li> einer Ebene enthaelt die <ul> der naechsten, und nach einem
    Seitenumbruch beginnen die Fortsetzungen aller Ebenen an derselben Stelle -
    auf einer Hoehe koennen deshalb mehrere Eintraege liegen. Gesammelt werden
    alle Klassen dieser Hoehe, sonst haengt das Ergebnis davon ab, welche
    Verschachtelungsebene der Baumdurchlauf zuletzt gesehen hat.
    """
    rows: dict = {}
    for box in walk(page._page_box, []):
        element = getattr(box, "element", None)
        if element is None or type(box).__name__ != "BlockBox":
            continue
        css = element.get("class") or ""
        if "toc-item" not in css:
            continue
        # content_box_y() statt position_y: letzteres ist die Oberkante der
        # Margin-Box. Der Abstand vor einem Part-Eintrag erschiene damit hinter
        # ihm statt davor - gemessen werden soll, wo der Text steht.
        rows.setdefault(round(box.content_box_y() / PX_PER_MM, 2), set()).update(css.split())
    return sorted(rows.items())


def toc_steps(pages):
    """[(schritt_mm, klassen_der_folgezeile)] - nur innerhalb einer Seite.

    Ueber einen Seitenumbruch hinweg ist die Differenz zweier Positionen
    bedeutungslos, deshalb wird pro Seite gepaart.
    """
    steps = []
    for page in pages:
        rows = toc_rows(page)
        # strict=False ist hier gewollt: die zweite Liste ist um eins kuerzer.
        steps += [
            (round(later[0] - earlier[0], 2), later[1])
            for earlier, later in zip(rows, rows[1:], strict=False)
        ]
    return steps


def test_toc_uses_one_uniform_line_height(tmp_path: Path):
    """
    Jeder Eintrag belegt genau eine Rasterzeile - unabhaengig von der
    Gliederungsebene.
    """
    steps = toc_steps(build_pages(tmp_path))
    assert len(steps) > 8, f"Zu wenige TOC-Eintraege zum Messen: {steps}"

    levels = {c for _, css in steps for c in css if "toc-item-part" not in c}
    assert len(levels) >= 3, f"Test braucht mehrere Gliederungsebenen: {levels}"

    normal = [step for step, css in steps if "toc-item-part" not in css]
    assert set(normal) == {TOC_LINE_MM}, (
        f"Uneinheitliche Zeilenabstaende im TOC: {sorted(set(normal))}"
    )


def test_toc_part_entry_keeps_the_grid(tmp_path: Path):
    """
    Ein Part-Eintrag darf sich absetzen - aber um ein Vielfaches der
    Rasterzeile, nicht um einen krummen Wert.
    """
    steps = toc_steps(build_pages(tmp_path))
    part_steps = [step for step, css in steps if "toc-item-part" in css]
    assert part_steps, "Kein Part-Eintrag im Inhaltsverzeichnis gefunden"
    for step in part_steps:
        multiple = step / TOC_LINE_MM
        assert multiple == pytest.approx(round(multiple), abs=0.01), (
            f"Part-Abstand {step}mm liegt nicht auf dem {TOC_LINE_MM}mm-Raster"
        )


def test_theme_declares_its_fonts_in_one_place():
    """
    Die Schriftfamilien stehen als Custom Property in :root. Verstreute
    font-family-Ketten waren der Grund, warum eine Schriftumstellung frueher
    fuenf Stellen brauchte - und eine davon vergessen wurde.
    """
    css = (resolve_template_path("pdf", "default") / "styles.css").read_text(
        encoding="utf-8"
    )

    assert "--font-sans:" in css
    assert "--font-mono:" in css
    assert '"Open Sans"' in css

    # Keine Deklaration darf die Variable umgehen.
    for line in css.splitlines():
        stripped = line.strip()
        if stripped.startswith("font-family:"):
            assert "var(--font-" in stripped, (
                f"font-family umgeht die Theme-Variable: {stripped}"
            )
