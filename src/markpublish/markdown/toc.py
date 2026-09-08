"""
TOC Generation and Autonumbering Engine for markpublish.
"""

from __future__ import annotations

import html
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

from markpublish.markdown.pattern import (
    LEVEL_PART,
    NumSlot,
    Pattern,
    PatternChain,
    int_to_roman,
)

__all__ = [
    "HEADING_REGEX",
    "NumberingContext",
    "PatternChain",
    "TOCNode",
    "int_to_roman",
    "process_html_headings_and_toc",
    "slugify",
]

#: Der Attributteil erlaubt '>' innerhalb von Anfuehrungszeichen -- ein
#: <h2 title="a > b"> wuerde ein simples [^>]* sonst mitten im Attribut kappen.
HEADING_REGEX = re.compile(
    r"""<h([1-6])((?:[^>"']|"[^"]*"|'[^']*')*)>(.*?)</h\1>""",
    re.IGNORECASE | re.DOTALL
)
STRIP_TAGS_REGEX = re.compile(r'<[^>]+>')


#: Umlaute und Eszett werden lautgetreu ersetzt, bevor die NFKD-Normalisierung
#: greift - sonst wird aus "Anhaenge" ein "anhange".
TRANSLITERATIONS = {
    "\u00e4": "ae", "\u00f6": "oe", "\u00fc": "ue",
    "\u00c4": "Ae", "\u00d6": "Oe", "\u00dc": "Ue",
    "\u00df": "ss",
}


def slugify(text: str, separator: str = "-") -> str:
    """Creates a URL-safe, lowercase slug from arbitrary text."""
    for src, dst in TRANSLITERATIONS.items():
        text = text.replace(src, dst)
    # Normalize unicode
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s_]+', separator, text)
    return text.strip(separator) or "section"


class TOCNode:
    """Represents an entry in the Table of Contents."""

    def __init__(
        self,
        title: str,
        slug: str,
        level: int = 1,
        number: Optional[str] = None,
        is_part: bool = False,
        summary: Optional[str] = None,
    ):
        self.title = title
        self.slug = slug
        self.level = level
        self.number = number
        self.is_part = is_part
        self.summary = summary
        self.children: List[TOCNode] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "slug": self.slug,
            "level": self.level,
            "number": self.number,
            "is_part": self.is_part,
            "summary": self.summary,
            "children": [c.to_dict() for c in self.children],
        }


class NumberingContext:
    """
    Fuehrt die Zaehler aller Ebenen durch das Dokument.

    Ein Zaehler je Ebene, nicht je Slot einer Liste: die Ebene ist das, was ein
    Pattern adressiert, und sie ueberlebt den Wechsel des Patterns zwischen
    Dokument, Part und Kapitel.
    """

    def __init__(self) -> None:
        self.counters: Dict[int, int] = {}
        self.used_slugs: set = set()

    def reset_below(self, level: int) -> None:
        """
        Laesst die Ebenen unter *level* wieder bei eins anfangen.

        Das ist `autonum_reset`. Noetig nur dort, wo kein Vorruecken einer
        nummerierten Ebene den Neustart ohnehin besorgt -- unter einer
        uebersprungenen Ebene und unter dem Part, der fuer sich zaehlt.
        """
        for deeper in [lvl for lvl in self.counters if lvl > level]:
            del self.counters[deeper]

    def unique_slug(self, text: str) -> str:
        base_slug = slugify(text)
        slug = base_slug
        count = 1
        while slug in self.used_slugs:
            slug = f"{base_slug}-{count}"
            count += 1
        self.used_slugs.add(slug)
        return slug

    def advance(self, level: int, pattern: Optional[Pattern]) -> Optional[str]:
        """
        Betritt *level* und gibt die fertige Nummer zurueck.

        Eine Ebene ohne Slot -- uebersprungen oder jenseits des letzten Slots --
        erhoeht nichts und verwirft nichts: fuer die Nummerierung existiert sie
        nicht, und die Zaehler darunter laufen ueber sie hinweg durch.
        """
        if pattern is None or not isinstance(pattern.slot_for(level), NumSlot):
            return None

        self.counters[level] = self.counters.get(level, 0) + 1

        # Der Part verwirft nichts: seine Nummer geht in keine Nummer darunter
        # ein, also darf sein Vorruecken die Kapitel auch nicht neu anfangen
        # lassen. Wer das will, notiert autonum_reset.
        if level != LEVEL_PART:
            self.reset_below(level)

        return pattern.render(level, self.counters)


def process_html_headings_and_toc(
    html_content: str,
    numbering_ctx: NumberingContext,
    patterns: Optional[PatternChain] = None,
) -> Tuple[str, List[TOCNode]]:
    """
    Parses HTML content, injects unique IDs/slugs and numbering into headings,
    and returns the modified HTML along with a flat/hierarchical list of TOCNodes.
    """
    toc_nodes: List[TOCNode] = []

    # Explizit gesetzte IDs (attr_list: "## Titel {#einleitung}") vorab
    # reservieren. Wuerden sie erst beim Durchlauf registriert, koennte eine
    # frueher generierte Ueberschrift denselben Slug bereits belegt haben und
    # das Dokument enthielte zwei Elemente mit gleicher id.
    for heading_match in HEADING_REGEX.finditer(html_content):
        existing_id = re.search(r'id=["\']([^"\']+)["\']', heading_match.group(2))
        if existing_id:
            numbering_ctx.used_slugs.add(existing_id.group(1))

    def _replace_heading(match: re.Match) -> str:
        orig_level = int(match.group(1))
        attrs = match.group(2)
        inner_html = match.group(3)

        plain_text = html.unescape(STRIP_TAGS_REGEX.sub('', inner_html).strip())

        # Check existing id in attrs
        id_match = re.search(r'id=["\']([^"\']+)["\']', attrs)
        if id_match:
            slug = id_match.group(1)
            numbering_ctx.used_slugs.add(slug)
        else:
            slug = numbering_ctx.unique_slug(plain_text)
            attrs = f'{attrs} id="{slug}"'.strip()

        # Die Ueberschriftenebene ist zugleich die Nummerierungsebene:
        # orig_level 1 = Kapitel, 2 = h2 und so fort.
        number_str = numbering_ctx.advance(
            orig_level,
            patterns.for_level(orig_level) if patterns else None,
        )

        node = TOCNode(
            title=plain_text,
            slug=slug,
            level=orig_level,
            number=number_str,
        )
        toc_nodes.append(node)

        # Injected heading content
        if number_str:
            new_inner = f'<span class="heading-number">{number_str}</span> {inner_html}'
        else:
            new_inner = inner_html

        attrs = attrs.strip()
        open_tag = f'<h{orig_level} {attrs}>' if attrs else f'<h{orig_level}>'
        return f'{open_tag}{new_inner}</h{orig_level}>'

    modified_html = HEADING_REGEX.sub(_replace_heading, html_content)
    return modified_html, toc_nodes

