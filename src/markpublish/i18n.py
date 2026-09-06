"""
Aufloesung der statischen Texte (Labels) fuer Templates und Stylesheets.

Ein Schluessel pro Text, aufgeloest ueber eine Kaskade aus vier Ebenen. Jede
tiefere Ebene ueberschreibt die daruber liegende -- und zwar nur die
Schluessel, die sie tatsaechlich setzt:

    1. Programm      markpublish/i18n.yaml
    2. Theme         <templates>/<theme>/i18n.yaml
    3. Zielformat    <templates>/<theme>/<target>/i18n.yaml
    4. Projekt       i18n.yaml neben der markpublish.yaml

Die Ebenen 2 und 3 stammen immer aus genau einem Theme: welches Template gilt,
entscheidet vorher die Aufloesung (User > Projekt > Paket). Gemischt wird nur
dieses eine Theme mit dem Programmstandard -- ein Projekt-Theme erbt nicht die
Texte des gleichnamigen Paket-Themes.

Ebene 4 gehoert dem Dokument. Sie ist da, weil `document:` beliebige eigene
Felder aufnimmt (`abteilung: "F&E"`) und deren Beschriftung sonst nirgends
stuende -- das Deckblatt druckte den rohen Schluessel. Sie darf auch Texte des
Themes ersetzen: wer eine einzelne Ueberschrift fuer ein Dokument anders haben
will, soll dafuer kein Theme forken muessen.

Alle Ebenen sind identisch aufgebaut: Sprachcode auf oberster Ebene,
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
bis 4 greifen nur fuer die gewaehlte Sprache, damit die englischen Texte eines
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

import difflib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

import yaml

from markpublish.syslang import detect_system_language
from markpublish.ui import t

#: Sprache, auf die zurueckgefallen wird, wenn `document.language` unbekannt
#: ist. Sie muss jeden Schluessel enthalten - build_labels() legt sie als Basis
#: unter jede andere Sprache, damit auch eine unvollstaendige Uebersetzung
#: niemals einen leeren Text erzeugt.
FALLBACK_LANGUAGE = "en"

#: Dateiname jeder Ebene der Kaskade.
I18N_FILENAME = "i18n.yaml"

#: Sprachcode, der auf jede Sprache angewendet wird.
ANY_LANGUAGE = "*"

#: Ebene 1, mitgeliefert im Paket.
BUILTIN_I18N_PATH = Path(__file__).resolve().parent / I18N_FILENAME

#: Kurznamen der Ebenen -- fuer die Anzeige in `markpublish labels`. Kurz, weil
#: die Spalte in jeder Zeile steht; der volle Pfad steht darunter im Fuss.
LEVEL_BUILTIN = "mpub"
LEVEL_THEME = "theme"
LEVEL_TARGET = "target"
LEVEL_PROJECT = "projekt"


class LabelFileError(ValueError):
    """Raised when an i18n.yaml exists but cannot be used."""


class UndefinedLabelError(ValueError):
    """
    Raised when a template uses a label that no level of the cascade defines.

    Aborting is the point: the alternative is an empty string in the finished
    PDF, which nobody notices until a reader does.
    """


class UndefinedMetadataError(ValueError):
    """
    Raised when a theme reads a metadata key the document does not define.

    Separate from UndefinedLabelError because the remedy differs: a label is
    added to a theme's i18n.yaml, a metadata key under `document:` in the
    markpublish.yaml. One shared message would send half the readers the
    wrong way.
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
            t("err.i18n.expects_languages", source=source, found=type(raw).__name__)
        )

    values = list(raw.values())
    if values and all(isinstance(v, str) for v in values):
        # Flache Form ohne Sprachebene - gilt fuer jede Sprache.
        return {ANY_LANGUAGE: {str(k): str(v) for k, v in raw.items()}}

    table: Dict[str, Dict[str, str]] = {}
    for lang, entries in raw.items():
        if not isinstance(entries, Mapping):
            raise LabelFileError(
                t("err.i18n.expects_mapping", source=source, language=lang)
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
        raise LabelFileError(t("err.i18n.invalid_yaml", path=path, error=err)) from err
    except OSError as err:
        raise LabelFileError(t("err.i18n.unreadable", path=path, error=err)) from err
    return normalize_table(raw, str(path))


def _load_builtin() -> Dict[str, Dict[str, str]]:
    """Loads level 1. A packaging error must fail loudly, not silently."""
    if not BUILTIN_I18N_PATH.is_file():
        raise LabelFileError(
            t("err.i18n.builtin_missing", path=BUILTIN_I18N_PATH)
        )
    table = _read_table_file(BUILTIN_I18N_PATH)
    if FALLBACK_LANGUAGE not in table:
        raise LabelFileError(
            t("err.i18n.fallback_missing", path=BUILTIN_I18N_PATH, language=FALLBACK_LANGUAGE)
        )
    return table


#: Ebene 1 als Dict. Wird beim Import einmal geladen.
LABELS: Dict[str, Dict[str, str]] = _load_builtin()


def available_languages() -> List[str]:
    """Returns the language codes level 1 covers."""
    return sorted(k for k in LABELS if k != ANY_LANGUAGE)


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

    # Ebene 2 bis 4
    for directory in template_dirs:
        _apply_level(merged, read_i18n_file(directory), candidates)

    return LabelMap(merged, language=language, template_dirs=template_dirs)


def describe_labels(
    language: Optional[str] = None,
    template_dirs: Iterable[Path] = (),
    level_names: Optional[Iterable[str]] = None,
) -> Dict[str, Dict[str, str]]:
    """
    Like build_labels(), but records which level supplied each value.

    Returns {key: {"value", "source", "language", "path"}}: "source" names the
    level for display, "language" the block within it ("de", "*", or the
    fallback language), "path" the file it came from. Backs
    `markpublish labels`, so the cascade stays debuggable.

    Args:
        level_names: Kurznamen fuer `template_dirs`, in derselben Reihenfolge
            -- typischerweise LEVEL_THEME, LEVEL_TARGET, LEVEL_PROJECT. Ohne
            Angabe steht der abgekuerzte Pfad da; ein Aufrufer, der die Ebenen
            kennt, sollte sie benennen.

    Datei und Sprachblock stehen getrennt, nicht als ein Anzeigetext
    ("i18n.yaml (de)"): welche Sprache gilt, steht in der Ausgabe ohnehin
    schon im Kopf. Interessant ist der Block nur, wo er davon abweicht -- ein
    Text aus der Fallback-Sprache oder aus "*". Diese Entscheidung gehoert in
    die Anzeige, nicht in eine hier zusammengesetzte Zeichenkette.
    """
    resolved: Dict[str, Dict[str, str]] = {}

    def record(key: str, value: str, source: str, lang: str, path: str = "") -> None:
        resolved[str(key)] = {
            "value": str(value),
            "source": source,
            "language": lang,
            "path": path,
        }

    def apply(table: Mapping[str, Mapping[str, str]], label: str, path: str) -> None:
        for lang in candidates:
            for key, value in table.get(lang, {}).items():
                record(key, value, label, lang, path)

    candidates = _language_candidates(language)
    builtin = str(BUILTIN_I18N_PATH)

    for key, value in LABELS[FALLBACK_LANGUAGE].items():
        record(key, value, LEVEL_BUILTIN, FALLBACK_LANGUAGE, builtin)
    for key, value in LABELS.get(ANY_LANGUAGE, {}).items():
        record(key, value, LEVEL_BUILTIN, ANY_LANGUAGE, builtin)
    lang = normalize_language(language)
    for key, value in LABELS[lang].items():
        record(key, value, LEVEL_BUILTIN, lang, builtin)

    names = list(level_names) if level_names is not None else []
    for index, directory in enumerate(template_dirs):
        file_path = Path(directory) / I18N_FILENAME
        # Ohne Ebenennamen die letzten Pfadkomponenten - der volle Pfad steht
        # in "path" und wuerde die Tabellenspalte sonst unlesbar machen.
        label = names[index] if index < len(names) else "/".join(file_path.parts[-3:])
        apply(read_i18n_file(directory), label, str(file_path))

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

#: Dateien, in denen nach Label-Verwendungen gesucht wird.
TEMPLATE_FILE_GLOBS = ("*.html", "*.css", "*.typ")

#: Attributnamen, die zu jedem dict gehoeren (inkl. Typst .at()).
_MAPPING_ATTRIBUTES = frozenset(
    {"at", "get", "items", "keys", "values", "copy", "pop", "setdefault", "update", "clear"}
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
        t("err.label.undefined", key=key),
        "  " + t("err.label.document_language", language=labels.language or FALLBACK_LANGUAGE),
    ]

    found = list(occurrences)
    if found:
        lines.append("  " + t("err.label.occurrence"))
        lines.extend(f"    {path}:{line}" for path, line in found)

    lines.append("  " + t("err.label.searched"))
    for path in labels.searched_files():
        state = t("err.label.state_present") if path.is_file() else t("err.label.state_absent")
        lines.append(f"    {path}  ({state})")

    lines.append(
        "  "
        + t(
            "err.label.remedy",
            language=labels.language or FALLBACK_LANGUAGE,
            any=ANY_LANGUAGE,
        )
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


#: Die Metadaten, die jedes Dokument kennt -- unabhaengig davon, ob sie gesetzt
#: sind. Sie stehen immer im `meta`-Dict, damit ein Theme `meta.at("version")`
#: schreiben darf, ohne zu wissen, ob dieses Dokument eine Version fuehrt.
CORE_METADATA_KEYS = (
    "title",
    "subtitle",
    "summary",
    "author",
    "status",
    "version",
    "date",
    "copyright",
)


@dataclass
class MetadataEntry:
    """Eine Dokumentangabe samt aufgeloester Beschriftung."""
    key: str
    label: Optional[str]
    value: Any
    #: Wurde der Wert von markpublish erzeugt statt im Dokument notiert?
    #: Heute nur `date: "auto"`.
    is_default: bool = False


def build_document_metadata(
    document: Any,
    labels: Mapping[str, str],
) -> Dict[str, MetadataEntry]:
    """
    Builds a unified metadata mapping for a document, resolving each key's
    localized i18n label.
    """
    entries: Dict[str, MetadataEntry] = {}

    for key in CORE_METADATA_KEYS:
        val = getattr(document, key, None)
        is_default = False
        if key == "date" and str(val).lower() in ("auto", "today"):
            is_default = True
            from markpublish.config.loader import format_current_date

            val = format_current_date(getattr(document, "language", None))

        entries[key] = MetadataEntry(
            key=key,
            label=labels.get(key),
            value=val,
            is_default=is_default,
        )

    # Freie Felder aus `extra: allow` -- alles unter `document:`, was kein
    # deklariertes Feld ist. Sie erreichen das Theme auf demselben Weg wie die
    # Kernangaben; einen Sonderfall gibt es unterhalb dieser Funktion nicht.
    extra_fields = getattr(document, "model_extra", None) or {}
    for key, val in extra_fields.items():
        entries[key] = MetadataEntry(
            key=key,
            label=labels.get(key),
            value=val,
            is_default=False,
        )

    return entries


def undefined_metadata_message(
    key: str,
    occurrences: Iterable[Tuple[Path, int]] = (),
    known_keys: Iterable[str] = (),
) -> str:
    """
    Baut die Abbruchmeldung fuer einen Metadatenschluessel, den das Theme
    liest und das Dokument nicht kennt.

    Bewusst nicht `undefined_label_message`: ein fehlendes Label wird in einer
    i18n.yaml des Themes ergaenzt, ein fehlender Metadatenschluessel unter
    `document:` in der markpublish.yaml. Dieselbe Meldung fuer beides zu
    verwenden hiesse, in der Haelfte der Faelle den falschen Weg zu weisen.
    """
    lines = [
        t("err.meta.undefined", key=key),
    ]

    found = list(occurrences)
    if found:
        lines.append("  " + t("err.meta.occurrence"))
        lines.extend(f"    {path}:{line}" for path, line in found)

    candidates = sorted(k for k in known_keys if k)
    if candidates:
        close = difflib.get_close_matches(key, candidates, n=1, cutoff=0.8)
        if close:
            lines.append(
                "  " + t("err.meta.typo", candidate=close[0])
            )
        lines.append("  " + t("err.meta.known", keys=", ".join(candidates)))

    lines.append(
        "  " + t("err.meta.remedy", key=key)
    )
    return "\n".join(lines)
