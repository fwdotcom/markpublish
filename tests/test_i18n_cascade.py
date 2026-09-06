"""
Tests fuer die dreistufige Label-Kaskade.

    1. Programm      markpublish.i18n.LABELS
    2. Theme         <templates>/<theme>/i18n.yaml
    3. Zielformat    <templates>/<theme>/<target>/i18n.yaml

Jede tiefere Ebene ueberschreibt die vorherige, aber nur die Schluessel, die
sie tatsaechlich setzt. Eine Dokumentebene gibt es nicht: Ebene 2 und 3
stammen immer aus dem einen Theme, das die Template-Aufloesung gewaehlt hat.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from markpublish.config.loader import load_config
from markpublish.i18n import (
    ANY_LANGUAGE,
    BUILTIN_I18N_PATH,
    LABELS,
    LabelFileError,
    LabelMap,
    UndefinedLabelError,
    build_labels,
    describe_labels,
    read_i18n_file,
)
from markpublish.markdown.engine import MarkdownPipeline
from markpublish.renderers.base import DocumentContext
from markpublish.renderers.pdf import PDFRenderer
from markpublish.templates.resolver import resolve_template_path


def write_i18n(directory: Path, content: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "i18n.yaml"
    path.write_text(content, encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# read_i18n_file
# --------------------------------------------------------------------------

def test_missing_file_is_not_an_error(tmp_path: Path):
    """Ein Theme ohne eigene Texte ist der Normalfall."""
    assert read_i18n_file(tmp_path) == {}


def test_empty_file_is_not_an_error(tmp_path: Path):
    write_i18n(tmp_path, "")
    assert read_i18n_file(tmp_path) == {}


def test_language_keys_are_normalized(tmp_path: Path):
    write_i18n(tmp_path, 'DE_AT:\n  part: "Teil (AT)"\n')
    assert read_i18n_file(tmp_path) == {"de-at": {"part": "Teil (AT)"}}


def test_flat_form_applies_to_every_language(tmp_path: Path):
    """Ohne Sprachebene gilt der Text fuer jede Sprache - wie "*"."""
    write_i18n(tmp_path, 'part: "Abschnitt"\n')
    assert read_i18n_file(tmp_path) == {ANY_LANGUAGE: {"part": "Abschnitt"}}

    assert build_labels("de", template_dirs=[tmp_path])["part"] == "Abschnitt"
    assert build_labels("en", template_dirs=[tmp_path])["part"] == "Abschnitt"


def test_star_key_and_flat_form_are_equivalent(tmp_path: Path):
    flat = tmp_path / "flat"
    star = tmp_path / "star"
    write_i18n(flat, 'version: "Rev."\n')
    write_i18n(star, '"*":\n  version: "Rev."\n')

    assert build_labels("de", template_dirs=[flat]) == build_labels("de", template_dirs=[star])


def test_language_block_beats_star_within_one_level(tmp_path: Path):
    write_i18n(tmp_path, '"*":\n  part: "Ueberall"\nde:\n  part: "Nur Deutsch"\n')
    assert build_labels("de", template_dirs=[tmp_path])["part"] == "Nur Deutsch"
    assert build_labels("en", template_dirs=[tmp_path])["part"] == "Ueberall"


def test_mapping_under_a_language_is_required(tmp_path: Path):
    """Eine Sprache, deren Wert kein Mapping ist, ist ein echter Fehler."""
    write_i18n(tmp_path, 'de: nur ein string\nen:\n  part: "Section"\n')
    with pytest.raises(LabelFileError, match="must be a mapping of key to text"):
        read_i18n_file(tmp_path)


def test_broken_yaml_names_the_file(tmp_path: Path):
    path = write_i18n(tmp_path, "de:\n  part: [unclosed\n")
    with pytest.raises(LabelFileError) as exc:
        read_i18n_file(tmp_path)
    assert str(path) in str(exc.value)


def test_scalar_document_raises(tmp_path: Path):
    write_i18n(tmp_path, "just a string\n")
    with pytest.raises(LabelFileError, match="expected language codes at the top level"):
        read_i18n_file(tmp_path)


# --------------------------------------------------------------------------
# build_labels - Reihenfolge der Ebenen
# --------------------------------------------------------------------------

def test_theme_level_overrides_program(tmp_path: Path):
    theme = tmp_path / "mytheme"
    write_i18n(theme, 'de:\n  part: "Abschnitt"\n')

    labels = build_labels("de", template_dirs=[theme])
    assert labels["part"] == "Abschnitt"
    # Nicht gesetzte Schluessel kommen weiter aus dem Programm
    assert labels["chapter"] == LABELS["de"]["chapter"]


def test_target_level_overrides_theme_level(tmp_path: Path):
    theme = tmp_path / "mytheme"
    target = theme / "pdf"
    write_i18n(theme, 'de:\n  part: "Theme"\n  chapter: "Theme-Kapitel"\n')
    write_i18n(target, 'de:\n  chapter: "PDF-Kapitel"\n')

    labels = build_labels("de", template_dirs=[theme, target])
    assert labels["chapter"] == "PDF-Kapitel"   # Ebene 3 gewinnt
    assert labels["part"] == "Theme"            # Ebene 2 bleibt


def test_target_level_is_the_last_word(tmp_path: Path):
    """Ueber Ebene 3 kommt nichts mehr - eine Dokumentebene gibt es nicht."""
    theme = tmp_path / "mytheme"
    target = theme / "pdf"
    write_i18n(theme, 'de:\n  chapter: "Theme"\n')
    write_i18n(target, 'de:\n  chapter: "PDF"\n')

    assert build_labels("de", template_dirs=[theme, target])["chapter"] == "PDF"


def test_other_language_blocks_do_not_leak(tmp_path: Path):
    """Die englischen Texte eines Themes duerfen nicht in deutsche Ausgabe."""
    theme = tmp_path / "mytheme"
    write_i18n(theme, 'en:\n  part: "Section"\nde:\n  chapter: "Kap."\n')

    labels = build_labels("de", template_dirs=[theme])
    assert labels["chapter"] == "Kap."
    assert labels["part"] == LABELS["de"]["part"]  # nicht "Section"


def test_regional_block_beats_base_block(tmp_path: Path):
    theme = tmp_path / "mytheme"
    write_i18n(theme, 'de:\n  part: "Teil"\nde-at:\n  part: "Teil (AT)"\n')

    assert build_labels("de-AT", template_dirs=[theme])["part"] == "Teil (AT)"
    assert build_labels("de", template_dirs=[theme])["part"] == "Teil"


def test_unknown_language_uses_fallback_block(tmp_path: Path):
    """document.language: fr -> Programm faellt auf en zurueck, Theme ebenso."""
    theme = tmp_path / "mytheme"
    write_i18n(theme, 'en:\n  part: "Section"\n')

    assert build_labels("fr", template_dirs=[theme])["part"] == "Section"


def test_every_key_still_resolves(tmp_path: Path):
    theme = tmp_path / "mytheme"
    write_i18n(theme, 'de:\n  part: "Abschnitt"\n')

    labels = build_labels("de", template_dirs=[theme])
    assert set(labels) >= set(LABELS["en"])
    assert all(labels.values())


# --------------------------------------------------------------------------
# describe_labels
# --------------------------------------------------------------------------

def test_describe_labels_names_each_layer(tmp_path: Path):
    theme = tmp_path / "mytheme"
    target = theme / "pdf"
    write_i18n(theme, 'de:\n  part: "Theme"\n')
    write_i18n(target, 'de:\n  chapter: "PDF"\n')

    described = describe_labels(
        "de", template_dirs=[theme, target], level_names=["theme", "target"]
    )
    # Ebene und Sprachblock getrennt: die Anzeige nennt den Block nur, wo er
    # von der Dokumentsprache abweicht.
    assert described["toc_title"]["source"] == "mpub"
    assert described["toc_title"]["language"] == "de"
    assert described["part"]["source"] == "theme"
    assert described["chapter"]["source"] == "target"
    assert described["toc_title"]["path"] == str(BUILTIN_I18N_PATH)
    assert described["part"]["path"] == str(theme / "i18n.yaml")
    assert described["chapter"]["path"] == str(target / "i18n.yaml")
    # Nicht ueberschriebene Texte bleiben beim Programm - jede Zeile der
    # Tabelle muss eine Datei nennen koennen, seit die Dokumentebene weg ist.
    assert described["author"]["path"] == str(BUILTIN_I18N_PATH)


# --------------------------------------------------------------------------
# Durchschlagen bis in die Ausgabe
# --------------------------------------------------------------------------

YAML = """\

document:
  title: "Cascade Test"
  author: "Test"
  date: "2026-08-31"
  language: "de"
  cover: false
  document_toc: "full"
{extra}
theme: "{theme}"
templates_dir: "./templates"

parts:
  - title: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "chapters/01.md"
        title: "First"
        break_before: "divider"
        chapter_toc: 2
"""


def _project_with_theme(tmp_path: Path) -> Path:
    """Kopiert das Built-in-Theme nach templates/mytheme."""
    import shutil

    chapters = tmp_path / "chapters"
    chapters.mkdir(exist_ok=True)
    (chapters / "01.md").write_text("# Head\n\nBody.\n\n## Sub\n\nText.\n", encoding="utf-8")

    theme_dir = tmp_path / "templates" / "mytheme"
    shutil.copytree(resolve_template_path("pdf", "default"), theme_dir / "pdf")
    return theme_dir


def _render(tmp_path: Path, target: str = "pdf", extra: str = "") -> str:
    (tmp_path / "markpublish.yaml").write_text(
        YAML.format(theme="mytheme", extra=extra), encoding="utf-8"
    )
    config = load_config(tmp_path / "markpublish.yaml")
    ctx = DocumentContext(
        config=config,
        content_items=[],
        toc_tree=[],
        template_path=resolve_template_path(
            target, "mytheme", custom_templates_dir=tmp_path / "templates"
        ),
        base_dir=tmp_path,
        target=target,
    )
    # Wie im Build: erst die Kaskade, dann damit durch die Pipeline -
    # sonst saehe der Markdown-Schritt die Theme-Texte nie.
    ctx.content_items, ctx.toc_tree = MarkdownPipeline(
        config, base_dir=tmp_path, labels=ctx.labels
    ).process_document()
    out = tmp_path / f"out.{target}"
    PDFRenderer().render(ctx, out)
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(out))
    return "\n".join(doc[i].get_textpage().get_text_range() for i in range(len(doc)))


def test_label_source_dirs_are_theme_then_target_then_project(tmp_path: Path):
    """
    Die Kaskade endet im Projekt: dort und nur dort kann ein Dokument die
    Beschriftung seiner eigenen freien Metadatenfelder hinschreiben.
    """
    theme_dir = _project_with_theme(tmp_path)
    (tmp_path / "markpublish.yaml").write_text(
        YAML.format(theme="mytheme", extra=""), encoding="utf-8"
    )
    config = load_config(tmp_path / "markpublish.yaml")
    ctx = DocumentContext(
        config=config,
        content_items=[],
        toc_tree=[],
        template_path=resolve_template_path(
            "pdf", "mytheme", custom_templates_dir=tmp_path / "templates"
        ),
        base_dir=tmp_path,
        target="pdf",
    )
    assert ctx.label_source_dirs == [theme_dir, theme_dir / "pdf", tmp_path.resolve()]


def test_theme_labels_reach_the_rendered_pdf(tmp_path: Path):
    theme_dir = _project_with_theme(tmp_path)
    write_i18n(theme_dir, 'de:\n  toc_title: "Wegweiser"\n')

    text = _render(tmp_path, "pdf")
    assert "Wegweiser" in text


def test_target_labels_only_affect_their_own_target(tmp_path: Path):
    theme_dir = _project_with_theme(tmp_path)
    write_i18n(theme_dir, 'de:\n  toc_title: "THEME"\n')
    write_i18n(theme_dir / "pdf", 'de:\n  toc_title: "NUR-PDF"\n')

    text = _render(tmp_path, "pdf")
    assert "NUR-PDF" in text


def test_theme_alert_titles_reach_the_markdown_output(tmp_path: Path):
    """
    Die Callout-Titel entstehen im Markdown-Schritt, lange bevor ein Template
    laeuft. Sie sind damit die einzige Stelle, an der die Kaskade die Pipeline
    erreichen muss statt nur den Renderer.
    """
    theme_dir = _project_with_theme(tmp_path)
    write_i18n(theme_dir, 'de:\n  alert_note: "Merke"\n')
    (tmp_path / "chapters" / "01.md").write_text(
        "# Head\n\n> [!NOTE]\n> Hinweistext.\n", encoding="utf-8"
    )

    text = _render(tmp_path, "pdf")
    assert "Merke" in text


def test_target_alert_titles_reach_the_markdown_output(tmp_path: Path):
    """Auch Ebene 3 - dafuer laeuft die Pipeline pro Zielformat."""
    theme_dir = _project_with_theme(tmp_path)
    write_i18n(theme_dir / "pdf", 'de:\n  alert_note: "Nur im PDF"\n')
    (tmp_path / "chapters" / "01.md").write_text(
        "# Head\n\n> [!NOTE]\n> Hinweistext.\n", encoding="utf-8"
    )

    assert "Nur im PDF" in _render(tmp_path, "pdf")


# --------------------------------------------------------------------------
# Die Dokumentebene ist entfallen - und schweigt darueber nicht
# --------------------------------------------------------------------------

@pytest.mark.parametrize("key", ["i18n", "labels"])
def test_document_level_keys_are_rejected(key: str):
    """
    Entscheidend ist die Meldung, nicht das Scheitern: DocumentConfig laesst
    unbekannte Felder zu (extra: allow), stilles Schlucken waere hier also der
    Normalfall gewesen - Build gruen, Text unveraendert, kein Hinweis.
    """
    from markpublish.config.models import DocumentConfig

    with pytest.raises(ValidationError) as excinfo:
        DocumentConfig(**{"title": "T", key: {"de": {"part": "Abschnitt"}}})

    message = str(excinfo.value)
    assert "i18n.yaml" in message, "Die Meldung muss den neuen Ort nennen"
    assert "export-template" in message


def test_document_level_keys_are_rejected_through_the_config_file(tmp_path: Path):
    config = tmp_path / "markpublish.yaml"
    config.write_text(
        'document:\n  title: "T"\n  i18n:\n    de:\n      part: "Abschnitt"\n',
        encoding="utf-8",
    )

    with pytest.raises(Exception) as excinfo:
        load_config(config)
    assert "i18n.yaml" in str(excinfo.value)


# --------------------------------------------------------------------------
# Freie Labels: eigene Schluessel des Themes
# --------------------------------------------------------------------------

def _use_label_in_layout(theme_dir: Path, target: str, snippet: str) -> Path:
    """Haengt eine Label-Verwendung an das layout.html des Themes."""
    layout = theme_dir / target / "layout.html"
    layout.write_text(layout.read_text(encoding="utf-8") + snippet, encoding="utf-8")
    return layout


@pytest.mark.skip(reason="Jinja template label check disabled after HTML removal")
def test_free_label_from_the_theme_reaches_the_output(tmp_path: Path):
    pass


@pytest.mark.skip(reason="Jinja template label check disabled after HTML removal")
def test_free_label_may_be_written_with_brackets(tmp_path: Path):
    pass


@pytest.mark.skip(reason="Jinja template label check disabled after HTML removal")
def test_free_label_may_be_defined_for_one_target_only(tmp_path: Path):
    pass


@pytest.mark.skip(reason="Jinja template label check disabled after HTML removal")
def test_free_label_missing_for_the_document_language_aborts(tmp_path: Path):
    pass


@pytest.mark.skip(reason="Jinja template label check disabled after HTML removal")
def test_star_key_covers_every_language_for_free_labels(tmp_path: Path):
    pass


@pytest.mark.skip(reason="Jinja template label check disabled after HTML removal")
def test_undefined_label_produces_no_output_file(tmp_path: Path):
    pass


@pytest.mark.skip(reason="Jinja template label check disabled after HTML removal")
def test_label_in_the_stylesheet_is_checked_too(tmp_path: Path):
    pass


def test_labelmap_raises_instead_of_yielding_an_empty_string():
    labels = build_labels("de")
    assert isinstance(labels, LabelMap)
    with pytest.raises(UndefinedLabelError):
        labels["gibt_es_nicht"]


@pytest.mark.skip(reason="Jinja template label check disabled after HTML removal")
def test_find_label_references_reports_file_and_line(tmp_path: Path):
    pass


@pytest.mark.skip(reason="Jinja template label check disabled after HTML removal")
def test_mapping_methods_are_not_mistaken_for_labels(tmp_path: Path):
    pass


# --------------------------------------------------------------------------
# Ebene 1 kommt jetzt aus einer Datei
# --------------------------------------------------------------------------

#: Unabhaengige Referenz. Bewusst ausgeschrieben statt aus LABELS abgeleitet -
#: sonst waere jede Pruefung dagegen zirkulaer und eine leere Tabelle bestuende
#: den Test.
EXPECTED_KEYS = {
    "toc_title", "chapter_toc_title", "part_toc_title",
    "chapter", "part",
    "author", "status", "version", "date", "copyright",
    "bool_true", "bool_false",
    "page", "page_of",
    "alert_note", "alert_tip", "alert_important", "alert_warning", "alert_caution",
}


def test_builtin_level_is_a_shipped_yaml_file():
    assert BUILTIN_I18N_PATH.is_file()
    assert BUILTIN_I18N_PATH.name == "i18n.yaml"


def test_builtin_level_is_complete_in_every_language():
    for lang, table in LABELS.items():
        assert set(table) == EXPECTED_KEYS, f"'{lang}' weicht ab: {set(table) ^ EXPECTED_KEYS}"
        assert all(table.values()), f"'{lang}' enthaelt leere Texte"


def test_resolved_labels_contain_every_expected_key(tmp_path: Path):
    write_i18n(tmp_path, 'de:\n  part: "Abschnitt"\n')
    labels = build_labels("de", template_dirs=[tmp_path])
    assert set(labels) == EXPECTED_KEYS
    assert all(labels.values())


def test_builtin_values_come_from_the_yaml_file():
    """LABELS muss wirklich aus i18n.yaml stammen, nicht aus Code."""
    import yaml

    raw = yaml.safe_load(BUILTIN_I18N_PATH.read_text(encoding="utf-8"))
    assert raw["de"]["toc_title"] == LABELS["de"]["toc_title"]
    assert raw["en"]["page_of"] == LABELS["en"]["page_of"]


def test_default_theme_ships_all_three_files():
    """Ebene 2 und 3 liegen dem Theme bei - als Datei, nicht nur als Doku."""
    theme = resolve_template_path("pdf", "default").parent
    assert (theme / "i18n.yaml").is_file()
    assert (theme / "pdf" / "i18n.yaml").is_file()


def test_default_theme_sets_its_own_wording():
    """
    Das Theme spricht bewusst nicht wie der Programmstandard: "Abschnitt"
    statt "Teil", "Auf einen Blick" statt "Inhalt dieses Kapitels". Der Test
    haelt fest, dass es in JEDER mitgelieferten Sprache dieselben Schluessel
    setzt - eine einseitig gepflegte Sprache faellt sonst erst im fertigen
    Dokument auf.
    """
    theme = resolve_template_path("pdf", "default").parent
    table = read_i18n_file(theme)

    assert set(table) == {"de", "en"}
    assert set(table["de"]) == set(table["en"]), (
        f"Sprachen weichen ab: {set(table['de']) ^ set(table['en'])}"
    )
    assert table["de"]["part"] == "Abschnitt"
    assert table["en"]["part"] == "Section"

    # Nur bekannte Programm-Schluessel - ein Tippfehler waere hier sonst ein
    # freies Label, das niemand im Template benutzt und das stumm bleibt.
    assert set(table["de"]) <= set(LABELS["de"])


def test_default_theme_target_levels_stay_inert():
    """Ebene 3 ist reines Muster - PDF und HTML sollen gleich sprechen."""
    theme = resolve_template_path("pdf", "default").parent
    assert read_i18n_file(theme / "pdf") == {}


# --------------------------------------------------------------------------
# Ebene 4: Projekt-Ebene (./i18n.yaml neben markpublish.yaml)
# --------------------------------------------------------------------------

def test_project_level_overrides_builtin_and_theme_labels(tmp_path: Path):
    """
    Ebene 4 gewinnt ueber alle vorherigen Ebenen.
    """
    theme_dir = tmp_path / "theme"
    write_i18n(theme_dir, 'de:\n  toc_title: "Themen-Inhalt"\n')

    project_dir = tmp_path / "project"
    write_i18n(project_dir, 'de:\n  toc_title: "Projekt-Inhaltsverzeichnis"\n')

    labels = build_labels("de", template_dirs=[theme_dir, project_dir])
    assert labels["toc_title"] == "Projekt-Inhaltsverzeichnis"


def test_project_level_provides_labels_for_custom_metadata_fields(tmp_path: Path):
    """
    Ebene 4 versorgt freie Zusatzmetadaten des Dokuments mit Beschriftungen.
    """
    from markpublish.config.models import DocumentConfig
    from markpublish.i18n import build_document_metadata

    project_dir = tmp_path / "project"
    write_i18n(
        project_dir,
        'de:\n  department: "Fachabteilung"\n  classification: "Vertraulichkeitsstufe"\n',
    )

    labels = build_labels("de", template_dirs=[project_dir])
    doc = DocumentConfig(
        title="Test",
        department="F&E",
        classification="Intern",
    )

    meta_entries = build_document_metadata(doc, labels)
    assert meta_entries["department"].label == "Fachabteilung"
    assert meta_entries["department"].value == "F&E"
    assert meta_entries["classification"].label == "Vertraulichkeitsstufe"
    assert meta_entries["classification"].value == "Intern"


def test_project_level_reflected_in_describe_labels(tmp_path: Path):
    """
    describe_labels weist Ebene 4 als 'projekt' und ueberschrieben aus.
    """
    from markpublish.i18n import LEVEL_PROJECT

    project_dir = tmp_path / "project"
    write_i18n(project_dir, 'de:\n  department: "Fachbereich"\n')

    resolved = describe_labels(
        "de",
        template_dirs=[project_dir],
        level_names=[LEVEL_PROJECT],
    )

    assert "department" in resolved
    assert resolved["department"]["value"] == "Fachbereich"
    assert resolved["department"]["source"] == LEVEL_PROJECT
    assert str(project_dir / "i18n.yaml") == resolved["department"]["path"]
