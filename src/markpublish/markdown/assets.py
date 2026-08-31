"""
Asset path resolution for markdown content.
Resolves relative image paths to absolute file URIs for WeasyPrint and web renderers.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


IMG_SRC_REGEX = re.compile(r'(<img\s+[^>]*?src=["\'])([^"\']+)(["\'][^>]*>)', re.IGNORECASE)


def resolve_asset_path(src: str, base_dir: Path) -> str:
    """
    Resolves a relative asset path against base_dir.
    If src is a remote URL (http://, https://) or data URI, it is left untouched.
    """
    src_trimmed = src.strip()
    if src_trimmed.startswith(("http://", "https://", "data:", "file://")):
        return src_trimmed

    # Handle local file path
    asset_file = (base_dir / src_trimmed).resolve()
    if asset_file.exists():
        return asset_file.as_uri()

    return src_trimmed


def rewrite_html_asset_paths(html_content: str, base_dir: Optional[Path]) -> str:
    """
    Rewrites relative <img> src attributes in rendered HTML to absolute file URIs.
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

