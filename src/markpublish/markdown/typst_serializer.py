"""
ElementTree to Typst Serializer for markpublish.

Converts the parsed and enhanced xml.etree.ElementTree from python-markdown
into clean, well-formed Typst markup.
"""

from __future__ import annotations

import re
import shutil
import xml.etree.ElementTree as etree
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from markpublish.config.models import AutonumStyle
from markpublish.markdown.toc import NumberingContext, TOCNode


def typst_string(value: Any) -> str:
    """
    Safely escapes a value for embedding in Typst string literals (double quotes).
    Backslashes and double quotes are escaped.
    """
    if value is None:
        return ""
    text = str(value)
    return text.replace("\\", "\\\\").replace('"', '\\"')


def typst_value(value: Any) -> str:
    """
    Renders a Python value as the Typst literal of the *same* type.

    `str()` on everything would ship Python spellings into the PDF: a YAML
    `reviewed: true` printed as "True" -- English, capitalised, and a
    programming-language token in the middle of a typeset page. A theme cannot
    repair that, because by then the type is gone. So the type survives the
    trip and the theme decides how to word it.
    """
    if value is None:
        return "none"
    if isinstance(value, bool):
        # Before int: bool is a subclass of int in Python.
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        # Typst has no NaN/inf literal; those fall back to text.
        if value == value and value not in (float("inf"), float("-inf")):
            return repr(value)
        return f'"{typst_string(value)}"'
    if isinstance(value, (list, tuple)):
        items = [typst_value(item) for item in value]
        if len(items) == 1:
            # A one-element Typst array needs the trailing comma, or the
            # parentheses read as grouping.
            return f"({items[0]},)"
        return "(" + ", ".join(items) + ")"
    return f'"{typst_string(value)}"'


def escape_typst_text(text: str) -> str:
    """
    Escapes plain text so that Typst does not interpret special markup characters.
    Characters escaped: \\, [, ], #, $, @, <, >, *, _, `, ~
    """
    if not text:
        return ""
    # Backslash first
    text = text.replace("\\", "\\\\")
    # Content block brackets
    text = text.replace("[", "\\[").replace("]", "\\]")
    # Typst directives and markup
    text = text.replace("#", "\\#")
    text = text.replace("$", "\\$")
    text = text.replace("@", "\\@")
    text = text.replace("<", "\\<").replace(">", "\\>")
    text = text.replace("*", "\\*")
    text = text.replace("_", "\\_")
    text = text.replace("`", "\\`")
    text = text.replace("~", "\\~")
    return text


class HTMLToTreeParser(HTMLParser):
    """
    Parses standard or extended HTML produced by python-markdown into an xml.etree.ElementTree.
    Handles unclosed void tags, entities, and preserved whitespace in <pre> tags.
    """

    VOID_TAGS = {"img", "br", "hr", "input", "meta", "link"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = etree.Element("div")
        self.stack: List[etree.Element] = [self.root]

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attr_dict = {k: v or "" for k, v in attrs}
        elem = etree.SubElement(self.stack[-1], tag, attr_dict)
        if tag.lower() not in self.VOID_TAGS:
            self.stack.append(elem)

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower not in self.VOID_TAGS:
            for i in range(len(self.stack) - 1, 0, -1):
                if self.stack[i].tag.lower() == tag_lower:
                    self.stack = self.stack[:i]
                    break

    def handle_data(self, data: str) -> None:
        if not self.stack:
            return
        current = self.stack[-1]
        if len(current) == 0:
            current.text = (current.text or "") + data
        else:
            last_child = current[-1]
            last_child.tail = (last_child.tail or "") + data


def html_to_tree(html_content: str) -> etree.Element:
    """Parses HTML markup into an ElementTree root element."""
    parser = HTMLToTreeParser()
    parser.feed(html_content)
    return parser.root


class TypstSerializer:
    """
    Traverses a python-markdown ElementTree and produces Typst markup.
    """

    CALLOUT_TYPES = {
        "note": "note",
        "tip": "tip",
        "important": "important",
        "warning": "warning",
        "caution": "caution",
    }

    def __init__(
        self,
        base_level_offset: int = 0,
        file_base_dir: Optional[Path] = None,
        images_dir: Optional[Path] = None,
        labels: Optional[Dict[str, str]] = None,
        allowed_toc_slugs: Optional[Set[str]] = None,
    ):
        self.base_level_offset = base_level_offset
        self.file_base_dir = file_base_dir
        self.images_dir = images_dir
        self.labels = labels or {}
        self.allowed_toc_slugs = allowed_toc_slugs
        self.copied_images: Dict[str, str] = {}
        self.footnotes: Dict[str, str] = {}  # footnote_id -> typst_text

    def serialize(self, root: etree.Element) -> str:
        """Serializes the root element into a Typst string."""
        # 1. First pass: collect footnote definitions if present (<div class="footnote">)
        self._extract_footnotes(root)

        # 2. Serialize all block-level children of root
        blocks: List[str] = []
        for child in root:
            # Skip the trailing footnote container as footnotes are inlined as #footnote[...]
            classes = child.attrib.get("class", "").split()
            if child.tag == "div" and "footnote" in classes:
                continue

            block_res = self._visit_block(child)
            if block_res.strip():
                blocks.append(block_res.strip())

        return "\n\n".join(blocks)

    def _extract_footnotes(self, root: etree.Element) -> None:
        """Extracts footnote bodies from <div class="footnote"> so they can be inlined."""
        for div in root.findall(".//div"):
            if "footnote" in div.attrib.get("class", "").split():
                for li in div.findall(".//li"):
                    fn_id = li.attrib.get("id", "")
                    if fn_id:
                        # Serialize the content of the footnote li, stripping the backlink
                        fn_text = self._serialize_footnote_body(li)
                        self.footnotes[fn_id] = fn_text

    def _serialize_footnote_body(self, li: etree.Element) -> str:
        """Serializes footnote content excluding the backreference link."""
        parts: List[str] = []
        for elem in li:
            if elem.tag == "p":
                # Filter out the backref link: <a href="#fnref:..." class="footnote-backref">
                p_parts: List[str] = []
                if elem.text:
                    p_parts.append(escape_typst_text(elem.text))
                for child in elem:
                    if child.tag == "a" and "footnote-backref" in child.attrib.get("class", "").split():
                        # skip backlink
                        if child.tail:
                            p_parts.append(escape_typst_text(child.tail))
                        continue
                    p_parts.append(self._visit_inline(child))
                    if child.tail:
                        p_parts.append(escape_typst_text(child.tail))
                parts.append("".join(p_parts).strip())
            else:
                parts.append(self._visit_block(elem).strip())
        return " ".join(parts).strip()

    def _visit_block(self, elem: etree.Element, list_depth: int = 0) -> str:
        """Visits a block-level element."""
        tag = elem.tag.lower()
        classes = elem.attrib.get("class", "").split()

        # Headings h1..h6
        heading_match = re.match(r"^h([1-6])$", tag)
        if heading_match:
            orig_level = int(heading_match.group(1))
            effective_level = max(1, min(6, orig_level + self.base_level_offset))
            slug = elem.attrib.get("id", "")
            number_prefix = elem.attrib.get("data-number", "")

            # Falls in einem Baum noch ein alter heading-number span existiert:
            for child in elem:
                if child.attrib.get("class") == "heading-number" and not number_prefix:
                    number_prefix = "".join(child.itertext()).strip()

            content = self._visit_heading_content(elem)
            label_str = f" <{slug}>" if slug else ""

            outlined_param = ""
            if self.allowed_toc_slugs is not None and slug not in self.allowed_toc_slugs:
                outlined_param = ", outlined: false"

            if number_prefix:
                num_esc = typst_string(number_prefix)
                return f'#heading(level: {effective_level}, numbering: (..nums) => "{num_esc}"{outlined_param})[{content}]{label_str}\n'
            else:
                return f"#heading(level: {effective_level}, numbering: none{outlined_param})[{content}]{label_str}\n"

        # Paragraph
        if tag == "p":
            content = self._visit_children_inline(elem)
            return f"{content}\n"

        # Blockquote or Admonition / Callout
        if tag == "blockquote":
            content = self._visit_container_blocks(elem)
            return f"#quote[\n{content}\n]\n"

        if tag == "div":
            # Check for arithmatex display math: <div class="arithmatex">\[...\]</div>
            if "arithmatex" in classes:
                math_text = "".join(elem.itertext()).strip()
                if math_text.startswith(r"\[") and math_text.endswith(r"\]"):
                    math_text = math_text[2:-2].strip()
                elif math_text.startswith("$$") and math_text.endswith("$$"):
                    math_text = math_text[2:-2].strip()
                norm_math = self._normalize_math(math_text)
                return f"$ {norm_math} $\n"

            # Check for admonitions (e.g. class="admonition note")
            if "admonition" in classes:
                callout_type = "note"
                for c in classes:
                    if c in self.CALLOUT_TYPES:
                        callout_type = c
                        break

                # Check if first child is title
                title = ""
                body_elements = list(elem)
                if body_elements and body_elements[0].tag == "p" and "admonition-title" in body_elements[0].attrib.get("class", "").split():
                    title_elem = body_elements.pop(0)
                    title = self._visit_children_inline(title_elem).strip()

                if not title:
                    label_key = f"alert_{callout_type}"
                    title = escape_typst_text(self.labels.get(label_key, callout_type.capitalize()))

                body_parts: List[str] = []
                for b in body_elements:
                    body_parts.append(self._visit_block(b))
                body_content = "\n\n".join(p.strip() for p in body_parts if p.strip())

                return f'#callout(type: "{callout_type}", title: [{title}])[\n{body_content}\n]\n'

            # General div: serialize its block children
            return self._visit_container_blocks(elem)

        # Code block: <pre><code>...</code></pre>
        if tag == "pre":
            code_elem = elem.find("code")
            target = code_elem if code_elem is not None else elem
            code_text = "".join(target.itertext())
            lang = ""
            if code_elem is not None:
                for c in code_elem.attrib.get("class", "").split():
                    if c.startswith("language-"):
                        lang = c[len("language-"):]
                        break

            # Calculate safe fence length (longer than any sequence of backticks in code)
            backticks_match = re.findall(r"`+", code_text)
            max_backticks = max((len(m) for m in backticks_match), default=0)
            fence = "`" * max(3, max_backticks + 1)

            clean_code = code_text.rstrip("\n")
            return f"{fence}{lang}\n{clean_code}\n{fence}\n"

        # Lists: ul / ol
        if tag in ("ul", "ol"):
            return self._visit_list(elem, is_ordered=(tag == "ol"), depth=list_depth)

        # Tables: table
        if tag == "table":
            return self._visit_table(elem)

        # Horizontal Rule
        if tag == "hr":
            return '#line(length: 100%, stroke: 0.5pt + rgb("#cbd5e1"))\n'

        # Definition list: dl, dt, dd
        if tag == "dl":
            return self._visit_def_list(elem)

        # Fallback: treat as container
        return self._visit_container_blocks(elem)

    def _visit_container_blocks(self, elem: etree.Element) -> str:
        """Renders children of a container block."""
        parts: List[str] = []
        for child in elem:
            parts.append(self._visit_block(child).strip())
        return "\n\n".join(p for p in parts if p)

    def _visit_list(self, elem: etree.Element, is_ordered: bool, depth: int = 0) -> str:
        """Renders an unordered or ordered list, including nested lists and tasklists."""
        items: List[str] = []
        indent = "  " * depth
        marker = "+" if is_ordered else "-"

        for child in elem:
            if child.tag.lower() != "li":
                continue

            # Check if this is a tasklist item
            is_task = "task-list-item" in child.attrib.get("class", "").split()
            checked = False
            task_checkbox = child.find(".//input[@type='checkbox']")
            if task_checkbox is not None:
                checked = "checked" in task_checkbox.attrib or task_checkbox.attrib.get("checked") == "checked"

            # Separate text/inline content from nested sub-lists
            inline_parts: List[str] = []
            sub_lists: List[str] = []

            # First handle child.text if not task checkbox
            if child.text:
                inline_parts.append(escape_typst_text(child.text))

            for sub in child:
                if sub.tag.lower() in ("ul", "ol"):
                    sub_lists.append(self._visit_list(sub, is_ordered=(sub.tag.lower() == "ol"), depth=depth + 1))
                elif sub.tag.lower() == "input" and sub.attrib.get("type") == "checkbox":
                    # skip input tag itself
                    if sub.tail:
                        inline_parts.append(escape_typst_text(sub.tail))
                elif sub.tag.lower() == "p":
                    # <p> inside <li>
                    inline_parts.append(self._visit_children_inline(sub))
                    if sub.tail:
                        inline_parts.append(escape_typst_text(sub.tail))
                else:
                    inline_parts.append(self._visit_inline(sub))
                    if sub.tail:
                        inline_parts.append(escape_typst_text(sub.tail))

            li_text = "".join(inline_parts).strip()

            if is_task:
                chk_str = "true" if checked else "false"
                item_line = f"{indent}#task-item(checked: {chk_str})[{li_text}]"
            else:
                item_line = f"{indent}{marker} {li_text}"

            if sub_lists:
                item_line += "\n" + "\n".join(sub_lists)

            items.append(item_line)

        return "\n".join(items)

    def _visit_table(self, table_elem: etree.Element) -> str:
        """Renders an HTML table into a clean Typst #table(...) block."""
        rows: List[List[Tuple[str, bool, str]]] = []  # (content_typst, is_header, align_str)

        all_trs = table_elem.findall(".//tr")
        for tr in all_trs:
            row: List[Tuple[str, bool, str]] = []
            for cell in tr:
                if cell.tag.lower() in ("th", "td"):
                    is_th = cell.tag.lower() == "th"
                    cell_align = cell.attrib.get("align", "").lower()
                    if not cell_align:
                        style = cell.attrib.get("style", "")
                        if "text-align: right" in style:
                            cell_align = "right"
                        elif "text-align: center" in style:
                            cell_align = "center"
                        elif "text-align: left" in style:
                            cell_align = "left"

                    content = self._visit_children_inline(cell).strip()
                    content = content.replace(r"\\|", "|")
                    row.append((content, is_th, cell_align or "left"))
            if row:
                rows.append(row)

        if not rows:
            return ""

        max_cols = max(len(r) for r in rows)

        # Build column alignment array
        align_spec: List[str] = []
        for col_idx in range(max_cols):
            col_align = "left"
            for r in rows:
                if col_idx < len(r) and r[col_idx][2] in ("left", "center", "right"):
                    col_align = r[col_idx][2]
                    break
            align_spec.append(col_align)

        align_typst = f"({', '.join(align_spec)})"

        cells_typst: List[str] = []
        has_header = any(cell[1] for cell in rows[0])

        start_row_idx = 0
        if has_header:
            header_row = rows[0]
            padded_header = list(header_row)
            while len(padded_header) < max_cols:
                padded_header.append(("", False, "left"))
            header_cells = [f"[#text(weight: \"bold\")[{content}]]" for content, _, _ in padded_header]
            cells_typst.append("  table.header(\n    " + ",\n    ".join(header_cells) + ",\n  )")
            start_row_idx = 1

        for r in rows[start_row_idx:]:
            padded_row = list(r)
            while len(padded_row) < max_cols:
                padded_row.append(("", False, "left"))

            for content, is_th, _ in padded_row:
                if is_th:
                    cells_typst.append(f"  [#text(weight: \"bold\")[{content}]]")
                else:
                    cells_typst.append(f"  [{content}]")

        cells_str = ",\n".join(cells_typst)
        return (
            f"#table(\n"
            f"  columns: {max_cols},\n"
            f"  align: {align_typst},\n"
            f"{cells_str},\n"
            f")\n"
        )

    def _visit_def_list(self, dl_elem: etree.Element) -> str:
        """Renders HTML definition lists <dl><dt>...</dt><dd>...</dd></dl>."""
        items: List[str] = []
        current_dt = ""
        for child in dl_elem:
            if child.tag.lower() == "dt":
                current_dt = self._visit_children_inline(child).strip()
            elif child.tag.lower() == "dd":
                dd_content = self._visit_children_inline(child).strip()
                items.append(f"/ {current_dt}: {dd_content}")
                current_dt = ""
        return "\n".join(items) + "\n"

    def _visit_children_inline(self, elem: etree.Element) -> str:
        """Collects and serializes all inline text and child elements."""
        parts: List[str] = []
        if elem.text:
            parts.append(escape_typst_text(elem.text))
        for child in elem:
            parts.append(self._visit_inline(child))
            if child.tail:
                parts.append(escape_typst_text(child.tail))
        return "".join(parts)

    def _visit_heading_content(self, elem: etree.Element) -> str:
        """Serializes inline content of a heading, skipping any legacy heading-number span."""
        parts: List[str] = []
        if elem.text:
            parts.append(escape_typst_text(elem.text))
        for child in elem:
            if child.attrib.get("class") == "heading-number":
                if child.tail:
                    parts.append(escape_typst_text(child.tail.lstrip()))
                continue
            parts.append(self._visit_inline(child))
            if child.tail:
                parts.append(escape_typst_text(child.tail))
        return "".join(parts).strip()

    @staticmethod
    def _extract_braced(text: str, start_idx: int) -> Tuple[str, int]:
        """Finds content inside balanced { ... } starting at or after start_idx."""
        open_idx = text.find("{", start_idx)
        if open_idx == -1:
            return "", start_idx
        depth = 0
        for i in range(open_idx, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return text[open_idx + 1:i], i + 1
        return text[open_idx + 1:], len(text)

    @classmethod
    def _normalize_math(cls, math_text: str) -> str:
        """Translates standard LaTeX math macros into Typst math syntax."""
        res = math_text

        # 1. Fractions: \frac{num}{den} -> ({num}) / ({den})
        while r"\frac" in res:
            idx = res.find(r"\frac")
            arg1, end1 = cls._extract_braced(res, idx + 5)
            arg2, end2 = cls._extract_braced(res, end1)
            norm_arg1 = cls._normalize_math(arg1)
            norm_arg2 = cls._normalize_math(arg2)
            res = res[:idx] + f"({norm_arg1}) / ({norm_arg2})" + res[end2:]

        # 2. Roots: \sqrt[n]{x} -> root(n, x), \sqrt{x} -> sqrt(x)
        while r"\sqrt" in res:
            idx = res.find(r"\sqrt")
            after = res[idx + 5:].lstrip()
            if after.startswith("["):
                close_bracket = after.find("]")
                n_val = after[1:close_bracket].strip()
                arg, end_idx = cls._extract_braced(res, idx + 5 + close_bracket + 1)
                norm_arg = cls._normalize_math(arg)
                res = res[:idx] + f"root({n_val}, {norm_arg})" + res[end_idx:]
            else:
                arg, end_idx = cls._extract_braced(res, idx + 5)
                norm_arg = cls._normalize_math(arg)
                res = res[:idx] + f"sqrt({norm_arg})" + res[end_idx:]

        # 3. Text and font macros: \text{...}, \mathrm{...}, \mathbf{...}, \mathit{...}
        for macro, wrapper in [
            (r"\text", lambda s: f'"{s}"'),
            (r"\mathrm", lambda s: f'"{s}"'),
            (r"\mathbf", lambda s: f"bold({s})"),
            (r"\mathit", lambda s: f"italic({s})"),
        ]:
            while macro in res:
                idx = res.find(macro)
                arg, end_idx = cls._extract_braced(res, idx + len(macro))
                res = res[:idx] + wrapper(arg) + res[end_idx:]

        # 4. Braced indices: _{abc} -> _(abc), ^{abc} -> ^(abc)
        res = re.sub(r"_\{([^}]+)\}", r"_(\1)", res)
        res = re.sub(r"\^\{([^}]+)\}", r"^(\1)", res)

        # 5. Scaled brackets: \left(, \right) etc.
        res = re.sub(r"\\left\s*([(\[{|])", r"\1", res)
        res = re.sub(r"\\right\s*([)\]}|])", r"\1", res)

        # 6. Differentials: ' dx' -> ' dif x' for integrals
        res = re.sub(r"\s+d([a-z])\b", r" dif \1", res)

        # 6. LaTeX command replacements using negative lookahead to allow subscripts like \sum_
        word_replacements = [
            (r"\\sum(?![a-zA-Z])", "sum"),
            (r"\\prod(?![a-zA-Z])", "product"),
            (r"\\int(?![a-zA-Z])", "integral"),
            (r"\\partial(?![a-zA-Z])", "diff"),
            (r"\\top(?![a-zA-Z])", "top"),
            (r"\\to(?![a-zA-Z])", "arrow.r"),
            (r"\\rightarrow(?![a-zA-Z])", "arrow.r"),
            (r"\\leftarrow(?![a-zA-Z])", "arrow.l"),
            (r"\\Rightarrow(?![a-zA-Z])", "arrow.r.double"),
            (r"\\Leftarrow(?![a-zA-Z])", "arrow.l.double"),
            (r"\\leftrightarrow(?![a-zA-Z])", "arrow.l.r"),
            (r"\\Leftrightarrow(?![a-zA-Z])", "arrow.l.r.double"),
            (r"\\quad(?![a-zA-Z])", "  "),
            (r"\\qquad(?![a-zA-Z])", "    "),
            (r"\\infty(?![a-zA-Z])", "infinity"),
            (r"\\times(?![a-zA-Z])", "times"),
            (r"\\cdot(?![a-zA-Z])", "dot"),
            (r"\\pm(?![a-zA-Z])", "plus.minus"),
            (r"\\leq(?![a-zA-Z])", "<="),
            (r"\\geq(?![a-zA-Z])", ">="),
            (r"\\neq(?![a-zA-Z])", "!="),
            (r"\\le(?![a-zA-Z])", "<="),
            (r"\\ge(?![a-zA-Z])", ">="),
            (r"\\ne(?![a-zA-Z])", "!="),
            (r"\\approx(?![a-zA-Z])", "approx"),
            # Greek lowercase
            (r"\\alpha(?![a-zA-Z])", "alpha"),
            (r"\\beta(?![a-zA-Z])", "beta"),
            (r"\\gamma(?![a-zA-Z])", "gamma"),
            (r"\\delta(?![a-zA-Z])", "delta"),
            (r"\\epsilon(?![a-zA-Z])", "epsilon"),
            (r"\\zeta(?![a-zA-Z])", "zeta"),
            (r"\\eta(?![a-zA-Z])", "eta"),
            (r"\\theta(?![a-zA-Z])", "theta"),
            (r"\\iota(?![a-zA-Z])", "iota"),
            (r"\\kappa(?![a-zA-Z])", "kappa"),
            (r"\\lambda(?![a-zA-Z])", "lambda"),
            (r"\\mu(?![a-zA-Z])", "mu"),
            (r"\\nu(?![a-zA-Z])", "nu"),
            (r"\\xi(?![a-zA-Z])", "xi"),
            (r"\\pi(?![a-zA-Z])", "pi"),
            (r"\\rho(?![a-zA-Z])", "rho"),
            (r"\\sigma(?![a-zA-Z])", "sigma"),
            (r"\\tau(?![a-zA-Z])", "tau"),
            (r"\\phi(?![a-zA-Z])", "phi"),
            (r"\\chi(?![a-zA-Z])", "chi"),
            (r"\\psi(?![a-zA-Z])", "psi"),
            (r"\\omega(?![a-zA-Z])", "omega"),
            # Greek uppercase
            (r"\\Gamma(?![a-zA-Z])", "Gamma"),
            (r"\\Delta(?![a-zA-Z])", "Delta"),
            (r"\\Theta(?![a-zA-Z])", "Theta"),
            (r"\\Lambda(?![a-zA-Z])", "Lambda"),
            (r"\\Xi(?![a-zA-Z])", "Xi"),
            (r"\\Pi(?![a-zA-Z])", "Pi"),
            (r"\\Sigma(?![a-zA-Z])", "Sigma"),
            (r"\\Phi(?![a-zA-Z])", "Phi"),
            (r"\\Psi(?![a-zA-Z])", "Psi"),
            (r"\\Omega(?![a-zA-Z])", "Omega"),
        ]
        for pattern, typst_sym in word_replacements:
            res = re.sub(pattern, typst_sym, res)

        return res

    def _visit_inline(self, elem: etree.Element) -> str:
        """Serializes an inline element to Typst syntax."""
        tag = elem.tag.lower()

        # Arithmatex inline math: <span class="arithmatex">\(...\)</span>
        if tag == "span" and "arithmatex" in elem.attrib.get("class", "").split():
            math_text = "".join(elem.itertext()).strip()
            if math_text.startswith(r"\(") and math_text.endswith(r"\)"):
                math_text = math_text[2:-2].strip()
            elif math_text.startswith("$") and math_text.endswith("$"):
                math_text = math_text[1:-1].strip()
            norm_math = self._normalize_math(math_text)
            return f"${norm_math}$"

        # Strong / Bold
        if tag in ("strong", "b"):
            inner = self._visit_children_inline(elem)
            return f"#strong[{inner}]"

        # Emph / Italic
        if tag in ("em", "i"):
            inner = self._visit_children_inline(elem)
            return f"#emph[{inner}]"

        # Strike-through / Del
        if tag in ("del", "s"):
            inner = self._visit_children_inline(elem)
            return f"#strike[{inner}]"

        # Mark / Highlight
        if tag == "mark":
            inner = self._visit_children_inline(elem)
            return f"#highlight[{inner}]"

        # Superscript
        if tag == "sup":
            fn_link = elem.find(".//a[@class='footnote-ref']")
            if fn_link is not None:
                target_href = fn_link.attrib.get("href", "")
                fn_id = target_href.lstrip("#")
                fn_body = self.footnotes.get(fn_id, "")
                if fn_body:
                    return f"#footnote[{fn_body}]"

            inner = self._visit_children_inline(elem)
            return f"#super[{inner}]"

        # Subscript
        if tag == "sub":
            inner = self._visit_children_inline(elem)
            return f"#sub[{inner}]"

        # Inline Code
        if tag == "code":
            code_text = elem.text or ""
            if "`" not in code_text:
                return f"`{code_text}`"
            escaped_raw = typst_string(code_text)
            return f'#raw("{escaped_raw}")'

        # Link
        if tag == "a":
            href = elem.attrib.get("href", "")
            inner = self._visit_children_inline(elem)
            if not inner:
                inner = escape_typst_text(href)
            escaped_href = typst_string(href)
            return f'#link("{escaped_href}")[{inner}]'

        # Image
        if tag == "img":
            src = elem.attrib.get("src", "")
            alt = elem.attrib.get("alt", "")
            resolved_src = self._resolve_and_copy_image(src)
            escaped_src = typst_string(resolved_src)
            escaped_alt = escape_typst_text(alt)
            alt_param = f', alt: "{escaped_alt}"' if escaped_alt else ""
            return f'#image("{escaped_src}"{alt_param})'

        # Line break
        if tag == "br":
            return "\\ "

        # Span or unknown inline element: simply recurse into children
        return self._visit_children_inline(elem)

    def _resolve_and_copy_image(self, src: str) -> str:
        """
        Resolves a local image path against file_base_dir, copies it into images_dir,
        and returns the relative path inside the Typst build directory.
        """
        if not src:
            return ""

        # Web URLs or data URIs remain unchanged
        if src.startswith(("http://", "https://", "data:")):
            return src

        # If already copied, reuse path
        if src in self.copied_images:
            return self.copied_images[src]

        if self.file_base_dir:
            orig_path = (self.file_base_dir / src).resolve()
            if orig_path.is_file():
                if self.images_dir:
                    self.images_dir.mkdir(parents=True, exist_ok=True)
                    safe_name = f"{len(self.copied_images)}_{orig_path.name}"
                    dest_file = self.images_dir / safe_name
                    shutil.copy2(orig_path, dest_file)
                    target_rel = f"images/{safe_name}"
                    self.copied_images[src] = target_rel
                    return target_rel
                return orig_path.as_posix()

        return src


def process_tree_headings_and_toc(
    root: etree.Element,
    numbering_ctx: NumberingContext,
    autonum_override: Optional[AutonumStyle] = None,
    base_level_offset: int = 0,
    autonum_from_level: int = 1,
    autonum_prefix: Optional[str] = None,
) -> List[TOCNode]:
    """
    Finds all headings in the ElementTree, computes numbering and slugs,
    updates heading element attributes (id and data-number) in-place,
    and returns a flat list of TOCNodes.
    """
    toc_nodes: List[TOCNode] = []

    # 1. Pre-register any explicit ids (from attr_list: ## Title {#my-id})
    for elem in root.iter():
        if re.match(r"^h[1-6]$", elem.tag.lower()):
            existing_id = elem.attrib.get("id")
            if existing_id:
                numbering_ctx.used_slugs.add(existing_id)

    # 2. Advance numbering and assign slugs
    for elem in root.iter():
        tag = elem.tag.lower()
        match = re.match(r"^h([1-6])$", tag)
        if not match:
            continue

        orig_level = int(match.group(1))
        effective_level = orig_level + base_level_offset
        plain_text = "".join(elem.itertext()).strip()

        # Slug
        slug = elem.attrib.get("id")
        if not slug:
            slug = numbering_ctx.unique_slug(plain_text)
            elem.attrib["id"] = slug

        # Numbering
        number_str = numbering_ctx.advance_counter(
            orig_level,
            autonum_override,
            from_level=autonum_from_level,
            prefix=autonum_prefix,
        )
        if number_str:
            elem.attrib["data-number"] = number_str
            span = etree.Element("span", {"class": "heading-number"})
            span.text = number_str
            orig_text = elem.text or ""
            elem.text = ""
            elem.insert(0, span)
            span.tail = f" {orig_text}" if orig_text else " "

        node = TOCNode(
            title=plain_text,
            slug=slug,
            level=effective_level,
            number=number_str,
        )
        toc_nodes.append(node)

    return toc_nodes
