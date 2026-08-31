"""
Template Resolver for markpublish.
Manages resolution hierarchy: User directory > Common/Project directory > Package built-ins.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
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


def resolve_template_path(
    target: str,
    theme: str,
    custom_templates_dir: Optional[Union[str, Path]] = None,
    config_base_dir: Optional[Path] = None,
) -> Path:
    """
    Resolves the theme template directory for a given target format.
    Hierarchy: User > Common/Project > Package.
    
    Args:
        target: Target format, e.g. "pdf" or "html"
        theme: Theme name, e.g. "default"
        custom_templates_dir: Optional explicit templates directory path
        config_base_dir: Base directory of the config file
        
    Returns:
        Resolved Path to template directory.
        
    Raises:
        FileNotFoundError if no matching template directory is found.
    """
    target = target.lower().strip()
    theme = theme.lower().strip()

    # 1. Check User Directory
    user_dir = get_user_templates_dir() / target / theme
    if user_dir.exists() and user_dir.is_dir():
        return user_dir

    # Also check ~/.markpublish/templates/<target>/<theme> directly if different from platformdirs
    direct_home = Path.home() / ".markpublish" / "templates" / target / theme
    if direct_home.exists() and direct_home.is_dir():
        return direct_home

    # 2. Check Common / Project Directory
    common_base = get_common_templates_dir(custom_templates_dir, config_base_dir)
    if common_base:
        common_dir = common_base / target / theme
        if common_dir.exists() and common_dir.is_dir():
            return common_dir

    # 3. Check Package Built-ins
    pkg_dir = get_package_templates_dir() / target / theme
    if pkg_dir.exists() and pkg_dir.is_dir():
        return pkg_dir

    searched_locations = [
        str(user_dir),
        str(direct_home),
        str((common_base / target / theme) if common_base else "<none>"),
        str(pkg_dir),
    ]
    raise FileNotFoundError(
        f"Template '{theme}' for target '{target}' not found. Searched locations:\n"
        + "\n".join(f" - {loc}" for loc in searched_locations)
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

    sources: List[Tuple[str, Path]] = []

    # User dirs
    sources.append(("user", get_user_templates_dir()))
    sources.append(("user", Path.home() / ".markpublish" / "templates"))

    # Common dir
    common_base = get_common_templates_dir(custom_templates_dir, config_base_dir)
    if common_base:
        sources.append(("common", common_base))

    # Package dir
    sources.append(("package", get_package_templates_dir()))

    for source_name, base_path in sources:
        if not base_path.exists() or not base_path.is_dir():
            continue

        for target_dir in base_path.iterdir():
            if not target_dir.is_dir() or target_dir.name.startswith((".", "_")):
                continue
            target_name = target_dir.name
            for theme_dir in target_dir.iterdir():
                if not theme_dir.is_dir() or theme_dir.name.startswith((".", "_")):
                    continue
                theme_name = theme_dir.name
                key = (target_name, theme_name)
                
                # Check if it has layout.html or styles.css
                has_layout = (theme_dir / "layout.html").is_file()
                has_styles = (theme_dir / "styles.css").is_file()
                if has_layout or has_styles:
                    results.append({
                        "target": target_name,
                        "theme": theme_name,
                        "source": source_name,
                        "path": str(theme_dir),
                        "is_active": key not in seen,
                    })
                    seen.add(key)

    return results

