"""
Integration tests executing real Typst compilation for edge cases.

Verifies fixes for review findings:
- B1, B6: Safe metadata escaping in Typst setup-document.
- B2, B5: Typst special characters ($5, C#, @, <tag>, brackets, math).
- B3: Local image resolution and copying to build directory.
- S1: Physical page count calculation across pagenum_reset.
- S2: Header/footer rendering when cover is disabled.
- S3: Suppressing header and footer via config switches.
- S7: Full markdown extensions (callouts, def_list, tables, footnotes).
"""

from __future__ import annotations

import base64
from pathlib import Path

import pypdfium2 as pdfium

from markpublish.config.loader import load_config
from markpublish.markdown.engine import MarkdownPipeline
from markpublish.renderers.base import DocumentContext
from markpublish.renderers.pdf import PDFRenderer
from markpublish.templates.resolver import (
    get_package_templates_dir,
    resolve_template_path,
)


def _compile_pdf(tmp_path: Path, yaml_text: str, files: dict[str, str | bytes]) -> Path:
    """Helper to set up files, build document context, and compile PDF via Typst."""
    (tmp_path / "markpublish.yaml").write_text(yaml_text, encoding="utf-8")
    for name, content in files.items():
        file_path = tmp_path / name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            file_path.write_bytes(content)
        else:
            file_path.write_text(content, encoding="utf-8")

    config = load_config(tmp_path / "markpublish.yaml")
    template_path = resolve_template_path(
        target="pdf",
        theme=config.theme,
        config_base_dir=tmp_path,
    )
    context = DocumentContext(
        config=config,
        content_items=[],
        toc_tree=[],
        template_path=template_path,
        base_dir=tmp_path,
        target="pdf",
    )
    pipeline = MarkdownPipeline(config, base_dir=tmp_path, labels=context.labels)
    context.content_items, context.toc_tree = pipeline.process_document()

    out_pdf = tmp_path / "output.pdf"
    renderer = PDFRenderer()
    renderer.render(context, out_pdf)
    assert out_pdf.is_file()
    assert out_pdf.stat().st_size > 500
    return out_pdf


def test_special_characters_compile_without_error(tmp_path: Path):
    """
    Test edge cases: $5.00 price, C# language name, @mentions, HTML-like tags,
    and brackets compile cleanly without Typst parsing errors.
    """
    yaml_text = """\
document:
  title: "Test with $5 and C# & Quotes \\"Special\\""
  subtitle: "Backslash \\\\ and brackets [test]"
  author: 'Author "The Great"'
  summary: 'Summary with $100 and C# code'
  cover: false
  document_toc:
    enabled: false
parts:
  - part: "Main Part"
    break_before: "none"
    chapters:
      - file: "chapter.md"
"""
    chapter_md = """\
# Heading with $5 and C# <label-test>

Here is a price of $5.00 and another price of $10.50.
Programming in C# and C++ is fun.
Reach out to @support or @user.
A comparison: 5 < 10 and 10 > 5.
Bracket test: [Link text](https://example.com) and literal [brackets].
Math block test:

$$
E = m c^2
$$

Inline formatting: *emphasis*, **bold**, `inline code with $5 and C#`.
"""
    out_pdf = _compile_pdf(tmp_path, yaml_text, {"chapter.md": chapter_md})

    doc = pdfium.PdfDocument(out_pdf)
    assert len(doc) >= 1
    page_text = doc[0].get_textpage().get_text_range()
    assert "$5.00" in page_text
    assert "C#" in page_text
    assert "5 < 10" in page_text or "5" in page_text


def test_local_image_is_copied_and_compiled(tmp_path: Path):
    """
    Tests that local images referenced in Markdown (even in subfolders)
    are copied into the build directory and rendered without Typst path errors.
    """
    # 1x1 transparent PNG
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    yaml_text = """\
document:
  title: "Image Test"
  cover: false
  document_toc:
    enabled: false
parts:
  - part: "Part"
    break_before: "none"
    chapters:
      - file: "ch/chapter.md"
"""
    chapter_md = """\
# Image Chapter

Here is an image:
![Test Pixel](../img/pixel.png)
"""
    out_pdf = _compile_pdf(
        tmp_path,
        yaml_text,
        {
            "ch/chapter.md": chapter_md,
            "img/pixel.png": png_data,
        },
    )
    assert out_pdf.is_file()
    doc = pdfium.PdfDocument(out_pdf)
    assert len(doc) >= 1


def test_pagenum_reset_total_pages_stays_accurate(tmp_path: Path):
    """
    Tests that when pagenum_reset is used, the footer's total page count
    accurately reflects the physical total page count rather than resetting.
    """
    yaml_text = """\
document:
  title: "Page Reset Test"
  language: "en"
  cover: false
  header: true
  footer: true
  document_toc:
    enabled: false
parts:
  - part: "First Part"
    break_before: "none"
    chapters:
      - file: "ch1.md"
  - part: "Second Part"
    break_before: "page"
    pagenum_reset: true
    chapters:
      - file: "ch2.md"
"""
    ch1_md = "# Chapter 1\n\nPage one content.\n"
    ch2_md = "# Chapter 2\n\nPage two content.\n"

    out_pdf = _compile_pdf(tmp_path, yaml_text, {"ch1.md": ch1_md, "ch2.md": ch2_md})
    doc = pdfium.PdfDocument(out_pdf)
    assert len(doc) == 2

    # Verify both pages show "of 2"
    page1_text = doc[0].get_textpage().get_text_range()
    page2_text = doc[1].get_textpage().get_text_range()

    assert "of 2" in page1_text
    assert "of 2" in page2_text


def test_header_and_footer_can_be_disabled(tmp_path: Path):
    """
    Tests that setting header: false and footer: false properly suppresses
    headers and footers in the generated PDF.
    """
    yaml_text = """\
document:
  title: "Header Suppression Test"
  language: "en"
  cover: false
  header: false
  footer: false
  document_toc:
    enabled: false
parts:
  - part: "Part"
    break_before: "none"
    chapters:
      - file: "ch.md"
"""
    ch_md = "# Title\n\nContent paragraph.\n"
    out_pdf = _compile_pdf(tmp_path, yaml_text, {"ch.md": ch_md})
    doc = pdfium.PdfDocument(out_pdf)
    text = doc[0].get_textpage().get_text_range()
    assert "Page 1 of 1" not in text
    assert "Header Suppression Test" not in text.split("\n")[0]


def test_single_chapter_header_suppresses_chapter_title(tmp_path: Path):
    """
    Bei genau einem Kapitel unterdrückt das Standard-Theme den Kapiteltitel
    oben rechts in der Kopfzeile, um Redundanz zum Dokumenttitel zu vermeiden.
    """
    yaml_text = """\
document:
  title: "Hauptdokument"
  language: "de"
  cover: false
  header: true
  footer: false
  document_toc: "none"
parts:
  - part: "Hauptteil"
    chapters:
      - file: "ch.md"
"""
    # Zwei Absätze, die durch viel Text oder Umbruch auf Seite 2 fließen
    ch_md = "# Einziges Kapitel\n\nErster Absatz.\n\n" + ("Viel Text im ersten Kapitel.\n\n" * 40)
    out_pdf = _compile_pdf(tmp_path, yaml_text, {"ch.md": ch_md})
    doc = pdfium.PdfDocument(out_pdf)
    assert len(doc) >= 2
    # Auf Folgeseiten steht der Dokumenttitel links, aber rechts nicht der redundante Kapiteltitel
    page2_text = doc[1].get_textpage().get_text_range()
    assert "Hauptdokument" in page2_text.split("\n")[0]
    assert "Einziges Kapitel" not in page2_text.split("\n")[0]


def test_multi_chapter_header_shows_chapter_title(tmp_path: Path):
    """
    Bei mehreren Kapiteln wird der aktive Kapiteltitel rechts in der Kopfzeile gedruckt.
    """
    yaml_text = """\
document:
  title: "Hauptdokument"
  language: "de"
  cover: false
  header: true
  footer: false
  document_toc: "none"
parts:
  - part: "Hauptteil"
    chapters:
      - file: "c1.md"
      - file: "c2.md"
"""
    c1_md = "# Erstes Kapitel\n\nText 1.\n"
    c2_md = "# Zweites Kapitel\n\n" + ("Viel Text im zweiten Kapitel.\n\n" * 40)
    out_pdf = _compile_pdf(tmp_path, yaml_text, {"c1.md": c1_md, "c2.md": c2_md})
    doc = pdfium.PdfDocument(out_pdf)
    assert len(doc) >= 3
    # Auf Folgeseiten von Kapitel 2 steht dessen Kapiteltitel im Header
    page3_text = doc[2].get_textpage().get_text_range()
    assert "Zweites Kapitel" in page3_text.split("\n")[0]


def test_markdown_extensions_render_properly(tmp_path: Path):
    """
    Tests that tables, callouts/admonitions, definition lists, and footnotes
    are properly converted and compiled into Typst.
    """
    yaml_text = """\
document:
  title: "Extensions Test"
  cover: false
  document_toc:
    enabled: false
parts:
  - part: "Part"
    break_before: "none"
    chapters:
      - file: "ext.md"
"""
    ext_md = """\
# Extensions

> [!NOTE]
> This is a callout note.

> [!WARNING]
> This is a warning callout.

| Header A | Header B |
| :--- | :--- |
| Cell 1 | Cell 2 |

Term 1
: Definition 1

Here is a footnote reference[^1].

[^1]: Footnote content explaining something.
"""
    out_pdf = _compile_pdf(tmp_path, yaml_text, {"ext.md": ext_md})
    doc = pdfium.PdfDocument(out_pdf)
    assert len(doc) >= 1
    text = doc[0].get_textpage().get_text_range()
    assert "Cell 1" in text
    assert "Cell 2" in text
    assert "Definition 1" in text


def _theme_with_extra_cover_field(tmp_path: Path, name: str, key: str) -> None:
    """
    Legt unter `tmp_path/templates/<name>` eine Kopie des Standard-Themes an,
    deren `cover-fields` zusaetzlich `key` druckt.

    Gebraucht, weil ein frei ergaenztes Feld das Titelblatt nur erreicht, wenn
    das Theme es ausdruecklich auffuehrt -- genau dieser Weg wird hier gesetzt
    und nicht bloss behauptet.
    """
    import shutil

    source = get_package_templates_dir() / "default"
    destination = tmp_path / "templates" / name
    shutil.copytree(source, destination)

    template = destination / "pdf" / "template.typ"
    text = template.read_text(encoding="utf-8")
    marker = '  meta.at("copyright", default: none),'
    assert marker in text, "cover-fields im Standard-Theme nicht gefunden"
    template.write_text(
        text.replace(marker, f'  meta.at("{key}", default: none),\n{marker}', 1),
        encoding="utf-8",
    )


def test_metadata_special_characters_in_key_and_value_compiles_cleanly(tmp_path: Path):
    """
    Tests that quotes and special characters in custom metadata keys and values
    do not inject syntax errors into the Typst document.
    """
    yaml_text = """\
document:
  title: "Meta Quote Test"
  cover: true
  status: 'Freigegeben "mit" $Zeichen$'
  'quo"te': 'value with "quotes" and $math$ and #tags'
parts:
  - part: "Part"
    break_before: "none"
    chapters:
      - file: "a.md"
"""
    a_md = "# Title\n\nContent.\n"
    out_pdf = _compile_pdf(tmp_path, yaml_text, {"a.md": a_md})
    doc = pdfium.PdfDocument(out_pdf)
    assert len(doc) >= 1
    text = doc[0].get_textpage().get_text_range()

    # Der gedruckte Wert: hier faellt eine kaputte Maskierung als falscher
    # Satz auf, nicht erst als Kompilierfehler.
    assert 'Freigegeben "mit" $Zeichen$' in text

    # Das freie Feld erreicht den Typst-Quelltext -- eine kaputte Maskierung
    # braechte den Build ab -- steht aber nicht auf dem Titelblatt: dorthin
    # kommt nur, was das Theme in `cover-fields` auffuehrt.
    assert 'value with "quotes"' not in text


def test_custom_metadata_with_project_i18n_renders_localized_label_on_cover(tmp_path: Path):
    """
    Ein Zusatzfeld erscheint auf dem Titelblatt, sobald das Theme es fuehrt --
    mit der Beschriftung aus der Projekt-i18n.yaml, der letzten Stufe der
    Kaskade.

    Beides gehoert zusammen geprueft: das Theme entscheidet ueber das Ob, die
    Kaskade ueber die Beschriftung. Faellt eine der beiden Seiten aus, steht
    entweder nichts auf dem Blatt oder der rohe Schluessel.
    """
    _theme_with_extra_cover_field(tmp_path, "mit-abteilung", "department")

    yaml_text = """\
document:
  title: "Projektbericht"
  language: "de"
  cover: true
  department: "F&E"

theme: "mit-abteilung"

parts:
  - part: "Hauptteil"
    break_before: "none"
    chapters:
      - file: "a.md"
"""
    # Project-level i18n.yaml
    project_i18n = """\
de:
  department: "Fachabteilung"
"""
    (tmp_path / "i18n.yaml").write_text(project_i18n, encoding="utf-8")
    a_md = "# Kapitel\n\nInhalt.\n"
    out_pdf = _compile_pdf(tmp_path, yaml_text, {"a.md": a_md})
    doc = pdfium.PdfDocument(out_pdf)
    assert len(doc) >= 1
    cover_text = doc[0].get_textpage().get_text_range()
    assert "Fachabteilung" in cover_text, "Das lokalisierte Label aus der Projekt-i18n.yaml fehlt auf dem Deckblatt"
    assert "F&E" in cover_text, "Der Metadatenwert fehlt auf dem Deckblatt"



def test_the_theme_decides_the_cover_metadata(tmp_path: Path):
    """
    Was im Metadatenraster steht und in welcher Reihenfolge, entscheidet das
    Theme (`cover-fields` in template.typ) -- nicht die markpublish.yaml.

    Ein frei ergaenztes Feld erreicht das Theme ueber `meta`, erscheint aber
    nicht von selbst auf dem Titelblatt. Sonst stuende dort jeder Tippfehler
    aus der Konfiguration als zusaetzliche Zeile.

    Geprueft wird am gesetzten Dokument, nicht am Quelltext: nur so faellt auf,
    wenn die Auswahl wirkungslos wird.
    """
    yaml_text = """\
document:
  title: "Reihenfolge"
  language: "de"
  cover: true
  document_toc: "none"
  author: "AUTORNAME"
  version: "VERSIONSNUMMER"
  date: "DATUMSWERT"
  copyright: "COPYRIGHTZEILE"
  status: "STATUSWERT"
  eigenes_feld: "FREIERWERT"
parts:
  - part: "P"
    break_before: "none"
    chapters:
      - file: "a.md"
"""
    out_pdf = _compile_pdf(tmp_path, yaml_text, {"a.md": "# A\n\nText.\n"})
    cover = pdfium.PdfDocument(out_pdf)[0].get_textpage().get_text_range()

    # cover-fields im mitgelieferten Theme, in genau dieser Reihenfolge.
    expected = [
        "VERSIONSNUMMER",
        "DATUMSWERT",
        "AUTORNAME",
        "COPYRIGHTZEILE",
        "STATUSWERT",
    ]
    positions = [cover.find(value) for value in expected]
    assert all(p >= 0 for p in positions), f"nicht alle Werte gesetzt: {positions}"

    # Das Theme fuehrt `eigenes_feld` nicht -- also steht es nicht darauf.
    assert "FREIERWERT" not in cover
    assert positions == sorted(positions), (
        f"Reihenfolge weicht ab: {list(zip(expected, positions, strict=True))}"
    )


def test_long_chapter_divider_breaks_cleanly_without_header_bleed(tmp_path: Path):
    """
    Sehr lange Kapitel-TOCs auf Trennseiten (Divider Pages) dürfen am Seitenende
    nicht gestaucht werden, sondern müssen sauber auf eine Folgeseite umbrechen.
    Auf allen Folgeseiten der Trennseite muss die Kopfzeile unterdrückt bleiben
    (kein Durchbluten des vorigen Kapitels).
    """
    yaml_text = """\
document:
  title: "Trennseiten-Test"
  language: "de"
  cover: false
  document_toc: "none"
  chapter_toc: "full"
  header: true
  footer: true

parts:
  - part: "Hauptteil"
    break_before: "none"
    chapters:
      - file: "ch1.md"
        break_before: "none"
      - file: "ch2.md"
        break_before: "divider"
"""
    ch1_content = "# Erstes Kapitel\n\nErster Text.\n"
    ch2_sections = "\n\n".join(f"## Unterabschnitt {i}\n\nInhalt {i}." for i in range(1, 45))
    ch2_content = f"# Zweites Kapitel\n\nEinleitung zu Kapitel 2.\n\n{ch2_sections}\n"

    out_pdf = _compile_pdf(
        tmp_path,
        yaml_text,
        {
            "ch1.md": ch1_content,
            "ch2.md": ch2_content,
        },
    )
    doc = pdfium.PdfDocument(out_pdf)

    # ch1 ist auf Seite 1.
    p1_text = doc[0].get_textpage().get_text_range()
    assert "Erstes Kapitel" in p1_text

    # ch2 Divider beginnt auf Seite 2.
    p2_text = doc[1].get_textpage().get_text_range()
    assert "Zweites Kapitel" in p2_text
    assert "AUF EINEN BLICK" in p2_text

    # Seite 3 ist die Fortsetzungsseite der Trennseite.
    # Das lokale TOC setzt sich hier fort, und die Kopfzeile darf das vorige Kapitel nicht anzeigen.
    p3_text = doc[2].get_textpage().get_text_range()
    assert "Unterabschnitt" in p3_text
    assert "Erstes Kapitel" not in p3_text


def test_long_part_divider_breaks_cleanly(tmp_path: Path):
    """
    Sehr lange Teil-TOCs auf Trennseiten (Part Dividers) dürfen am Seitenende
    nicht gestaucht werden, sondern müssen sauber auf Folgeseiten umbrechen.
    """
    files = {}
    chapters_yaml = []
    for i in range(1, 70):
        fn = f"ch_{i}.md"
        files[fn] = f"# Kapitel {i}\n\nInhalt für Kapitel {i}.\n"
        chapters_yaml.append(f'      - file: "{fn}"\n        break_before: "none"')

    ch_list_str = "\n".join(chapters_yaml)
    yaml_text = f"""\
document:
  title: "Part-Divider-Test"
  language: "de"
  cover: false
  document_toc: "full"
  part_toc: "full"
  header: true
  footer: true

parts:
  - part: "Umfangreicher Teil"
    break_before: "divider"
    chapters:
{ch_list_str}
"""
    out_pdf = _compile_pdf(tmp_path, yaml_text, files)
    doc = pdfium.PdfDocument(out_pdf)

    # Das Dokument-TOC nimmt die ersten Seiten ein.
    # Der Part-Divider beginnt danach (auf Seite 4).
    p4_text = doc[3].get_textpage().get_text_range()
    assert "Umfangreicher Teil" in p4_text
    assert "Kapitel 1" in p4_text

    # Der Part-Divider bricht sauber auf Folgeseiten (Seite 5) um:
    p5_text = doc[4].get_textpage().get_text_range()
    assert "Kapitel 25" in p5_text
    # Und unterdrückt die Kopfzeile auf der Fortsetzungsseite der Trennseite:
    assert "Part-Divider-Test" not in p5_text


def test_chapter_local_toc_items_include_heading_levels(tmp_path: Path):
    """
    Stellt sicher, dass lokale Inhaltsverzeichnisse auf Kapitel-Trennseiten
    die Überschriftenebene (level) an das Theme übergeben, damit die
    Zusammenhalt-Logik (sticky: true bei übergeordneten Einträgen) greift.
    """
    yaml_text = """\
document:
  title: "Sticky-TOC-Test"
  language: "de"
  cover: false
  document_toc: "none"
  chapter_toc: "full"
  header: false
  footer: false

parts:
  - part: "Hauptteil"
    break_before: "none"
    chapters:
      - file: "ch.md"
        break_before: "divider"
"""
    ch_content = """\
# Hauptkapitel

## Abschnitt 1
Text 1.

### Unterabschnitt 1.1
Text 1.1.

## Abschnitt 2
Text 2.
"""
    out_pdf = _compile_pdf(tmp_path, yaml_text, {"ch.md": ch_content})
    doc = pdfium.PdfDocument(out_pdf)
    assert len(doc) >= 1
    # Erste Seite ist der Chapter-Divider
    p1_text = doc[0].get_textpage().get_text_range()
    assert "Hauptkapitel" in p1_text
    assert "Abschnitt 1" in p1_text
    assert "Unterabschnitt 1.1" in p1_text
    assert "Abschnitt 2" in p1_text


def test_list_types_compile_cleanly(tmp_path: Path):
    """
    Stellt sicher, dass ungeordnete Listen, nummerierte Listen, Definitionslisten
    und Aufgabenlisten mit den Flatterrand-Regeln (justify: false) sauber kompilieren.
    """
    yaml_text = """\
document:
  title: "Listen-Test"
  language: "de"
  cover: false
  document_toc: "none"
  header: false
  footer: false

parts:
  - part: "Hauptteil"
    break_before: "none"
    chapters:
      - file: "lists.md"
        break_before: "none"
"""
    lists_content = """\
# Listen im Test

- Ungeordneter Punkt 1 mit laengerem Text zur Pruefung des Flatterrands.
- Ungeordneter Punkt 2 mit Inline-Code `markpublish --format pdf`.
  - Verschachtelter Punkt 2.1

1. Erster nummerierter Schritt
2. Zweiter nummerierter Schritt

- [ ] Offene Aufgabe
- [x] Erledigte Aufgabe

Begriff A
: Definition von Begriff A
"""
    out_pdf = _compile_pdf(tmp_path, yaml_text, {"lists.md": lists_content})
    doc = pdfium.PdfDocument(out_pdf)
    assert len(doc) >= 1
    text = doc[0].get_textpage().get_text_range()
    assert "Ungeordneter Punkt 1" in text
    assert "Erster nummerierter Schritt" in text
    assert "Offene Aufgabe" in text
    assert "Begriff A" in text
