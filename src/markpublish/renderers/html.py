"""
HTML Preview and Static Site Renderer for markpublish.
"""

from __future__ import annotations

from pathlib import Path
from markpublish.renderers.base import BaseRenderer, DocumentContext


class HTMLRenderer(BaseRenderer):
    """Generates standalone HTML files for web viewing and browser preview."""

    def render(self, context: DocumentContext, output_path: Path) -> Path:
        rendered_html = self.render_template(context, template_name="layout.html")

        # Ensure parent output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        return output_path

