"""
WeasyPrint PDF Renderer for markpublish with automatic Windows GTK/Pango runtime discovery.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from markpublish.renderers.base import BaseRenderer, DocumentContext


def _init_windows_gtk() -> None:
    """Auto-detects and configures GTK/Pango libraries on Windows."""
    if sys.platform != "win32":
        return

    # Check standard search locations for GTK/Pango on Windows
    candidate_paths = [
        Path(os.environ.get("GTK_PATH", "")),
        Path(r"C:\Program Files\GTK3-Runtime Win64\bin"),
        Path(r"C:\msys64\mingw64\bin"),
        Path(r"C:\msys64\ucrt64\bin"),
        Path(r"C:\Program Files\darktable\bin"),
        Path(r"C:\Program Files\Inkscape\bin"),
        Path(r"C:\Program Files\GIMP 2\bin"),
    ]

    for p in candidate_paths:
        if p and p.is_dir() and (p / "libgobject-2.0-0.dll").is_file():
            try:
                os.add_dll_directory(str(p.resolve()))
            except Exception:
                pass
            if str(p) not in os.environ.get("PATH", ""):
                os.environ["PATH"] = str(p) + os.pathsep + os.environ.get("PATH", "")
            break


_init_windows_gtk()

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
    WEASYPRINT_ERROR = None
except Exception as _err:
    WEASYPRINT_AVAILABLE = False
    WEASYPRINT_ERROR = str(_err)


class PDFRenderer(BaseRenderer):
    """Generates print-ready PDF files using WeasyPrint and CSS Paged Media."""

    def render(self, context: DocumentContext, output_path: Path) -> Path:
        if not WEASYPRINT_AVAILABLE:
            raise RuntimeError(
                f"WeasyPrint is not available on this system:\n{WEASYPRINT_ERROR}\n\n"
                "Please ensure GTK3/Pango libraries are installed:\n"
                " - Windows: Install GTK3-Runtime (https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer) or MSYS2\n"
                " - macOS: brew install pango\n"
                " - Linux (Debian/Ubuntu): sudo apt install libpango-1.0-0 libpangoft2-1.0-0\n"
            )

        rendered_html = self.render_template(context, template_name="layout.html")

        # Ensure parent output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        base_url = str(context.base_dir)

        html_doc = HTML(
            string=rendered_html,
            base_url=base_url,
        )

        html_doc.write_pdf(target=str(output_path))
        return output_path

