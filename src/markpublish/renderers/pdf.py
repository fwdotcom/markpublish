"""
Native Typst PDF Renderer for markpublish.
"""

from __future__ import annotations

import shutil
import tempfile
import warnings
from pathlib import Path
from typing import Any, List, Optional, Set, Tuple

import typst

from markpublish.i18n import (
    UndefinedLabelError,
    UndefinedMetadataError,
    build_document_metadata,
    undefined_label_message,
    undefined_metadata_message,
)
from markpublish.markdown.typst_serializer import (
    TypstSerializer,
    typst_string,
    typst_value,
)
from markpublish.renderers.base import BaseRenderer, DocumentContext
from markpublish.templates.contract import (
    ThemeContractWarning,
    check_theme_contract,
    parse_sent_arguments,
    parse_theme_contract,
)
from markpublish.ui import t


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

            # 2b. Theme und Aufruf gegeneinander halten, bevor Typst startet.
            #     Geprueft wird gegen das Original-Theme, nicht gegen die Kopie
            #     im Build-Verzeichnis: in der Meldung soll der Pfad stehen, den
            #     der Nutzer bearbeiten kann.
            self._check_theme_contract(context, typst_source)

            # 3. Determine font search paths
            font_paths: List[Path] = []
            theme_fonts = context.template_path / "fonts"
            if theme_fonts.is_dir():
                font_paths.append(theme_fonts)

            # 4. Compile with Typst
            compile_kwargs: dict = {
                "input": main_typ,
                "output": output_path,
                "root": tmp_path,
            }
            if font_paths:
                compile_kwargs["font_paths"] = font_paths

            try:
                typst.compile(**compile_kwargs)
            except Exception as e:
                # Retain generated source in working directory for easy diagnosis (A4)
                debug_dir = Path.cwd() / ".markpublish"
                try:
                    debug_dir.mkdir(parents=True, exist_ok=True)
                    debug_file = debug_dir / "last_failed_build.typ"
                    shutil.copy2(main_typ, debug_file)
                    debug_msg = t("err.typst.debug_saved", path=debug_file)
                except Exception:
                    debug_msg = ""
                raise RuntimeError(t("err.typst.compile", error=e) + debug_msg) from e

        return output_path

    def _check_theme_contract(self, context: DocumentContext, typst_source: str) -> None:
        """
        Prueft das Theme gegen den erzeugten Aufruf.

        Abgebrochen wird nur, wo Typst ohnehin abbraeche -- der Gewinn ist die
        Meldung, nicht ein neues Verbot. Was heute still leer bleibt, bleibt
        still leer und wird als Warnung gemeldet.
        """
        contract = parse_theme_contract(context.template_path)
        if not contract.parameters:
            # Kein `.typ` lesbar: das Theme ist entweder leer oder liegt in
            # einer Form vor, die dieses Modul nicht kennt. Dann ist Schweigen
            # richtig -- Typst meldet sich gleich selbst.
            return

        labels = context.labels
        meta_entries = build_document_metadata(context.config.document, labels)
        report = check_theme_contract(
            contract,
            parse_sent_arguments(typst_source),
            labels=labels,
            language=getattr(labels, "language", None),
            meta_keys=set(meta_entries.keys()),
        )

        if report.missing_labels:
            blocks = [
                undefined_label_message(key, labels, places)
                for key, places in sorted(report.missing_labels.items())
            ]
            raise UndefinedLabelError("\n\n".join(blocks))

        if report.missing_metadata:
            # Eigene Meldung, nicht die der Labels: ein fehlendes Metadatum
            # wird unter `document:` ergaenzt, nicht in einer i18n.yaml. Die
            # Label-Meldung wuerde hier einen Weg weisen, der nicht hilft.
            blocks = [
                undefined_metadata_message(key, places, known_keys=meta_entries.keys())
                for key, places in sorted(report.missing_metadata.items())
            ]
            raise UndefinedMetadataError("\n\n".join(blocks))

        if report.errors:
            raise RuntimeError(
                t("err.theme.signature_mismatch")
                + "\n".join(f"  {message}" for message in report.errors)
                + "\n  "
                + t("err.theme.signature_theme", path=context.template_path)
            )

        for message in report.warnings:
            warnings.warn(message, ThemeContractWarning, stacklevel=2)

    def _assemble_typst_document(self, context: DocumentContext, build_dir: Path) -> str:
        """
        Assembles all parts, chapters, and metadata into a complete Typst source string.
        """
        config = context.config
        doc = config.document
        labels = context.labels
        lang_code = (doc.language or "de").split("-")[0].split("_")[0].lower()

        show_header = getattr(doc, "header", True)
        show_footer = getattr(doc, "footer", True)

        toc_title_default = "Table of Contents" if lang_code == "en" else "Inhaltsverzeichnis"
        toc_title_esc = typst_string(labels.get("toc_title", toc_title_default))

        # Safely escape all label entries
        labels_entries: List[str] = []
        for k, v in labels.items():
            k_clean = typst_string(str(k).replace("-", "_"))
            labels_entries.append(f'    "{k_clean}": "{typst_string(v)}",')
        labels_str = "\n".join(labels_entries)

        # Saemtliche Dokumentangaben -- Kernfelder wie freie -- gehen als ein
        # Woerterbuch an das Theme. Nicht zusaetzlich als Einzelparameter: zwei
        # Wege zur selben Angabe koennen auseinanderlaufen, und jedes neue Feld
        # muesste sonst wieder entscheiden, ob es auch einen Parameter bekommt.
        meta_entries = build_document_metadata(doc, labels)
        metadata_lines: List[str] = []
        for k, entry in meta_entries.items():
            k_clean = typst_string(str(k).replace("-", "_"))
            lbl_escaped = f'"{typst_string(entry.label)}"' if entry.label else "none"
            metadata_lines.append(
                f'    "{k_clean}": (key: "{k_clean}", label: {lbl_escaped}, '
                f"value: {typst_value(entry.value)}),"
            )
        metadata_str = "\n".join(metadata_lines)

        parts: List[str] = [
            '#import "template.typ": *',
            "",
            "#show: doc => setup-document(",
            f'  language: "{lang_code}",',
            f'  show-cover: {str(doc.cover).lower()},',
            f'  show-toc: {str(doc.document_toc.enabled).lower()},',
            f'  toc-title: "{toc_title_esc}",',
            f'  toc-depth: {doc.document_toc.max_depth or 3},',
            f'  show-header: {str(show_header).lower()},',
            f'  show-footer: {str(show_footer).lower()},',
            "  meta: (",
            f"{metadata_str}",
            "  ),",
            "  labels: (",
            f"{labels_str}",
            "  ),",
            "  doc,",
            ")",
            "",
        ]

        link_targets = self._collect_link_targets(context)

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
                    part_title_esc = typst_string(getattr(item, "divider_title", None) or getattr(item, "display_title", None) or item.title)
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
                        part_heading_title = typst_string(getattr(item, "toc_title", None) or getattr(item, "display_title", None) or item.title)
                        parts.append(f'#heading(level: 1, outlined: true, numbering: none)[{part_heading_title}] <part-entry>\n')

                if getattr(item, "pagenum_reset", False):
                    parts.append("#counter(page).update(1)\n")
            else:
                ch_typst, has_content = self._render_chapter(
                    item, labels, build_dir, has_content,
                    lang_code=lang_code, link_targets=link_targets,
                )
                parts.append(ch_typst)

        return "\n".join(parts)

    @staticmethod
    def _collect_link_targets(context: DocumentContext) -> Set[str]:
        """
        Alle Marken, die im fertigen Dokument als Sprungziel existieren.

        Gebraucht fuer Anker im Markdown (`[Text](#slug)`): nur ein Ziel, das
        es wirklich gibt, darf als `label()` gesetzt werden -- eine Marke ohne
        Fundstelle bricht die Typst-Kompilierung ab.

        Zwei Quellen, weil es zwei Arten von Marken gibt: die Ueberschriften
        aus den Kapiteln setzt der Serializer aus ihrer `id`, die Marken fuer
        Teile und Kapitel stehen an den Trennseiten und im Verzeichnisbaum.
        """
        targets: Set[str] = set()

        def walk(nodes: Any) -> None:
            for node in nodes or []:
                slug = getattr(node, "slug", None)
                if slug:
                    targets.add(slug)
                walk(getattr(node, "children", None))

        walk(context.toc_tree)

        for item in context.content_items:
            slug = getattr(item, "slug", None)
            if slug:
                targets.add(slug)

            tree = getattr(item, "element_tree", None)
            if tree is None:
                continue
            for level in range(1, 7):
                for heading in tree.iter("h" + str(level)):
                    heading_id = heading.attrib.get("id")
                    if heading_id:
                        targets.add(heading_id)

        return targets

    def _render_chapter(
        self,
        chapter_item: Any,
        labels: Any,
        build_dir: Path,
        has_content: bool,
        lang_code: str = "de",
        link_targets: Optional[Set[str]] = None,
    ) -> Tuple[str, bool]:
        """Renders an individual chapter item into Typst markup."""
        res: List[str] = []

        bb_val = chapter_item.break_before.value if getattr(chapter_item, "break_before", None) else "page"

        has_file_h1 = getattr(chapter_item, "has_h1", False)
        show_title = getattr(chapter_item, "show_title", True)
        needs_synth = getattr(chapter_item, "needs_synthetic_toc_heading", False)

        def _synthetic_heading() -> str:
            t_esc = typst_string(getattr(chapter_item, "toc_title", None) or chapter_item.display_title)
            num_prefix = getattr(chapter_item, "number_prefix", None)
            ch_slug = getattr(chapter_item, "slug", "")
            lbl_str = f" <{ch_slug}>" if (ch_slug and (not has_file_h1 or not show_title)) else ""
            if num_prefix:
                num_esc = typst_string(num_prefix)
                return f'#place(top + left)[#hide[#heading(level: 1, outlined: true, numbering: (..nums) => "{num_esc}")[{t_esc}]{lbl_str}]]\n'
            else:
                return f'#place(top + left)[#hide[#heading(level: 1, outlined: true, numbering: none)[{t_esc}]{lbl_str}]]\n'

        synth_placed_on_divider = False
        if bb_val == "divider":
            if has_content:
                res.append("#pagebreak()\n")
            if needs_synth and (not has_file_h1 or not show_title):
                res.append(_synthetic_heading())
                synth_placed_on_divider = True
            tag_label = labels.get("chapter", "Chapter" if lang_code == "en" else "Kapitel")
            num_prefix = getattr(chapter_item, "number_prefix", None)
            full_tag = typst_string(f"{tag_label} {num_prefix}".strip() if num_prefix else tag_label)
            summary_esc = typst_string(chapter_item.summary or "")
            ch_title_esc = typst_string(getattr(chapter_item, "divider_title", None) or chapter_item.display_title)
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

        if needs_synth and not synth_placed_on_divider:
            res.append(_synthetic_heading())

        images_dir = build_dir / "images"
        element_tree = getattr(chapter_item, "element_tree", None)
        file_base_dir = getattr(chapter_item, "file_base_dir", None)
        if element_tree is not None:
            serializer = TypstSerializer(
                file_base_dir=file_base_dir,
                images_dir=images_dir,
                labels=labels,
                allowed_toc_slugs=getattr(chapter_item, "allowed_toc_slugs", None),
                known_labels=link_targets,
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
                    serializer = TypstSerializer(
                        file_base_dir=file_base_dir,
                        images_dir=images_dir,
                        labels=labels,
                    )
                    ch_typst = serializer.serialize(tree)
                    if ch_typst.strip():
                        res.append(ch_typst)
                        has_content = True

        res.append("\n")
        return "\n".join(res), has_content

