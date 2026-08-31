"""
WeasyPrint PDF Renderer for markpublish with automatic Windows GTK/Pango runtime discovery.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Optional, Tuple

from markpublish.renderers.base import BaseRenderer, DocumentContext

# Standard search locations for the GTK/Pango runtime on Windows
GTK_CANDIDATE_PATHS = [
    r"C:\Program Files\GTK3-Runtime Win64\bin",
    r"C:\msys64\mingw64\bin",
    r"C:\msys64\ucrt64\bin",
    r"C:\Program Files\darktable\bin",
    r"C:\Program Files\Inkscape\bin",
    r"C:\Program Files\GIMP 2\bin",
]

# Minimal fontconfig config used when the detected runtime ships none.
BUNDLED_FONTS_CONF = Path(__file__).resolve().parent.parent / "data" / "fonts.conf"

_gtk_initialized = False


def _path_entries() -> set:
    """Returns the current PATH as a set of normalized directory strings."""
    raw = os.environ.get("PATH", "")
    return {
        os.path.normcase(os.path.normpath(entry))
        for entry in raw.split(os.pathsep)
        if entry
    }


def _init_windows_gtk() -> None:
    """
    Auto-detects and configures GTK/Pango libraries on Windows.

    Deliberately not run at import time: this mutates the process-wide PATH,
    which an importable library should not do as a side effect of being
    imported. It is called lazily from _load_weasyprint().
    """
    global _gtk_initialized
    if _gtk_initialized or sys.platform != "win32":
        return
    _gtk_initialized = True

    candidates = [os.environ.get("GTK_PATH", ""), *GTK_CANDIDATE_PATHS]

    for candidate in candidates:
        if not candidate:
            continue
        p = Path(candidate)
        if not p.is_dir() or not (p / "libgobject-2.0-0.dll").is_file():
            continue

        resolved = str(p.resolve())
        try:
            os.add_dll_directory(resolved)
        except OSError:
            pass
        # Exakter Eintragsvergleich statt Substring-Test: ein PATH-Eintrag, der
        # den Kandidaten nur als Praefix enthaelt, darf ihn nicht verdecken.
        if os.path.normcase(os.path.normpath(resolved)) not in _path_entries():
            os.environ["PATH"] = resolved + os.pathsep + os.environ.get("PATH", "")
        _init_fontconfig(Path(resolved))
        break


def _init_fontconfig(gtk_dir: Path) -> None:
    """
    Points fontconfig at a usable configuration file.

    Runtimes such as darktable or GIMP ship libfontconfig-1.dll but not the
    etc/fonts/fonts.conf it looks for one level above its own bin directory.
    Without it fontconfig prints "Cannot load default config file: File not
    found" on every run and falls back to a built-in config that defines no
    aliases, so a bare `font-family: monospace` resolves to an arbitrary face.

    Must run before WeasyPrint is imported: fontconfig reads FONTCONFIG_FILE
    when Pango first initializes it.
    """
    if os.environ.get("FONTCONFIG_FILE") or os.environ.get("FONTCONFIG_PATH"):
        return  # explicit user setup wins

    # Eine vollstaendige Runtime (GTK3-Runtime, MSYS2) bringt ihre eigene
    # Konfiguration mit - die hat Vorrang, sie kennt die Fonts der Installation.
    runtime_conf = gtk_dir.parent / "etc" / "fonts" / "fonts.conf"
    conf = runtime_conf if runtime_conf.is_file() else BUNDLED_FONTS_CONF
    if not conf.is_file():
        return

    os.environ["FONTCONFIG_FILE"] = str(conf)
    os.environ["FONTCONFIG_PATH"] = str(conf.parent)


def _load_weasyprint() -> Tuple[Optional[Any], Optional[str]]:
    """Imports WeasyPrint, configuring the Windows GTK runtime first."""
    _init_windows_gtk()
    try:
        from weasyprint import HTML
        return HTML, None
    except Exception as err:  # pragma: no cover - depends on system libraries
        return None, str(err)


class PDFRenderer(BaseRenderer):
    """Generates print-ready PDF files using WeasyPrint and CSS Paged Media."""

    def render(self, context: DocumentContext, output_path: Path) -> Path:
        html_cls, error = _load_weasyprint()
        if html_cls is None:
            raise RuntimeError(
                f"WeasyPrint is not available on this system:\n{error}\n\n"
                "Please ensure GTK3/Pango libraries are installed:\n"
                " - Windows: Install GTK3-Runtime (https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer) or MSYS2\n"
                " - macOS: brew install pango\n"
                " - Linux (Debian/Ubuntu): sudo apt install libpango-1.0-0 libpangoft2-1.0-0\n"
            )

        rendered_html = self.render_template(context, template_name="layout.html")

        # Ensure parent output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        base_url = str(context.base_dir)

        html_doc = html_cls(
            string=rendered_html,
            base_url=base_url,
        )

        html_doc.write_pdf(target=str(output_path))
        return output_path
