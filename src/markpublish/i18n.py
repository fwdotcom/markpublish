"""
Uebersetzungstabelle fuer die statischen Texte in Templates und Stylesheets.

Eine Zeile pro Sprache, ein Schluessel pro Text. Templates greifen ueber das
`labels`-Objekt darauf zu (`{{ labels.toc_title }}`), das Stylesheet ebenso --
`styles.css` wird durch dieselbe Jinja-Umgebung gerendert.

Gesteuert wird die Auswahl ueber `document.language` in der markpublish.yaml.
Einzelne Texte lassen sich dort unter `document.labels` ueberschreiben, ohne
das Template anzufassen; dieselbe Stelle dient dazu, eine hier noch nicht
gepflegte Sprache vollstaendig selbst zu setzen.
"""

from __future__ import annotations

from typing import Dict, List, Mapping, Optional

#: Sprache, auf die zurueckgefallen wird, wenn `document.language` unbekannt
#: ist. Sie muss jeden Schluessel enthalten - get_labels() legt sie als Basis
#: unter jede andere Sprache, damit auch eine unvollstaendige Uebersetzung
#: niemals einen leeren Text erzeugt.
FALLBACK_LANGUAGE = "en"

LABELS: Dict[str, Dict[str, str]] = {
    "en": {
        # Table of contents
        "toc_title": "Table of Contents",
        "toc_sidebar": "Contents",
        "chapter_toc_title": "In this chapter",
        # Structural tags on divider pages
        "chapter": "Chapter",
        "part": "Part",
        # Cover metadata
        "author": "Author",
        "status": "Status",
        "version": "Version",
        "date": "Date",
        "copyright": "Copyright",
        # Running footer: "Page 3 of 24"
        "page": "Page",
        "page_of": "of",
        # GitHub-style callouts
        "alert_note": "Note",
        "alert_tip": "Tip",
        "alert_important": "Important",
        "alert_warning": "Warning",
        "alert_caution": "Caution",
    },
    "de": {
        "toc_title": "Inhaltsverzeichnis",
        "toc_sidebar": "Inhalt",
        "chapter_toc_title": "Inhalt dieses Kapitels",
        "chapter": "Kapitel",
        "part": "Teil",
        "author": "Autor",
        "status": "Status",
        "version": "Version",
        "date": "Datum",
        "copyright": "Copyright",
        "page": "Seite",
        "page_of": "von",
        "alert_note": "Hinweis",
        "alert_tip": "Tipp",
        "alert_important": "Wichtig",
        "alert_warning": "Warnung",
        "alert_caution": "Achtung",
    },
}


def available_languages() -> List[str]:
    """Returns the language codes the built-in table covers."""
    return sorted(LABELS)


def normalize_language(language: Optional[str]) -> str:
    """
    Maps a document language onto a key of LABELS.

    Accepts regional forms: "de-AT" and "de_DE" both resolve to "de". Anything
    the table does not cover falls back to FALLBACK_LANGUAGE.
    """
    if not language:
        return FALLBACK_LANGUAGE

    code = str(language).strip().lower().replace("_", "-")
    if code in LABELS:
        return code

    base = code.split("-", 1)[0]
    return base if base in LABELS else FALLBACK_LANGUAGE


def get_labels(
    language: Optional[str] = None,
    overrides: Optional[Mapping[str, str]] = None,
) -> Dict[str, str]:
    """
    Builds the label set for one document.

    Layered so that every key always resolves: the fallback language provides
    the base, the document language overlays it, and `document.labels` from the
    YAML wins last. A missing translation therefore shows the English text
    rather than an empty string.
    """
    merged = dict(LABELS[FALLBACK_LANGUAGE])
    merged.update(LABELS[normalize_language(language)])
    if overrides:
        merged.update({str(k): str(v) for k, v in overrides.items()})
    return merged
