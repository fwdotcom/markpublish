"""
Platzhalter im Text: `{{author}}` fuer Dokumentangaben, `{{custom.a.b}}` fuer
eigene Werte unter `document.custom`.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from markpublish.config.models import ConfigurationError
from markpublish.i18n import CORE_METADATA_KEYS
from markpublish.ui import t

NAME = r"[A-Za-z0-9_-]+"
PLACEHOLDER_RE = re.compile(r"\{\{\s*(" + NAME + r"(?:\." + NAME + r")*)\s*\}\}")

#: Code zeigt den Platzhalter woertlich -- so laesst sich die Syntax selbst
#: dokumentieren.
SKIP_TAGS = {"code", "pre"}
ATTRIBUTES = ("href", "src", "alt", "title")

#: `\{{name}}` zeigt den Platzhalter woertlich. Markdown entfernt den Backslash
#: vor der Ersetzung, daher steht bis dahin ein Zeichen aus dem Private-Use-Bereich.
ESCAPE = ""


def protect_escapes(markdown: str) -> str:
    return markdown.replace("\\{{", ESCAPE)


def build_variables(document: Any) -> Dict[str, Any]:
    """Die Werte, die ein Platzhalter erreichen kann."""
    values: Dict[str, Any] = {}
    for key in (*CORE_METADATA_KEYS, "language"):
        values[key] = getattr(document, key, None)
    values.update(getattr(document, "model_extra", None) or {})
    values["custom"] = getattr(document, "custom", None) or {}
    return values


def _lookup(name: str, variables: Dict[str, Any]) -> Optional[str]:
    value: Any = variables
    for part in name.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    if value is None or isinstance(value, (dict, list)):
        return None
    return str(value)


def substitute(text: str, variables: Dict[str, Any], where: str) -> str:
    def _replace(match: re.Match) -> str:
        value = _lookup(match.group(1), variables)
        if value is None:
            raise ConfigurationError(
                t("err.variable.unknown", name=match.group(1), file=where)
            )
        return value

    return PLACEHOLDER_RE.sub(_replace, text)


def substitute_document(document: Any) -> None:
    """Ersetzt `{{custom.a.b}}` in den Textangaben unter `document` selbst.

    Deckblatt, Kopfzeile, Dateiname und PDF-Metadaten lesen diese Felder
    direkt -- ohne diesen Schritt stuende dort `{{custom.verfahren.name}}`.
    Nur custom.* ist erlaubt: Verweise der Felder untereinander
    (`{{title}}` in summary) braeuchten eine Reihenfolge und Kreiserkennung.
    """
    custom = {"custom": getattr(document, "custom", None) or {}}
    extra = getattr(document, "model_extra", None) or {}

    def _replace(match: re.Match, where: str) -> str:
        name = match.group(1)
        value = _lookup(name, custom) if name.startswith("custom.") else None
        if value is None:
            raise ConfigurationError(t("err.variable.document_field", name=name, file=where))
        return value

    for key in CORE_METADATA_KEYS:
        value = getattr(document, key, None)
        if isinstance(value, str):
            where = f"document.{key}"
            setattr(document, key, PLACEHOLDER_RE.sub(lambda m: _replace(m, where), value))
    for key, value in extra.items():
        if isinstance(value, str):
            where = f"document.{key}"
            extra[key] = PLACEHOLDER_RE.sub(lambda m: _replace(m, where), value)


def _unescape(text: str, literal: str) -> str:
    return text.replace(ESCAPE, literal)


def _restore_code(elem: Any) -> None:
    """In Code bleibt `\\{{` stehen, wie geschrieben."""
    if elem.text:
        elem.text = _unescape(elem.text, "\\{{")
    for child in elem:
        _restore_code(child)
        if child.tail:
            child.tail = _unescape(child.tail, "\\{{")


def substitute_tree(elem: Any, variables: Dict[str, Any], where: str) -> None:
    """Ersetzt in Text und Attributen, Code ausgenommen (dessen tail nicht)."""
    if elem.tag in SKIP_TAGS:
        _restore_code(elem)
    else:
        if elem.text:
            elem.text = _unescape(substitute(elem.text, variables, where), "{{")
        for attr in ATTRIBUTES:
            if elem.attrib.get(attr):
                elem.attrib[attr] = _unescape(substitute(elem.attrib[attr], variables, where), "{{")
        for child in elem:
            substitute_tree(child, variables, where)
    if elem.tail:
        elem.tail = _unescape(substitute(elem.tail, variables, where), "{{")
