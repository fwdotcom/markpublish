"""
Der Vertrag zwischen markpublish und einem Theme.

markpublish erzeugt eine `main.typ`, die `setup-document(...)` und die
Trennseiten-Funktionen mit benannten Argumenten aufruft. Die Funktionen selbst
stehen im Theme. Beide Seiten koennen auseinanderlaufen:

  * markpublish sendet ein Argument, das ein aelteres Theme nicht deklariert
    -> Typst bricht mit `unexpected argument: status` ab. Die Meldung nennt
       weder das Theme noch den Grund; sie liest sich wie ein Fehler in
       markpublish.
  * das Theme liest ein Label, das keine i18n-Ebene aufloest
    -> ohne `default:` bricht Typst mit `dictionary does not contain key` ab,
       mit `default:` bleibt die Stelle im PDF still leer.

Dieses Modul liest beide Seiten aus dem Quelltext und vergleicht sie, bevor
Typst startet.

Zur Schwere: als Fehler gilt nur, was Typst ohnehin abbrechen laesst -- der
Gewinn ist die verstaendliche Meldung, nicht ein neues Verbot. Alles, was heute
durchlaeuft, laeuft weiter durch und wird hoechstens gemeldet. Ein Build, der
gestern ein PDF erzeugt hat, erzeugt auch morgen eins.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from markpublish.i18n import CORE_METADATA_KEYS


class ThemeContractWarning(UserWarning):
    """
    Das Theme passt nicht ganz, der Build laeuft aber durch.

    Eigene Kategorie, damit die CLI sie erkennt und lesbar ausgibt statt sie
    Python mit Dateiname und Zeilennummer der Warnstelle drucken zu lassen --
    die interessiert den Nutzer nicht, die Fundstelle im Theme schon.
    """


#: Die Funktionen, die markpublish im Theme erwartet und selbst aufruft.
CONTRACT_FUNCTIONS = (
    "setup-document",
    "render-part-divider",
    "render-chapter-divider",
)

#: `#let name(` -- Typst-Bezeichner duerfen Bindestriche enthalten.
_LET_RE = re.compile(r"#let\s+([A-Za-z][A-Za-z0-9_-]*)\s*\(")

#: `labels.at("key")` mit optionalem `default:` dahinter.
_LABEL_AT_RE = re.compile(
    r"""labels\s*\.\s*at\s*\(\s*
        (?P<quote>["'])(?P<key>[^"']+)(?P=quote)
        (?P<rest>\s*,\s*default\s*:\s*(?:(?P<quote2>["'])(?P<def>[^"']+)(?P=quote2)|(?P<bare_def>[^),]+)))?""",
    re.VERBOSE,
)

#: `labels.foo` ohne `.at(` -- in Typst ein Feldzugriff, der ohne den
#: Schluessel abbricht. Selten, aber gueltig.
_LABEL_FIELD_RE = re.compile(r"labels\s*\.\s*(?!at\b)(?P<key>[A-Za-z_][A-Za-z0-9_]*)")

#: `meta.at("key")` mit optionalem `default:` dahinter.
_META_AT_RE = re.compile(
    r"""meta\s*\.\s*at\s*\(\s*
        (?P<quote>["'])(?P<key>[^"']+)(?P=quote)
        (?P<rest>\s*,\s*default\s*:\s*(?:(?P<quote2>["'])(?P<def>[^"']+)(?P=quote2)|(?P<bare_def>[^),]+)))?""",
    re.VERBOSE,
)

#: `meta.foo` ohne `.at(`
_META_FIELD_RE = re.compile(r"meta\s*\.\s*(?!at\b)(?P<key>[A-Za-z_][A-Za-z0-9_]*)")

#: `meta.at(schluessel)` -- der Schluessel steht in einer Variablen, nicht als
#: Literal. Welches Feld gemeint ist, laesst sich dann nicht mehr ablesen.
#: Typisch fuer einen eigenen Helfer: `#let hole(meta, key) = meta.at(key)`.
_META_AT_DYNAMIC_RE = re.compile(r"""meta\s*\.\s*at\s*\(\s*(?!["'])""")

#: Was hinter einem `meta`-Zugriff steht: `.value` oder `.label`. Ohne diese
#: Unterscheidung gaelte jeder Zugriff als Bedarf an *beidem*, und ein Theme,
#: das nur den Wert setzt, bekaeme eine Warnung ueber eine Beschriftung, die es
#: gar nicht liest.
_META_FIELD_SUFFIX_RE = re.compile(r"^\s*\)?\s*\.\s*(?P<field>value|label)\b")

_TYPST_DICT_METHODS = frozenset(
    {"len", "values", "keys", "at", "insert", "remove", "filter", "map"}
)


def _read_fields(line: str, after: int) -> Tuple[bool, bool]:
    """
    Sagt, ob ein `meta`-Zugriff die Beschriftung, den Wert oder beides nimmt.

    Steht hinter dem Zugriff kein `.value`/`.label`, nimmt die Stelle den
    ganzen Datensatz -- dann gilt beides.
    """
    match = _META_FIELD_SUFFIX_RE.match(line[after:])
    if not match:
        return True, True
    return match.group("field") == "label", match.group("field") == "value"


def _balanced(text: str, open_idx: int) -> Tuple[str, int]:
    """
    Gibt den Inhalt der bei `open_idx` beginnenden Klammer zurueck.

    Eine Signatur enthaelt selbst Klammern (`labels: (:)`, `authors: ()`,
    `fill: rgb("#fff")`), deshalb reicht ein `[^)]*` nicht -- es endet an der
    ersten inneren Klammer und schneidet die halbe Signatur ab.
    """
    depth = 0
    in_string = False
    i = open_idx
    while i < len(text):
        ch = text[i]
        if in_string:
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[open_idx + 1:i], i
        i += 1
    return text[open_idx + 1:], len(text)


def _split_top_level(params: str) -> List[str]:
    """Trennt an Kommas, die nicht in Klammern oder Zeichenketten stehen."""
    parts: List[str] = []
    depth = 0
    in_string = False
    current: List[str] = []
    i = 0
    while i < len(params):
        ch = params[i]
        if in_string:
            current.append(ch)
            if ch == "\\" and i + 1 < len(params):
                current.append(params[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
            current.append(ch)
        elif ch in "([{":
            depth += 1
            current.append(ch)
        elif ch in ")]}":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
        i += 1
    parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


@dataclass
class LabelReference:
    """Eine Stelle im Theme, die ein Label liest."""
    key: str
    path: Path
    line: int
    has_default: bool
    default_value: Optional[str] = None


@dataclass
class MetaReference:
    """
    Eine Stelle im Theme, die eine Dokumentangabe liest.

    Gleiche Form wie LabelReference und aus demselben Grund: ohne Datei und
    Zeile kann die Abbruchmeldung die Fundstelle nur behaupten. Vorher war das
    eine blosse Schluesselmenge, und die Meldung nannte pauschal `template.typ:1`.
    """
    key: str
    path: Path
    line: int
    has_default: bool
    default_value: Optional[str] = None
    #: Liest die Stelle `.label`? Ohne erkennbares Feld gilt beides als
    #: moeglich -- die Stelle nimmt den ganzen Datensatz.
    reads_label: bool = True
    #: Liest die Stelle `.value`?
    reads_value: bool = True


@dataclass
class ThemeContract:
    """Was ein Theme anbietet: Funktionen samt Parametern und Label-Bedarf."""
    #: Pfad zum Theme-Verzeichnis oder zur Template-Datei
    theme_path: Optional[Path] = None
    #: Funktionsname -> benannte Parameter
    parameters: Dict[str, Set[str]] = field(default_factory=dict)
    #: Funktionsname -> nimmt die Funktion beliebige weitere Argumente (`..rest`)?
    accepts_extra: Dict[str, bool] = field(default_factory=dict)
    label_references: List[LabelReference] = field(default_factory=list)
    #: Zaehlt das Theme das `meta`-Dict auf, statt einzelne Schluessel zu nennen?
    has_meta_iteration: bool = False
    #: Greift das Theme mit einem Schluessel zu, der im Quelltext nicht steht
    #: (`meta.at(key)` in einem eigenen Helfer)? Dann ist nicht ablesbar,
    #: welche Angaben es liest -- "ungenutzt" waere dann eine Behauptung.
    has_dynamic_meta_access: bool = False
    #: Stellen, die einen Schluessel des `meta`-Dicts namentlich lesen.
    meta_references: List[MetaReference] = field(default_factory=list)
    def declares(self, function: str) -> bool:
        return function in self.parameters

    @property
    def meta_keys(self) -> Set[str]:
        """Jeder Schluessel, den das Theme namentlich aus `meta` liest."""
        return {reference.key for reference in self.meta_references}

    @property
    def meta_label_keys(self) -> Set[str]:
        """Schluessel, deren Beschriftung das Theme liest."""
        return {r.key for r in self.meta_references if r.reads_label}

    @property
    def meta_value_keys(self) -> Set[str]:
        """Schluessel, deren Wert das Theme liest."""
        return {r.key for r in self.meta_references if r.reads_value}

    @property
    def meta_defaults(self) -> Dict[str, str]:
        """Schluessel -> im Theme notierter Fallback, wo einer notiert ist."""
        return {
            reference.key: reference.default_value
            for reference in self.meta_references
            if reference.default_value
        }

    def meta_reads_without_default(self, key: str) -> List[MetaReference]:
        """
        Die Fundstellen, an denen `key` ohne Fallback gelesen wird.

        Eine genuegt fuer den Abbruch -- gemeldet werden trotzdem alle, damit
        niemand eine Stelle repariert und ueber die naechste stolpert.
        """
        return [
            reference
            for reference in self.meta_references
            if reference.key == key and not reference.has_default
        ]


@dataclass
class ContractReport:
    """Ergebnis der Pruefung, getrennt nach Schwere."""
    #: Faelle, bei denen Typst ohnehin abbraeche -- hier mit besserer Meldung.
    errors: List[str] = field(default_factory=list)
    #: Faelle, die still falsch werden: der Build laeuft, die Stelle bleibt leer.
    warnings: List[str] = field(default_factory=list)
    #: Labels ohne Fallback, die keine Ebene aufloest -- fuer UndefinedLabelError.
    missing_labels: Dict[str, List[Tuple[Path, int]]] = field(default_factory=dict)
    #: Metadatenschluessel ohne Fallback, die das Dokument nicht kennt.
    #: Getrennt von `missing_labels`, weil die Abhilfe eine andere ist: hier
    #: die markpublish.yaml, dort die i18n.yaml des Themes.
    missing_metadata: Dict[str, List[Tuple[Path, int]]] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return bool(
            self.errors or self.warnings or self.missing_labels or self.missing_metadata
        )

    @property
    def passed(self) -> bool:
        return not self.errors and not self.missing_labels and not self.missing_metadata


def parse_theme_contract(template_path: Path) -> ThemeContract:
    """
    Liest Signaturen und Label-Zugriffe aus den `.typ`-Dateien eines Themes.

    Gescannt wird das Verzeichnis, nicht nur `template.typ`: ein Theme darf
    seine Funktionen auf mehrere Dateien verteilen.
    """
    template_path = Path(template_path)
    theme_dir = template_path if template_path.is_dir() else template_path.parent
    contract = ThemeContract(theme_path=theme_dir)
    files = (
        sorted(template_path.glob("*.typ"))
        if template_path.is_dir()
        else [template_path]
    )

    for path in files:
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            continue

        for match in _LET_RE.finditer(source):
            name = match.group(1)
            params, _ = _balanced(source, match.end() - 1)
            named: Set[str] = set()
            takes_extra = False
            for part in _split_top_level(params):
                if part.startswith(".."):
                    takes_extra = True
                elif ":" in part:
                    named.add(part.split(":", 1)[0].strip())
            contract.parameters[name] = named
            contract.accepts_extra[name] = takes_extra

        # Zaehlt das Theme `meta` auf, statt Schluessel zu nennen?
        if re.search(r"\bmeta\s*\.\s*(?:values|filter|map|len)\b", source) or re.search(r"for\s+[^\n]+in\s+meta\b", source):
            contract.has_meta_iteration = True

        # Greift es mit einem Schluessel zu, der hier nicht steht?
        if _META_AT_DYNAMIC_RE.search(source):
            contract.has_dynamic_meta_access = True

        for number, line in enumerate(source.splitlines(), start=1):
            for match in _LABEL_AT_RE.finditer(line):
                has_def = bool(match.group("rest"))
                def_val = match.group("def") or match.group("bare_def")
                contract.label_references.append(
                    LabelReference(
                        key=match.group("key"),
                        path=path,
                        line=number,
                        has_default=has_def,
                        default_value=def_val.strip().strip("\"'") if def_val else None,
                    )
                )
            for match in _LABEL_FIELD_RE.finditer(line):
                key = match.group("key")
                if key in _TYPST_DICT_METHODS:
                    continue
                contract.label_references.append(
                    LabelReference(
                        key=key,
                        path=path,
                        line=number,
                        has_default=False,
                    )
                )
            for match in _META_AT_RE.finditer(line):
                key = match.group("key")
                if key in _TYPST_DICT_METHODS:
                    continue
                def_val = match.group("def") or match.group("bare_def")
                reads_label, reads_value = _read_fields(line, match.end())
                contract.meta_references.append(
                    MetaReference(
                        key=key,
                        path=path,
                        line=number,
                        has_default=bool(match.group("rest")),
                        default_value=def_val.strip().strip("\"'") if def_val else None,
                        reads_label=reads_label,
                        reads_value=reads_value,
                    )
                )
            for match in _META_FIELD_RE.finditer(line):
                key = match.group("key")
                if key in _TYPST_DICT_METHODS:
                    continue
                reads_label, reads_value = _read_fields(line, match.end())
                contract.meta_references.append(
                    MetaReference(
                        key=key,
                        path=path,
                        line=number,
                        has_default=False,
                        reads_label=reads_label,
                        reads_value=reads_value,
                    )
                )

    return contract


#: Typst-Codeblocks: ```...``` und `...`. Was darin steht, ist Text im
#: fertigen PDF und kein Aufruf.
_RAW_BLOCK_RE = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)


def strip_raw_blocks(source: str) -> str:
    """
    Entfernt Typst-Rohtextblocks, laesst die Zeilenzahl aber unveraendert.

    Ein Dokument darf ueber markpublish schreiben. Das Handbuch tut es: sein
    Theme-Kapitel zeigt eine `setup-document(...)`-Signatur in einem
    Codeblock. Ohne diesen Schritt liest die Vertragspruefung das Beispiel als
    echten Aufruf und meldet Parameter, die niemand sendet.
    """
    return _RAW_BLOCK_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), source)


def parse_sent_arguments(main_typ: str) -> Dict[str, Set[str]]:
    """
    Liest aus der erzeugten `main.typ`, welche Argumente markpublish sendet.

    Ausgewertet wird der tatsaechliche Aufruf statt einer zweiten, gepflegten
    Liste im Code -- eine solche Liste waere genau die Stelle, die beim
    naechsten neuen Parameter vergessen wird.

    Codeblocks bleiben aussen vor: dort steht Inhalt des Dokuments, nicht
    Aufruf an das Theme.
    """
    main_typ = strip_raw_blocks(main_typ)
    sent: Dict[str, Set[str]] = {}
    for function in CONTRACT_FUNCTIONS:
        names: Set[str] = set()
        for match in re.finditer(re.escape(function) + r"\s*\(", main_typ):
            args, _ = _balanced(main_typ, match.end() - 1)
            for part in _split_top_level(args):
                key, sep, _ = part.partition(":")
                if sep and re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", key.strip()):
                    names.add(key.strip())
        if names:
            sent[function] = names
    return sent



def _unknown_parameter_message(
    function: str,
    unknown: List[str],
    declared: Set[str],
) -> str:
    """
    Beschreibt, was beobachtet wurde -- nicht, warum.

    Die Pruefung vergleicht zwei Namensmengen und kennt keine Versionen.
    Ein nicht deklarierter Parameter kann ein veraltetes Theme bedeuten,
    ein von Hand geschriebenes, das die Angabe nie unterstuetzen sollte,
    oder einen Schreibfehler in der Signatur. Eine dieser Ursachen zu
    behaupten waere geraten -- genannt werden deshalb der Befund und die
    Wege, die in jedem der Faelle helfen.

    Ein aehnlich geschriebener Parameter wird erwaehnt, weil auch das ein
    Befund ist und keine Vermutung: der Name steht so in der Signatur.
    """
    listed = ", ".join(f"'{name}'" for name in unknown)
    single = len(unknown) == 1
    lines = [
        f"{'Parameter' if single else 'Die Parameter'} {listed} "
        f"{'ist' if single else 'sind'} in der Signatur von '{function}' "
        f"nicht deklariert; markpublish uebergibt "
        f"{'ihn' if single else 'sie'} beim Rendern."
    ]

    for name in unknown:
        close = difflib.get_close_matches(name, sorted(declared), n=1, cutoff=0.8)
        if close:
            lines.append(
                f"  Das Theme deklariert '{close[0]}' -- moeglicherweise "
                f"ein Schreibfehler."
            )

    def_example = f"{unknown[0]}: (:)" if unknown[0] in ("meta", "labels") else f'{unknown[0]}: ""'
    lines.append(
        f"  Moegliche Wege: {'den Parameter' if single else 'die Parameter'} "
        f"in '{function}' aufnehmen (mit Default, z. B. {def_example}); "
        f"oder '..rest' vor 'body' setzen, wenn das Theme unbekannte "
        f"Angaben bewusst ignorieren soll; oder das mitgelieferte Theme "
        f"neu exportieren und die eigenen Anpassungen uebertragen."
    )
    return "\n".join(lines)

def check_theme_contract(
    contract: ThemeContract,
    sent: Dict[str, Set[str]],
    labels: Optional[Dict[str, str]] = None,
    language: Optional[str] = None,
    meta_keys: Optional[Set[str]] = None,
) -> ContractReport:
    """
    Haelt Theme und Aufruf gegeneinander.

    Args:
        contract: aus dem Theme gelesen
        sent: aus der erzeugten main.typ gelesen
        labels: die aufgeloeste Label-Kaskade fuer die Dokumentsprache
        language: Dokumentsprache, nur fuer die Meldungstexte
        meta_keys: optionale Menge bekannter Metadatenschluessel im Dokument

    Returns:
        ContractReport; `errors` bricht den Build ab, `warnings` nicht.
    """
    report = ContractReport()

    for function, arguments in sorted(sent.items()):
        if not contract.declares(function):
            report.errors.append(
                f"Das Theme definiert '{function}' nicht. "
                f"markpublish ruft die Funktion beim Rendern auf; ohne sie "
                f"kann das Dokument nicht gesetzt werden."
            )
            continue

        if contract.accepts_extra.get(function):
            # `..rest` faengt alles ab - kein Bruch moeglich.
            continue

        unknown = sorted(arguments - contract.parameters[function])
        if unknown:
            report.errors.append(
                _unknown_parameter_message(
                    function, unknown, contract.parameters[function]
                )
            )

    if labels is not None:
        seen: Set[str] = set()
        for reference in contract.label_references:
            if reference.key in labels:
                continue
            if reference.has_default:
                if reference.key in seen:
                    continue
                seen.add(reference.key)
                report.warnings.append(
                    f"Label '{reference.key}' loest in keiner i18n-Ebene auf "
                    f"(Sprache: {language or '?'}).\n"
                    f"  Fundstelle: {reference.path}:{reference.line}\n"
                    f"  Das Theme hat einen Fallback notiert, die Stelle bleibt "
                    f"im PDF also leer statt den Build abzubrechen."
                )
            else:
                report.missing_labels.setdefault(reference.key, []).append(
                    (reference.path, reference.line)
                )

    if meta_keys is not None:
        for reference in contract.meta_references:
            if reference.key in meta_keys or reference.has_default:
                continue
            report.missing_metadata.setdefault(reference.key, []).append(
                (reference.path, reference.line)
            )

    return report


# --------------------------------------------------------------------------
# Uebersicht: welches Label ist definiert, welches wird gelesen
# --------------------------------------------------------------------------

#: Labels, die markpublish selbst aus der Kaskade liest und dem Theme als
#: fertigen Parameter reicht -- sie stehen deshalb in keinem `labels.at(...)`
#: des Templates und waeren bei einem reinen Textscan faelschlich "unbenutzt".
#: Die Alert-Titel entstehen dynamisch (`f"alert_{typ}"`), darum abgeleitet
#: statt abgeschrieben.
ENGINE_LABELS = frozenset(
    {
        "toc_title",
        "chapter",
        "part",
        "chapter_toc_title",
        "part_toc_title",
    }
)

#: Woher ein Label gelesen wird - fuer die Anzeige.
READER_THEME = "Theme"
READER_ENGINE = "markpublish"


def engine_labels() -> Set[str]:
    """
    Die Labels, die markpublish selbst liest.

    Die Alert-Titel kommen aus den Callout-Typen des Serializers, damit ein
    neuer Typ hier nicht nachgetragen werden muss.
    """
    from markpublish.markdown.typst_serializer import TypstSerializer

    alerts = {f"alert_{name}" for name in TypstSerializer.CALLOUT_TYPES}
    return set(ENGINE_LABELS) | alerts


# --------------------------------------------------------------------------
# Diagnose: Theme, i18n-Kaskade und Dokument gegeneinander
# --------------------------------------------------------------------------


class ThemeUsage(str, Enum):
    """Wofuer das Theme einen Schluessel braucht."""
    NONE = "-"
    KEY = "key"
    VALUE = "wert"
    BOTH = "key/wert"


class Severity(str, Enum):
    """Wie schwer ein Befund wiegt."""
    OK = "ok"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class DiagnosisStatus(str, Enum):
    """
    Der Befund einer Zeile -- ein Wert, kein Satz.

    Vorher stand hier fertiges Rich-Markup, und die Bilanz in der CLI musste
    `"[yellow]" in status` fragen, um die Warnungen zu zaehlen. Eine
    Farbaenderung haette damit die Zaehlung verschoben. Der Text gehoert in die
    Anzeige, die Schwere hierher.
    """
    OK = "ok"
    UNUSED = "unused"
    LABEL_MISSING = "label_missing"
    LABEL_FALLBACK = "label_fallback"
    VALUE_MISSING = "value_missing"
    VALUE_FALLBACK = "value_fallback"
    LABEL_AND_VALUE_FALLBACK = "label_and_value_fallback"
    LABEL_FALLBACK_VALUE_MISSING = "label_fallback_value_missing"
    LABEL_BREAKS = "label_breaks"
    META_KEY_UNKNOWN = "meta_key_unknown"
    LABEL_AND_META_BREAK = "label_and_meta_break"

    @property
    def severity(self) -> "Severity":
        if self in _ERROR_STATES:
            return Severity.ERROR
        if self in _WARNING_STATES:
            return Severity.WARNING
        if self in (DiagnosisStatus.UNUSED, DiagnosisStatus.VALUE_MISSING):
            return Severity.INFO
        return Severity.OK


#: Befunde, bei denen Typst abbricht.
_ERROR_STATES = frozenset(
    {
        DiagnosisStatus.LABEL_BREAKS,
        DiagnosisStatus.META_KEY_UNKNOWN,
        DiagnosisStatus.LABEL_AND_META_BREAK,
    }
)

#: Befunde, bei denen der Build laeuft, aber etwas anderes im PDF steht als
#: gedacht.
_WARNING_STATES = frozenset(
    {
        DiagnosisStatus.LABEL_MISSING,
        DiagnosisStatus.LABEL_FALLBACK,
        DiagnosisStatus.VALUE_FALLBACK,
        DiagnosisStatus.LABEL_AND_VALUE_FALLBACK,
        DiagnosisStatus.LABEL_FALLBACK_VALUE_MISSING,
    }
)


@dataclass
class LabelDiagnosisRow:
    """Eine Zeile der Diagnose -- Befund, nicht Darstellung."""
    key: str
    theme_usage: ThemeUsage
    #: Der aufgeloeste i18n-Text, oder None, wenn keine Ebene ihn kennt.
    i18n_label: Optional[str]
    #: Der im Theme notierte `default:` fuer das Label.
    label_fallback: Optional[str]
    #: Der Dokumentwert, oder None.
    value: Optional[str]
    value_fallback: Optional[str]
    status: DiagnosisStatus
    #: Der Fallback-Text, auf den sich der Status bezieht -- fuer die Anzeige.
    status_detail: Optional[str] = None
    #: Hat dieser Schluessel ueberhaupt einen Dokumentwert? Ein Label wie
    #: `page_of` hat keinen; die Spalte bleibt dann leer statt "fehlt".
    applies_value: bool = True
    #: Hat dieser Schluessel eine Beschriftung? `title` wird nur als Wert
    #: gesetzt, nicht beschriftet.
    applies_label: bool = True

    @property
    def breaks_build(self) -> bool:
        return self.status.severity is Severity.ERROR

    @property
    def severity(self) -> Severity:
        return self.status.severity


def diagnose_labels_and_metadata(
    contract: ThemeContract,
    document: Any,
    resolved_labels: Dict[str, Dict[str, str]],
) -> List[LabelDiagnosisRow]:
    """
    Haelt Theme, i18n-Kaskade und Dokument gegeneinander -- eine Zeile je
    Schluessel, den mindestens eine der drei Seiten kennt.

    Liefert Befunde. Wie sie heissen und welche Farbe sie tragen, entscheidet
    die CLI.
    """
    from markpublish.i18n import build_document_metadata

    flat_labels = {k: v.get("value", "") for k, v in resolved_labels.items()}
    meta_entries = build_document_metadata(document, flat_labels) if document else {}

    label_keys = {reference.key for reference in contract.label_references}
    label_defaults = {
        reference.key: reference.default_value
        for reference in contract.label_references
        if reference.default_value
    }
    meta_label_keys = contract.meta_label_keys
    meta_value_keys = contract.meta_value_keys
    meta_keys = contract.meta_keys
    meta_defaults = contract.meta_defaults
    engine = engine_labels()

    all_keys = (
        set(meta_entries)
        | set(resolved_labels)
        | label_keys
        | meta_keys
    )

    rows: List[LabelDiagnosisRow] = []
    for key in sorted(all_keys):
        entry = meta_entries.get(key)
        # Ein Kernfeld ist auch dann bekannt, wenn dieses Dokument es nicht
        # setzt: `meta.at("version")` findet den Schluessel, der Wert ist leer.
        known_metadata = key in meta_entries or key in CORE_METADATA_KEYS

        # Zaehlt das Theme `meta` auf, erreicht es jede Angabe des Rasters --
        # aber keine, die das Titelblatt oben setzt.
        reached_by_iteration = (
            contract.has_meta_iteration and entry is not None and entry.in_grid
        )

        uses_key = (
            key in label_keys
            or key in meta_label_keys
            or key in engine
            or reached_by_iteration
        )
        uses_value = (
            key in meta_value_keys
            or reached_by_iteration
            # Der Zugriff steht im Theme, nur der Schluessel nicht. Lieber
            # nichts behaupten als faelschlich "ungenutzt" melden.
            or (contract.has_dynamic_meta_access and known_metadata)
        )

        if uses_key and uses_value:
            usage = ThemeUsage.BOTH
        elif uses_key:
            usage = ThemeUsage.KEY
        elif uses_value:
            usage = ThemeUsage.VALUE
        else:
            usage = ThemeUsage.NONE

        i18n_label = resolved_labels.get(key, {}).get("value")
        label_fallback = label_defaults.get(key)

        value: Optional[str] = None
        value_fallback: Optional[str] = meta_defaults.get(key)
        if entry is not None and entry.value is not None and entry.value != "":
            value = _format_value(entry.value, flat_labels)
        if entry is not None and entry.is_default and value:
            value_fallback = value

        # Bricht Typst ab, wenn die Seite fehlt? Nur ein Zugriff *ohne*
        # `default:` tut das -- fuer Labels wie fuer Metadaten.
        label_breaks = not i18n_label and any(
            reference.key == key and not reference.has_default
            for reference in contract.label_references
        )
        meta_breaks = not known_metadata and bool(
            contract.meta_reads_without_default(key)
        )

        status, detail = _classify(
            usage=usage,
            i18n_label=i18n_label,
            label_fallback=label_fallback,
            value=value,
            value_fallback=value_fallback,
            known_metadata=known_metadata,
            label_breaks=label_breaks,
            meta_breaks=meta_breaks,
        )

        rows.append(
            LabelDiagnosisRow(
                key=key,
                theme_usage=usage,
                i18n_label=i18n_label,
                label_fallback=label_fallback,
                value=value,
                value_fallback=value_fallback,
                status=status,
                status_detail=detail,
                applies_value=known_metadata and usage is not ThemeUsage.KEY,
                applies_label=usage is not ThemeUsage.VALUE,
            )
        )

    return rows


def _format_value(value: Any, labels: Dict[str, str]) -> str:
    """
    Bringt einen Dokumentwert in die Form, in der ihn das PDF zeigt.

    Insbesondere Wahrheitswerte: seit sie ihren Typ behalten, druckt das Theme
    "Ja"/"Yes" statt "True". Die Diagnose muss dasselbe zeigen -- sonst stuende
    in der Tabelle etwas anderes als auf dem Titelblatt.
    """
    if isinstance(value, bool):
        key = "bool_true" if value else "bool_false"
        return labels.get(key) or ("Ja" if value else "Nein")
    if isinstance(value, (list, tuple)):
        return ", ".join(_format_value(item, labels) for item in value)
    return str(value)


def _classify(
    *,
    usage: ThemeUsage,
    i18n_label: Optional[str],
    label_fallback: Optional[str],
    value: Optional[str],
    value_fallback: Optional[str],
    known_metadata: bool,
    label_breaks: bool,
    meta_breaks: bool,
) -> Tuple[DiagnosisStatus, Optional[str]]:
    """
    Ordnet einer Zeile ihren Befund zu.

    Die harten Faelle zuerst: was Typst abbrechen laesst, ueberdeckt jeden
    weicheren Befund. Danach die beiden Haelften -- Beschriftung und Wert --
    einzeln, statt in einer Kaskade aus Sonderfaellen, in der sich ein toter
    Zweig verstecken kann.
    """
    if label_breaks and meta_breaks:
        return DiagnosisStatus.LABEL_AND_META_BREAK, None
    if label_breaks:
        return DiagnosisStatus.LABEL_BREAKS, None
    if meta_breaks:
        return DiagnosisStatus.META_KEY_UNKNOWN, None

    if usage is ThemeUsage.NONE:
        return DiagnosisStatus.UNUSED, None

    # "In Ordnung" heisst je Haelfte: entweder vorhanden, oder von diesem
    # Schluessel gar nicht verlangt.
    label_ok = bool(i18n_label) or usage is ThemeUsage.VALUE
    value_ok = value is not None or usage is ThemeUsage.KEY or not known_metadata

    if label_ok and value_ok:
        return DiagnosisStatus.OK, None

    if not label_ok and not value_ok:
        if label_fallback and value_fallback:
            return DiagnosisStatus.LABEL_AND_VALUE_FALLBACK, None
        if label_fallback:
            return DiagnosisStatus.LABEL_FALLBACK_VALUE_MISSING, label_fallback
        if value_fallback:
            return DiagnosisStatus.VALUE_FALLBACK, value_fallback
        return DiagnosisStatus.LABEL_MISSING, None

    if not label_ok:
        if label_fallback:
            return DiagnosisStatus.LABEL_FALLBACK, label_fallback
        return DiagnosisStatus.LABEL_MISSING, None

    if value_fallback:
        return DiagnosisStatus.VALUE_FALLBACK, value_fallback
    return DiagnosisStatus.VALUE_MISSING, None
