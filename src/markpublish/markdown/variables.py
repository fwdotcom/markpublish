"""
Platzhalter im Text: `{{author}}` fuer Dokumentangaben, `{{custom.a.b}}` fuer
eigene Werte unter `document.custom`.

Steueranweisungen `{% for %}` und `{% set %}` loest `expand_statements` vor dem
Markdown auf: Eine Schleife ueber Tabellenzeilen laesst sich im fertigen Baum
nicht mehr aufloesen.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as etree
from typing import Any, Dict, List, Optional, Tuple

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


_MISSING = object()


def _child(value: Any, part: str) -> Any:
    """`value[part]`; YAML-Schluessel wie `2024` sind Zahlen, der Pfad ist Text."""
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) == part:
                return child
    return _MISSING


def _lookup(name: str, variables: Dict[str, Any]) -> Optional[str]:
    value: Any = variables
    for part in name.split("."):
        value = _child(value, part)
        if value is _MISSING:
            return None
    if value is None or isinstance(value, (dict, list)):
        return None
    return str(value)


def _value(match: re.Match, variables: Dict[str, Any], where: str) -> str:
    value = _lookup(match.group(1), variables)
    if value is None:
        raise ConfigurationError(t("err.variable.unknown", name=match.group(1), file=where))
    return value


def substitute(text: str, variables: Dict[str, Any], where: str) -> str:
    return PLACEHOLDER_RE.sub(lambda match: _value(match, variables, where), text)


#: Ein Wert, der als Ganzes eine Adresse ist, wird ein Link -- wie derselbe Text,
#: direkt geschrieben, durch magiclink. Die Ersetzung laeuft erst nach Markdown.
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
URL_RE = re.compile(r"(?:https?://|ftps?://|www\.)\S+")


def _link_target(value: str) -> Optional[str]:
    if EMAIL_RE.fullmatch(value):
        return "mailto:" + value
    if URL_RE.fullmatch(value):
        return value if "://" in value else "http://" + value
    return None


def _substitute_linked(text: str, variables: Dict[str, Any], where: str) -> Tuple[str, List[Any]]:
    """Wie `substitute`, aber Adressen als `<a>`: (Text davor, Links samt tail)."""
    runs: List[List[str]] = [[]]  # Text vor dem ersten Link, dann tail je Link
    links: List[Any] = []
    last = 0
    for match in PLACEHOLDER_RE.finditer(text):
        value = _value(match, variables, where)
        target = _link_target(value)
        runs[-1].append(text[last:match.start()])
        if target:
            link = etree.Element("a", href=target)
            link.text = value
            links.append(link)
            runs.append([])
        else:
            runs[-1].append(value)
        last = match.end()
    runs[-1].append(text[last:])
    head, *tails = (_unescape("".join(run), "{{") for run in runs)
    for link, tail in zip(links, tails, strict=True):
        link.tail = tail
    return head, links


def substitute_document(document: Any) -> None:
    """Ersetzt `{{custom.a.b}}` in den Textangaben unter `document` selbst.

    Deckblatt, Kopfzeile, Dateiname und PDF-Metadaten lesen diese Felder
    direkt -- ohne diesen Schritt stuende dort `{{custom.verfahren.name}}`.
    Nur custom.* ist erlaubt: Verweise der Felder untereinander
    (`{{title}}` in summary) braeuchten eine Reihenfolge und Kreiserkennung.
    """
    custom = {"custom": getattr(document, "custom", None) or {}}
    extra = getattr(document, "model_extra", None) or {}

    def _substitute(text: str, where: str) -> str:
        def _replace(match: re.Match) -> str:
            name = match.group(1)
            value = _lookup(name, custom) if name.startswith("custom.") else None
            if value is None:
                raise ConfigurationError(t("err.variable.document_field", name=name, file=where))
            return value

        return PLACEHOLDER_RE.sub(_replace, text)

    for key in CORE_METADATA_KEYS:
        value = getattr(document, key, None)
        if isinstance(value, str):
            setattr(document, key, _substitute(value, f"document.{key}"))
    for key, value in extra.items():
        if isinstance(value, str):
            extra[key] = _substitute(value, f"document.{key}")


#: Eine Anweisung steht allein in ihrer Zeile, auch in Zitat oder Hinweisbox (`> `).
STATEMENT_RE = re.compile(r"^[ \t]*(?:>[ \t]*)*\{%\s*(.*?)\s*%\}[ \t]*\r?\n?$")
#: `\{% ... %}` zeigt die Anweisung woertlich; Markdown entfernt den Backslash.
INLINE_STATEMENT_RE = re.compile(r"(?<!\\)\{%.*?%\}")
FENCE_RE = re.compile(r"^[ \t]*(?:>[ \t]*)*(`{3,}|~{3,})")
CODE_SPAN_RE = re.compile(r"(`+).+?\1")
QUOTE_RE = re.compile(r"(?:[ \t]{0,3}>[ \t]?)*")
#: Liste, Hinweisbox, Definition, Fussnote: ihr Inhalt ist 4 Zeichen eingerueckt,
#: ein Codeblock darin 4 weitere.
CONTAINER_RE = re.compile(r"(?:[-*+]|\d+[.)])[ \t]|!!!|\?\?\?|:[ \t]|\[\^[^\]]+\]:")
PATH = NAME + r"(?:\." + NAME + r")*"
FOR_RE = re.compile(
    r"for\s+(?:(" + NAME + r")|\(\s*(" + NAME + r")\s*,\s*(" + NAME + r")\s*\))"
    r"\s+in\s+(" + PATH + r")$"
)
SET_RE = re.compile(r"set\s+(" + NAME + r")\s*=\s*(" + PATH + r")$")

#: Ein Name im Geltungsbereich steht fuer einen Pfad (`role` -> `custom.app.roles.x`)
#: oder fuer einen festen Text (den Schluessel einer Schleife).
Binding = Tuple[str, str]
#: (Zeilennummer, Zeile, ganz Code oder Kommentar, beginnt in offenem HTML-Kommentar)
Line = Tuple[int, str, bool, bool]


class _Expander:
    """Schreibt Schleifen und Namen in volle Platzhalter `{{custom...}}` um.

    Den Wert setzt danach `substitute_tree` ein -- Fehlermeldungen, Escapes
    und die Ausnahme fuer Code gelten so auch innerhalb einer Schleife.
    """

    def __init__(self, variables: Dict[str, Any], where: str) -> None:
        self.variables = variables
        self.where = where

    def error(self, key: str, line: int, **kwargs: Any) -> ConfigurationError:
        return ConfigurationError(t(key, file=self.where, line=line, **kwargs))

    def parse(self, lines: List[Line], pos: int = 0, opener: int = 0):
        """Zeilen zu Knoten; liefert (Knoten, Position hinter `endfor`)."""
        nodes: List[Any] = []
        while pos < len(lines):
            number, text, in_code, in_comment = lines[pos]
            match = None if in_code or in_comment else STATEMENT_RE.match(text)
            pos += 1
            if not match:
                nodes.append(("text", number, text, in_code, in_comment))
                continue
            statement = match.group(1)
            if statement == "endfor":
                if not opener:
                    raise self.error("err.statement.stray_end", number)
                return nodes, pos
            loop = FOR_RE.match(statement)
            if loop:
                body, pos = self.parse(lines, pos, number)
                var = loop.group(1) or loop.group(2)
                nodes.append(("for", number, var, loop.group(3), loop.group(4), body))
                continue
            alias = SET_RE.match(statement)
            if alias:
                nodes.append(("set", number, alias.group(1), alias.group(2)))
                continue
            raise self.error("err.statement.syntax", number, text=statement)
        if opener:
            raise self.error("err.statement.unclosed", opener)
        return nodes, pos

    def resolve(self, path: str, scope: Dict[str, Binding], line: int) -> Tuple[Binding, Any]:
        first, _, rest = path.partition(".")
        if first in scope:
            kind, target = scope[first]
            if kind == "value":
                if rest:
                    raise self.error("err.statement.unknown_path", line, path=path)
                return scope[first], target
            path = target + ("." + rest if rest else "")
        value: Any = self.variables
        for part in path.split("."):
            value = _child(value, part)
            if value is _MISSING:
                raise self.error("err.statement.unknown_path", line, path=path)
        return ("path", path), value

    def bind(self, scope: Dict[str, Binding], name: str, binding: Binding, line: int) -> None:
        if name in self.variables:
            raise self.error("err.statement.reserved", line, name=name)
        scope[name] = binding

    def render(self, nodes: List[Any], scope: Dict[str, Binding]) -> List[str]:
        scope = dict(scope)
        out: List[str] = []
        for node in nodes:
            if node[0] == "text":
                _, line, text, in_code, in_comment = node
                out.append(text if in_code else self.rewrite(text, in_comment, scope, line))
            elif node[0] == "set":
                _, line, name, path = node
                self.bind(scope, name, self.resolve(path, scope, line)[0], line)
            else:
                _, line, var, key_var, path, body = node
                (_, target), group = self.resolve(path, scope, line)
                if not isinstance(group, dict):
                    raise self.error("err.statement.not_group", line, path=path)
                for key in group:
                    inner = dict(scope)
                    self.bind(inner, var, ("path", f"{target}.{key}"), line)
                    if key_var:
                        self.bind(inner, key_var, ("value", str(key)), line)
                    out.extend(self.render(body, inner))
        return out

    def rewrite(self, text: str, in_comment: bool, scope: Dict[str, Binding], line: int) -> str:
        def _placeholder(match: re.Match) -> str:
            first, _, rest = match.group(1).partition(".")
            if first not in scope:
                return match.group(0)
            kind, target = scope[first]
            if kind == "value":
                return match.group(0) if rest else target
            return "{{" + target + ("." + rest if rest else "") + "}}"

        pieces = []
        for is_comment, segment in _split_comments(text, in_comment)[0]:
            if is_comment:
                pieces.append(segment)
                continue
            last = 0
            for span in CODE_SPAN_RE.finditer(segment):
                pieces.append(self._rewrite_prose(segment[last:span.start()], _placeholder, line))
                pieces.append(span.group(0))
                last = span.end()
            pieces.append(self._rewrite_prose(segment[last:], _placeholder, line))
        return "".join(pieces)

    def _rewrite_prose(self, text: str, replace: Any, line: int) -> str:
        if INLINE_STATEMENT_RE.search(text):
            raise self.error("err.statement.inline", line)
        return PLACEHOLDER_RE.sub(replace, text)


def _split_comments(text: str, open_: bool) -> Tuple[List[Tuple[bool, str]], bool]:
    """Zeile in (ist HTML-Kommentar, Text); dazu, ob am Ende ein Kommentar offen ist."""
    masked = CODE_SPAN_RE.sub(lambda span: " " * len(span.group(0)), text)
    parts: List[Tuple[bool, str]] = []
    pos = 0
    while pos < len(text):
        if open_:
            end = text.find("-->", pos)
            stop = len(text) if end < 0 else end + 3
            parts.append((True, text[pos:stop]))
            open_ = end < 0
        else:
            start = masked.find("<!--", pos)
            stop = len(text) if start < 0 else start
            parts.append((False, text[pos:stop]))
            open_ = start >= 0
        pos = stop
    return parts, open_


def _mark_code(markdown: str) -> List[Line]:
    """Code- und Kommentarzeilen bleiben woertlich: umzaeunt, eingerueckt, `<!-- -->`."""
    lines: List[Line] = []
    fence: Optional[str] = None
    comment = False
    containers: List[int] = []  # Einrueckung des Inhalts je offener Liste o. ae.
    code_indent: Optional[int] = None
    after_blank = True
    for number, text in enumerate(markdown.splitlines(keepends=True), start=1):
        body = text[QUOTE_RE.match(text).end():].expandtabs(4)
        blank = not body.strip()
        indent = len(body) - len(body.lstrip())
        fence_match = FENCE_RE.match(text)
        if fence is not None:
            in_code = True
            closer = fence_match.group(1) if fence_match else ""
            if closer[:1] == fence[0] and len(closer) >= len(fence):
                fence = None
        elif comment:
            in_code = False
        else:
            if code_indent is not None and not blank and indent < code_indent:
                code_indent = None
            if after_blank and not blank:
                while containers and indent < containers[-1]:
                    containers.pop()
            base = containers[-1] if containers else 0
            if code_indent is None and after_blank and not blank and indent >= base + 4:
                code_indent = base + 4
            in_code = code_indent is not None
            if not in_code and fence_match:
                fence, in_code = fence_match.group(1), True
            elif not in_code and CONTAINER_RE.match(body.lstrip()):
                containers.append(indent + 4)
        if in_code:
            lines.append((number, text, True, False))
        else:
            parts, open_after = _split_comments(text, comment)
            literal = any(is_comment for is_comment, _ in parts) and all(
                is_comment or not part.strip() for is_comment, part in parts
            )
            lines.append((number, text, literal, comment and not literal))
            comment = open_after
        after_blank = blank
    return lines


def expand_statements(markdown: str, variables: Dict[str, Any], where: str) -> str:
    """Loest `{% for %}`, `{% endfor %}` und `{% set %}` im Markdown auf."""
    if "{%" not in markdown:
        return markdown
    expander = _Expander(variables, where)
    nodes, _ = expander.parse(_mark_code(markdown))
    return "".join(expander.render(nodes, {}))


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


def substitute_tree(elem: Any, variables: Dict[str, Any], where: str, in_link: bool = False) -> None:
    """Ersetzt in Text und Attributen, Code ausgenommen (dessen tail nicht).

    Das tail eines Kindes ersetzt das Elternelement: Nur dort laesst sich ein
    Link als Geschwister einfuegen.
    """
    if elem.tag in SKIP_TAGS:
        _restore_code(elem)
        return
    in_link = in_link or elem.tag == "a"

    def _text(text: str) -> Tuple[str, List[Any]]:
        if in_link:
            return _unescape(substitute(text, variables, where), "{{"), []
        return _substitute_linked(text, variables, where)

    children = list(elem)
    if elem.text:
        elem.text, links = _text(elem.text)
        elem[0:0] = links
    for attr in ATTRIBUTES:
        if elem.attrib.get(attr):
            elem.attrib[attr] = _unescape(substitute(elem.attrib[attr], variables, where), "{{")
    for child in children:
        substitute_tree(child, variables, where, in_link)
        if child.tail:
            child.tail, links = _text(child.tail)
            index = list(elem).index(child) + 1
            elem[index:index] = links
