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

import re
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

#: Ein Block der obersten Ebene - ein Kapitel ohne Elternteil oder ein Part.
#: Nur diese setzen sich im Verzeichnis durch eine Leerzeile voneinander ab;
#: Parts gibt es ausschliesslich dort, und ein Kapitel unter einem Part liegt
#: bereits auf Ebene 2.
TOP_LEVEL_CLASSES = {"toc-item-h1", "toc-item-part"}

YAML = """\

document:
  title: "Raster Test"
  author: "Test"
  date: "01.09.2026"
  language: "de"
  cover: false
  document_toc: "full"

theme: "default"

parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "chapters/01.md"
      - file: "chapters/02.md"
  - part: "Anhaenge"
    chapters:
      - file: "chapters/03.md"
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


@pytest.mark.skip(reason="WeasyPrint specific box-tree test")
def test_toc_uses_one_uniform_line_height(tmp_path: Path):
    """
    Innerhalb des Verzeichnisses liegen alle Zeilen exakt auf dem 6mm-Raster
    (Folgezeile: 6mm, Block-Trennung: 12mm).
    """
    steps = toc_steps(build_pages(tmp_path))
    assert len(steps) > 8, f"Zu wenige TOC-Eintraege zum Messen: {steps}"

    levels = {c for _, css in steps for c in css if c.startswith("toc-item-h")}
    assert len(levels) >= 3, f"Test braucht mehrere Gliederungsebenen: {levels}"

    all_step_sizes = {step for step, _ in steps}
    assert all_step_sizes == {TOC_LINE_MM, 2 * TOC_LINE_MM}, (
        f"Uneinheitliche Zeilenabstaende im TOC: {sorted(all_step_sizes)}"
    )


@pytest.mark.skip(reason="WeasyPrint specific box-tree test")
def test_toc_separates_the_top_level_blocks(tmp_path: Path):
    """
    Vor Hauptbloecken (neues Kapitel auf Hauptebene, neuer Part) steht
    genau eine leere Rasterzeile (12.0 mm).
    """
    steps = toc_steps(build_pages(tmp_path))
    block_separators = [
        step for step, _ in steps if step == pytest.approx(2 * TOC_LINE_MM, abs=0.01)
    ]
    assert len(block_separators) >= 2, (
        f"Zu wenige Block-Trenner im Inhaltsverzeichnis: {steps}"
    )


@pytest.mark.skip(reason="WeasyPrint specific CSS test")
def test_theme_declares_its_fonts_in_one_place():
    """
    Die Schriftfamilien stehen als Custom Property in :root. Verstreute
    font-family-Ketten wuerden eine Schriftumstellung auf fuenf Stellen
    verteilen - und eine davon bliebe stehen.
    """
    css = (resolve_template_path("pdf", "default") / "styles.css").read_text(
        encoding="utf-8"
    )

    assert "--font-sans:" in css
    assert "--font-mono:" in css
    assert '"Open Sans"' in css

    # In @font-face ist font-family ein Deskriptor - er benennt die Schrift, die
    # gerade definiert wird, und darf keine Variable sein. Nur die uebrigen
    # Deklarationen muessen ueber :root gehen.
    without_faces = re.sub(r"@font-face\s*\{[^}]*\}", "", css)

    for line in without_faces.splitlines():
        stripped = line.strip()
        if stripped.startswith("font-family:"):
            assert "var(--font-" in stripped, (
                f"font-family umgeht die Theme-Variable: {stripped}"
            )


# --------------------------------------------------------------------------
# Mitgelieferte Schrift
# --------------------------------------------------------------------------

#: Die beiden variablen Schnitte plus Lizenz, je Zielformat.
FONT_FILES = (
    "OpenSans-VariableFont_wdth,wght.ttf",
    "OpenSans-Italic-VariableFont_wdth,wght.ttf",
    "OFL.txt",
)


@pytest.mark.skip(reason="HTML target is currently disabled")
@pytest.mark.parametrize("target", ["html"])
def test_theme_ships_the_font_files(target: str):
    pass


@pytest.mark.skip(reason="WeasyPrint font test replaced by native Typst font handling")
def test_bundled_font_supplies_faces_the_system_lacks(tmp_path: Path):
    """
    Der Beweis, dass die Datei benutzt wird und nicht die Installation: Bold und
    Kursiv liefert die variable Schrift ueber ihre Achse. Ein System, auf dem
    Open Sans nur als Regular und SemiBold installiert ist, kann sie nicht
    beisteuern - dort wuerde WeasyPrint sie sonst rechnen statt zeichnen.
    """
    pages = build_pages(tmp_path)
    pdf = tmp_path / "fonts.pdf"

    from markpublish.renderers.pdf import PDFRenderer, _load_weasyprint

    html_cls, error = _load_weasyprint()
    if html_cls is None:
        pytest.skip(f"WeasyPrint/GTK nicht verfuegbar: {error}")

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
    PDFRenderer().render(context, pdf)

    names = " ".join(embedded_fonts(pdf))
    assert "Open-Sans" in names, f"Open Sans nicht eingebettet: {names}"
    assert "Bold" in names, f"Kein Fettschnitt aus der Achse: {names}"
    assert len(pages) >= 1


def embedded_fonts(pdf_path: Path):
    """Namen der im PDF eingebetteten Schriften, auch aus komprimierten Objekten."""
    import zlib

    data = pdf_path.read_bytes()
    found = set(re.findall(rb"/BaseFont\s*/([#\w+.-]+)", data))
    for match in re.finditer(rb"stream\r?\n", data):
        start = match.end()
        end = data.find(b"endstream", start)
        try:
            found |= set(re.findall(rb"/BaseFont\s*/([#\w+.-]+)",
                                    zlib.decompress(data[start:end])))
        except Exception:
            continue
    return sorted(name.decode() for name in found)


#: Ein Kapitel ohne Zwischenueberschriften - fuer die Umbruchtests genuegt das.
#: Bewusst NICHT CHAPTER_MD: diese Datei definiert weiter oben bereits eine
#: Vorlage dieses Namens, aus der build_pages seine Kapitel baut. Eine zweite
#: Zuweisung auf Modulebene wuerde sie ueberschreiben - den dortigen Tests
#: fehlten dann saemtliche Zwischenueberschriften.
BREAK_CHAPTER_MD = "# {title}\n\nText.\n"


def _render_pages(tmp_path: Path, yaml_body: str):
    """Baut ein Dokument und gibt die gerenderten PDF-Seiten zurueck."""
    import pypdfium2 as pdfium

    from markpublish.renderers.pdf import PDFRenderer

    (tmp_path / "markpublish.yaml").write_text(yaml_body, encoding="utf-8")

    config = load_config(tmp_path / "markpublish.yaml")
    tmpl = resolve_template_path(target="pdf", theme=config.theme, config_base_dir=tmp_path)
    context = DocumentContext(
        config=config,
        content_items=[],
        toc_tree=[],
        template_path=tmpl,
        base_dir=tmp_path,
        target="pdf",
    )
    pipeline = MarkdownPipeline(config, base_dir=tmp_path, labels=context.labels)
    context.content_items, context.toc_tree = pipeline.process_document()

    out_pdf = tmp_path / "out.pdf"
    PDFRenderer().render(context, out_pdf)
    return pdfium.PdfDocument(str(out_pdf))


def _page_text(page) -> str:
    return page.get_textpage().get_text_range()


def test_chapters_start_on_a_new_page_by_default(tmp_path: Path):
    """
    Ein Kapitel beginnt oben auf einer Seite. Ohne diese Regel liefen kurze
    Kapitel ineinander, was in einem gesetzten Dokument niemand erwartet.
    """
    for name in ("a", "b", "c"):
        (tmp_path / f"{name}.md").write_text(BREAK_CHAPTER_MD.format(title=name.upper()), encoding="utf-8")

    pages = _render_pages(
        tmp_path,
        """\
document:
  title: "T"
  cover: false
  document_toc: "none"
parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "a.md"
      - file: "b.md"
      - file: "c.md"
""",
    )

    assert len(pages) == 3
    # Kein Leerblatt am Anfang: der Umbruch vor dem ersten Kapitel darf keine
    # Seite erzeugen.
    assert "A" in _page_text(pages[0])


def test_break_before_none_lets_chapters_run_on(tmp_path: Path):
    """Der Schalter muss den Umbruch wirklich abstellen, nicht nur verschieben."""
    for name in ("a", "b"):
        (tmp_path / f"{name}.md").write_text(BREAK_CHAPTER_MD.format(title=name.upper()), encoding="utf-8")

    pages = _render_pages(
        tmp_path,
        """\
document:
  title: "T"
  cover: false
  document_toc: "none"
parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "a.md"
      - file: "b.md"
        break_before: "none"
""",
    )

    assert len(pages) == 1
    text = _page_text(pages[0])
    assert "A" in text and "B" in text


def test_a_divider_page_does_not_add_a_blank_page(tmp_path: Path):
    """
    Trennseite und Kapitelumbruch fallen auf dieselbe Stelle. Verschmelzen sie
    nicht, steht vor jeder Trennseite ein Leerblatt - im PDF sofort sichtbar,
    im Code leicht zu uebersehen.
    """
    (tmp_path / "a.md").write_text(BREAK_CHAPTER_MD.format(title="A"), encoding="utf-8")

    pages = _render_pages(
        tmp_path,
        """\
document:
  title: "T"
  cover: false
  document_toc: "none"
parts:
  - part: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "a.md"
        break_before: "divider"
""",
    )

    assert len(pages) == 2, "Trennseite und Kapitelseite - dazwischen nichts"
    assert _page_text(pages[0]).strip(), "die erste Seite ist die Trennseite, nicht leer"


def test_toc_does_not_leave_a_blank_page_before_first_content(tmp_path: Path):
    """
    Nach dem Inhaltsverzeichnis (TOC) darf keine Leerseite vor der ersten
    Trennseite oder dem ersten Kapitel entstehen.
    """
    (tmp_path / "a.md").write_text("# Kapitel A\n\nInhalt.", encoding="utf-8")

    pages = _render_pages(
        tmp_path,
        """\
document:
  title: "T"
  language: "de"
  cover: true
  document_toc: "full"
parts:
  - part: "Hauptteil"
    break_before: "none"
    chapters:
      - file: "a.md"
        break_before: "divider"
""",
    )

    # Seite 1: Cover
    # Seite 2: Inhaltsverzeichnis
    # Seite 3: Trennseite von Kapitel A
    # Seite 4: Inhalt von Kapitel A
    assert len(pages) == 4
    assert "Inhaltsverzeichnis" in _page_text(pages[1])
    assert "KAPITEL" in _page_text(pages[2]).upper()
    assert "Kapitel A" in _page_text(pages[2])
    assert "Inhalt." in _page_text(pages[3])
