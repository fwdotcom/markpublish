"""
Tests fuer die Uebersetzungstabelle der statischen Template-Texte.
"""

import re
from pathlib import Path

import pytest

from markpublish.config.loader import load_config
from markpublish.i18n import (
    FALLBACK_LANGUAGE,
    LABELS,
    available_languages,
    default_document_language,
    detect_system_language,
    get_labels,
    normalize_language,
)
from markpublish.markdown.engine import MarkdownEngine, MarkdownPipeline
from markpublish.renderers.base import DocumentContext
from markpublish.renderers.pdf import PDFRenderer
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


def test_available_languages():
    assert set(available_languages()) >= {"de", "en"}


def test_alert_titles_come_from_the_same_table():
    """Die Alert-Titel kommen aus derselben Tabelle wie alle anderen Texte."""
    de = MarkdownEngine(language="de").convert("> [!WARNING]\n> Text.")
    en = MarkdownEngine(language="en").convert("> [!WARNING]\n> Text.")
    assert LABELS["de"]["alert_warning"] in de
    assert LABELS["en"]["alert_warning"] in en


def test_alert_titles_follow_the_resolved_cascade():
    """
    Die Callout-Titel entstehen beim Markdown-Parsen, nicht im Template. Ohne
    durchgereichte Labels sah dieser Schritt nur Ebene 1 - ein Theme konnte
    alert_note setzen, im Callout stand trotzdem "Hinweis".
    """
    labels = dict(LABELS["de"], alert_note="Merke")
    html = MarkdownEngine(language="de", labels=labels).convert("> [!NOTE]\n> Text.")

    assert "Merke" in html
    assert "Hinweis" not in html


def test_alert_titles_fall_back_to_the_program_texts():
    """Ohne uebergebene Labels bleibt es beim Programmstandard."""
    html = MarkdownEngine(language="de", labels=None).convert("> [!NOTE]\n> Text.")
    assert LABELS["de"]["alert_note"] in html


# --------------------------------------------------------------------------
# Durchschlagen bis in die gerenderte Ausgabe
# --------------------------------------------------------------------------

YAML = """\
document:
  title: "i18n Test"
  author: "Test"
  date: "2026-08-31"
  language: "{lang}"
  cover: true
  document_toc: "full"
{extra}
theme: "default"

parts:
  - part: "Part"
    break_before: "none"
    chapters:
      - file: "chapters/01.md"
"""


def _render_pdf(tmp_path: Path, lang: str, extra: str = "") -> str:
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
        template_path=resolve_template_path("pdf", "default"),
        base_dir=tmp_path,
        target="pdf",
    )
    out = tmp_path / "out.pdf"
    PDFRenderer().render(ctx, out)
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(out))
    return "\n".join(doc[i].get_textpage().get_text_range() for i in range(len(doc)))


def test_german_labels_reach_the_pdf_output(tmp_path: Path):
    text = _render_pdf(tmp_path, "de")
    assert "Inhaltsverzeichnis" in text
    assert "AUTOR" in text.upper()
    assert "DATUM" in text.upper()


def test_english_labels_reach_the_pdf_output(tmp_path: Path):
    text = _render_pdf(tmp_path, "en")
    assert "Table of Contents" in text or "Contents" in text
    assert "AUTHOR" in text.upper()
    assert "DATE" in text.upper()


def test_document_level_labels_are_rejected_by_the_loader(tmp_path: Path):
    """
    Der Test nimmt den kompletten Weg - YAML-Datei, Loader, Modell - und nicht
    nur das Modell direkt.
    """
    extra = '  labels:\n    chapter_toc_title: "Auf dieser Seite"\n'
    with pytest.raises(Exception) as excinfo:
        _render_pdf(tmp_path, "de", extra)
    assert "i18n.yaml" in str(excinfo.value)


@pytest.mark.skip(reason="PDF stylesheet replaced by native Typst pagination")
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


# --------------------------------------------------------------------------
# Systemsprache
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("de_DE.UTF-8", "de-DE"),
        ("de-de", "de-DE"),
        ("pt_BR", "pt-BR"),
        ("en", "en"),
        ("fr_FR@euro", "fr-FR"),
        # Prioritaetsliste: der erste Eintrag zaehlt.
        ("de:en:C", "de"),
        # "Keine Sprache gewaehlt" ist keine Sprache.
        ("C", None),
        ("POSIX", None),
        ("", None),
    ],
)
def test_locale_strings_are_reduced_to_a_language_code(monkeypatch, raw, expected):
    """
    Aus dem, was ein System meldet, muss ein Sprachcode werden - Zeichensatz,
    Modifikator und Prioritaetsliste gehoeren nicht dazu. Geschrieben wird die
    uebliche Form 'de-DE', weil der Wert in einer markpublish.yaml landen kann.
    """
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        monkeypatch.delenv(var, raising=False)
    if raw:
        monkeypatch.setenv("LANGUAGE", raw)

    detected = detect_system_language()
    if expected is None:
        # Ohne brauchbare Variable darf die Erkennung das System befragen; nur
        # der leere/neutrale Wert selbst darf nicht durchschlagen.
        assert detected != raw
    else:
        assert detected == expected


def test_detected_language_resolves_to_a_label_set(monkeypatch):
    """Regionale Formen muessen bei den Beschriftungen ankommen."""
    monkeypatch.setenv("LANGUAGE", "de_AT.UTF-8")

    assert detect_system_language() == "de-AT"
    assert normalize_language(detect_system_language()) == "de"


def test_document_language_falls_back_when_nothing_is_detected(monkeypatch):
    """
    Ohne erkennbare Systemsprache bleibt die Fallback-Sprache - raten waere
    hier schlimmer als der bekannte Standard.
    """
    monkeypatch.setattr("markpublish.i18n.detect_system_language", lambda: None)

    assert default_document_language() == FALLBACK_LANGUAGE


def test_document_without_language_takes_the_system_language(tmp_path, monkeypatch):
    """
    Wer nichts hinschreibt, schreibt fast immer in der Sprache seines Rechners.
    Ein fest verdrahteter Code waere fuer die Haelfte aller Nutzer falsch.
    """
    monkeypatch.setenv("LANGUAGE", "de_DE.UTF-8")

    config = load_config({"document": {"title": "Ohne Sprachangabe"}})

    assert normalize_language(config.document.language) == "de"
    # Das Datum folgt derselben Sprache - sonst stuende ein ISO-Datum unter
    # einem deutschen Dokument.
    assert re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", config.document.date)
