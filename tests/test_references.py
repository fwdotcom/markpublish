"""
Verweise `[](#id)` auf Ueberschriften: Wort, Nummer und Titel, je nach Verweisstelle.
"""

from pathlib import Path

import pypdfium2 as pdfium
import pytest

from markpublish.config.loader import load_config
from markpublish.config.models import ConfigurationError
from markpublish.markdown.engine import MarkdownPipeline
from markpublish.renderers.base import DocumentContext
from markpublish.renderers.pdf import PDFRenderer
from markpublish.templates.resolver import resolve_template_path

LABELS = {
    "part": "Teil",
    "chapter": "Kapitel",
    "section": "Abschnitt",
    "quote_open": "„",
    "quote_close": "“",
    "label_separator": ": ",
}

CONFIG = """\
document:
  title: "T"
  language: "de"
  autonum_pattern: "I|1|.1|+"
parts:
  - part: "Grundlagen"
    chapters:
      - file: "a.md"
  - part: "Praxis"
    autonum_reset: true
    chapters:
      - file: "b.md"
      - file: "c.md"
        label: "Anhang"
"""

FILES = {
    "a.md": (
        "# Einleitung\n\n"
        "Fern [](#test), Anhang [](#daten), Teil [](#praxis).\n\n"
        "## Überblick\n\n"
        "Eigenes Kapitel [](#einleitung), tiefer [](#tief).\n\n"
        "### Tief {#tief}\n"
    ),
    "b.md": (
        "# Zweites Kapitel\n\n"
        "## Testabschnitt {#test}\n\n"
        "Nachbar [](#weiter), mit Text [siehe dort](#tief), Absatz [](#absatz).\n\n"
        "## Weiter {#weiter}\n\n"
        "Ein Absatz.\n{#absatz}\n\n"
        "| A |\n| - |\n| 1 |\n\n"
        "/// table-caption\n    attrs: {id: tbl-x}\nTabelle\n///\n\n"
        "Tabelle [](#tbl-x).\n"
    ),
    "c.md": "# Daten {#daten}\n\nText.\n",
}


def _process(tmp_path: Path, config: str = CONFIG, files: dict = FILES):
    (tmp_path / "markpublish.yaml").write_text(config, encoding="utf-8")
    for name, body in files.items():
        (tmp_path / name).write_text(body, encoding="utf-8")
    pipeline = MarkdownPipeline(load_config(tmp_path / "markpublish.yaml"), base_dir=tmp_path, labels=LABELS)
    items, _ = pipeline.process_document()
    return items


def _links(items) -> dict:
    """href -> Linktext, ueber alle Kapitel."""
    return {
        (item.slug, a.attrib["href"]): a.text
        for item in items
        if item.element_tree is not None
        for a in item.element_tree.iter("a")
    }


def test_reference_names_the_levels_from_the_first_that_differs(tmp_path: Path):
    links = _links(_process(tmp_path))

    assert links[("einleitung", "#test")] == "Teil II, Kapitel 1, Abschnitt 1.1 „Testabschnitt“"
    assert links[("zweites-kapitel", "#weiter")] == "Abschnitt 1.2 „Weiter“"
    assert links[("einleitung", "#tief")] == "Abschnitt 1.1.1 „Tief“", "nur die tiefste Abschnittsebene"


def test_reference_to_a_chapter_uses_its_label_and_title(tmp_path: Path):
    links = _links(_process(tmp_path))

    assert links[("einleitung", "#daten")] == "Teil II, Anhang 2 „Daten“"
    assert links[("einleitung", "#einleitung")] == "Kapitel 1 „Einleitung“"


def test_an_unnumbered_level_is_named_by_its_title(tmp_path: Path):
    """Das Standard-Pattern nummeriert Parts nicht."""
    config = CONFIG.replace('  autonum_pattern: "I|1|.1|+"\n', "")
    links = _links(_process(tmp_path, config))

    assert links[("einleitung", "#praxis")] == "„Praxis“"
    assert links[("einleitung", "#test")] == "Teil „Praxis“, Kapitel 1, Abschnitt 1.1 „Testabschnitt“"


def test_links_with_text_figures_and_other_ids_stay_as_they_are(tmp_path: Path):
    links = _links(_process(tmp_path))

    assert links[("zweites-kapitel", "#tief")] == "siehe dort"
    assert links[("zweites-kapitel", "#tbl-x")] is None, "Nummer und Wort setzt Typst"
    assert links[("zweites-kapitel", "#absatz")] is None


def test_unknown_reference_stops_the_build(tmp_path: Path):
    files = dict(FILES, **{"c.md": "# Daten\n\nSiehe [](#gibt-es-nicht).\n"})
    with pytest.raises(ConfigurationError, match=r"#gibt-es-nicht.*c\.md"):
        _process(tmp_path, files=files)


def test_references_compile_and_jump_to_parts_without_a_page(tmp_path: Path):
    """Ein Part ohne Trennseite hat keine Ueberschrift; die Marke traegt sein erstes Kapitel."""
    (tmp_path / "markpublish.yaml").write_text(CONFIG, encoding="utf-8")
    for name, body in FILES.items():
        (tmp_path / name).write_text(body, encoding="utf-8")
    config = load_config(tmp_path / "markpublish.yaml")
    context = DocumentContext(
        config=config,
        content_items=[],
        toc_tree=[],
        template_path=resolve_template_path(target="pdf", theme=config.theme, config_base_dir=tmp_path),
        base_dir=tmp_path,
        target="pdf",
    )
    pipeline = MarkdownPipeline(config, base_dir=tmp_path, labels=context.labels)
    context.content_items, context.toc_tree = pipeline.process_document()

    out_pdf = PDFRenderer().render(context, tmp_path / "output.pdf")

    text = "".join(page.get_textpage().get_text_range() for page in pdfium.PdfDocument(out_pdf))
    assert "Kapitel 1, Abschnitt 1.1" in text


def test_a_part_without_page_or_toc_entry_is_left_out(tmp_path: Path):
    """Den Part sieht die Leserin nirgends, also nennt ihn auch kein Verweis."""
    config = CONFIG.replace(
        '  - part: "Grundlagen"\n', '  - part: "Grundlagen"\n    document_toc: "none"\n'
    )
    files = dict(FILES, **{"c.md": "# Daten {#daten}\n\nZurück: [](#tief).\n"})
    links = _links(_process(tmp_path, config, files))
    assert links[("daten", "#tief")] == "Kapitel 1, Abschnitt 1.1.1 „Tief“"
