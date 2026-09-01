"""
Template Resolver for markpublish.
Manages resolution hierarchy: User directory > Common/Project directory > Package built-ins.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import platformdirs


def get_package_templates_dir() -> Path:
    """Returns the path to the built-in package templates directory."""
    return Path(__file__).resolve().parent


def get_user_templates_dir() -> Path:
    """Returns the path to user templates directory in OS config or home."""
    # 1. ~/.markpublish/templates
    home_path = Path.home() / ".markpublish" / "templates"
    if home_path.exists():
        return home_path
    # 2. OS specific config directory
    return Path(platformdirs.user_config_dir("markpublish")) / "templates"


def get_common_templates_dir(
    custom_dir: Optional[Union[str, Path]] = None,
    config_base_dir: Optional[Path] = None
) -> Optional[Path]:
    """
    Resolves the common/project templates directory using precedence:
    1. Explicit custom_dir argument (e.g. from CLI or config.templates_dir)
    2. MARKPUBLISH_TEMPLATES_DIR environment variable
    3. ./templates in current directory or next to config file
    """
    if custom_dir:
        p = Path(custom_dir)
        if not p.is_absolute() and config_base_dir:
            p = config_base_dir / p
        return p.resolve()

    env_dir = os.environ.get("MARKPUBLISH_TEMPLATES_DIR")
    if env_dir:
        return Path(env_dir).resolve()

    if config_base_dir:
        p = config_base_dir / "templates"
        if p.exists() and p.is_dir():
            return p.resolve()

    local_p = Path.cwd() / "templates"
    if local_p.exists() and local_p.is_dir():
        return local_p.resolve()

    return None


def _search_bases(
    custom_templates_dir: Optional[Union[str, Path]] = None,
    config_base_dir: Optional[Path] = None,
    package_only: bool = False,
) -> List[Tuple[str, Path]]:
    """
    Returns the template base directories in resolution order:
    User > Common/Project > Package. Duplicates are dropped.

    `package_only` skips the User- and Projekt-Ebene und laesst ausschliesslich
    die mitgelieferten Themes zu. Gedacht fuer Dokumente, die das Programm
    selbst ausliefert: die duerfen nicht daran scheitern, dass im
    Arbeitsverzeichnis ein halbfertiges eigenes Theme liegt.
    """
    if package_only:
        return [("package", get_package_templates_dir())]

    bases: List[Tuple[str, Path]] = [
        ("user", get_user_templates_dir()),
        ("user", Path.home() / ".markpublish" / "templates"),
    ]

    common_base = get_common_templates_dir(custom_templates_dir, config_base_dir)
    if common_base:
        bases.append(("common", common_base))

    bases.append(("package", get_package_templates_dir()))

    # get_user_templates_dir() gibt ~/.markpublish/templates zurueck, sobald es
    # existiert - dann waeren die beiden User-Eintraege identisch.
    deduped: List[Tuple[str, Path]] = []
    seen: set = set()
    for source_name, base_path in bases:
        try:
            key = base_path.resolve()
        except OSError:
            key = base_path
        if key not in seen:
            seen.add(key)
            deduped.append((source_name, base_path))
    return deduped


def resolve_template_path(
    target: str,
    theme: str,
    custom_templates_dir: Optional[Union[str, Path]] = None,
    config_base_dir: Optional[Path] = None,
    package_only: bool = False,
) -> Path:
    """
    Resolves the theme template directory for a given target format.

    Layout is <base>/<theme>/<target>, e.g. templates/default/pdf.

    Hierarchy: User > Common/Project > Package.

    Args:
        target: Target format, e.g. "pdf" or "html"
        theme: Theme name, e.g. "default"
        custom_templates_dir: Optional explicit templates directory path
        config_base_dir: Base directory of the config file
        package_only: Ignore user and project themes, use the built-ins only

    Returns:
        Resolved Path to template directory.

    Raises:
        FileNotFoundError if no matching template directory is found.
    """
    target = target.lower().strip()
    theme = theme.lower().strip()

    bases = _search_bases(custom_templates_dir, config_base_dir, package_only)

    for _, base_path in bases:
        candidate = base_path / theme / target
        if candidate.is_dir():
            return candidate

    searched = [str(base / theme / target) for _, base in bases]
    raise FileNotFoundError(
        f"Template '{theme}' for target '{target}' not found. Searched locations:\n"
        + "\n".join(f" - {loc}" for loc in searched)
    )


def list_templates(
    custom_templates_dir: Optional[Union[str, Path]] = None,
    config_base_dir: Optional[Path] = None,
) -> List[Dict[str, str]]:
    """
    Lists all available templates across User, Common, and Package locations.
    """
    results: List[Dict[str, str]] = []
    seen: set = set()

    def add(target_name: str, theme_name: str, source: str, path: Path) -> None:
        if not ((path / "layout.html").is_file() or (path / "styles.css").is_file()):
            return
        key = (target_name, theme_name)
        results.append({
            "target": target_name,
            "theme": theme_name,
            "source": source,
            "path": str(path),
            "is_active": key not in seen,
        })
        seen.add(key)

    for source_name, base_path in _search_bases(custom_templates_dir, config_base_dir):
        if not base_path.is_dir():
            continue

        # <base>/<theme>/<target>
        for theme_entry in sorted(base_path.iterdir()):
            if not theme_entry.is_dir() or theme_entry.name.startswith((".", "_")):
                continue
            for target_dir in sorted(theme_entry.iterdir()):
                if target_dir.is_dir() and not target_dir.name.startswith((".", "_")):
                    add(target_dir.name, theme_entry.name, source_name, target_dir)

    return results
