"""
Abbildungen und Tabellen: Beschriftung, Verweis, Bildattribute, Verzeichnisse.
"""

from __future__ import annotations

import base64
from pathlib import Path

import pypdfium2 as pdfium
import pytest
from pydantic import ValidationError

from markpublish.config.models import ChapterItem, ListOf
from markpublish.markdown.engine import MarkdownEngine
from markpublish.markdown.typst_serializer import (
    TypstSerializer,
    html_to_tree,
    typst_length,
)
from tests.test_typst_compile_cases import _compile_pdf

LABELS = {"figure": "Abbildung", "table": "Tabelle"}

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


def _typst(md: str, **kwargs) -> str:
    html = MarkdownEngine(language="de").convert(md)
    return TypstSerializer(labels=LABELS, **kwargs).serialize(html_to_tree(html))


FIGURE_MD = """\
![Balken](img/u.png){width=60%}

/// figure-caption
    attrs: {id: fig-umsatz}
Umsatz *2025*
///
"""


def test_figure_caption_becomes_typst_figure_with_label():
    out = _typst(FIGURE_MD)
    assert "#figure(kind: image, supplement: [Abbildung], caption: [Umsatz #emph[2025]])" in out
    assert '#box[#image("img/u.png", width: 60%, alt: "Balken")] <mp-image>' in out
    assert out.rstrip().endswith("<fig-umsatz>")
    # Die Nummer setzt Typst, nicht pymdownx.
    assert "Figure 1" not in out


def test_table_caption_becomes_table_figure():
    md = "| A | B |\n|---|---|\n| 1 | 2 |\n\n/// table-caption\n    attrs: {id: tbl-k}\nKennzahlen\n///\n"
    out = _typst(md)
    assert "#figure(kind: table, supplement: [Tabelle], caption: [Kennzahlen])" in out
    assert "#table(" in out
    assert "<tbl-k>" in out


def test_supplement_follows_the_labels():
    html = MarkdownEngine(language="en").convert(FIGURE_MD)
    out = TypstSerializer(labels={"figure": "Fig."}).serialize(html_to_tree(html))
    assert "supplement: [Fig.]" in out


def test_empty_link_to_figure_is_a_reference():
    out = _typst(
        FIGURE_MD + "\nSiehe [](#fig-umsatz) und [dort](#fig-umsatz).\n",
        known_labels={"fig-umsatz"},
        figure_labels={"fig-umsatz"},
    )
    assert '#ref(label("fig-umsatz"))' in out
    assert '#link(label("fig-umsatz"))[dort]' in out


def test_empty_link_to_heading_stays_a_link():
    out = _typst("Siehe [](#abschnitt).\n", known_labels={"abschnitt"})
    assert "#ref(" not in out
    assert '#link(label("abschnitt"))' in out


def test_block_image_gets_block_and_frame_marks():
    out = _typst("![A](a.png){width=4cm}\n\n![B](b.png){.noframe}\n")
    assert '#block[#box[#image("a.png", width: 4cm, alt: "A")] <mp-image>] <mp-image-block>' in out
    assert '#block[#box[#image("b.png", alt: "B")] <mp-image-noframe>] <mp-image-block>' in out


def test_width_and_height_keep_the_aspect_ratio():
    out = _typst("![A](a.png){width=4cm height=3cm}\n")
    assert 'image("a.png", width: 4cm, height: 3cm, fit: "contain", alt: "A")' in out
    assert "fit:" not in _typst("![A](a.png){width=4cm}\n")


def test_frame_marks_work_with_and_without_the_dot():
    out = _typst("![A](a.png){noframe}\n\n![B](b.png){frame}\n\n![C](c.png){.frame}\n")
    assert '#image("a.png", alt: "A")] <mp-image-noframe>' in out
    assert '#image("b.png", alt: "B")] <mp-image-frame>' in out
    assert '#image("c.png", alt: "C")] <mp-image-frame>' in out


def test_inline_image_stays_in_the_line():
    out = _typst("Text ![i](i.png){height=8pt} weiter.\n")
    assert '#box(image("i.png", height: 8pt, alt: "i"))' in out


@pytest.mark.parametrize(
    "value, expected",
    [("60%", "60%"), ("4cm", "4cm"), ("12.5mm", "12.5mm"), ("300", "225pt"), ("300px", "225pt"), ("breit", None), (None, None)],
)
def test_typst_length(value, expected):
    assert typst_length(value) == expected


def test_list_of_parses_and_rejects():
    assert ChapterItem(list_of="figures").list_of is ListOf.FIGURES
    with pytest.raises(ValidationError):
        ChapterItem(list_of="pictures")
    with pytest.raises(ValidationError):
        ChapterItem(list_of="tables", file="x.md")
    with pytest.raises(ValidationError):
        ChapterItem(list_of="tables", break_before="divider")


def test_lists_compile_with_numbered_captions_and_references(tmp_path: Path):
    yaml_text = """\
document:
  title: "Verzeichnisse"
  language: "de"
  cover: false
parts:
  - part: "Teil"
    chapters:
      - list_of: figures
      - list_of: tables
        toc_title: "Tabellen"
      - file: "k.md"
"""
    chapter = FIGURE_MD + """
| A | B |
|---|---|
| 1 | 2 |

/// table-caption
    attrs: {id: tbl-k}
Kennzahlen
///

# Kapitel

Siehe [](#fig-umsatz) und [](#tbl-k).
"""
    out_pdf = _compile_pdf(tmp_path, yaml_text, {"k.md": chapter, "img/u.png": PNG})
    doc = pdfium.PdfDocument(out_pdf)
    text = "\n".join(page.get_textpage().get_text_range() for page in doc)

    assert "Abbildungsverzeichnis" in text
    assert "Tabellen" in text
    assert "Abbildung 1: Umsatz 2025" in text.replace("\xa0", " ")
    assert "Tabelle 1: Kennzahlen" in text.replace("\xa0", " ")
    assert "Siehe Abbildung 1 und Tabelle 1" in text.replace("\xa0", " ")
