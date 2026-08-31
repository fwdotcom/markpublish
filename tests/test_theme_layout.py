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


@pytest.mark.parametrize("target", ["pdf", "html"])
def test_theme_ships_the_font_files(target: str):
    """
    Bewusst je Zielformat abgelegt, nicht auf Theme-Ebene - dafuer muessen sie
    auch in beiden liegen, sonst faellt eines der Formate still auf die
    Systemschrift zurueck.
    """
    fonts = resolve_template_path(target, "default") / "fonts"
    for name in FONT_FILES:
        assert (fonts / name).is_file(), f"{target}: {name} fehlt"


@pytest.mark.parametrize("target", ["pdf", "html"])
def test_font_face_name_matches_the_file(target: str):
    """
    Der Name unter font-family muss dem Familiennamen IN der Datei entsprechen.
    Weicht er ab, faellt WeasyPrint still auf die naechste Schrift der Kette
    zurueck - ohne Fehlermeldung, nur mit anderem Satzbild.
    """
    fonttools = pytest.importorskip("fontTools.ttLib")

    directory = resolve_template_path(target, "default")
    css = (directory / "styles.css").read_text(encoding="utf-8")

    declared = set(re.findall(r'@font-face\s*\{[^}]*?font-family:\s*"([^"]+)"', css))
    assert declared, f"{target}: keine @font-face-Regel gefunden"

    for name in FONT_FILES:
        if not name.endswith(".ttf"):
            continue
        family = fonttools.TTFont(directory / "fonts" / name)["name"].getDebugName(1)
        assert family in declared, (
            f"{target}: Datei {name} heisst {family!r}, deklariert ist {declared}"
        )


@pytest.mark.parametrize("target", ["pdf", "html"])
def test_font_is_inlined_not_linked(target: str):
    """
    Die Schrift wird ueber asset_url() als data-URI eingebettet. Ein relativer
    Pfad wuerde gegen das Dokumentverzeichnis aufgeloest, nicht gegen das
    Template - und dort liegt keine Schrift.
    """
    css = (resolve_template_path(target, "default") / "styles.css").read_text(
        encoding="utf-8"
    )
    for match in re.finditer(r"@font-face\s*\{([^}]*)\}", css):
        block = match.group(1)
        assert "asset_url(" in block, f"{target}: @font-face ohne asset_url:\n{block}"


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
