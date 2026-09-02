"""
Native Typst PDF Renderer for markpublish.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any, List, Tuple

import typst

from markpublish.markdown.typst_serializer import TypstSerializer, typst_string
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
                # Retain generated source in working directory for easy diagnosis (A4)
                debug_dir = Path.cwd() / ".markpublish"
                try:
                    debug_dir.mkdir(parents=True, exist_ok=True)
                    debug_file = debug_dir / "last_failed_build.typ"
                    shutil.copy2(main_typ, debug_file)
                    debug_msg = f" (Quelltext zur Fehlerdiagnose gespeichert unter: {debug_file})"
                except Exception:
                    debug_msg = ""
                raise RuntimeError(f"Typst-Kompilierungsfehler: {e}{debug_msg}") from e

        return output_path

    def _assemble_typst_document(self, context: DocumentContext, build_dir: Path) -> str:
        """
        Assembles all parts, chapters, and metadata into a complete Typst source string.
        """
        config = context.config
        doc = config.document
        labels = context.labels
        lang_code = (doc.language or "de").split("-")[0].split("_")[0].lower()

        authors_list: List[str] = []
        if isinstance(doc.author, list):
            authors_list = [str(a) for a in doc.author]
        elif doc.author:
            authors_list = [str(doc.author)]

        authors_typst = ", ".join(f'"{typst_string(a)}"' for a in authors_list)
        if len(authors_list) == 1:
            authors_typst += ","

        title_esc = typst_string(doc.title)
        subtitle_esc = typst_string(doc.subtitle or "")
        version_esc = typst_string(doc.version or "")
        date_esc = typst_string(doc.date or "")
        copyright_esc = typst_string(doc.copyright or "")
        summary_esc = typst_string(doc.summary or "")

        show_header = getattr(doc, "header", True)
        show_footer = getattr(doc, "footer", True)

        toc_title_default = "Table of Contents" if lang_code == "en" else "Inhaltsverzeichnis"
        toc_title_esc = typst_string(labels.get("toc_title", toc_title_default))

        # Safely escape all label entries
        labels_entries: List[str] = []
        for k, v in labels.items():
            k_clean = str(k).replace("-", "_")
            labels_entries.append(f'    "{k_clean}": "{typst_string(v)}",')
        labels_str = "\n".join(labels_entries)

        parts: List[str] = [
            '#import "template.typ": *',
            "",
            "#show: doc => setup-document(",
            f'  title: "{title_esc}",',
            f'  subtitle: "{subtitle_esc}",',
            f'  authors: ({authors_typst}),',
            f'  version: "{version_esc}",',
            f'  date: "{date_esc}",',
            f'  copyright: "{copyright_esc}",',
            f'  language: "{lang_code}",',
            f'  show-cover: {str(doc.cover).lower()},',
            f'  summary: "{summary_esc}",',
            f'  show-toc: {str(doc.document_toc.enabled).lower()},',
            f'  toc-title: "{toc_title_esc}",',
            f'  toc-depth: {doc.document_toc.max_depth or 3},',
            f'  show-header: {str(show_header).lower()},',
            f'  show-footer: {str(show_footer).lower()},',
            "  labels: (",
            f"{labels_str}",
            "  ),",
            "  doc,",
            ")",
            "",
        ]

        # Track if there is already content on the current page.
        # At document start (after cover and/or TOC pagebreak), we are already on a fresh page.
        has_content = False

        for item in context.content_items:
            if item.is_part:
                part_in_toc = True
                if hasattr(item, "document_toc") and item.document_toc is not None:
                    part_in_toc = bool(item.document_toc.enabled)

                bb_val = item.break_before.value if getattr(item, "break_before", None) else "page"

                if bb_val == "divider":
                    if has_content:
                        parts.append("#pagebreak()\n")
                    summary_typ = typst_string(item.summary or "")
                    part_title_esc = typst_string(item.title)
                    part_sub_esc = typst_string(item.subtitle or "")
                    part_tag_esc = typst_string(labels.get("part", "Part" if lang_code == "en" else "Abschnitt"))
                    part_toc_title_esc = typst_string(labels.get("part_toc_title", "Table of Contents" if lang_code == "en" else "Inhalt dieses Abschnitts"))

                    toc_items_typ: List[str] = []
                    for n in getattr(item, "local_toc_items", []):
                        if getattr(n, "is_header", False):
                            t_esc = typst_string(n.title)
                            toc_items_typ.append(f'(title: "{t_esc}", is_header: true)')
                        else:
                            indent = max(0, (n.level - 1)) * 12
                            raw_title = f"{n.number} {n.title}" if getattr(n, "number", None) else (getattr(n, "display_title", None) or n.title)
                            t_esc = typst_string(raw_title)
                            toc_items_typ.append(
                                f'(title: "{t_esc}", slug: "{n.slug}", level: {n.level}, indent: {indent}pt)'
                            )

                    toc_items_str = f"({toc_items_typ[0]},)" if len(toc_items_typ) == 1 else (f"({', '.join(toc_items_typ)})" if toc_items_typ else "()")
                    parts.append(
                        f'#render-part-divider(title: "{part_title_esc}", subtitle: "{part_sub_esc}", '
                        f'summary: "{summary_typ}", tag: "{part_tag_esc}", in-toc: {str(part_in_toc).lower()}, '
                        f'toc-title: "{part_toc_title_esc}", toc-items: {toc_items_str})\n'
                    )
                    has_content = False  # Divider ends on a fresh page
                elif bb_val == "page":
                    if has_content:
                        parts.append("#pagebreak()\n")
                        has_content = False
                    if part_in_toc:
                        part_heading_title = typst_string(item.title)
                        parts.append(f'#heading(level: 1, outlined: true, numbering: none)[{part_heading_title}] <part-entry>\n')

                if getattr(item, "pagenum_reset", False):
                    parts.append("#counter(page).update(1)\n")
            else:
                ch_typst, has_content = self._render_chapter(item, labels, build_dir, has_content, lang_code=lang_code)
                parts.append(ch_typst)

        return "\n".join(parts)

    def _render_chapter(
        self,
        chapter_item: Any,
        labels: Any,
        build_dir: Path,
        has_content: bool,
        lang_code: str = "de",
    ) -> Tuple[str, bool]:
        """Renders an individual chapter item into Typst markup."""
        res: List[str] = []

        bb_val = chapter_item.break_before.value if getattr(chapter_item, "break_before", None) else "page"

        if bb_val == "divider":
            if has_content:
                res.append("#pagebreak()\n")
            tag_label = labels.get("chapter", "Chapter" if lang_code == "en" else "Kapitel")
            num_prefix = getattr(chapter_item, "number_prefix", None)
            full_tag = typst_string(f"{tag_label} {num_prefix}".strip() if num_prefix else tag_label)
            summary_esc = typst_string(chapter_item.summary or "")
            ch_title_esc = typst_string(chapter_item.display_title)
            ch_sub_esc = typst_string(chapter_item.subtitle or "")
            ch_toc_title_esc = typst_string(labels.get("chapter_toc_title", "Chapter Contents" if lang_code == "en" else "Inhalt dieses Kapitels"))

            toc_items_typ: List[str] = []
            for n in getattr(chapter_item, "local_toc_items", []):
                indent = max(0, (n.level - 2)) * 8
                raw_title = f"{n.number} {n.title}" if getattr(n, "number", None) else (getattr(n, "display_title", None) or n.title)
                t_esc = typst_string(raw_title)
                toc_items_typ.append(
                    f'(title: "{t_esc}", slug: "{n.slug}", indent: {indent}pt)'
                )

            toc_items_str = f"({toc_items_typ[0]},)" if len(toc_items_typ) == 1 else (f"({', '.join(toc_items_typ)})" if toc_items_typ else "()")
            res.append(
                f'#render-chapter-divider(title: "{ch_title_esc}", subtitle: "{ch_sub_esc}", '
                f'summary: "{summary_esc}", tag: "{full_tag}", '
                f'toc-title: "{ch_toc_title_esc}", toc-items: {toc_items_str})\n'
            )
            has_content = False  # Divider ends on a fresh page
        elif bb_val == "page":
            if has_content:
                res.append("#pagebreak()\n")
                has_content = False

        if getattr(chapter_item, "pagenum_reset", False):
            res.append("#counter(page).update(1)\n")

        images_dir = build_dir / "images"
        element_tree = getattr(chapter_item, "element_tree", None)
        file_base_dir = getattr(chapter_item, "file_base_dir", None)

        if element_tree is not None:
            serializer = TypstSerializer(
                base_level_offset=0,
                file_base_dir=file_base_dir,
                images_dir=images_dir,
                labels=labels,
            )
            ch_typst = serializer.serialize(element_tree)
            if ch_typst.strip():
                res.append(ch_typst)
                has_content = True
        else:
            typst_content = getattr(chapter_item, "typst_content", "")
            if typst_content:
                res.append(typst_content)
                has_content = True
            else:
                raw_md = getattr(chapter_item, "raw_markdown", "") or getattr(chapter_item, "html_content", "")
                if raw_md:
                    from markpublish.markdown.typst_serializer import html_to_tree
                    tree = html_to_tree(raw_md)
                    serializer = TypstSerializer(file_base_dir=file_base_dir, images_dir=images_dir, labels=labels)
                    ch_typst = serializer.serialize(tree)
                    if ch_typst.strip():
                        res.append(ch_typst)
                        has_content = True

        res.append("\n")
        return "\n".join(res), has_content

