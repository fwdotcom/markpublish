"""
Tests fuer die vierstufige Label-Kaskade.

    1. Programm      markpublish.i18n.LABELS
    2. Theme         <templates>/<theme>/i18n.yaml
    3. Zielformat    <templates>/<theme>/<target>/i18n.yaml
    4. Dokument      document.i18n

Jede tiefere Ebene ueberschreibt die vorherige, aber nur die Schluessel, die
sie tatsaechlich setzt.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from markpublish.config.loader import load_config
from markpublish.i18n import (
    ANY_LANGUAGE,
    BUILTIN_I18N_PATH,
    LABELS,
    LabelFileError,
    build_labels,
    describe_labels,
    read_i18n_file,
)
from markpublish.markdown.engine import MarkdownPipeline
from markpublish.renderers.base import DocumentContext
from markpublish.renderers.html import HTMLRenderer
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
    with pytest.raises(LabelFileError, match="Zuordnung von Schluessel zu Text"):
        read_i18n_file(tmp_path)


def test_broken_yaml_names_the_file(tmp_path: Path):
    path = write_i18n(tmp_path, "de:\n  part: [unclosed\n")
    with pytest.raises(LabelFileError) as exc:
        read_i18n_file(tmp_path)
    assert str(path) in str(exc.value)


def test_scalar_document_raises(tmp_path: Path):
    write_i18n(tmp_path, "just a string\n")
    with pytest.raises(LabelFileError, match="Sprachcodes auf oberster Ebene"):
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


def test_document_overrides_win_over_everything(tmp_path: Path):
    theme = tmp_path / "mytheme"
    target = theme / "pdf"
    write_i18n(theme, 'de:\n  chapter: "Theme"\n')
    write_i18n(target, 'de:\n  chapter: "PDF"\n')

    labels = build_labels("de", template_dirs=[theme, target], overrides={"chapter": "Dokument"})
    assert labels["chapter"] == "Dokument"


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
        "de", template_dirs=[theme, target], overrides={"author": "Verfasser"}
    )
    assert described["toc_title"]["source"] == "i18n.yaml (de)"
    assert described["toc_title"]["path"] == str(BUILTIN_I18N_PATH)
    assert "i18n.yaml" in described["part"]["source"]
    assert described["part"]["path"] == str(theme / "i18n.yaml")
    assert described["chapter"]["path"] == str(target / "i18n.yaml")
    assert described["author"]["source"] == "document.i18n"
    assert described["author"]["path"] == ""


# --------------------------------------------------------------------------
# Durchschlagen bis in die Ausgabe
# --------------------------------------------------------------------------

YAML = """
document:
  title: "Cascade Test"
  author: "Test"
  date: "2026-08-31"
  language: "de"
  cover: false
  toc: true
{extra}
theme: "{theme}"
templates_dir: "./templates"

chapters:
  - file: "chapters/01.md"
    title: "First"
    divider_page: true
    toc: 2
"""


def _project_with_theme(tmp_path: Path) -> Path:
    """Kopiert das Built-in-Theme nach templates/mytheme."""
    import shutil

    chapters = tmp_path / "chapters"
    chapters.mkdir(exist_ok=True)
    (chapters / "01.md").write_text("# Head\n\nBody.\n\n## Sub\n\nText.\n", encoding="utf-8")

    theme_dir = tmp_path / "templates" / "mytheme"
    for tgt in ("pdf", "html"):
        shutil.copytree(resolve_template_path(tgt, "default"), theme_dir / tgt)
    return theme_dir


def _render(tmp_path: Path, target: str, extra: str = "") -> str:
    (tmp_path / "markpublish.yaml").write_text(
        YAML.format(theme="mytheme", extra=extra), encoding="utf-8"
    )
    config = load_config(tmp_path / "markpublish.yaml")
    items, tree = MarkdownPipeline(config, base_dir=tmp_path).process_document()
    ctx = DocumentContext(
        config=config,
        content_items=items,
        toc_tree=tree,
        template_path=resolve_template_path(
            target, "mytheme", custom_templates_dir=tmp_path / "templates"
        ),
        base_dir=tmp_path,
        target=target,
    )
    out = tmp_path / f"out.{target}"
    HTMLRenderer().render(ctx, out)
    return out.read_text(encoding="utf-8")


def test_label_source_dirs_are_theme_then_target(tmp_path: Path):
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
    assert ctx.label_source_dirs == [theme_dir, theme_dir / "pdf"]


def test_theme_labels_reach_the_rendered_html(tmp_path: Path):
    theme_dir = _project_with_theme(tmp_path)
    write_i18n(theme_dir, 'de:\n  chapter_toc_title: "Auf dieser Seite"\n')

    html = _render(tmp_path, "html")
    assert "Auf dieser Seite" in html
    assert "Inhalt dieses Kapitels" not in html


def test_target_labels_only_affect_their_own_target(tmp_path: Path):
    theme_dir = _project_with_theme(tmp_path)
    write_i18n(theme_dir, 'de:\n  chapter: "THEME"\n')
    write_i18n(theme_dir / "pdf", 'de:\n  chapter: "NUR-PDF"\n')

    html = _render(tmp_path, "html")
    assert "THEME" in html
    assert "NUR-PDF" not in html


def test_legacy_layout_skips_the_theme_level(tmp_path: Path):
    """
    Im alten <target>/<theme> ist das Elternverzeichnis das Zielformat und
    wird von allen Themes geteilt - es darf nicht als Theme-Ebene zaehlen.
    """
    import shutil

    legacy = tmp_path / "templates" / "pdf" / "altes-theme"
    shutil.copytree(resolve_template_path("pdf", "default"), legacy)

    (tmp_path / "markpublish.yaml").write_text(
        YAML.format(theme="altes-theme", extra=""), encoding="utf-8"
    )
    config = load_config(tmp_path / "markpublish.yaml")

    with pytest.warns(DeprecationWarning):
        resolved = resolve_template_path(
            "pdf", "altes-theme", custom_templates_dir=tmp_path / "templates"
        )

    ctx = DocumentContext(
        config=config,
        content_items=[],
        toc_tree=[],
        template_path=resolved,
        base_dir=tmp_path,
        target="pdf",
    )
    assert ctx.label_source_dirs == [legacy]


# --------------------------------------------------------------------------
# Ebene 4 - gleicher Aufbau wie die Dateien
# --------------------------------------------------------------------------

def test_document_level_accepts_the_language_keyed_form():
    labels = build_labels("de", overrides={"de": {"part": "Abschnitt"}, "en": {"part": "Section"}})
    assert labels["part"] == "Abschnitt"


def test_document_level_language_block_does_not_leak():
    labels = build_labels("en", overrides={"de": {"part": "Abschnitt"}})
    assert labels["part"] == LABELS["en"]["part"]


def test_document_level_flat_form_still_works():
    """Kurzform ohne Sprachebene - gilt fuer jede Sprache."""
    assert build_labels("de", overrides={"part": "Abschnitt"})["part"] == "Abschnitt"


def test_labels_key_is_accepted_as_alias_for_i18n():
    from markpublish.config.models import DocumentConfig

    doc = DocumentConfig(title="T", labels={"de": {"part": "Abschnitt"}})
    assert doc.i18n == {"de": {"part": "Abschnitt"}}


def test_i18n_wins_when_both_keys_are_present():
    from markpublish.config.models import DocumentConfig

    doc = DocumentConfig(title="T", i18n={"de": {"part": "Neu"}}, labels={"de": {"part": "Alt"}})
    assert doc.i18n == {"de": {"part": "Neu"}}


# --------------------------------------------------------------------------
# Ebene 1 kommt jetzt aus einer Datei
# --------------------------------------------------------------------------

#: Unabhaengige Referenz. Bewusst ausgeschrieben statt aus LABELS abgeleitet -
#: sonst waere jede Pruefung dagegen zirkulaer und eine leere Tabelle bestuende
#: den Test.
EXPECTED_KEYS = {
    "toc_title", "toc_sidebar", "chapter_toc_title",
    "chapter", "part",
    "author", "status", "version", "date", "copyright",
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


def test_default_theme_ships_pattern_files():
    """Muster fuer Ebene 2 und 3 - vorhanden, aber ohne Wirkung."""
    theme = resolve_template_path("pdf", "default").parent
    assert (theme / "i18n.yaml").is_file()
    assert (theme / "pdf" / "i18n.yaml").is_file()
    assert (theme / "html" / "i18n.yaml").is_file()

    # Sie duerfen den Standard nicht veraendern
    assert read_i18n_file(theme) == {}
    assert read_i18n_file(theme / "pdf") == {}
    assert read_i18n_file(theme / "html") == {}
