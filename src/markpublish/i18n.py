"""
Aufloesung der statischen Texte (Labels) fuer Templates und Stylesheets.

Ein Schluessel pro Text, aufgeloest ueber eine Kaskade aus vier Ebenen. Jede
tiefere Ebene ueberschreibt die daruber liegende -- und zwar nur die
Schluessel, die sie tatsaechlich setzt:

    1. Programm      markpublish/i18n.yaml
    2. Theme         <templates>/<theme>/i18n.yaml
    3. Zielformat    <templates>/<theme>/<target>/i18n.yaml
    4. Dokument      document.i18n in der markpublish.yaml

Alle vier Ebenen sind identisch aufgebaut: Sprachcode auf oberster Ebene,
darunter die Texte.

    de:
      part: "Abschnitt"
      chapter_toc_title: "Auf dieser Seite"
    en:
      part: "Section"

Der Sonderschluessel "*" gilt fuer jede Sprache und wird vor dem
sprachspezifischen Block angewendet -- praktisch fuer Begriffe, die unabhaengig
von der Sprache gleich heissen sollen.

Ebene 1 muss vollstaendig sein; sie legt zusaetzlich die Fallback-Sprache unter
die Dokumentsprache, damit jeder Schluessel garantiert aufloest. Die Ebenen 2-4
greifen nur fuer die gewaehlte Sprache, damit die englischen Texte eines Themes
nicht in eine deutsche Ausgabe durchschlagen.

Templates greifen auf das Ergebnis ueber `labels` zu (`{{ labels.toc_title }}`),
das Stylesheet ebenso -- `styles.css` laeuft durch dieselbe Jinja-Umgebung.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

import yaml

#: Sprache, auf die zurueckgefallen wird, wenn `document.language` unbekannt
#: ist. Sie muss jeden Schluessel enthalten - build_labels() legt sie als Basis
#: unter jede andere Sprache, damit auch eine unvollstaendige Uebersetzung
#: niemals einen leeren Text erzeugt.
FALLBACK_LANGUAGE = "en"

#: Dateiname der Ebenen 1-3.
I18N_FILENAME = "i18n.yaml"

#: Sprachcode, der auf jede Sprache angewendet wird.
ANY_LANGUAGE = "*"

#: Ebene 1, mitgeliefert im Paket.
BUILTIN_I18N_PATH = Path(__file__).resolve().parent / I18N_FILENAME


class LabelFileError(ValueError):
    """Raised when an i18n.yaml exists but cannot be used."""


def _normalize_language_key(value: Any) -> str:
    return str(value).strip().lower().replace("_", "-")


def normalize_table(raw: Any, source: str) -> Dict[str, Dict[str, str]]:
    """
    Brings one level of the cascade into the shape {language: {key: text}}.

    Accepts the canonical language-keyed form and, for convenience, a flat
    mapping of key -> text; the latter is treated as ANY_LANGUAGE, i.e. it
    applies whatever the document language is.

    Args:
        raw: the parsed YAML (or dict) of one level
        source: human-readable origin, used in error messages
    """
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise LabelFileError(
            f"{source}: erwartet werden Sprachcodes auf oberster Ebene, "
            f"gefunden {type(raw).__name__}."
        )

    values = list(raw.values())
    if values and all(isinstance(v, str) for v in values):
        # Flache Form ohne Sprachebene - gilt fuer jede Sprache.
        return {ANY_LANGUAGE: {str(k): str(v) for k, v in raw.items()}}

    table: Dict[str, Dict[str, str]] = {}
    for lang, entries in raw.items():
        if not isinstance(entries, Mapping):
            raise LabelFileError(
                f"{source}: '{lang}' muss eine Zuordnung von Schluessel zu Text sein. "
                'Erwartetes Format:  de:\n    part: "Abschnitt"'
            )
        table[_normalize_language_key(lang)] = {str(k): str(v) for k, v in entries.items()}
    return table


def read_i18n_file(directory: Path) -> Dict[str, Dict[str, str]]:
    """
    Reads <directory>/i18n.yaml.

    Returns an empty mapping if the file does not exist - a theme without
    custom texts is the normal case. A file that exists but is malformed raises
    LabelFileError naming the path, because silently ignoring it would leave
    the user staring at unchanged output with no hint why.
    """
    path = Path(directory) / I18N_FILENAME
    if not path.is_file():
        return {}
    return _read_table_file(path)


def _read_table_file(path: Path) -> Dict[str, Dict[str, str]]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as err:
        raise LabelFileError(f"{path}: kein gueltiges YAML - {err}") from err
    except OSError as err:
        raise LabelFileError(f"{path}: nicht lesbar - {err}") from err
    return normalize_table(raw, str(path))


def _load_builtin() -> Dict[str, Dict[str, str]]:
    """Loads level 1. A packaging error must fail loudly, not silently."""
    if not BUILTIN_I18N_PATH.is_file():
        raise LabelFileError(
            f"Mitgelieferte Standardtexte nicht gefunden: {BUILTIN_I18N_PATH}. "
            "Vermutlich ein unvollstaendiges Paket - i18n.yaml gehoert zu den "
            "package-data von markpublish."
        )
    table = _read_table_file(BUILTIN_I18N_PATH)
    if FALLBACK_LANGUAGE not in table:
        raise LabelFileError(
            f"{BUILTIN_I18N_PATH}: die Fallback-Sprache '{FALLBACK_LANGUAGE}' fehlt."
        )
    return table


#: Ebene 1 als Dict. Wird beim Import einmal geladen.
LABELS: Dict[str, Dict[str, str]] = _load_builtin()


def available_languages() -> List[str]:
    """Returns the language codes level 1 covers."""
    return sorted(k for k in LABELS if k != ANY_LANGUAGE)


def normalize_language(language: Optional[str]) -> str:
    """
    Maps a document language onto a key of LABELS.

    Accepts regional forms: "de-AT" and "de_DE" both resolve to "de". Anything
    level 1 does not cover falls back to FALLBACK_LANGUAGE.
    """
    if not language:
        return FALLBACK_LANGUAGE

    code = _normalize_language_key(language)
    if code in LABELS and code != ANY_LANGUAGE:
        return code

    base = code.split("-", 1)[0]
    return base if base in LABELS and base != ANY_LANGUAGE else FALLBACK_LANGUAGE


def _language_candidates(language: Optional[str]) -> List[str]:
    """
    Keys to try within one level, least specific first.

    ANY_LANGUAGE applies everywhere and therefore comes first; "de-AT" then
    looks up "de" before "de-at", so a theme can be specific about a regional
    variant without repeating the whole table.
    """
    resolved = normalize_language(language)
    candidates = [ANY_LANGUAGE, resolved]

    if language:
        code = _normalize_language_key(language)
        base = code.split("-", 1)[0]
        for candidate in (base, code):
            if candidate not in candidates:
                candidates.append(candidate)

    return candidates


def _apply_level(
    merged: Dict[str, str],
    table: Mapping[str, Mapping[str, str]],
    candidates: Iterable[str],
) -> None:
    for lang in candidates:
        merged.update(table.get(lang, {}))


def build_labels(
    language: Optional[str] = None,
    template_dirs: Iterable[Path] = (),
    overrides: Optional[Mapping[str, Any]] = None,
) -> Dict[str, str]:
    """
    Resolves the label cascade for one document.

    Args:
        language: document.language, e.g. "de" or "en-GB"
        template_dirs: directories holding an i18n.yaml, outermost first --
            typically [<theme>, <theme>/<target>]
        overrides: document.i18n from the markpublish.yaml, same shape as the
            files

    Returns:
        A complete label set; every key of level 1 is present.
    """
    candidates = _language_candidates(language)

    # Ebene 1: Fallback als Basis, darueber die Dokumentsprache.
    merged = dict(LABELS[FALLBACK_LANGUAGE])
    merged.update(LABELS.get(ANY_LANGUAGE, {}))
    merged.update(LABELS[normalize_language(language)])

    # Ebene 2 und 3
    for directory in template_dirs:
        _apply_level(merged, read_i18n_file(directory), candidates)

    # Ebene 4
    if overrides:
        _apply_level(merged, normalize_table(overrides, "document.i18n"), candidates)

    return merged


def describe_labels(
    language: Optional[str] = None,
    template_dirs: Iterable[Path] = (),
    overrides: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Dict[str, str]]:
    """
    Like build_labels(), but records which level supplied each value.

    Returns {key: {"value", "source", "path"}} where "source" is a short level
    name for display and "path" the file it came from (empty for level 4).
    Backs `markpublish labels`, so the cascade stays debuggable.
    """
    resolved: Dict[str, Dict[str, str]] = {}

    def record(key: str, value: str, source: str, path: str = "") -> None:
        resolved[str(key)] = {"value": str(value), "source": source, "path": path}

    def apply(table: Mapping[str, Mapping[str, str]], label: str, path: str) -> None:
        for lang in candidates:
            for key, value in table.get(lang, {}).items():
                suffix = "" if lang == ANY_LANGUAGE else f" ({lang})"
                record(key, value, f"{label}{suffix}", path)

    candidates = _language_candidates(language)
    builtin = str(BUILTIN_I18N_PATH)

    for key, value in LABELS[FALLBACK_LANGUAGE].items():
        record(key, value, f"i18n.yaml ({FALLBACK_LANGUAGE})", builtin)
    for key, value in LABELS.get(ANY_LANGUAGE, {}).items():
        record(key, value, "i18n.yaml (*)", builtin)
    lang = normalize_language(language)
    for key, value in LABELS[lang].items():
        record(key, value, f"i18n.yaml ({lang})", builtin)

    for directory in template_dirs:
        file_path = Path(directory) / I18N_FILENAME
        # Nur die letzten Komponenten anzeigen - der volle Pfad steht in "path"
        # und wuerde die Tabellenspalte sonst unlesbar machen.
        short = "/".join(file_path.parts[-3:])
        apply(read_i18n_file(directory), short, str(file_path))

    if overrides:
        apply(normalize_table(overrides, "document.i18n"), "document.i18n", "")

    return resolved


def get_labels(
    language: Optional[str] = None,
    overrides: Optional[Mapping[str, Any]] = None,
) -> Dict[str, str]:
    """
    Builds the label set without template-level files.

    Convenience wrapper around build_labels() for callers that have no template
    directory in play, e.g. the Markdown extension that localises callout titles.
    """
    return build_labels(language, template_dirs=(), overrides=overrides)
