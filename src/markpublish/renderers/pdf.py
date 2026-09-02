"""
Native Typst PDF Renderer for markpublish.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any, List, Tuple

import typst

from markpublish.markdown.typst_converter import MarkdownToTypstConverter
from markpublish.renderers.base import BaseRenderer, DocumentContext


class PDFRenderer(BaseRenderer):
    """
    Renders documents to PDF using the native Typst compiler.
    """

    def render(self, context: DocumentContext, output_path: Path) -> Path:
        """
        Renders the document context to a PDF file via Typst.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Create a working build directory for Typst compilation
        with tempfile.TemporaryDirectory(prefix="markpublish_typst_") as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Copy template assets (template.typ, assets/, fonts/, etc.) to build directory
            if context.template_path.is_dir():
                for item in context.template_path.iterdir():
                    if item.is_dir():
                        shutil.copytree(item, tmp_path / item.name, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, tmp_path / item.name)

            # 2. Assemble main Typst source document
            typst_source = self._assemble_typst_document(context, tmp_path)
            main_typ = tmp_path / "main.typ"
            main_typ.write_text(typst_source, encoding="utf-8")

            # 3. Determine font search paths
            font_paths: List[Path] = []
            theme_fonts = context.template_path / "fonts"
            if theme_fonts.is_dir():
                font_paths.append(theme_fonts)

            # 4. Compile with Typst
            try:
                typst.compile(
                    input=main_typ,
                    output=output_path,
                    root=tmp_path,
                    font_paths=font_paths if font_paths else None,
                )
            except Exception as e:
                raise RuntimeError(f"Typst-Kompilierungsfehler: {e}") from e

        return output_path

    def _assemble_typst_document(self, context: DocumentContext, build_dir: Path) -> str:
        """
        Assembles all parts, chapters, and metadata into a complete Typst source string.
        """
        config = context.config
        doc = config.document
        labels = context.labels

        converter = MarkdownToTypstConverter(labels=labels)

        authors_list: List[str] = []
        if isinstance(doc.author, list):
            authors_list = [str(a) for a in doc.author]
        elif doc.author:
            authors_list = [str(doc.author)]

        authors_typst = ", ".join(f'"{a}"' for a in authors_list)
        if len(authors_list) == 1:
            authors_typst += ","

        summary_escaped = doc.summary.replace('"', '\\"') if doc.summary else ""
        date_str = str(doc.date) if doc.date else ""
        lang_code = (doc.language or "de").split("-")[0].split("_")[0].lower()

        parts: List[str] = [
            '#import "template.typ": *',
            "",
            "#show: doc => setup-document(",
            f'  title: "{doc.title}",',
            f'  subtitle: "{doc.subtitle or ""}",',
            f'  authors: ({authors_typst}),',
            f'  version: "{doc.version or ""}",',
            f'  date: "{date_str}",',
            f'  copyright: "{doc.copyright or ""}",',
            f'  language: "{lang_code}",',
            f'  show-cover: {str(doc.cover).lower()},',
            f'  summary: "{summary_escaped}",',
            f'  show-toc: {str(doc.document_toc.enabled).lower()},',
            f'  toc-title: "{labels.get("toc_title", "Inhaltsverzeichnis")}",',
            f'  toc-depth: {doc.document_toc.max_depth or 3},',
            "  labels: (",
            f'    version: "{labels.get("version", "Version")}",',
            f'    date: "{labels.get("date", "Datum")}",',
            f'    author: "{labels.get("author", "Autor")}",',
            f'    copyright: "{labels.get("copyright", "Copyright")}",',
            f'    page: "{labels.get("page", "Seite")}",',
            f'    page_of: "{labels.get("page_of", "von")}",',
            f'    chapter: "{labels.get("chapter", "Kapitel")}",',
            f'    part: "{labels.get("part", "Abschnitt")}",',
            "  ),",
            "  doc,",
            ")",
            "",
        ]

        # Track if we are at the very beginning of a fresh document without cover/TOC
        has_content = bool(doc.cover or doc.document_toc.enabled)

        for item in context.content_items:
            if item.is_part:
                part_in_toc = True
                if hasattr(item, "document_toc") and item.document_toc is not None:
                    part_in_toc = bool(item.document_toc.enabled)

                bb_val = item.break_before.value if getattr(item, "break_before", None) else "page"

                if bb_val == "divider":
                    if has_content:
                        parts.append("#pagebreak()\n")
                    summary_typ = (item.summary or "").replace('"', '\\"')
                    toc_items_typ: List[str] = []
                    for n in getattr(item, "local_toc_items", []):
                        if getattr(n, "is_header", False):
                            title_esc = n.title.replace('"', '\\"')
                            toc_items_typ.append(f'(title: "{title_esc}", is_header: true)')
                        else:
                            indent = max(0, (n.level - 1)) * 12
                            raw_title = f"{n.number} {n.title}" if getattr(n, "number", None) else (getattr(n, "display_title", None) or n.title)
                            title_esc = raw_title.replace('"', '\\"')
                            toc_items_typ.append(
                                f'(title: "{title_esc}", slug: "{n.slug}", level: {n.level}, indent: {indent}pt)'
                            )

                    toc_items_str = f"({toc_items_typ[0]},)" if len(toc_items_typ) == 1 else (f"({', '.join(toc_items_typ)})" if toc_items_typ else "()")
                    parts.append(
                        f'#render-part-divider(title: "{item.title}", subtitle: "{item.subtitle or ""}", '
                        f'summary: "{summary_typ}", tag: "{labels.get("part", "Abschnitt")}", in-toc: {str(part_in_toc).lower()}, '
                        f'toc-title: "{labels.get("part_toc_title", "Inhalt dieses Abschnitts")}", toc-items: {toc_items_str})\n'
                    )
                    has_content = False  # Divider ends on a fresh page
                elif bb_val == "page":
                    if has_content:
                        parts.append("#pagebreak()\n")
                        has_content = False
                    if part_in_toc:
                        parts.append(f'#heading(level: 1, outlined: true, numbering: none)[{item.title}] <part-entry>\n')

                if getattr(item, "pagenum_reset", False):
                    parts.append("#counter(page).update(1)\n")
            else:
                ch_typst, has_content = self._render_chapter(item, converter, labels, has_content)
                parts.append(ch_typst)

        return "\n".join(parts)

    def _render_chapter(
        self,
        chapter_item: Any,
        converter: MarkdownToTypstConverter,
        labels: Any,
        has_content: bool,
    ) -> Tuple[str, bool]:
        """Renders an individual chapter item into Typst markup."""
        res: List[str] = []

        bb_val = chapter_item.break_before.value if getattr(chapter_item, "break_before", None) else "page"

        if bb_val == "divider":
            if has_content:
                res.append("#pagebreak()\n")
            tag_label = labels.get("chapter", "Kapitel")
            num_prefix = getattr(chapter_item, "number_prefix", None)
            full_tag = f"{tag_label} {num_prefix}".strip() if num_prefix else tag_label
            summary_esc = (chapter_item.summary or "").replace('"', '\\"')

            toc_items_typ: List[str] = []
            for n in getattr(chapter_item, "local_toc_items", []):
                indent = max(0, (n.level - 2)) * 8
                raw_title = f"{n.number} {n.title}" if getattr(n, "number", None) else (getattr(n, "display_title", None) or n.title)
                title_esc = raw_title.replace('"', '\\"')
                toc_items_typ.append(
                    f'(title: "{title_esc}", slug: "{n.slug}", indent: {indent}pt)'
                )

            toc_items_str = f"({toc_items_typ[0]},)" if len(toc_items_typ) == 1 else (f"({', '.join(toc_items_typ)})" if toc_items_typ else "()")
            res.append(
                f'#render-chapter-divider(title: "{chapter_item.display_title}", subtitle: "{chapter_item.subtitle or ""}", '
                f'summary: "{summary_esc}", tag: "{full_tag}", '
                f'toc-title: "{labels.get("chapter_toc_title", "Inhalt dieses Kapitels")}", toc-items: {toc_items_str})\n'
            )
            has_content = False  # Divider ends on a fresh page
        elif bb_val == "page":
            if has_content:
                res.append("#pagebreak()\n")
                has_content = False

        if getattr(chapter_item, "pagenum_reset", False):
            res.append("#counter(page).update(1)\n")

        typst_content = getattr(chapter_item, "typst_content", "")
        if typst_content:
            res.append(typst_content)
            has_content = True
        else:
            raw_md = getattr(chapter_item, "raw_markdown", "") or getattr(chapter_item, "html", "")
            if raw_md:
                converted_typst = converter.convert(raw_md)
                res.append(converted_typst)
                has_content = True

        res.append("\n")
        return "\n".join(res), has_content

