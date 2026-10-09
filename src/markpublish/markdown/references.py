"""
Verweise auf Ueberschriften: `[](#id)` wird "Teil II, Kapitel 5, Abschnitt 5.3 „Titel“".

Ausgegeben werden die Ebenen ab der ersten, in der sich Verweisstelle und Ziel
unterscheiden -- im selben Kapitel genuegt "Abschnitt 5.3 „Titel“". Erst wenn
alle Kapitel nummeriert sind, steht jede Nummer fest; deshalb laeuft das als
eigener Schritt ueber das ganze Dokument.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple

from markpublish.config.models import ConfigurationError
from markpublish.ui import t

HEADING_RE = re.compile(r"^h([1-6])$")


@dataclass(frozen=True)
class Level:
    """Eine Gliederungsebene im Pfad eines Ziels: Teil, Kapitel oder Abschnitt."""

    kind: str
    slug: str
    word: str
    number: Optional[str]
    title: str


def heading_title(elem: Any) -> str:
    """Text der Ueberschrift ohne die vorangestellte Nummer."""
    pieces = [elem.text or ""]
    for child in elem:
        if child.attrib.get("class") != "heading-number":
            pieces.append("".join(child.itertext()))
        pieces.append(child.tail or "")
    return "".join(pieces).strip()


def _is_empty_anchor(elem: Any) -> bool:
    href = elem.attrib.get("href", "")
    return href.startswith("#") and len(href) > 1 and not (elem.text or "").strip() and not len(elem)


class References:
    """Sammelt die Ziele aller Kapitel und setzt danach die Verweise."""

    def __init__(self, labels: Mapping[str, str]) -> None:
        self.labels = labels
        self.targets: Dict[str, List[Level]] = {}
        self.ids: Set[str] = set()
        self.figures: Set[str] = set()
        #: (Baum, Pfad bis zum Kapitel, Datei) je Kapitel, in Dokumentreihenfolge
        self.chapters: List[Tuple[Any, List[Level], str]] = []

    def word(self, label: Optional[str], key: str) -> str:
        """Ein notiertes Wort gilt, auch leer; sonst das aus der i18n-Kaskade."""
        return label if label is not None else self.labels.get(key, "")

    def add_target(self, chain: List[Level]) -> None:
        self.targets.setdefault(chain[-1].slug, chain)

    def add_chapter(self, tree: Any, base: List[Level], where: str) -> None:
        """Registriert Ueberschriften, Abbildungen und sonstige ids eines Kapitels."""
        self.chapters.append((tree, base, where))
        if base:
            self.add_target(base)
        for elem, chain in self._walk(tree, base):
            if HEADING_RE.match(elem.tag.lower()) and chain:
                self.add_target(chain)
            elem_id = elem.attrib.get("id")
            if elem_id:
                self.ids.add(elem_id)
                if elem.tag == "figure" and elem.find("figcaption") is not None:
                    self.figures.add(elem_id)

    def _walk(self, tree: Any, base: List[Level]):
        """Jedes Element mit dem Pfad, in dem es steht."""
        chapter = base[-1] if base and base[-1].kind == "chapter" else None
        prefix = base[:-1] if chapter else base
        stack: List[Tuple[int, Level]] = [(1, chapter)] if chapter else []
        for elem in tree.iter():
            match = HEADING_RE.match(elem.tag.lower())
            if match:
                level = int(match.group(1))
                while stack and stack[-1][0] >= level:
                    stack.pop()
                slug = elem.attrib.get("id", "")
                if level == 1 and chapter and slug == chapter.slug:
                    current = chapter
                else:
                    chapter_word = chapter.word if chapter else self.word(None, "chapter")
                    current = Level(
                        kind="chapter" if level == 1 else "section",
                        slug=slug,
                        word=chapter_word if level == 1 else self.word(None, "section"),
                        number=elem.attrib.get("data-number") or None,
                        title=heading_title(elem),
                    )
                stack.append((level, current))
            yield elem, prefix + [lvl for _, lvl in stack]

    def resolve(self) -> Set[int]:
        """Setzt den Text leerer Verweise; liefert die `id()` der geaenderten Baeume."""
        changed: Set[int] = set()
        for tree, base, where in self.chapters:
            for elem, here in self._walk(tree, base):
                if elem.tag != "a" or not _is_empty_anchor(elem):
                    continue
                target_id = elem.attrib["href"][1:]
                if target_id in self.figures:
                    continue  # Abbildung oder Tabelle: Nummer und Wort setzt Typst
                chain = self.targets.get(target_id)
                if chain is None:
                    if target_id in self.ids:
                        continue
                    raise ConfigurationError(t("err.reference.unknown", id=target_id, file=where))
                elem.text = self.phrase(chain, here)
                changed.add(id(tree))
        return changed

    def phrase(self, target: List[Level], here: List[Level]) -> str:
        """Der Verweistext: die Ebenen ab der ersten, die sich unterscheidet."""
        same = 0
        while same < min(len(target), len(here)) and target[same].slug == here[same].slug:
            same += 1
        shown = target[min(same, len(target) - 1):]
        # Ab Ebene 2 heisst jede Ebene "Abschnitt"; nur die tiefste zaehlt.
        shown = [lvl for lvl in shown[:-1] if lvl.kind != "section"] + shown[-1:]
        return ", ".join(
            self._name(lvl, is_target=lvl is shown[-1]) for lvl in shown
        )

    def _name(self, level: Level, is_target: bool) -> str:
        quote_open = self.labels.get("quote_open", '"')
        quote_close = self.labels.get("quote_close", '"')
        quoted = f"{quote_open}{level.title}{quote_close}" if level.title else ""
        if level.number:
            head = f"{level.word} {level.number}".strip()
            return f"{head} {quoted}".strip() if is_target else head
        if is_target:
            return quoted or level.word
        return f"{level.word} {quoted}".strip()
