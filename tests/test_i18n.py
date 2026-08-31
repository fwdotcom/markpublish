"""
Tests fuer die Uebersetzungstabelle der statischen Template-Texte.
"""

from pathlib import Path

import pytest

from markpublish.config.loader import load_config
from markpublish.i18n import (
    FALLBACK_LANGUAGE,
    LABELS,
    available_languages,
    get_labels,
    normalize_language,
)
from markpublish.markdown.engine import MarkdownEngine, MarkdownPipeline
from markpublish.renderers.base import DocumentContext
from markpublish.renderers.html import HTMLRenderer
from markpublish.templates.resolver import resolve_template_path


def test_all_languages_cover_the_same_keys():
    """Eine unvollstaendige Sprache wuerde sonst leere Texte erzeugen."""
    reference = set(LABELS[FALLBACK_LANGUAGE])
    for lang, table in LABELS.items():
        assert set(table) == reference, f"Sprache '{lang}' weicht ab: {set(table) ^ reference}"


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("de", "de"),
        ("DE", "de"),
        ("de-AT", "de"),
        ("de_DE", "de"),
        ("en", "en"),
        ("en-GB", "en"),
        ("fr", FALLBACK_LANGUAGE),
        ("", FALLBACK_LANGUAGE),
        (None, FALLBACK_LANGUAGE),
    ],
)
def test_normalize_language(raw, expected):
    assert normalize_language(raw) == expected


def test_get_labels_picks_the_language():
    assert get_labels("de")["toc_title"] == "Inhaltsverzeichnis"
    assert get_labels("en")["toc_title"] == "Table of Contents"


def test_unknown_language_falls_back_without_gaps():
    labels = get_labels("fr")
    assert set(labels) == set(LABELS[FALLBACK_LANGUAGE])
    assert all(v for v in labels.values()), "Kein Text darf leer sein"


def test_overrides_win():
    labels = get_labels("de", {"toc_title": "Übersicht", "chapter": "Abschnitt"})
    assert labels["toc_title"] == "Übersicht"
    assert labels["chapter"] == "Abschnitt"
    # Nicht ueberschriebene Texte bleiben in der Dokumentsprache
    assert labels["page"] == "Seite"


def test_overrides_can_supply_an_unlisted_language():
    """Eine dritte Sprache laesst sich ohne Template-Aenderung setzen."""
    labels = get_labels("fr", {"toc_title": "Table des matières", "chapter": "Chapitre"})
    assert labels["toc_title"] == "Table des matières"
    assert labels["chapter"] == "Chapitre"


def test_available_languages():
    assert set(available_languages()) >= {"de", "en"}


def test_alert_titles_come_from_the_same_table():
    """alerts.py hatte frueher eine eigene Titeltabelle - jetzt nur noch eine."""
    de = MarkdownEngine(language="de").convert("> [!WARNING]\n> Text.")
    en = MarkdownEngine(language="en").convert("> [!WARNING]\n> Text.")
    assert LABELS["de"]["alert_warning"] in de
    assert LABELS["en"]["alert_warning"] in en


# --------------------------------------------------------------------------
# Durchschlagen bis in die gerenderte Ausgabe
# --------------------------------------------------------------------------

YAML = """
document:
  title: "Language Test"
  author: "Test"
  date: "2026-08-31"
  language: "{lang}"
  cover: true
  toc: true
{extra}
chapters:
  - file: "chapters/01.md"
    title: "First"
    divider_page: true
    toc: 2
"""


def _render_html(tmp_path: Path, lang: str, extra: str = "") -> str:
    chapters = tmp_path / "chapters"
    chapters.mkdir(exist_ok=True)
    (chapters / "01.md").write_text(
        "# Heading\n\nBody.\n\n## Section\n\nText.\n", encoding="utf-8"
    )
    (tmp_path / "markpublish.yaml").write_text(
        YAML.format(lang=lang, extra=extra), encoding="utf-8"
    )
    config = load_config(tmp_path / "markpublish.yaml")
    items, tree = MarkdownPipeline(config, base_dir=tmp_path).process_document()
    ctx = DocumentContext(
        config=config,
        content_items=items,
        toc_tree=tree,
        template_path=resolve_template_path("html", "default"),
        base_dir=tmp_path,
        target="html",
    )
    out = tmp_path / "out.html"
    HTMLRenderer().render(ctx, out)
    return out.read_text(encoding="utf-8")


def _body_only(html: str) -> str:
    """Ohne das eingebettete Stylesheet - dort stehen deutsche CSS-Kommentare."""
    start = html.index("</style>")
    return html[start:]


def test_german_labels_reach_the_html_output(tmp_path: Path):
    html = _render_html(tmp_path, "de")
    assert "Inhalt dieses Kapitels" in html
    assert ">Kapitel 1<" in html or "Kapitel 1" in html
    assert "<strong>Autor:</strong>" in html


def test_english_labels_reach_the_html_output(tmp_path: Path):
    html = _render_html(tmp_path, "en")
    assert "In this chapter" in html
    assert "Chapter 1" in html
    assert "<strong>Author:</strong>" in html

    body = _body_only(html)
    assert "Kapitel" not in body
    assert "Autor" not in body
    assert "Inhalt dieses Kapitels" not in body


def test_document_labels_override_reaches_the_output(tmp_path: Path):
    extra = '  labels:\n    chapter_toc_title: "Auf dieser Seite"\n    author: "Verfasst von"\n'
    html = _render_html(tmp_path, "de", extra)
    assert "Auf dieser Seite" in html
    assert "<strong>Verfasst von:</strong>" in html
    assert "Inhalt dieses Kapitels" not in _body_only(html)


def test_page_label_reaches_the_pdf_stylesheet(tmp_path: Path):
    """Die Fusszeile 'Seite X von Y' steht im CSS, nicht im HTML-Template."""
    from markpublish.renderers.base import BaseRenderer

    class _Probe(BaseRenderer):
        def render(self, context, output_path):  # pragma: no cover - ungenutzt
            raise NotImplementedError

    chapters = tmp_path / "chapters"
    chapters.mkdir()
    (chapters / "01.md").write_text("# H\n\nText.\n", encoding="utf-8")
    (tmp_path / "markpublish.yaml").write_text(
        YAML.format(lang="en", extra=""), encoding="utf-8"
    )
    config = load_config(tmp_path / "markpublish.yaml")
    items, tree = MarkdownPipeline(config, base_dir=tmp_path).process_document()
    ctx = DocumentContext(
        config=config,
        content_items=items,
        toc_tree=tree,
        template_path=resolve_template_path("pdf", "default"),
        base_dir=tmp_path,
        target="pdf",
    )
    rendered = _Probe().render_template(ctx)
    assert '"Page " counter(page) " of " counter(pages)' in rendered
