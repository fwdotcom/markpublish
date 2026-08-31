"""
Asset path resolution for markdown content.

Local assets are inlined as data URIs so that a single output file is
self-contained: WeasyPrint embeds them into the PDF, and the generated HTML
stays portable instead of pointing at absolute file:// paths that only resolve
on the machine that produced it.
"""

from __future__ import annotations

import base64
import mimetypes
import re
import urllib.parse
from pathlib import Path
from typing import Optional

IMG_SRC_REGEX = re.compile(r'(<img\s+[^>]*?src=["\'])([^"\']+)(["\'][^>]*>)', re.IGNORECASE)

EXTERNAL_PREFIXES = ("http://", "https://", "data:", "file://", "//", "mailto:")

#: Assets above this size stay linked rather than inlined - base64 grows a file
#: by a third, and a multi-megabyte inline blob helps nobody.
MAX_INLINE_BYTES = 12 * 1024 * 1024


def file_to_data_uri(asset_file: Path) -> Optional[str]:
    """
    Encodes a local file as a data URI.

    SVG is percent-encoded as UTF-8 (smaller and still readable); everything
    else is base64. Returns None if the file is missing or too large to inline.
    """
    try:
        if not asset_file.is_file():
            return None
        if asset_file.stat().st_size > MAX_INLINE_BYTES:
            return None
    except OSError:
        return None

    if asset_file.suffix.lower() == ".svg":
        content = asset_file.read_text(encoding="utf-8").strip()
        # quote() leaves "'" alone, but these URIs are embedded in CSS
        # url('...') and HTML attributes - encode it so neither breaks.
        encoded = urllib.parse.quote(content).replace("'", "%27")
        return f"data:image/svg+xml;utf8,{encoded}"

    mime, _ = mimetypes.guess_type(asset_file.name)
    mime = mime or "application/octet-stream"
    encoded = base64.b64encode(asset_file.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def resolve_asset_path(src: str, base_dir: Path) -> str:
    """
    Resolves a relative asset path against base_dir and inlines it as a data URI.

    Remote URLs and existing data URIs are left untouched. A path that cannot be
    inlined (missing, unreadable, or oversized) falls back to an absolute file
    URI so that at least local rendering keeps working.
    """
    src_trimmed = src.strip()
    if src_trimmed.startswith(EXTERNAL_PREFIXES):
        return src_trimmed

    asset_file = (base_dir / src_trimmed).resolve()
    data_uri = file_to_data_uri(asset_file)
    if data_uri:
        return data_uri

    if asset_file.is_file():
        return asset_file.as_uri()

    return src_trimmed


def rewrite_html_asset_paths(html_content: str, base_dir: Optional[Path]) -> str:
    """
    Rewrites relative <img> src attributes in rendered HTML to inline data URIs.
    """
    if not base_dir:
        return html_content

    def _replace_img(match: re.Match) -> str:
        prefix = match.group(1)
        src = match.group(2)
        suffix = match.group(3)
        resolved = resolve_asset_path(src, base_dir)
        return f"{prefix}{resolved}{suffix}"

    return IMG_SRC_REGEX.sub(_replace_img, html_content)
