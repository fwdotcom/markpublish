"""
Base Renderer interface and Document Context.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import List

from markpublish.config.models import MarkpublishConfig
from markpublish.i18n import LabelMap, build_labels
from markpublish.markdown.engine import ContentItem
from markpublish.markdown.toc import TOCNode


@dataclass
class DocumentContext:
    """Carries complete state and data needed by renderers."""
    config: MarkpublishConfig
    content_items: List[ContentItem]
    toc_tree: List[TOCNode]
    template_path: Path
    base_dir: Path
    target: str

    @property
    def label_source_dirs(self) -> List[Path]:
        """
        Directories whose labels.yaml feeds the label cascade, outermost first:
        the theme directory, then the target directory inside it.
        """
        dirs: List[Path] = []
        theme_dir = self.template_path.parent
        if theme_dir.name.strip().lower() == str(self.config.theme).strip().lower():
            dirs.append(theme_dir)
        dirs.append(self.template_path)
        return dirs

    @cached_property
    def labels(self) -> LabelMap:
        """The resolved static texts for this document and target."""
        return build_labels(
            self.config.document.language,
            template_dirs=self.label_source_dirs,
        )


class BaseRenderer(ABC):
    """Abstract Base Class for document renderers."""

    @abstractmethod
    def render(self, context: DocumentContext, output_path: Path) -> Path:
        """
        Renders the document to the specified output path.

        Args:
            context: Prepared DocumentContext.
            output_path: Target destination file path.

        Returns:
            The Path to the generated output file.
        """
        pass

