"""
YAML Configuration Loader and Validator for markpublish.
"""

from __future__ import annotations

import copy
import datetime
from pathlib import Path
from typing import Any, Dict, Union

import yaml

from markpublish.config.models import MarkpublishConfig
from markpublish.i18n import normalize_language


def format_current_date(language: str = "de") -> str:
    """Formats current date according to language conventions."""
    now = datetime.date.today()
    if normalize_language(language) == "de":
        return now.strftime("%d.%m.%Y")
    return now.strftime("%Y-%m-%d")


def load_config(config_path_or_str: Union[str, Path, Dict[str, Any]]) -> MarkpublishConfig:
    """
    Loads and validates a markpublish configuration.

    Args:
        config_path_or_str: Path to YAML file, YAML content string, or raw dictionary.

    Returns:
        Validated MarkpublishConfig object.
    """
    raw_data: Dict[str, Any] = {}

    if isinstance(config_path_or_str, dict):
        # Kopieren, bevor unten document["date"] gesetzt wird - sonst schreibt
        # eine reine Ladefunktion in das Objekt des Aufrufers zurueck.
        raw_data = copy.deepcopy(config_path_or_str)
    elif isinstance(config_path_or_str, (str, Path)):
        path = Path(config_path_or_str)
        if path.is_file():
            with open(path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    raw_data = loaded
        else:
            # Try parsing as YAML string
            loaded = yaml.safe_load(str(config_path_or_str))
            if isinstance(loaded, dict):
                raw_data = loaded
            else:
                raise FileNotFoundError(f"Configuration file not found: {config_path_or_str}")

    # Process date: "auto" / "today"
    doc = raw_data.get("document", {})
    if isinstance(doc, dict):
        date_val = str(doc.get("date", "")).strip().lower()
        if date_val in ("auto", "today", "now", ""):
            lang = str(doc.get("language", "de"))
            doc["date"] = format_current_date(lang)

    return MarkpublishConfig(**raw_data)

