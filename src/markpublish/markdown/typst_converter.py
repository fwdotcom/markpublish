"""
Native Markdown-to-Typst Converter for markpublish.

Converts CommonMark / GitHub Flavored Markdown (GFM) text into clean,
valid Typst markup suitable for compilation with the Typst compiler.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from markpublish.i18n import LabelMap


def escape_typst_text(text: str) -> str:
    """
    Escapes characters that have special structural meaning in Typst text mode.
    Preserves normal punctuation while preventing unintended Typst syntax.
    """
    result = text
    # Escape backslashes first
    result = result.replace("\\", "\\\\")
    # Escape structural characters
    result = result.replace("#", "\\#")
    result = result.replace("[", "\\[")
    result = result.replace("]", "\\]")
    result = result.replace("@", "\\@")
    result = result.replace("<", "\\<")
    result = result.replace(">", "\\>")
    result = result.replace("$", "\\$")
    result = result.replace("*", "\\*")
    result = result.replace("_", "\\_")
    return result


def slugify_heading(text: str) -> str:
    """Creates a URL-/Typst-safe label slug from heading text."""
    cleaned = re.sub(r"[*_`~\[\]]", "", text)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    cleaned = cleaned.lower().strip()
    cleaned = re.sub(r"[äÄ]", "ae", cleaned)
    cleaned = re.sub(r"[öÖ]", "oe", cleaned)
    cleaned = re.sub(r"[üÜ]", "ue", cleaned)
    cleaned = re.sub(r"ß", "ss", cleaned)
    cleaned = re.sub(r"[^a-z0-9]+", "-", cleaned)
    return cleaned.strip("-") or "section"


@dataclass
class HeadingInfo:
    """Extracted metadata for a document heading."""
    level: int
    title: str
    slug: str
    number: Optional[str] = None


class MarkdownToTypstConverter:
    """
    Stateful and configurable parser converting Markdown text to Typst markup.
    """

    ALERT_TYPES = {
        "NOTE": ("note", "Hinweis", "Note"),
        "TIP": ("tip", "Tipp", "Tip"),
        "IMPORTANT": ("important", "Wichtig", "Important"),
        "WARNING": ("warning", "Warnung", "Warning"),
        "CAUTION": ("caution", "Achtung", "Caution"),
    }

    def __init__(
        self,
        labels: Optional[Any] = None,
        base_heading_level: int = 1,
        slug_generator: Optional[Callable[[str], str]] = None,
        toc_nodes: Optional[List[Any]] = None,
    ):
        self.labels = labels or {}
        self.base_heading_level = base_heading_level
        self.slug_generator = slug_generator or slugify_heading
        self.toc_nodes = list(toc_nodes) if toc_nodes else []
        self.node_index = 0
        self.extracted_headings: List[HeadingInfo] = []

    def convert(self, markdown_text: str) -> str:
        """Converts Markdown text into Typst markup."""
        lines = markdown_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        output_blocks: List[str] = []
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i]
            stripped = line.strip()

            # 1. Empty lines
            if not stripped:
                i += 1
                continue

            # 2. Fenced code block (``` or ~~~)
            if stripped.startswith("```") or stripped.startswith("~~~"):
                code_block, i = self._parse_code_block(lines, i)
                output_blocks.append(code_block)
                continue

            # 3. GitHub Alerts / Admonitions (> [!NOTE]) or Blockquotes
            if stripped.startswith(">"):
                quote_block, i = self._parse_blockquote(lines, i)
                output_blocks.append(quote_block)
                continue

            # 4. Markdown Headings (# Heading)
            heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if heading_match:
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()
                output_blocks.append(self._convert_heading(level, heading_text))
                i += 1
                continue

            # 5. Thematic Break / Horizontal Rule (---, ***, ___)
            if re.match(r"^(\*{3,}|-{3,}|_{3,})$", stripped):
                output_blocks.append("#line(length: 100%, stroke: 0.5pt + luma(200))")
                i += 1
                continue

            # 6. Tables (| col 1 | col 2 |)
            if "|" in stripped and (i + 1 < n and re.match(r"^\s*\|?\s*[-:]+[-| :]*$", lines[i + 1])):
                table_block, i = self._parse_table(lines, i)
                output_blocks.append(table_block)
                continue

            # 7. Math Display Block ($$ math $$)
            if stripped.startswith("$$"):
                math_block, i = self._parse_math_block(lines, i)
                output_blocks.append(math_block)
                continue

            # 8. Lists (Unordered, Ordered, Tasklists)
            if self._is_list_item(stripped):
                list_block, i = self._parse_list(lines, i)
                output_blocks.append(list_block)
                continue

            # 9. Regular Paragraph
            para_block, i = self._parse_paragraph(lines, i)
            output_blocks.append(para_block)

        return "\n\n".join(output_blocks)

    def _convert_heading(self, md_level: int, raw_text: str) -> str:
        """Converts a Markdown heading to Typst heading with label anchor and autonumbering."""
        inline_typst = self._convert_inline(raw_text)
        slug = self.slug_generator(raw_text)
        number_prefix = ""

        if self.node_index < len(self.toc_nodes):
            node = self.toc_nodes[self.node_index]
            self.node_index += 1
            if getattr(node, "number", None):
                number_prefix = f"{node.number} "
            if getattr(node, "slug", None):
                slug = node.slug

        self.extracted_headings.append(
            HeadingInfo(
                level=md_level,
                title=raw_text,
                slug=slug,
                number=number_prefix.strip() or None,
            )
        )
        equal_signs = "=" * md_level
        return f"{equal_signs} {number_prefix}{inline_typst} <{slug}>"

    def _parse_code_block(self, lines: List[str], start_idx: int) -> Tuple[str, int]:
        """Parses a fenced code block."""
        fence = lines[start_idx].strip()[:3]
        lang = lines[start_idx].strip()[3:].strip()
        code_lines: List[str] = []
        i = start_idx + 1
        n = len(lines)

        while i < n:
            line = lines[i]
            if line.strip().startswith(fence):
                i += 1
                break
            code_lines.append(line)
            i += 1

        code_content = "\n".join(code_lines)
        lang_spec = f"{lang}" if lang else ""
        return f"```{lang_spec}\n{code_content}\n```", i

    def _parse_blockquote(self, lines: List[str], start_idx: int) -> Tuple[str, int]:
        """Parses a blockquote or GitHub-style Callout/Alert."""
        quote_lines: List[str] = []
        i = start_idx
        n = len(lines)

        while i < n and (lines[i].strip().startswith(">") or (quote_lines and lines[i].strip() and not self._is_block_start(lines[i]))):
            line = lines[i].strip()
            if line.startswith(">"):
                line = line[1:].strip()
            quote_lines.append(line)
            i += 1

        if not quote_lines:
            return "", i

        first_line = quote_lines[0]
        alert_match = re.match(r"^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\](?:\s+(.*))?$", first_line, re.IGNORECASE)

        if alert_match:
            alert_type_key = alert_match.group(1).upper()
            custom_title = alert_match.group(2)
            alert_info = self.ALERT_TYPES.get(alert_type_key, ("note", "Hinweis", "Note"))
            typst_type = alert_info[0]

            # Label lookup (supports Dict, LabelMap, or object)
            label_key = f"alert_{typst_type}"
            default_label = None
            if hasattr(self.labels, "__getitem__"):
                try:
                    default_label = self.labels[label_key]
                except Exception:
                    try:
                        default_label = self.labels[typst_type]
                    except Exception:
                        pass
            elif isinstance(self.labels, dict):
                default_label = self.labels.get(label_key) or self.labels.get(typst_type)
            else:
                default_label = getattr(self.labels, label_key, getattr(self.labels, typst_type, None))

            if not default_label:
                default_label = alert_info[1]

            title = custom_title.strip() if custom_title else default_label
            title_escaped = self._convert_inline(title)

            body_text = "\n".join(quote_lines[1:]).strip()
            body_typst = self.convert(body_text) if body_text else ""
            return f'#callout(type: "{typst_type}", title: [{title_escaped}])[\n{body_typst}\n]', i
        else:
            # Generic blockquote
            body_text = "\n".join(quote_lines)
            body_typst = self.convert(body_text)
            return f"#quote[\n{body_typst}\n]", i

    def _split_table_row(self, line: str) -> List[str]:
        """Splits a table row by unescaped pipe characters."""
        stripped = line.strip()
        if stripped.startswith("|"):
            stripped = stripped[1:]
        if stripped.endswith("|") and not stripped.endswith(r"\|"):
            stripped = stripped[:-1]
        raw_cells = re.split(r"(?<!\\)\|", stripped)
        return [c.replace(r"\|", "|").strip() for c in raw_cells]

    def _parse_table(self, lines: List[str], start_idx: int) -> Tuple[str, int]:
        """Parses a GFM Markdown pipe table into Typst #table()."""
        raw_rows: List[List[str]] = []
        alignments: List[str] = []
        i = start_idx
        n = len(lines)

        # Header row
        headers = self._split_table_row(lines[i])
        raw_rows.append(headers)
        i += 1

        # Separator row (alignments)
        if i < n and "|" in lines[i]:
            cols = self._split_table_row(lines[i])
            for col in cols:
                if col.startswith(":") and col.endswith(":"):
                    alignments.append("center")
                elif col.endswith(":"):
                    alignments.append("right")
                else:
                    alignments.append("left")
            i += 1

        # Data rows
        while i < n and "|" in lines[i] and lines[i].strip():
            row_cols = self._split_table_row(lines[i])
            while len(row_cols) < len(headers):
                row_cols.append("")
            raw_rows.append(row_cols[:len(headers)])
            i += 1

        num_cols = len(headers)
        align_str = ", ".join(alignments[:num_cols]) if alignments else ", ".join(["left"] * num_cols)

        if num_cols == 2:
            columns_spec = "(1fr, 2fr)"
        elif num_cols == 3:
            columns_spec = "(1.2fr, 1.2fr, 2fr)"
        elif num_cols == 4:
            columns_spec = "(1.2fr, 0.9fr, 1fr, 2fr)"
        else:
            columns_spec = f"{num_cols}"

        typst_rows: List[str] = []
        # Render Header
        header_cells = [f"[* {self._convert_inline(h)} *]" for h in raw_rows[0]]
        typst_rows.append(f"  table.header({', '.join(header_cells)}),")

        # Render Data Rows
        for row in raw_rows[1:]:
            row_cells = [f"[{self._convert_inline(cell)}]" for cell in row]
            typst_rows.append(f"  {', '.join(row_cells)},")

        return f"#table(\n  columns: {columns_spec},\n  align: ({align_str}),\n" + "\n".join(typst_rows) + "\n)", i

    def _parse_math_block(self, lines: List[str], start_idx: int) -> Tuple[str, int]:
        """Parses a $$...$$ display math block."""
        first_line = lines[start_idx].strip()
        if first_line == "$$":
            math_lines: List[str] = []
            i = start_idx + 1
            while i < len(lines):
                if lines[i].strip() == "$$":
                    i += 1
                    break
                math_lines.append(lines[i])
                i += 1
            math_content = "\n".join(math_lines).strip()
            return f"$ {math_content} $", i
        else:
            content = first_line.strip("$").strip()
            return f"$ {content} $", start_idx + 1

    def _parse_list(self, lines: List[str], start_idx: int) -> Tuple[str, int]:
        """Parses ordered, unordered, and task lists."""
        list_lines: List[str] = []
        i = start_idx
        n = len(lines)

        while i < n:
            line = lines[i]
            if not line.strip():
                if i + 1 < n and (lines[i + 1].startswith("  ") or self._is_list_item(lines[i + 1].strip())):
                    i += 1
                    continue
                else:
                    break

            if not self._is_list_item(line.strip()) and not line.startswith("  "):
                break

            indent_len = len(line) - len(line.lstrip())
            indent = " " * indent_len
            stripped = line.strip()

            # Task list: - [ ] or - [x]
            task_match = re.match(r"^[-*+]\s+\[([ xX])\]\s*(.*)$", stripped)
            if task_match:
                checked = task_match.group(1).lower() == "x"
                item_text = self._convert_inline(task_match.group(2))
                checked_bool = "true" if checked else "false"
                list_lines.append(f"{indent}- #task-item(checked: {checked_bool})[{item_text}]")
            # Unordered list: - or *
            elif re.match(r"^[-*]\s+(.*)$", stripped):
                item_text = self._convert_inline(re.sub(r"^[-*]\s+", "", stripped))
                list_lines.append(f"{indent}- {item_text}")
            # Ordered list: 1. or 1)
            elif re.match(r"^\d+[\.\)]\s+(.*)$", stripped):
                item_text = self._convert_inline(re.sub(r"^\d+[\.\)]\s+", "", stripped))
                list_lines.append(f"{indent}+ {item_text}")
            else:
                list_lines.append(f"{indent}{self._convert_inline(stripped)}")

            i += 1

        return "\n".join(list_lines), i

    def _parse_paragraph(self, lines: List[str], start_idx: int) -> Tuple[str, int]:
        """Parses a standard text paragraph."""
        para_lines: List[str] = []
        i = start_idx
        n = len(lines)

        while i < n:
            line = lines[i]
            if not line.strip() or self._is_block_start(line.strip()):
                break
            para_lines.append(line)
            i += 1

        full_para = " ".join(l.strip() for l in para_lines)
        return self._convert_inline(full_para), i

    def _is_list_item(self, line: str) -> bool:
        """Checks if a string begins with a list marker."""
        return bool(re.match(r"^([-*+]|\d+[\.\)])\s+", line))

    def _is_block_start(self, line: str) -> bool:
        """Checks if a line begins a distinct block element."""
        if not line:
            return False
        if line.startswith("#") or line.startswith(">") or line.startswith("```") or line.startswith("~~~") or line.startswith("$$"):
            return True
        if self._is_list_item(line):
            return True
        if re.match(r"^(\*{3,}|-{3,}|_{3,})$", line):
            return True
        return False

    def _convert_inline(self, text: str) -> str:
        """
        Transforms inline Markdown markup to Typst markup using safe tokens.
        """
        tokens: Dict[str, str] = {}
        counter = 0

        def make_token(typst_replacement: str) -> str:
            nonlocal counter
            tok = f"\x00MPTOK{counter}\x00"
            tokens[tok] = typst_replacement
            counter += 1
            return tok

        s = text

        # 1. Inline code: `code`
        s = re.sub(r"`([^`]+)`", lambda m: make_token(f"`{m.group(1)}`"), s)

        # 2. Inline math: $math$
        s = re.sub(r"\$([^\$]+)\$", lambda m: make_token(f"${m.group(1)}$"), s)

        # 3. Images: ![alt](url)
        s = re.sub(
            r"!\[(.*?)\]\((.*?)\)",
            lambda m: make_token(f'#image("{m.group(2)}", alt: "{escape_typst_text(m.group(1))}")'),
            s,
        )

        # 4. Links: [text](url)
        s = re.sub(
            r"\[(.*?)\]\((.*?)\)",
            lambda m: make_token(f'#link("{m.group(2)}")[{m.group(1)}]'),
            s,
        )

        # 5. Bold-Italic (***text*** or ___text___)
        s = re.sub(r"\*\*\*(.*?)\*\*\*", lambda m: make_token(f"#strong[#emph[{m.group(1)}]]"), s)
        s = re.sub(r"___(.*?)___", lambda m: make_token(f"#strong[#emph[{m.group(1)}]]"), s)

        # 6. Bold (**text** or __text__)
        s = re.sub(r"\*\*(.*?)\*\*", lambda m: make_token(f"#strong[{m.group(1)}]"), s)
        s = re.sub(r"__(.*?)__", lambda m: make_token(f"#strong[{m.group(1)}]"), s)

        # 7. Italic (*text* or _text_)
        s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", lambda m: make_token(f"#emph[{m.group(1)}]"), s)
        s = re.sub(r"(?<!_)_([^_]+)_(?!_)", lambda m: make_token(f"#emph[{m.group(1)}]"), s)

        # 8. Strikethrough (~~text~~)
        s = re.sub(r"~~(.*?)~~", lambda m: make_token(f"#strike[{m.group(1)}]"), s)

        # 9. Escape remaining raw text
        parts = re.split(r"(\x00MPTOK\d+\x00)", s)
        escaped_parts: List[str] = []
        for p in parts:
            if not p:
                continue
            if p.startswith("\x00MPTOK") and p.endswith("\x00"):
                escaped_parts.append(p)
            else:
                escaped_parts.append(escape_typst_text(p))

        result = "".join(escaped_parts)

        # 10. Iteratively substitute tokens from inner to outer
        while "\x00MPTOK" in result:
            prev = result
            for tok, replacement in list(tokens.items()):
                if tok in result:
                    result = result.replace(tok, replacement)
            if result == prev:
                # Break to avoid infinite loop if an unmatched token pattern remains
                break

        return result
