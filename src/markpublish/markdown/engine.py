"""
Markdown parsing and compilation engine for markpublish.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

import frontmatter
import markdown

from markpublish.config.models import (
    AutonumType,
    BreakBefore,
    ChapterItem,
    MarkpublishConfig,
    TocScope,
)
from markpublish.markdown.alerts import GitHubAlertsExtension
from markpublish.markdown.assets import rewrite_html_asset_paths
from markpublish.markdown.toc import (
    NumberingContext,
    TOCNode,
    process_html_headings_and_toc,
)

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
]

DEFAULT_EXTENSION_CONFIGS = {
    "pymdownx.highlight": {
        "use_pygments": True,
        # Mit noclasses=False gibt Pygments CSS-Klassen aus; die Farben stehen
        # dann im Theme-Stylesheet (.highlight .k usw.), nicht hier. Ein
        # pygments_style waere an dieser Stelle wirkungslos.
        "noclasses": False,
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
        summary: Optional[str] = None,
        break_before: BreakBefore = BreakBefore.PAGE,
        number_prefix: Optional[str] = None,
        html_content: str = "",
        chapter_toc: Any = False,
        local_toc_items: Optional[List[TOCNode]] = None,
    ):
        self.title = title
        self.display_title = display_title
        self.slug = slug
        self.is_part = is_part
        self.summary = summary
        self.break_before = break_before
        self.number_prefix = number_prefix
        self.html_content = html_content
        self.chapter_toc = chapter_toc
        self.local_toc_items = local_toc_items or []
        self.children: List[ContentItem] = []

    @property
    def has_divider_page(self) -> bool:
        """True, wenn dem Kapitel eine eigene Trennseite vorangeht."""
        return self.break_before == BreakBefore.DIVIDER

    @property
    def starts_new_page(self) -> bool:
        """True, wenn das Kapitel oben auf einer Seite beginnt."""
        return self.break_before != BreakBefore.NONE


def _resolve_autonum(value: Any) -> Optional[AutonumType]:
    """Bringt eine autonum-Angabe auf den Enum-Wert; None heisst 'nicht gesetzt'."""
    if not value:
        return None
    if isinstance(value, AutonumType):
        return value
    wanted = str(value).lower().strip()
    for candidate in AutonumType:
        if candidate.value == wanted:
            return candidate
    return None


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
        # Die Labels haengen am Zielformat (Ebene 3), deshalb kommen sie von
        # aussen herein statt hier gebaut zu werden - die Pipeline laeuft pro
        # Zielformat.
        self.engine = MarkdownEngine(language=config.document.language, labels=labels)
        self.numbering_ctx = NumberingContext(default_autonum_type=config.document.autonum_type)

    def process_document(self) -> Tuple[List[ContentItem], List[TOCNode]]:
        """
        Parses all chapters and parts, builds content items and global TOC tree.
        """
        content_items: List[ContentItem] = []
        all_toc_nodes: List[TOCNode] = []

        # Die Vorgabe aus dem document-Block steht am Anfang jeder Vererbungs-
        # kette. 'none' laesst das Verzeichnis ohnehin weg; jeder andere Wert
        # gibt die Tiefe vor, von der Kapitel und Parts abweichen duerfen.
        document_toc_root = self.config.document.document_toc

        for item_cfg in self.config.chapters:
            if item_cfg.is_part:
                # Part container
                part_title = item_cfg.part or item_cfg.title or "Part"
                part_slug = self.numbering_ctx.unique_slug(part_title)

                part_item = ContentItem(
                    title=part_title,
                    display_title=part_title,
                    slug=part_slug,
                    is_part=True,
                    summary=item_cfg.summary,
                    break_before=item_cfg.break_before,
                    number_prefix=None,
                    html_content="",
                )

                part_toc_node = TOCNode(
                    title=part_title,
                    slug=part_slug,
                    level=1,
                    number=None,
                    is_part=True,
                    summary=item_cfg.summary,
                )
                all_toc_nodes.append(part_toc_node)

                # Process child chapters in part
                for child_cfg in item_cfg.chapters:
                    child_item, child_toc_nodes = self._process_chapter(
                        child_cfg,
                        base_level=2,
                        inherited_document_toc=(
                            item_cfg.document_toc
                            if item_cfg.document_toc is not None
                            else document_toc_root
                        ),
                        inherited_autonum=_resolve_autonum(item_cfg.autonum),
                    )
                    part_item.children.append(child_item)

                    # In dieselbe flache Liste wie alle anderen Kapitel, statt
                    # von Hand an den Part-Knoten gehaengt: build_toc_tree
                    # verschachtelt anschliessend nach Ebene. Haengte man sie
                    # direkt an, laegen im Inhaltsverzeichnis saemtliche
                    # Zwischenueberschriften des Anhangs auf einer Hoehe mit den
                    # Kapiteltiteln - der Part-Knoten steht auf Ebene 1, seine
                    # Kapitel auf Ebene 2, die Verschachtelung ergibt sich also
                    # von selbst.
                    all_toc_nodes.extend(child_toc_nodes)

                content_items.append(part_item)

            else:
                # Regular top-level chapter
                chapter_item, chapter_toc_nodes = self._process_chapter(
                    item_cfg,
                    base_level=1,
                    inherited_document_toc=document_toc_root,
                )
                content_items.append(chapter_item)
                all_toc_nodes.extend(chapter_toc_nodes)

        global_toc_tree = build_toc_tree(all_toc_nodes)
        return content_items, global_toc_tree

    def _process_chapter(
        self,
        chapter_cfg: ChapterItem,
        base_level: int = 1,
        inherited_document_toc: Optional[TocScope] = None,
        inherited_autonum: Optional[AutonumType] = None,
    ) -> Tuple[ContentItem, List[TOCNode]]:
        raw_md = ""
        file_base_dir = self.base_dir

        # 1. Read file and extract frontmatter
        title = chapter_cfg.title
        summary = chapter_cfg.summary
        break_before = chapter_cfg.break_before

        # Nicht gesetzt heisst: die Vorgabe aus dem document-Block gilt. Anders
        # als document_toc wird der Wert nicht vom Elternkapitel geerbt - er
        # beschreibt eine Trennseite, und die hat jedes Kapitel fuer sich.
        chapter_toc = (
            chapter_cfg.chapter_toc
            if chapter_cfg.chapter_toc is not None
            else self.config.document.chapter_toc
        )

        # Ein Part gibt seinen document_toc an alle Kapitel darunter weiter, ein
        # Kapitel an seine Unterkapitel. So genuegt eine Zeile am Anhang-Part, um
        # den gesamten Anhang im Dokumentverzeichnis flach zu halten. Ein
        # Kapitel, das selbst etwas sagt, schlaegt das Geerbte - auch zurueck auf
        # 'full', wofuer es das Schluesselwort ueberhaupt gibt.
        effective_document_toc = (
            chapter_cfg.document_toc
            if chapter_cfg.document_toc is not None
            else inherited_document_toc
        )

        if chapter_cfg.file:
            file_path = (self.base_dir / chapter_cfg.file).resolve()
            if file_path.is_file():
                file_base_dir = file_path.parent
                with open(file_path, "r", encoding="utf-8") as f:
                    post = frontmatter.load(f)
                    raw_md = post.content
                    if "title" in post.metadata and not title:
                        title = str(post.metadata["title"])
                    if "summary" in post.metadata and not summary:
                        summary = str(post.metadata["summary"])
                    if "break_before" in post.metadata:
                        break_before = BreakBefore(str(post.metadata["break_before"]).lower().strip())

        # Nummerierung: was das Kapitel selbst sagt, sonst das Geerbte. Ein
        # Part mit autonum: "none" nimmt damit seinen gesamten Anhang aus der
        # Zaehlung - ohne Vererbung bliebe die Angabe am Part wirkungslos, weil
        # die Ueberschriften in den Kapiteldateien stehen, nicht im Part.
        autonum_override = _resolve_autonum(chapter_cfg.autonum) or inherited_autonum

        # Convert markdown to HTML
        raw_html = self.engine.convert(raw_md) if raw_md else ""

        # Rewrite asset paths
        asset_html = rewrite_html_asset_paths(raw_html, file_base_dir)

        # Process headings, numbering, and extract TOC
        processed_html, toc_nodes = process_html_headings_and_toc(
            asset_html,
            self.numbering_ctx,
            autonum_override=autonum_override,
            base_level_offset=base_level - 1,
        )

        display_title = title or (toc_nodes[0].title if toc_nodes else "Chapter")
        slug = toc_nodes[0].slug if toc_nodes else self.numbering_ctx.unique_slug(display_title)
        number_prefix = toc_nodes[0].number if toc_nodes else None

        # Filter local TOC items if enabled.
        # Tiefe wird innerhalb des Kapitels gezaehlt: die Kapitelueberschrift
        # ist Tiefe 1, ihre h2 Tiefe 2 usw. `toc: 2` liefert also die h2-Ebene.
        # n.level ist dagegen absolut (enthaelt base_level_offset), deshalb die
        # Umrechnung ueber chapter_level -- so bedeutet `toc: 2` dasselbe, egal
        # wie tief das Kapitel selbst haengt.
        # Tiefe 1 bleibt draussen: die eigene Ueberschrift steht auf der
        # Trennseite bereits als Titel darueber.
        local_toc_items: List[TOCNode] = []
        if chapter_toc:
            chapter_level = base_level
            if chapter_toc.max_depth is None:
                local_toc_items = [n for n in toc_nodes if n.level > chapter_level]
            else:
                local_toc_items = [
                    n for n in toc_nodes
                    if chapter_level < n.level <= chapter_level + chapter_toc.max_depth - 1
                ]

        item = ContentItem(
            title=display_title,
            display_title=display_title,
            slug=slug,
            is_part=False,
            summary=summary,
            break_before=break_before,
            number_prefix=number_prefix,
            html_content=processed_html,
            chapter_toc=chapter_toc,
            local_toc_items=local_toc_items,
        )

        # Beitrag zum Dokumentverzeichnis kuerzen. Gefiltert wird nur ueber die
        # eigenen Ueberschriften - die Kinder haben ihren eigenen document_toc
        # bereits angewandt, jeweils relativ zu sich selbst. Wuerde man ueber die
        # zusammengelegte Liste filtern, fiele mit `document_toc: 1` auch jedes
        # Unterkapitel weg, statt nur dessen Zwischenueberschriften.
        if effective_document_toc is None or effective_document_toc.max_depth is None:
            # Nicht gesetzt oder 'full' - beides heisst: jede Ebene.
            global_toc_nodes = list(toc_nodes) if _document_toc_enabled(effective_document_toc) else []
        elif not effective_document_toc.enabled:
            global_toc_nodes = []
        else:
            max_level = base_level + effective_document_toc.max_depth - 1
            global_toc_nodes = [n for n in toc_nodes if n.level <= max_level]

        # Process recursive child chapters
        for sub_child in chapter_cfg.chapters:
            sub_item, sub_tocs = self._process_chapter(
                sub_child,
                base_level=base_level + 1,
                inherited_document_toc=effective_document_toc,
                inherited_autonum=autonum_override,
            )
            item.children.append(sub_item)
            global_toc_nodes.extend(sub_tocs)

        return item, global_toc_nodes

