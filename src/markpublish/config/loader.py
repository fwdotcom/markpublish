"""
YAML Configuration Loader and Validator for markpublish.
"""

from __future__ import annotations

import copy
import datetime
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, FrozenSet, Optional, Union
from urllib.parse import urljoin, urlparse

import yaml

from markpublish.config.models import MarkpublishConfig
from markpublish.i18n import default_document_language, normalize_language
from markpublish.markdown.variables import substitute_document
from markpublish.ui import t


def format_current_date(language: Optional[str] = None) -> str:
    """Formats current date according to language conventions."""
    now = datetime.date.today()
    if normalize_language(language or default_document_language()) == "de":
        return now.strftime("%d.%m.%Y")
    return now.strftime("%Y-%m-%d")


#: Woher eine Konfiguration stammt: Verzeichnis einer Datei oder eine URL.
#: Relative Verweise mit `!file` loesen sich dagegen auf.
Base = Union[Path, str]

FILE_TAG = "!file"
YAML_SUFFIXES = (".yaml", ".yml")
URL_TIMEOUT = 10


def _is_url(src: str) -> bool:
    return src.startswith(("http://", "https://"))


def _resolve_ref(src: str, base: Base) -> Union[Path, str]:
    """Absoluter Ort eines `!file`-Verweises, relativ zu der Datei, in der er steht."""
    if _is_url(src):
        return src
    if isinstance(base, str):
        return urljoin(base, src)
    return (base / src).resolve()


def _read_ref(target: Union[Path, str], src: str) -> str:
    if isinstance(target, str):
        try:
            with urllib.request.urlopen(target, timeout=URL_TIMEOUT) as response:
                return response.read().decode("utf-8")
        except (urllib.error.URLError, OSError, UnicodeDecodeError) as exc:
            raise ValueError(t("err.config.file_ref_url", src=src, reason=exc)) from exc
    if not target.is_file():
        raise FileNotFoundError(t("err.config.file_ref_missing", src=src, path=target))
    return target.read_text(encoding="utf-8")


def _load_yaml(text: Any, base: Base, seen: FrozenSet[Union[Path, str]] = frozenset()) -> Any:
    """
    Wie `yaml.safe_load`, zusaetzlich mit `!file "pfad-oder-url"`.

    Ein Verweis auf .yaml/.yml setzt deren Inhalt an seine Stelle, jede
    andere Datei ihren Text. Nachgeladene YAML-Dateien duerfen selbst wieder
    `!file` enthalten; deren Pfade gelten relativ zu ihnen. `seen` haelt die
    Kette der offenen Dateien -- dieselbe Datei in zwei Zweigen ist erlaubt,
    nur ein Verweis zurueck in die eigene Kette nicht.
    """

    def construct(loader: yaml.SafeLoader, node: yaml.Node) -> Any:
        src = loader.construct_scalar(node)
        target = _resolve_ref(src, base)
        if target in seen:
            raise ValueError(t("err.config.file_ref_cycle", src=src, path=target))
        content = _read_ref(target, src)
        name = urlparse(target).path if isinstance(target, str) else target.name
        if not name.lower().endswith(YAML_SUFFIXES):
            return content.rstrip("\n")
        child_base = target if isinstance(target, str) else target.parent
        return _load_yaml(content, child_base, seen | {target})

    # Eigene Loader-Klasse je Aufruf: der Konstruktor haengt an `base` und
    # `seen`, und SafeLoader selbst soll unveraendert bleiben.
    loader_cls = type("_FileLoader", (yaml.SafeLoader,), {})
    loader_cls.add_constructor(FILE_TAG, construct)
    return yaml.load(text, Loader=loader_cls)  # noqa: S506 - SafeLoader-Unterklasse


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
        config_path = config_path_or_str.resolve()
        with open(config_path, "r", encoding="utf-8") as f:
            loaded = _load_yaml(f, config_path.parent, frozenset({config_path}))
            if loaded is None:
                raise ValueError(t("err.config.expected_mapping", type="empty"))
            if not isinstance(loaded, dict):
                raise ValueError(t("err.config.expected_mapping", type=type(loaded).__name__))
            raw_data = loaded
    elif isinstance(config_path_or_str, str):
        candidate_path = Path(config_path_or_str)
        # YAML-Text mit Zeilenumbruch ist nie ein Pfad; ein langer liesse is_file()
        # unter Linux/macOS vor Python 3.14 mit ENAMETOOLONG scheitern.
        if "\n" not in config_path_or_str and candidate_path.is_file():
            config_path = candidate_path.resolve()
            with open(config_path, "r", encoding="utf-8") as f:
                loaded = _load_yaml(f, config_path.parent, frozenset({config_path}))
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
                loaded = _load_yaml(config_path_or_str, Path.cwd())
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

    config = MarkpublishConfig(**raw_data)
    substitute_document(config.document)
    return config

