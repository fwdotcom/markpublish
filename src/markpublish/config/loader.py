"""
YAML Configuration Loader and Validator for markpublish.
"""

from __future__ import annotations

import copy
import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

from markpublish.config.models import MarkpublishConfig
from markpublish.i18n import default_document_language, normalize_language
from markpublish.ui import t


def format_current_date(language: Optional[str] = None) -> str:
    """Formats current date according to language conventions."""
    now = datetime.date.today()
    if normalize_language(language or default_document_language()) == "de":
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
    elif isinstance(config_path_or_str, Path):
        if not config_path_or_str.is_file():
            raise FileNotFoundError(t("err.config.not_found_file", path=config_path_or_str))
        with open(config_path_or_str, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
            if loaded is None:
                raise ValueError(t("err.config.expected_mapping", type="empty"))
            if not isinstance(loaded, dict):
                raise ValueError(t("err.config.expected_mapping", type=type(loaded).__name__))
            raw_data = loaded
    elif isinstance(config_path_or_str, str):
        candidate_path = Path(config_path_or_str)
        if candidate_path.is_file():
            with open(candidate_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if loaded is None:
                    raise ValueError(t("err.config.expected_mapping", type="empty"))
                if not isinstance(loaded, dict):
                    raise ValueError(t("err.config.expected_mapping", type=type(loaded).__name__))
                raw_data = loaded
        else:
            # Wenn der String wie ein Pfad aussieht (keine Zeilenumbrueche und typische Pfadmerkmale)
            looks_like_path = (
                ("\n" not in config_path_or_str and "\r" not in config_path_or_str)
                and (
                    config_path_or_str.endswith((".yaml", ".yml"))
                    or "/" in config_path_or_str
                    or "\\" in config_path_or_str
                )
            )
            if looks_like_path:
                raise FileNotFoundError(t("err.config.not_found_file", path=config_path_or_str))

            # Versuche als YAML-String zu parsen
            try:
                loaded = yaml.safe_load(config_path_or_str)
            except yaml.YAMLError as exc:
                raise ValueError(str(exc)) from exc

            if loaded is None:
                raise ValueError(t("err.config.expected_mapping", type="empty"))
            if not isinstance(loaded, dict):
                if "\n" not in config_path_or_str and "\r" not in config_path_or_str:
                    raise FileNotFoundError(t("err.config.not_found_file", path=config_path_or_str))
                raise ValueError(t("err.config.expected_mapping", type=type(loaded).__name__))
            raw_data = loaded
    else:
        raise TypeError(t("err.config.expected_mapping", type=type(config_path_or_str).__name__))

    # Process date: "auto" / "today"
    doc = raw_data.get("document", {})
    if isinstance(doc, dict):
        date_val = str(doc.get("date", "")).strip().lower()
        if date_val in ("auto", "today", "now", ""):
            # Kein zweiter Default: format_current_date() greift selbst auf
            # die Systemsprache zurueck, wenn hier nichts steht. Zwei Stellen
            # mit eigenem Standard laufen frueher oder spaeter auseinander.
            doc["date"] = format_current_date(doc.get("language"))

    return MarkpublishConfig(**raw_data)

