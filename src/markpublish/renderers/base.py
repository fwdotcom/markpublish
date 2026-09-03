"""
Base Renderer interface and Document Context.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import List, Tuple

from markpublish.config.models import MarkpublishConfig
from markpublish.i18n import (
    LEVEL_PROJECT,
    LEVEL_TARGET,
    LEVEL_THEME,
    LabelMap,
    build_labels,
)
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
    def label_levels(self) -> List[Tuple[str, Path]]:
        """
        The cascade above the program default, outermost first: the theme
        directory, the target directory inside it, and finally the project
        directory -- the one holding markpublish.yaml.

        The project comes last because it is the most specific level. It is
        also the only place where a document can name its own free metadata
        fields: `abteilung: "F&E"` under `document:` has no caption anywhere
        else, and without this level the cover would have to print the raw key.

        Der Name steht neben dem Verzeichnis, weil `markpublish labels` die
        Ebene benennen soll ("theme", "target") statt einen Pfad zu zeigen.
        Wer die Reihenfolge hier aendert, aendert damit auch die Anzeige --
        besser, als beides getrennt zu pflegen.
        """
        levels: List[Tuple[str, Path]] = []
        theme_dir = self.template_path.parent
        if theme_dir.name.strip().lower() == str(self.config.theme).strip().lower():
            levels.append((LEVEL_THEME, theme_dir))
        levels.append((LEVEL_TARGET, self.template_path))

        # Nur wenn das Projekt nicht ohnehin das Theme ist: sonst laese
        # dieselbe Datei zweimal, und ein Theme-Ordner, der zufaellig neben der
        # markpublish.yaml liegt, saehe aus wie eine eigene Ebene.
        project_dir = Path(self.base_dir).resolve()
        if project_dir not in {d.resolve() for _, d in levels}:
            levels.append((LEVEL_PROJECT, project_dir))
        return levels

    @property
    def label_source_dirs(self) -> List[Path]:
        """Die Verzeichnisse aus `label_levels`, in derselben Reihenfolge."""
        return [directory for _, directory in self.label_levels]

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

