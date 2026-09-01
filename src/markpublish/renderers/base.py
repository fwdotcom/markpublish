"""
Base Renderer interface and Document Context.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List

import jinja2

from markpublish.config.models import MarkpublishConfig
from markpublish.i18n import LabelMap, build_labels, validate_label_references
from markpublish.markdown.assets import file_to_data_uri
from markpublish.markdown.engine import ContentItem
from markpublish.markdown.toc import TOCNode


def css_string(value: Any) -> str:
    """
    Escapes a value for use inside a single-quoted CSS string.

    Running headers are fed through inline `string-set:` declarations, so an
    apostrophe in a chapter title would otherwise terminate the CSS string and
    break the whole declaration.
    """
    return str(value).replace("\\", "\\\\").replace("'", "\\'")


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

        template_path points at <theme>/<target>. Its parent only counts as the
        theme level when it actually carries the theme name -- a parent that
        does not is shared across themes, and taking it would leak one theme's
        texts into another.
        """
        dirs: List[Path] = []
        theme_dir = self.template_path.parent
        if theme_dir.name.strip().lower() == str(self.config.theme).strip().lower():
            dirs.append(theme_dir)
        dirs.append(self.template_path)
        return dirs

    @cached_property
    def labels(self) -> LabelMap:
        """
        The resolved static texts for this document and target.

        Cached because the Markdown pipeline, the stylesheet and the templates
        all read the same set -- and because reading the i18n.yaml files three
        times would report a malformed file three times.
        """
        return build_labels(
            self.config.document.language,
            template_dirs=self.label_source_dirs,
        )

    def to_template_context(self) -> Dict[str, Any]:
        """Builds dictionary passed into Jinja2 templates."""
        return {
            "document": self.config.document,
            "theme": self.config.theme,
            "content_items": self.content_items,
            "toc_tree": [t.to_dict() if hasattr(t, "to_dict") else t for t in self.toc_tree],
            "target": self.target,
            # Statische Template-Texte. Kaskade: i18n.yaml (Programm) ->
            # <theme>/i18n.yaml -> <theme>/<target>/i18n.yaml. Siehe
            # markpublish.i18n.
            "labels": self.labels,
        }


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

    def setup_jinja_env(self, template_path: Path) -> jinja2.Environment:
        """Configures Jinja2 environment with FileSystemLoader."""
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_path)),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        return env

    def render_template(self, context: DocumentContext, template_name: str = "layout.html") -> str:
        """Renders the main Jinja2 template and stylesheet."""
        # Vor dem ersten Zeichen Ausgabe: ein Label, das das Template notiert,
        # aber keine Ebene definiert, bricht den Build ab. Geprueft werden die
        # Quelldateien, nicht der Renderlauf -- sonst bliebe ein Label in einem
        # Zweig unentdeckt, den genau dieses Dokument nicht durchlaeuft.
        validate_label_references(context.labels, context.template_path)

        env = self.setup_jinja_env(context.template_path)
        env.filters["css_string"] = css_string
        tmpl_ctx = context.to_template_context()

        def asset_url(rel_path: str) -> str:
            """Inlines a template asset so the output file stays self-contained."""
            asset_file = (context.template_path / rel_path).resolve()
            data_uri = file_to_data_uri(asset_file)
            if data_uri:
                return data_uri
            if asset_file.is_file():
                return asset_file.as_uri()
            return rel_path

        tmpl_ctx["asset_url"] = asset_url

        # Render styles.css if present (without HTML escaping for CSS strings)
        css_file = context.template_path / "styles.css"
        rendered_css = ""
        if css_file.is_file():
            css_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(str(context.template_path)),
                autoescape=False,
                trim_blocks=True,
                lstrip_blocks=True,
            )
            css_env.filters["css_string"] = css_string
            css_tmpl = css_env.from_string(css_file.read_text(encoding="utf-8"))
            rendered_css = css_tmpl.render(**tmpl_ctx)

        tmpl_ctx["rendered_css"] = rendered_css

        main_tmpl = env.get_template(template_name)
        return main_tmpl.render(**tmpl_ctx)

