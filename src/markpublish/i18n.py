"""
Aufloesung der statischen Texte (Labels) fuer Templates und Stylesheets.

Ein Schluessel pro Text, aufgeloest ueber eine Kaskade aus drei Ebenen. Jede
tiefere Ebene ueberschreibt die daruber liegende -- und zwar nur die
Schluessel, die sie tatsaechlich setzt:

    1. Programm      markpublish/i18n.yaml
    2. Theme         <templates>/<theme>/i18n.yaml
    3. Zielformat    <templates>/<theme>/<target>/i18n.yaml

Die Ebenen 2 und 3 stammen immer aus genau einem Theme: welches Template gilt,
entscheidet vorher die Aufloesung (User > Projekt > Paket). Gemischt wird nur
dieses eine Theme mit dem Programmstandard -- ein Projekt-Theme erbt nicht die
Texte des gleichnamigen Paket-Themes.

Alle drei Ebenen sind identisch aufgebaut: Sprachcode auf oberster Ebene,
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
die Dokumentsprache, damit jeder Programmtext garantiert aufloest. Die Ebenen 2
und 3 greifen nur fuer die gewaehlte Sprache, damit die englischen Texte eines
Themes nicht in eine deutsche Ausgabe durchschlagen.

Ein Theme darf eigene Schluessel definieren, die das Programm nicht kennt --
"freie" Labels fuer die statischen Texte des Templates selbst. Fuer sie gibt es
keinen Programmstandard, der einspringen koennte: notiert das Template
{{ labels.foo }} und loest 'foo' in keiner Ebene auf, bricht der Build ab
(UndefinedLabelError). Das ist Absicht -- ein leerer Text im fertigen PDF faellt
niemandem auf, ein Abbruch mit Fundstelle schon.

Templates greifen auf das Ergebnis ueber `labels` zu (`{{ labels.toc_title }}`),
das Stylesheet ebenso -- `styles.css` laeuft durch dieselbe Jinja-Umgebung.
"""

from __future__ import annotations

import locale
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

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


class UndefinedLabelError(ValueError):
    """
    Raised when a template uses a label that no level of the cascade defines.

    Aborting is the point: the alternative is an empty string in the finished
    PDF, which nobody notices until a reader does.
    """


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


#: Umgebungsvariablen, in denen POSIX die Sprachwahl fuehrt, spezifisch zuerst.
#: LANGUAGE darf eine Prioritaetsliste sein ("de:en"); genommen wird der erste
#: Eintrag.
_LOCALE_ENV_VARS = ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")

#: Werte, die "keine Sprache gewaehlt" bedeuten und keine sind.
_NEUTRAL_LOCALES = frozenset({"c", "posix", "c.utf-8", "und"})


def _clean_locale(value: str) -> Optional[str]:
    """
    Schaelt aus 'de_DE.UTF-8@euro' den Sprachcode 'de-DE'.

    Geschrieben wird die uebliche Form -- Sprache klein, Region gross. Fuer die
    Aufloesung ist das gleichgueltig, jede Suche normalisiert selbst; hier geht
    es darum, dass der Wert in einer markpublish.yaml landen kann, ohne dass
    jemand ueber ein 'de-de' stolpert.
    """
    code = value.split(":", 1)[0].split(".", 1)[0].split("@", 1)[0].strip()
    if not code or code.lower() in _NEUTRAL_LOCALES:
        return None

    language, _, region = _normalize_language_key(code).partition("-")
    return f"{language}-{region.upper()}" if region else language


def detect_system_language() -> Optional[str]:
    """
    Sprache der Benutzeroberflaeche des Systems, oder None.

    Reihenfolge: erst die POSIX-Umgebungsvariablen -- sie sind die einzige
    Stelle, an der ein Benutzer die Sprache pro Aufruf oder pro Shell
    uebersteuern kann, und wer sie setzt, meint sie auch. Danach fragt Windows
    seine UI-Sprache ueber die API ab; `locale.getlocale()` liefert dort
    'German_Germany' statt eines ISO-Codes und waere unbrauchbar. Auf allen
    anderen Systemen bleibt getlocale() als Rueckfallebene.

    Zurueckgegeben wird ein roher Code wie "de", "de-AT" oder "pt-BR" -- ob es
    ihn ueberhaupt gibt, entscheidet der Aufrufer: normalize_language() fuer die
    Labels, das Vorhandensein eines Verzeichnisses fuer die mitgelieferten
    Dokumente. Erkennung, die nichts findet, gibt None zurueck statt zu raten.
    """
    for var in _LOCALE_ENV_VARS:
        value = os.environ.get(var)
        if value and (code := _clean_locale(value)):
            return code

    if sys.platform == "win32":
        try:
            import ctypes

            lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            windows_code = locale.windows_locale.get(lcid)
        except Exception:
            windows_code = None
        return _clean_locale(windows_code) if windows_code else None

    try:
        code = locale.getlocale()[0]
    except (TypeError, ValueError):
        return None
    return _clean_locale(code) if code else None


def default_document_language() -> str:
    """
    Sprache eines Dokuments, das selbst keine angibt.

    Die Systemsprache ist hier die bessere Vermutung als ein festverdrahteter
    Code: wer nichts angibt, schreibt mit ueberwaeltigender Wahrscheinlichkeit
    in der Sprache, in der sein Rechner mit ihm spricht. Verbindlich ist sie
    nicht -- `markpublish init` schreibt den erkannten Wert in die
    markpublish.yaml, damit ein Dokument auf jedem Rechner gleich baut.
    """
    return detect_system_language() or FALLBACK_LANGUAGE


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
) -> "LabelMap":
    """
    Resolves the label cascade for one document.

    Args:
        language: document.language, e.g. "de" or "en-GB"
        template_dirs: directories holding an i18n.yaml, outermost first --
            typically [<theme>, <theme>/<target>] of the ONE resolved theme

    Returns:
        A LabelMap holding every key of level 1 plus whatever free labels the
        theme adds. Reading a key it does not know raises UndefinedLabelError
        instead of yielding an empty string.
    """
    candidates = _language_candidates(language)

    # Ebene 1: Fallback als Basis, darueber die Dokumentsprache.
    merged = dict(LABELS[FALLBACK_LANGUAGE])
    merged.update(LABELS.get(ANY_LANGUAGE, {}))
    merged.update(LABELS[normalize_language(language)])

    # Ebene 2 und 3
    for directory in template_dirs:
        _apply_level(merged, read_i18n_file(directory), candidates)

    return LabelMap(merged, language=language, template_dirs=template_dirs)


def describe_labels(
    language: Optional[str] = None,
    template_dirs: Iterable[Path] = (),
) -> Dict[str, Dict[str, str]]:
    """
    Like build_labels(), but records which level supplied each value.

    Returns {key: {"value", "source", "path"}} where "source" is a short level
    name for display and "path" the file it came from. Backs
    `markpublish labels`, so the cascade stays debuggable.
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

    return resolved


def get_labels(language: Optional[str] = None) -> "LabelMap":
    """
    Builds the label set from level 1 alone, without any theme files.

    Convenience wrapper around build_labels() for callers that have no resolved
    theme in play - the Markdown pipeline gets the full cascade handed to it and
    does not use this.
    """
    return build_labels(language, template_dirs=())


# --------------------------------------------------------------------------
# Freie Labels: Verwendung im Template gegen die Kaskade pruefen
# --------------------------------------------------------------------------

#: Dateien, in denen nach Label-Verwendungen gesucht wird. styles.css laeuft
#: durch dieselbe Jinja-Umgebung wie die Templates und darf Labels benutzen.
TEMPLATE_FILE_GLOBS = ("*.html", "*.css")

#: Attributnamen, die zu jedem dict gehoeren. `labels.items` ist der Aufruf
#: einer Mapping-Methode, kein Label - ohne diese Liste meldete die Pruefung
#: sie als fehlend.
_MAPPING_ATTRIBUTES = frozenset(
    {"get", "items", "keys", "values", "copy", "pop", "setdefault", "update", "clear"}
)

#: {{ labels.foo }} und {{ labels["foo"] }} - beide Schreibweisen zaehlen.
_LABEL_REFERENCE_RE = re.compile(
    r"""\blabels\s*(?:
            \.\s*(?P<attr>[A-Za-z_][A-Za-z0-9_]*)
          | \[\s*(?P<quote>['"])(?P<item>[^'"]+)(?P=quote)\s*\]
        )""",
    re.VERBOSE,
)


class LabelMap(Dict[str, str]):
    """
    The resolved label set, strict about keys it does not know.

    A plain dict would hand Jinja an Undefined for `labels.foo`, and Jinja
    renders that as an empty string - the missing text would ship. Here the
    lookup raises instead, naming the key, the language and where it was
    searched.
    """

    def __init__(
        self,
        values: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
        template_dirs: Iterable[Path] = (),
    ):
        super().__init__(values or {})
        self.language = language
        self.template_dirs: List[Path] = [Path(d) for d in template_dirs]

    def searched_files(self) -> List[Path]:
        """The i18n.yaml files that fed this map, most specific first."""
        files = [Path(d) / I18N_FILENAME for d in reversed(self.template_dirs)]
        files.append(BUILTIN_I18N_PATH)
        return files

    def __missing__(self, key: str) -> str:
        raise UndefinedLabelError(undefined_label_message(key, self))

    def copy(self) -> "LabelMap":
        return LabelMap(dict(self), language=self.language, template_dirs=self.template_dirs)


def undefined_label_message(
    key: str,
    labels: "LabelMap",
    occurrences: Iterable[Tuple[Path, int]] = (),
) -> str:
    """Builds the abort message for one undefined label."""
    lines = [
        f"Label '{key}' ist im Template notiert, aber in keiner i18n-Ebene definiert.",
        f"  Dokumentsprache: {labels.language or FALLBACK_LANGUAGE}",
    ]

    found = list(occurrences)
    if found:
        lines.append("  Fundstelle:")
        lines.extend(f"    {path}:{line}" for path, line in found)

    lines.append("  Gesucht in:")
    for path in labels.searched_files():
        state = "vorhanden" if path.is_file() else "nicht vorhanden"
        lines.append(f"    {path}  ({state})")

    lines.append(
        f"  Abhilfe: den Schluessel unter '{labels.language or FALLBACK_LANGUAGE}:' "
        f"(oder unter '{ANY_LANGUAGE}:' fuer jede Sprache) in einer der oben "
        "genannten Theme-Dateien ergaenzen."
    )
    return "\n".join(lines)


def find_label_references(directory: Path) -> Dict[str, List[Tuple[Path, int]]]:
    """
    Collects every label a template directory refers to, with file and line.

    Scans the sources rather than waiting for the render, so a label inside a
    branch that happens not to run this time is reported too.
    """
    references: Dict[str, List[Tuple[Path, int]]] = {}
    directory = Path(directory)
    if not directory.is_dir():
        return references

    for pattern in TEMPLATE_FILE_GLOBS:
        for path in sorted(directory.glob(pattern)):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for number, line in enumerate(text.splitlines(), start=1):
                for match in _LABEL_REFERENCE_RE.finditer(line):
                    key = match.group("attr") or match.group("item")
                    if match.group("attr") and key in _MAPPING_ATTRIBUTES:
                        continue
                    references.setdefault(key, []).append((path, number))
    return references


def validate_label_references(labels: "LabelMap", directory: Path) -> None:
    """
    Checks a template directory against the resolved labels.

    Raises UndefinedLabelError listing every unresolved label with its
    occurrences. Called before rendering starts: a build that cannot produce
    correct text should not produce a file at all.
    """
    references = find_label_references(directory)
    missing = {key: places for key, places in references.items() if key not in labels}
    if not missing:
        return

    blocks = [
        undefined_label_message(key, labels, places)
        for key, places in sorted(missing.items())
    ]
    raise UndefinedLabelError("\n\n".join(blocks))

