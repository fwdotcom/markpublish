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
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


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

#: `labels.at("key")` mit optionalem `default:` dahinter. Die Gruppe `rest`
#: faengt nur so viel, wie fuer die Default-Erkennung noetig ist.
_LABEL_AT_RE = re.compile(
    r"""labels\s*\.\s*at\s*\(\s*
        (?P<quote>["'])(?P<key>[^"']+)(?P=quote)
        (?P<rest>\s*,\s*default\s*:)?""",
    re.VERBOSE,
)

#: `labels.foo` ohne `.at(` -- in Typst ein Feldzugriff, der ohne den
#: Schluessel abbricht. Selten, aber gueltig.
_LABEL_FIELD_RE = re.compile(r"labels\s*\.\s*(?!at\b)(?P<key>[A-Za-z_][A-Za-z0-9_]*)")


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


@dataclass
class ThemeContract:
    """Was ein Theme anbietet: Funktionen samt Parametern und Label-Bedarf."""
    #: Funktionsname -> benannte Parameter
    parameters: Dict[str, Set[str]] = field(default_factory=dict)
    #: Funktionsname -> nimmt die Funktion beliebige weitere Argumente (`..rest`)?
    accepts_extra: Dict[str, bool] = field(default_factory=dict)
    label_references: List[LabelReference] = field(default_factory=list)

    def declares(self, function: str) -> bool:
        return function in self.parameters


@dataclass
class ContractReport:
    """Ergebnis der Pruefung, getrennt nach Schwere."""
    #: Faelle, bei denen Typst ohnehin abbraeche -- hier mit besserer Meldung.
    errors: List[str] = field(default_factory=list)
    #: Faelle, die still falsch werden: der Build laeuft, die Stelle bleibt leer.
    warnings: List[str] = field(default_factory=list)
    #: Labels ohne Fallback, die keine Ebene aufloest -- fuer UndefinedLabelError.
    missing_labels: Dict[str, List[Tuple[Path, int]]] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return bool(self.errors or self.warnings or self.missing_labels)


def parse_theme_contract(template_path: Path) -> ThemeContract:
    """
    Liest Signaturen und Label-Zugriffe aus den `.typ`-Dateien eines Themes.

    Gescannt wird das Verzeichnis, nicht nur `template.typ`: ein Theme darf
    seine Funktionen auf mehrere Dateien verteilen.
    """
    contract = ThemeContract()
    template_path = Path(template_path)
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

        for number, line in enumerate(source.splitlines(), start=1):
            for match in _LABEL_AT_RE.finditer(line):
                contract.label_references.append(
                    LabelReference(
                        key=match.group("key"),
                        path=path,
                        line=number,
                        has_default=bool(match.group("rest")),
                    )
                )
            for match in _LABEL_FIELD_RE.finditer(line):
                contract.label_references.append(
                    LabelReference(
                        key=match.group("key"),
                        path=path,
                        line=number,
                        has_default=False,
                    )
                )

    return contract


def parse_sent_arguments(main_typ: str) -> Dict[str, Set[str]]:
    """
    Liest aus der erzeugten `main.typ`, welche Argumente markpublish sendet.

    Ausgewertet wird der tatsaechliche Aufruf statt einer zweiten, gepflegten
    Liste im Code -- eine solche Liste waere genau die Stelle, die beim
    naechsten neuen Parameter vergessen wird.
    """
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

    lines.append(
        f"  Moegliche Wege: {'den Parameter' if single else 'die Parameter'} "
        f"in '{function}' aufnehmen (mit Default, z. B. {unknown[0]}: \"\"); "
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
) -> ContractReport:
    """
    Haelt Theme und Aufruf gegeneinander.

    Args:
        contract: aus dem Theme gelesen
        sent: aus der erzeugten main.typ gelesen
        labels: die aufgeloeste Label-Kaskade fuer die Dokumentsprache
        language: Dokumentsprache, nur fuer die Meldungstexte

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

    if labels is None:
        return report

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


@dataclass
class LabelUsage:
    """Eine Zeile der Uebersicht."""
    key: str
    defined: bool
    readers: Set[str] = field(default_factory=set)
    #: Nur fuer Theme-Zugriffe: haengt ein `default:` dran?
    has_fallback: bool = True

    @property
    def used(self) -> bool:
        return bool(self.readers)

    @property
    def breaks_build(self) -> bool:
        """Ein gelesenes Label ohne Definition und ohne Fallback bricht ab."""
        return self.used and not self.defined and not self.has_fallback


def label_overview(
    contract: ThemeContract,
    defined_keys: Set[str],
) -> List[LabelUsage]:
    """
    Fuehrt Kaskade und Verwendung zusammen.

    Vier Faelle, und alle vier sind interessant:
      definiert + gelesen    -> in Ordnung
      definiert + ungelesen  -> Leerlauf; eine Uebersetzung, die niemand liest
      gelesen + undefiniert  -> Luecke; leer im PDF oder Abbruch
      weder noch             -> kommt nicht vor
    """
    rows: Dict[str, LabelUsage] = {
        key: LabelUsage(key=key, defined=True) for key in defined_keys
    }

    for key in engine_labels():
        rows.setdefault(key, LabelUsage(key=key, defined=False))
        rows[key].readers.add(READER_ENGINE)

    for reference in contract.label_references:
        row = rows.setdefault(
            reference.key, LabelUsage(key=reference.key, defined=False)
        )
        row.readers.add(READER_THEME)
        if not reference.has_default:
            # Eine Fundstelle ohne Fallback genuegt fuer den Abbruch.
            row.has_fallback = False

    return [rows[key] for key in sorted(rows)]
