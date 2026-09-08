"""
Auswertung von `autonum_pattern`: Grammatik, Pruefung und Nummernaufbau.

Ein Pattern beschreibt die Ebenen *unterhalb* der Stelle, an der es notiert
ist. Slot 1 gehoert deshalb zur ersten Ebene darunter -- unter `document:` ist
das der Part, an einem Part das Kapitel, an einem Kapitel `h2`. Die Umrechnung
von Slotnummer auf Ebene passiert einmal hier beim Kompilieren und nicht bei
jeder Ueberschrift.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

from markpublish.ui import t


class PatternError(ValueError):
    """Ein Pattern, das sich nicht auswerten laesst. Bricht den Build ab."""
    pass


#: Nummerierbare Ebenen: 0 = Part, 1 = Kapitel (die `h1` seiner Datei), 2..6 = h2..h6.
LEVEL_PART = 0
LEVEL_CHAPTER = 1
MAX_LEVEL = 6

#: Basisebene je Notationsort -- die erste Ebene, die ein dort notiertes
#: Pattern beschreibt.
BASE_LEVEL: Dict[str, int] = {
    "document": LEVEL_PART,
    "part": LEVEL_CHAPTER,
    "chapter": LEVEL_CHAPTER + 1,
}

#: Alles ausserhalb dieser Menge ist unmittelbar Literal und braucht keine
#: Anfuehrungszeichen.
RESERVED = set("01aAiI_+|'")
LETTER_SYMBOLS = set("aAiI")


def int_to_roman(num: int) -> str:
    """Positive Ganzzahl als roemische Zahl; 0 und Negatives ergeben 'I'."""
    values = (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1)
    signs = ("M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I")
    roman = ""
    for value, sign in zip(values, signs, strict=True):
        while num >= value:
            roman += sign
            num -= value
    return roman or "I"


def int_to_alpha(num: int) -> str:
    """1 -> a, 26 -> z, 27 -> aa. Wie Tabellenspalten, ohne Null."""
    if num < 1:
        return "a"
    letters = ""
    while num > 0:
        num, rest = divmod(num - 1, 26)
        letters = chr(ord("a") + rest) + letters
    return letters


@dataclass(frozen=True)
class NumSlot:
    """Eine nummerierte Ebene: Literale, Zaehler, Literale."""

    prefix: str
    symbol: str
    suffix: str

    def render(self, value: int) -> str:
        if self.symbol == "a":
            body = int_to_alpha(value)
        elif self.symbol == "A":
            body = int_to_alpha(value).upper()
        elif self.symbol == "i":
            body = int_to_roman(value).lower()
        elif self.symbol == "I":
            body = int_to_roman(value)
        else:
            # "1", "01", "001" -- die Laenge des Symbols ist die Stellenzahl.
            body = str(value).zfill(len(self.symbol))
        return f"{self.prefix}{body}{self.suffix}"


@dataclass(frozen=True)
class SkipSlot:
    """Eine Ebene ohne Nummer. Gibt nichts aus und haelt keinen Zaehler."""
    pass


Slot = Union[NumSlot, SkipSlot]

#: Platzhalter waehrend des Parsens; nach der Expansion kommt er nicht mehr vor.
_CONT = "+"


@dataclass(frozen=True)
class Pattern:
    """Ein kompiliertes Pattern, aufgeloest auf eine Ebene je Slot."""

    source: str
    base_level: int
    slots: Tuple[Slot, ...]

    @property
    def last_level(self) -> int:
        return self.base_level + len(self.slots) - 1

    def slot_for(self, level: int) -> Optional[Slot]:
        index = level - self.base_level
        if 0 <= index < len(self.slots):
            return self.slots[index]
        return None

    def numbers(self, level: int) -> bool:
        """True, wenn diese Ebene einen eigenen Zaehler fuehrt."""
        return isinstance(self.slot_for(level), NumSlot)

    def render(self, level: int, counters: Dict[int, int]) -> Optional[str]:
        """
        Baut die Nummer aus den Slots der Ebenen bis *level*.

        Der Part bleibt dabei aussen vor, sobald es um etwas unter ihm geht:
        seine Nummer ist eine Aufschrift auf der Trennseite, keine Koordinate,
        die in Kapitelnummern eingeht.
        """
        if not self.numbers(level):
            return None

        pieces: List[str] = []
        for current in range(self.base_level, level + 1):
            if current == LEVEL_PART and level != LEVEL_PART:
                continue
            slot = self.slots[current - self.base_level]
            if isinstance(slot, NumSlot):
                pieces.append(slot.render(counters.get(current, 0)))
        return "".join(pieces) or None


# ---------------------------------------------------------------------------
# Parsen
# ---------------------------------------------------------------------------

def _split_slots(source: str) -> List[List[Tuple[str, str]]]:
    """
    Zerlegt das Pattern an den `|`, ohne die in Anfuehrungszeichen zu treffen.

    Jedes Zeichen kommt als ('lit', c) -- woertlich gemeint -- oder als
    ('raw', c) heraus; erst der zweite Durchgang entscheidet, ob ein rohes
    Zeichen Symbol oder Literal ist.
    """
    slots: List[List[Tuple[str, str]]] = []
    current: List[Tuple[str, str]] = []
    in_quote = False
    index = 0

    while index < len(source):
        char = source[index]
        if char == "'":
            if in_quote and index + 1 < len(source) and source[index + 1] == "'":
                current.append(("lit", "'"))
                index += 2
                continue
            in_quote = not in_quote
            index += 1
            continue
        if in_quote:
            current.append(("lit", char))
            index += 1
            continue
        if char == "|":
            slots.append(current)
            current = []
            index += 1
            continue
        current.append(("raw", char))
        index += 1

    if in_quote:
        raise PatternError(
            t("err.pattern.unbalanced_quote", pattern=source, slot=len(slots) + 1)
        )

    slots.append(current)
    return slots


def _parse_slot(tokens: List[Tuple[str, str]], source: str, number: int) -> Union[Slot, str]:
    """Macht aus den Zeichen eines Slots einen NumSlot, SkipSlot oder `+`."""
    if not tokens:
        raise PatternError(t("err.pattern.empty_slot", pattern=source, slot=number))

    if len(tokens) == 1 and tokens[0] == ("raw", "_"):
        return SkipSlot()
    if len(tokens) == 1 and tokens[0] == ("raw", "+"):
        return _CONT

    prefix: List[str] = []
    suffix: List[str] = []
    symbol = ""
    index = 0

    while index < len(tokens):
        kind, char = tokens[index]
        if kind == "lit" or char not in RESERVED:
            (suffix if symbol else prefix).append(char)
            index += 1
            continue

        if char in ("_", "+", "|"):
            raise PatternError(
                t("err.pattern.unknown_char", pattern=source, slot=number, char=char)
            )

        if symbol:
            raise PatternError(
                t("err.pattern.two_symbols", pattern=source, slot=number)
            )

        if char in LETTER_SYMBOLS:
            symbol = char
            index += 1
            continue

        # Dezimal: beliebig viele Nullen, dann genau eine Eins.
        run = ""
        while index < len(tokens) and tokens[index][0] == "raw" and tokens[index][1] in "01":
            run += tokens[index][1]
            index += 1
        if run.strip("0") != "1" or not run.endswith("1"):
            raise PatternError(
                t("err.pattern.bad_decimal", pattern=source, slot=number, run=run)
            )
        symbol = run

    if not symbol:
        raise PatternError(t("err.pattern.no_symbol", pattern=source, slot=number))

    return NumSlot(prefix="".join(prefix), symbol=symbol, suffix="".join(suffix))


#: Welche Ebene Slot 1 je Notationsort meint. Haengt an jeder Fehlermeldung,
#: denn bei einem verschobenen Slot ist genau das die offene Frage.
_SCOPE_HINT = {
    "document": "err.pattern.scope.document",
    "part": "err.pattern.scope.part",
    "chapter": "err.pattern.scope.chapter",
}


def compile_pattern(source: Optional[str], scope: str) -> Optional[Pattern]:
    """
    Uebersetzt ein Pattern in Slots je Ebene. `None` heisst: keine Nummern.

    Ein fehlerhaftes Pattern bricht ab. Ein stiller Rueckfall auf einen
    Standardwert waere hier teuer: ein Tippfehler nummerierte sonst unbemerkt
    das ganze Dokument falsch.
    """
    if source is None:
        return None
    text = str(source).strip()
    if not text or text.lower() == "none":
        return None

    try:
        return _compile(text, scope)
    except PatternError as error:
        raise PatternError(f"{error}\n{t(_SCOPE_HINT[scope])}") from None


def _compile(text: str, scope: str) -> Pattern:
    base = BASE_LEVEL[scope]
    raw_slots = _split_slots(text)
    parsed = [_parse_slot(tokens, text, i + 1) for i, tokens in enumerate(raw_slots)]

    limit = MAX_LEVEL - base + 1
    if len(parsed) > limit:
        raise PatternError(
            t("err.pattern.too_deep", pattern=text, slots=len(parsed), max=limit)
        )

    for position, slot in enumerate(parsed):
        if slot is not _CONT:
            continue
        if position == 0:
            raise PatternError(t("err.pattern.cont_first", pattern=text))
        if position != len(parsed) - 1:
            raise PatternError(
                t("err.pattern.cont_not_last", pattern=text, slot=position + 1)
            )
        if isinstance(parsed[position - 1], SkipSlot):
            raise PatternError(
                t("err.pattern.cont_after_skip", pattern=text, slot=position + 1)
            )
        if base == LEVEL_PART and position == 1:
            raise PatternError(t("err.pattern.cont_after_part", pattern=text))

    if isinstance(parsed[-1], SkipSlot):
        raise PatternError(
            t("err.pattern.skip_last", pattern=text, slot=len(parsed))
        )

    # `+` aufloesen: der Slot davor wiederholt sich bis zur letzten Ebene.
    if parsed and parsed[-1] is _CONT:
        repeated = parsed[-2]
        parsed = parsed[:-1]
        while base + len(parsed) - 1 < MAX_LEVEL:
            parsed.append(repeated)

    return Pattern(source=text, base_level=base, slots=tuple(parsed))


#: Unterscheidet "an dieser Stelle steht nichts" von "hier steht `none`".
#: In YAML sind beide leer, fuer die Kaskade sind sie das Gegenteil: das eine
#: erbt weiter, das andere schaltet ab.
UNSET = object()


class PatternChain:
    """
    Welches Pattern eine Ebene beschreibt -- die innerste Stelle gewinnt.

    Eine Stelle, die nichts notiert, wird uebersprungen. Eine, die `none`
    notiert, schaltet die Ebenen ab, die sie beschreibt; fuer alles darueber
    gilt weiter die Stelle davor. Ein Kapitel kann seine eigene Nummer damit
    nicht abschalten, und das ist richtig so: sie gehoert seinem Part.
    """

    def __init__(self, document=UNSET, part=UNSET, chapter=UNSET):
        self._places = (
            (chapter, BASE_LEVEL["chapter"]),
            (part, BASE_LEVEL["part"]),
            (document, BASE_LEVEL["document"]),
        )

    def for_level(self, level: int) -> Optional[Pattern]:
        for value, base in self._places:
            if value is UNSET or level < base:
                continue
            return value
        return None
