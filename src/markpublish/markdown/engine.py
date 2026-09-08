"""
Markdown parsing and compilation engine for markpublish.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

import markdown

from markpublish.config.models import (
    AutonumStyle,
    BreakBefore,
    ChapterItem,
    ConfigurationError,
    MarkpublishConfig,
    TocScope,
)
from markpublish.markdown.alerts import GitHubAlertsExtension
from markpublish.markdown.toc import (
    NumberingContext,
    TOCNode,
)
from markpublish.markdown.typst_serializer import (
    TypstSerializer,
    html_to_tree,
    process_tree_headings_and_toc,
)
from markpublish.ui import t

#: Namen der String-Extensions. Der GitHubAlertsExtension wird pro Sprache
#: instanziiert und deshalb erst in _build_default_extensions() vorangestellt --
#: eine Liste, damit Aenderungen nicht an zwei Stellen gepflegt werden muessen.
DEFAULT_EXTENSION_NAMES = [
    "tables",
    "admonition",
    "def_list",
    "attr_list",
    "footnotes",
    "sane_lists",
    "smarty",
    "pymdownx.superfences",
    "pymdownx.highlight",
    "pymdownx.inlinehilite",
    "pymdownx.magiclink",
    "pymdownx.tasklist",
    "pymdownx.tilde",
    "pymdownx.caret",
    "pymdownx.smartsymbols",
    "pymdownx.arithmatex",
]

DEFAULT_EXTENSION_CONFIGS = {
    "pymdownx.arithmatex": {
        "generic": True,
    },
    "pymdownx.highlight": {
        # Typst verfuegt ueber eine eigene, hochqualitative Syntax-Highlighting-Engine.
        # use_pygments=False uebergibt die Sprachklasse (z.B. language-yaml) an Typst.
        "use_pygments": False,
    },
    "pymdownx.tasklist": {
        "custom_checkbox": True,
    },
    "pymdownx.superfences": {
        "custom_fences": []
    },
}


class MarkdownEngine:
    """Handles Markdown to HTML conversion with rich PyMdown extensions."""

    def __init__(
        self,
        language: str = "de",
        extensions: Optional[List[Any]] = None,
        extension_configs: Optional[Dict[str, Any]] = None,
        labels: Optional[Mapping[str, str]] = None,
    ):
        self.language = language
        self.labels = labels
        # `is None` statt `or`: ein bewusst leeres extensions=[] soll leer
        # bleiben und nicht stillschweigend auf die Defaults zurueckfallen.
        self.extensions = (
            self._build_default_extensions(language, labels) if extensions is None else extensions
        )
        self.extension_configs = (
            DEFAULT_EXTENSION_CONFIGS if extension_configs is None else extension_configs
        )

    @staticmethod
    def _build_default_extensions(
        language: str = "de",
        labels: Optional[Mapping[str, str]] = None,
    ) -> List[Any]:
        return [
            GitHubAlertsExtension(language=language, labels=labels or {}),
            *DEFAULT_EXTENSION_NAMES,
        ]

    def create_markdown_instance(self) -> markdown.Markdown:
        return markdown.Markdown(
            extensions=self.extensions,
            extension_configs=self.extension_configs,
            output_format="html5",
        )

    def convert(self, md_text: str) -> str:
        md = self.create_markdown_instance()
        return md.convert(md_text)


class ContentItem:
    """Prepared content node for rendering in templates."""

    def __init__(
        self,
        title: str,
        display_title: str,
        slug: str,
        is_part: bool = False,
        subtitle: Optional[str] = None,
        summary: Optional[str] = None,
        break_before: BreakBefore = BreakBefore.PAGE,
        number_prefix: Optional[str] = None,
        html_content: str = "",
        chapter_toc: Any = False,
        part_toc: Any = False,
        pagenum_reset: bool = False,
        local_toc_items: Optional[List[TOCNode]] = None,
        raw_markdown: str = "",
        document_toc: Any = None,
        typst_content: str = "",
        element_tree: Any = None,
        file_base_dir: Optional[Path] = None,
        toc_title: Optional[str] = None,
        divider_title: Optional[str] = None,
        has_h1: bool = False,
        show_title: bool = True,
    ):
        self.title = title
        self.display_title = display_title
        self.slug = slug
        self.is_part = is_part
        self.subtitle = subtitle
        self.summary = summary
        self.break_before = break_before
        self.number_prefix = number_prefix
        self.html_content = html_content
        self.chapter_toc = chapter_toc
        self.part_toc = part_toc
        self.pagenum_reset = pagenum_reset
        self.local_toc_items = local_toc_items or []
        self.raw_markdown = raw_markdown
        self.document_toc = document_toc
        self.typst_content = typst_content
        self.element_tree = element_tree
        self.file_base_dir = file_base_dir
        self.toc_title = toc_title
        self.divider_title = divider_title
        self.has_h1 = has_h1
        self.show_title = show_title
        self.children: List[ContentItem] = []

    @property
    def has_divider_page(self) -> bool:
        """True, wenn dem Kapitel eine eigene Trennseite vorangeht."""
        return self.break_before == BreakBefore.DIVIDER

    @property
    def starts_new_page(self) -> bool:
        """True, wenn das Kapitel oben auf einer Seite beginnt."""
        return self.break_before != BreakBefore.NONE


def _resolve_autonum_style(value: Any) -> Optional[AutonumStyle]:
    """Bringt eine autonum_style-Angabe auf den Enum-Wert; None heisst 'nicht gesetzt'."""
    if value is None:
        return None
    if isinstance(value, AutonumStyle):
        return value
    val_str = str(value).lower().strip()
    for item in AutonumStyle:
        if item.value == val_str:
            return item
    return None


_resolve_autonum = _resolve_autonum_style


def _document_toc_enabled(scope: Optional[TocScope]) -> bool:
    """Nicht gesetzt heisst voll dabei; sonst entscheidet der Wert."""
    return True if scope is None else bool(scope.enabled)


def build_toc_tree(flat_nodes: List[TOCNode]) -> List[TOCNode]:
    """Builds a hierarchical tree from a flat list of TOC nodes."""
    root_nodes: List[TOCNode] = []
    stack: List[TOCNode] = []

    for node in flat_nodes:
        while stack and stack[-1].level >= node.level:
            stack.pop()

        if not stack:
            root_nodes.append(node)
        else:
            stack[-1].children.append(node)

        stack.append(node)

    return root_nodes


class MarkdownPipeline:
    """Orchestrates parsing of the full document configuration into render-ready objects."""

    def __init__(
        self,
        config: MarkpublishConfig,
        base_dir: Path,
        labels: Optional[Mapping[str, str]] = None,
    ):
        self.config = config
        self.base_dir = base_dir
        self.labels = labels or {}
        lang = config.document.language if (config and getattr(config, "document", None)) else "de"
        autonum_style = config.document.autonum_style if (config and getattr(config, "document", None)) else None
        self.engine = MarkdownEngine(language=lang, labels=labels)
        self.numbering_ctx = NumberingContext(default_autonum_style=autonum_style)

    def _build_local_toc(self, chapter_cfg: ChapterItem) -> List[TOCNode]:
        item, _ = self._process_chapter(chapter_cfg)
        return item.local_toc_items

    def process_document(self) -> Tuple[List[ContentItem], List[TOCNode]]:
        """
        Parses all parts and chapters, builds content items and global TOC tree.
        """
        content_items: List[ContentItem] = []
        global_toc_tree: List[TOCNode] = []

        document_toc_root = self.config.document.document_toc
        part_toc_root = self.config.document.part_toc
        chapter_toc_root = self.config.document.chapter_toc
        autonum_style_root = self.config.document.autonum_style

        for part_cfg in self.config.parts:
            part_toc_children: List[TOCNode] = []
            part_title = part_cfg.display_title
            part_slug = self.numbering_ctx.unique_slug(part_title)

            effective_part_toc = (
                part_cfg.part_toc
                if part_cfg.part_toc is not None
                else part_toc_root
            )
            effective_part_pagenum_reset = (
                part_cfg.pagenum_reset
                if part_cfg.pagenum_reset is not None
                else self.config.document.pagenum_reset
            )
            part_item: Optional[ContentItem] = None
            if part_cfg.effective_break_before != BreakBefore.NONE:
                part_item = ContentItem(
                    title=part_title,
                    display_title=part_title,
                    slug=part_slug,
                    is_part=True,
                    subtitle=part_cfg.subtitle,
                    summary=part_cfg.summary,
                    break_before=part_cfg.effective_break_before,
                    number_prefix=None,
                    html_content="",
                    part_toc=effective_part_toc if (effective_part_toc and effective_part_toc.enabled) else None,
                    pagenum_reset=effective_part_pagenum_reset,
                    document_toc=part_cfg.document_toc,
                    toc_title=part_cfg.toc_title,
                    divider_title=part_cfg.divider_title,
                )
                content_items.append(part_item)

            part_in_document_toc = True
            if part_cfg.document_toc is not None:
                if not part_cfg.document_toc.enabled:
                    part_in_document_toc = False
                    inherited_document_toc = document_toc_root
                else:
                    inherited_document_toc = part_cfg.document_toc
            else:
                inherited_document_toc = document_toc_root

            inherited_chapter_toc = (
                part_cfg.chapter_toc
                if part_cfg.chapter_toc is not None
                else chapter_toc_root
            )
            inherited_autonum = _resolve_autonum_style(part_cfg.autonum_style) or autonum_style_root
            inherited_autonum_from_level = part_cfg.autonum_from_level
            inherited_autonum_prefix = part_cfg.autonum_prefix
            inherited_autonum_reset = part_cfg.autonum_reset
            inherited_pagenum_reset = effective_part_pagenum_reset

            for ch_cfg in part_cfg.chapters:
                ch_item, ch_toc_nodes = self._process_chapter(
                    ch_cfg,
                    inherited_document_toc=inherited_document_toc,
                    inherited_part_toc=effective_part_toc,
                    inherited_chapter_toc=inherited_chapter_toc,
                    inherited_autonum=inherited_autonum,
                    inherited_autonum_from_level=inherited_autonum_from_level,
                    inherited_autonum_prefix=inherited_autonum_prefix,
                    inherited_autonum_reset=inherited_autonum_reset,
                    inherited_pagenum_reset=inherited_pagenum_reset,
                )
                content_items.append(ch_item)
                if part_in_document_toc:
                    part_toc_children.extend(ch_toc_nodes)
                else:
                    global_toc_tree.extend(build_toc_tree(ch_toc_nodes))

            if part_item and effective_part_toc and effective_part_toc.enabled:
                if effective_part_toc.max_depth is None:
                    part_item.local_toc_items = list(part_toc_children)
                else:
                    part_item.local_toc_items = [
                        n for n in part_toc_children if n.level <= effective_part_toc.max_depth
                    ]

            if part_in_document_toc and _document_toc_enabled(inherited_document_toc):
                part_tree = build_toc_tree(part_toc_children)
                part_node = TOCNode(
                    title=part_title,
                    slug=part_slug,
                    level=1,
                    number=None,
                    is_part=True,
                    summary=part_cfg.summary,
                )
                part_node.children = part_tree
                global_toc_tree.append(part_node)

        return content_items, global_toc_tree

    def _process_chapter(
        self,
        chapter_cfg: ChapterItem,
        inherited_document_toc: Optional[TocScope] = None,
        inherited_part_toc: Optional[TocScope] = None,
        inherited_chapter_toc: Optional[TocScope] = None,
        inherited_autonum: Optional[AutonumStyle] = None,
        inherited_autonum_from_level: Optional[int] = None,
        inherited_autonum_prefix: Optional[str] = None,
        inherited_autonum_reset: Optional[bool] = None,
        inherited_pagenum_reset: bool = False,
    ) -> Tuple[ContentItem, List[TOCNode]]:
        if isinstance(chapter_cfg, dict):
            chapter_cfg = ChapterItem(**chapter_cfg)

        raw_md = ""
        file_base_dir = self.base_dir

        # 1. Read the chapter file
        subtitle = chapter_cfg.subtitle
        summary = chapter_cfg.summary
        break_before = chapter_cfg.break_before

        chapter_toc = (
            chapter_cfg.chapter_toc
            if chapter_cfg.chapter_toc is not None
            else inherited_chapter_toc
        )

        effective_document_toc = (
            chapter_cfg.document_toc
            if chapter_cfg.document_toc is not None
            else inherited_document_toc
        )

        effective_pagenum_reset = (
            chapter_cfg.pagenum_reset
            if chapter_cfg.pagenum_reset is not None
            else inherited_pagenum_reset
        )

        if chapter_cfg.file:
            file_path = (self.base_dir / chapter_cfg.file).resolve()
            if file_path.is_file():
                file_base_dir = file_path.parent
                raw_md = file_path.read_text(encoding="utf-8")

        autonum_override = _resolve_autonum_style(chapter_cfg.autonum_style) or inherited_autonum
        doc_cfg = self.config.document if (self.config and getattr(self.config, "document", None)) else None

        effective_from_level = (
            chapter_cfg.autonum_from_level
            if chapter_cfg.autonum_from_level is not None
            else (
                inherited_autonum_from_level
                if inherited_autonum_from_level is not None
                else (doc_cfg.autonum_from_level if doc_cfg else 1)
            )
        )
        effective_prefix = (
            chapter_cfg.autonum_prefix
            if chapter_cfg.autonum_prefix is not None
            else (
                inherited_autonum_prefix
                if inherited_autonum_prefix is not None
                else (doc_cfg.autonum_prefix if doc_cfg else None)
            )
        )
        effective_reset = (
            chapter_cfg.autonum_reset
            if chapter_cfg.autonum_reset is not None
            else (
                inherited_autonum_reset
                if inherited_autonum_reset is not None
                else (True if effective_from_level > 1 else (doc_cfg.autonum_reset if doc_cfg else False))
            )
        )

        # Wenn Reset gewuenscht (oder from_level > 1, z. B. bei Anhaengen):
        # Der Zaehler startet fuer dieses Kapitel isoliert wieder bei 0.
        if effective_reset:
            self.numbering_ctx.reset_counters()

        # Convert markdown to HTML via python-markdown (all extensions active)
        raw_html = self.engine.convert(raw_md) if raw_md else ""

        # Parse HTML into ElementTree and process headings / numbering directly in the AST
        tree = html_to_tree(raw_html)

        # Pruefe vorab, ob die Datei mit einer H1 (Level 1) beginnt
        import re
        has_file_h1 = False
        if raw_md:
            for elem in tree.iter():
                m = re.match(r"^h([1-6])$", elem.tag.lower())
                if m:
                    has_file_h1 = (int(m.group(1)) == 1)
                    break

        chapter_number: Optional[str] = None
        if not has_file_h1 and chapter_cfg.toc_title:
            chapter_number = self.numbering_ctx.advance_counter(
                1,
                autonum_override,
                from_level=effective_from_level,
                prefix=effective_prefix,
            )

        toc_nodes = process_tree_headings_and_toc(
            tree,
            self.numbering_ctx,
            autonum_override=autonum_override,
            autonum_from_level=effective_from_level,
            autonum_prefix=effective_prefix,
        )

        file_h1 = (
            toc_nodes[0].title
            if (toc_nodes and toc_nodes[0].level == 1)
            else None
        )
        effective_toc_title = chapter_cfg.toc_title or file_h1
        effective_divider_title = chapter_cfg.divider_title or file_h1

        file_desc = (
            t("chapter.desc.in_file", file=chapter_cfg.file)
            if chapter_cfg.file
            else t("chapter.desc.no_file")
        )

        # Validierung 1: Trennseite verlangt
        if break_before == BreakBefore.DIVIDER and not effective_divider_title:
            raise ConfigurationError(
                t("err.chapter.no_divider_title", file=file_desc)
            )

        # Validierung 2: Inhaltsverzeichnis (Haupt-TOC oder Part-TOC) verlangt
        in_doc_toc = _document_toc_enabled(effective_document_toc)
        in_part_toc = bool(inherited_part_toc and _document_toc_enabled(inherited_part_toc))
        if (in_doc_toc or in_part_toc) and not effective_toc_title:
            raise ConfigurationError(
                t("err.chapter.no_toc_title", file=file_desc)
            )

        display_title = effective_toc_title or effective_divider_title or "Chapter"
        slug = (
            toc_nodes[0].slug
            if (toc_nodes and toc_nodes[0].level == 1)
            else self.numbering_ctx.unique_slug(display_title)
        )
        number_prefix = (
            toc_nodes[0].number
            if (toc_nodes and toc_nodes[0].level == 1)
            else chapter_number
        )

        # Wenn die Datei keine H1 besitzt, aber ins TOC soll:
        # Fuege einen synthetischen TOCNode fuer das Kapitel an den Anfang
        if not file_h1 and effective_toc_title and (in_doc_toc or in_part_toc):
            synthetic_node = TOCNode(
                title=effective_toc_title,
                slug=slug,
                level=1,
                number=chapter_number,
                summary=summary,
            )
            toc_nodes.insert(0, synthetic_node)
            number_prefix = chapter_number
        elif file_h1 and chapter_cfg.toc_title:
            # Datei-H1 existiert, aber toc_title weicht ab:
            # Im TOCNode steht der toc_title!
            toc_nodes[0].title = chapter_cfg.toc_title

        # Filter local TOC items if enabled.
        local_toc_items: List[TOCNode] = []
        if chapter_toc:
            chapter_level = 1
            if chapter_toc.max_depth is None:
                local_toc_items = [n for n in toc_nodes if n.level > chapter_level]
            else:
                local_toc_items = [
                    n for n in toc_nodes
                    if chapter_level < n.level <= chapter_level + chapter_toc.max_depth - 1
                ]

        # Beitrag zum Dokumentverzeichnis kuerzen
        if effective_document_toc is None or effective_document_toc.max_depth is None:
            global_toc_nodes = list(toc_nodes) if _document_toc_enabled(effective_document_toc) else []
        elif not effective_document_toc.enabled:
            global_toc_nodes = []
        else:
            max_level = effective_document_toc.max_depth
            global_toc_nodes = [n for n in toc_nodes if n.level <= max_level]

        # Wenn show_title False ist und die Datei eine H1 besitzt:
        # Entferne das erste h1-Element aus dem ElementTree, damit es nicht im Text gerendert wird.
        if file_h1 and not chapter_cfg.show_title:
            for parent in tree.iter():
                for child in list(parent):
                    if child.tag.lower() == "h1":
                        parent.remove(child)
                        break
                else:
                    continue
                break

        # Wenn chapter_cfg.toc_title gesetzt ist und von file_h1 abweicht,
        # soll die H1 im Text nicht als Outlined-Heading gerendert werden (sondern ueber
        # das separate hidden TOC-Heading im Renderer).
        allowed_toc_slugs = {n.slug for n in global_toc_nodes} if toc_nodes else None
        if chapter_cfg.toc_title and file_h1 and allowed_toc_slugs:
            allowed_toc_slugs = {s for s in allowed_toc_slugs if s != slug}

        # Convert ElementTree to Typst markup using the clean AST serializer
        serializer = TypstSerializer(
            file_base_dir=file_base_dir,
            labels=self.labels,
            allowed_toc_slugs=allowed_toc_slugs,
        )
        typst_content = serializer.serialize(tree) if raw_md else ""

        # Produce enhanced HTML for html_content
        import xml.etree.ElementTree as etree
        processed_html = "".join(etree.tostring(child, encoding="unicode", method="html") for child in tree) if raw_md else ""

        item = ContentItem(
            title=display_title,
            display_title=display_title,
            slug=slug,
            is_part=False,
            subtitle=subtitle,
            summary=summary,
            break_before=break_before,
            number_prefix=number_prefix,
            html_content=processed_html,
            chapter_toc=chapter_toc,
            part_toc=False,
            pagenum_reset=effective_pagenum_reset,
            local_toc_items=local_toc_items,
            raw_markdown=raw_md,
            document_toc=effective_document_toc,
            typst_content=typst_content,
            element_tree=tree,
            file_base_dir=file_base_dir,
            toc_title=effective_toc_title,
            divider_title=effective_divider_title,
            has_h1=bool(file_h1),
            show_title=chapter_cfg.show_title,
        )

        item.needs_synthetic_toc_heading = bool(
            in_doc_toc and effective_toc_title and (not file_h1 or bool(chapter_cfg.toc_title) or not chapter_cfg.show_title)
        )
        item.allowed_toc_slugs = allowed_toc_slugs

        return item, global_toc_nodes

