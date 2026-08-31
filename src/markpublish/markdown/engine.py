"""
Markdown parsing and compilation engine for markpublish.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import frontmatter
import markdown

from markpublish.config.models import AutonumType, ChapterItem, MarkpublishConfig
from markpublish.markdown.alerts import GitHubAlertsExtension
from markpublish.markdown.assets import rewrite_html_asset_paths
from markpublish.markdown.toc import (
    NumberingContext,
    TOCNode,
    process_html_headings_and_toc,
)


DEFAULT_MARKDOWN_EXTENSIONS = [
    GitHubAlertsExtension(),
    "tables",
    "admonition",
    "def_list",
    "attr_list",
    "footnotes",
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
        "noclasses": False,
        "pygments_style": "github-dark",
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
        extension_configs: Optional[Dict[str, Any]] = None
    ):
        self.language = language
        self.extensions = extensions or self._build_default_extensions(language)
        self.extension_configs = extension_configs or DEFAULT_EXTENSION_CONFIGS

    @staticmethod
    def _build_default_extensions(language: str = "de") -> List[Any]:
        return [
            GitHubAlertsExtension(language=language),
            "tables",
            "admonition",
            "def_list",
            "attr_list",
            "footnotes",
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
        divider_page: bool = False,
        number_prefix: Optional[str] = None,
        html_content: str = "",
        toc_config: Any = False,
        local_toc_items: Optional[List[TOCNode]] = None,
    ):
        self.title = title
        self.display_title = display_title
        self.slug = slug
        self.is_part = is_part
        self.summary = summary
        self.divider_page = divider_page
        self.number_prefix = number_prefix
        self.html_content = html_content
        self.toc = toc_config
        self.local_toc_items = local_toc_items or []
        self.children: List[ContentItem] = []


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

    def __init__(self, config: MarkpublishConfig, base_dir: Path):
        self.config = config
        self.base_dir = base_dir
        self.engine = MarkdownEngine(language=config.document.language)
        self.numbering_ctx = NumberingContext(default_autonum_type=config.document.autonum_type)

    def process_document(self) -> Tuple[List[ContentItem], List[TOCNode]]:
        """
        Parses all chapters and parts, builds content items and global TOC tree.
        """
        content_items: List[ContentItem] = []
        all_toc_nodes: List[TOCNode] = []

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
                    divider_page=item_cfg.divider_page,
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
                    child_item, child_toc_nodes = self._process_chapter(child_cfg, base_level=2)
                    part_item.children.append(child_item)
                    for n in child_toc_nodes:
                        part_toc_node.children.append(n)

                content_items.append(part_item)

            else:
                # Regular top-level chapter
                chapter_item, chapter_toc_nodes = self._process_chapter(item_cfg, base_level=1)
                content_items.append(chapter_item)
                all_toc_nodes.extend(chapter_toc_nodes)

        global_toc_tree = build_toc_tree(all_toc_nodes)
        return content_items, global_toc_tree

    def _process_chapter(self, chapter_cfg: ChapterItem, base_level: int = 1) -> Tuple[ContentItem, List[TOCNode]]:
        raw_md = ""
        file_base_dir = self.base_dir

        # 1. Read file and extract frontmatter
        title = chapter_cfg.title
        summary = chapter_cfg.summary
        divider_page = chapter_cfg.divider_page
        toc_config = chapter_cfg.toc

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
                    if "divider_page" in post.metadata:
                        divider_page = bool(post.metadata["divider_page"])

        # Determine autonum override
        autonum_override = None
        if chapter_cfg.autonum:
            if isinstance(chapter_cfg.autonum, AutonumType):
                autonum_override = chapter_cfg.autonum
            else:
                for a in AutonumType:
                    if a.value == str(chapter_cfg.autonum).lower().strip():
                        autonum_override = a
                        break

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

        # Filter local TOC items if enabled
        local_toc_items: List[TOCNode] = []
        if toc_config:
            max_depth = 3
            if hasattr(toc_config, "max_depth"):
                max_depth = toc_config.max_depth
            elif isinstance(toc_config, int):
                max_depth = toc_config
            local_toc_items = [n for n in toc_nodes if n.level <= max_depth]

        item = ContentItem(
            title=display_title,
            display_title=display_title,
            slug=slug,
            is_part=False,
            summary=summary,
            divider_page=divider_page,
            number_prefix=number_prefix,
            html_content=processed_html,
            toc_config=toc_config,
            local_toc_items=local_toc_items,
        )

        # Process recursive child chapters
        for sub_child in chapter_cfg.chapters:
            sub_item, sub_tocs = self._process_chapter(sub_child, base_level=base_level + 1)
            item.children.append(sub_item)
            toc_nodes.extend(sub_tocs)

        return item, toc_nodes

