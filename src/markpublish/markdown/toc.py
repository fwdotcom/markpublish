"""
TOC Generation and Autonumbering Engine for markpublish.
"""

from __future__ import annotations

import html
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple, Union
from markpublish.config.models import AutonumType


HEADING_REGEX = re.compile(
    r'<h([1-6])([^>]*)>(.*?)</h\1>',
    re.IGNORECASE | re.DOTALL
)
STRIP_TAGS_REGEX = re.compile(r'<[^>]+>')


def slugify(text: str) -> str:
    """Creates a URL-safe, lowercase slug from arbitrary text."""
    # Normalize unicode
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s]+', '-', text)
    return text or "section"


def int_to_roman(num: int) -> str:
    """Converts positive integer to Roman numeral."""
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syb = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    roman_num = ""
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syb[i]
            num -= val[i]
        i += 1
    return roman_num or "I"


def format_number(counters: List[int], autonum_type: AutonumType) -> Optional[str]:
    """Formats list of counter levels according to autonum_type."""
    if autonum_type == AutonumType.NONE or not counters:
        return None

    if autonum_type == AutonumType.ROMAN:
        first = int_to_roman(counters[0])
        if len(counters) == 1:
            return first
        return f"{first}." + ".".join(str(c) for c in counters[1:])

    if autonum_type == AutonumType.LEGAL:
        return ".".join(str(c) for c in counters) + "."

    # Default DECIMAL (1, 1.1, 1.1.1)
    return ".".join(str(c) for c in counters)


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
    """Maintains state for hierarchical heading numbering across documents."""

    def __init__(self, default_autonum_type: AutonumType = AutonumType.DECIMAL):
        self.default_autonum_type = default_autonum_type
        self.counters: List[int] = []
        self.used_slugs: set = set()

    def unique_slug(self, text: str) -> str:
        base_slug = slugify(text)
        slug = base_slug
        count = 1
        while slug in self.used_slugs:
            slug = f"{base_slug}-{count}"
            count += 1
        self.used_slugs.add(slug)
        return slug

    def advance_counter(self, level: int, autonum_type: Optional[AutonumType] = None) -> Optional[str]:
        type_to_use = autonum_type or self.default_autonum_type
        if type_to_use == AutonumType.NONE:
            return None

        # Adjust counter list length to match heading level (1-indexed)
        while len(self.counters) < level:
            self.counters.append(0)
        while len(self.counters) > level:
            self.counters.pop()

        self.counters[level - 1] += 1
        return format_number(self.counters, type_to_use)


def process_html_headings_and_toc(
    html_content: str,
    numbering_ctx: NumberingContext,
    autonum_override: Optional[AutonumType] = None,
    base_level_offset: int = 0,
) -> Tuple[str, List[TOCNode]]:
    """
    Parses HTML content, injects unique IDs/slugs and numbering into headings,
    and returns the modified HTML along with a flat/hierarchical list of TOCNodes.
    """
    toc_nodes: List[TOCNode] = []

    def _replace_heading(match: re.Match) -> str:
        orig_level = int(match.group(1))
        attrs = match.group(2)
        inner_html = match.group(3)

        effective_level = orig_level + base_level_offset
        plain_text = html.unescape(STRIP_TAGS_REGEX.sub('', inner_html).strip())

        # Check existing id in attrs
        id_match = re.search(r'id=["\']([^"\']+)["\']', attrs)
        if id_match:
            slug = id_match.group(1)
            numbering_ctx.used_slugs.add(slug)
        else:
            slug = numbering_ctx.unique_slug(plain_text)
            attrs = f'{attrs} id="{slug}"'.strip()

        number_str = numbering_ctx.advance_counter(effective_level, autonum_override)

        node = TOCNode(
            title=plain_text,
            slug=slug,
            level=effective_level,
            number=number_str,
        )
        toc_nodes.append(node)

        # Injected heading content
        if number_str:
            new_inner = f'<span class="heading-number">{number_str}</span> {inner_html}'
        else:
            new_inner = inner_html

        return f'<h{orig_level} {attrs}>{new_inner}</h{orig_level}>'

    modified_html = HEADING_REGEX.sub(_replace_heading, html_content)
    return modified_html, toc_nodes

