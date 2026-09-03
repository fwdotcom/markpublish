"""
Pydantic data models for markpublish configuration.
"""

from __future__ import annotations

import difflib
from enum import Enum
from typing import Any, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from markpublish.i18n import default_document_language


class ConfigurationError(ValueError):
    """Raised when a configuration or document structure rule is violated."""
    pass


class AutonumStyle(str, Enum):
    DECIMAL = "decimal"    # 1, 1.1, 1.1.1
    ROMAN = "roman"        # I, I.1, I.1.1
    LEGAL = "legal"        # 1., 1.1., 1.1.1.
    NONE = "none"          # No automatic numbering



class BreakBefore(str, Enum):
    """
    Wie ein Kapitel gegenueber dem vorigen abgesetzt wird.

    Die drei Werte sind eine Achse, keine unabhaengigen Schalter - deshalb ein
    Schluessel und nicht zwei. Als zwei Booleans liesse sich "Trennseite, aber
    kein Umbruch" hinschreiben; das gibt es nicht, eine Trennseite bricht immer
    um. Ein Zustand, den man notieren kann und der nichts bewirkt, ist eine
    Fehlerquelle ohne Gegenwert.
    """
    PAGE = "page"          # Kapitel beginnt oben auf einer neuen Seite
    DIVIDER = "divider"    # Kapitel beginnt mit einer eigenen Trennseite
    NONE = "none"          # Kapitel laeuft im Fliesstext weiter


class TocScope(BaseModel):
    """
    Wie weit ein Kapitel in *ein* Inhaltsverzeichnis hineinreicht.

    Dasselbe Wertevokabular fuer beide Verzeichnisse - `chapter_toc` fuer das
    kleine auf der Trennseite, `document_toc` fuer das grosse vorn im Dokument:

        none     gar nicht
        full     jede Ebene
        <Zahl>   bis zu dieser Tiefe, gezaehlt ab der Kapitelueberschrift

    Die Standardwerte unterscheiden sich - `chapter_toc` ist aus, `document_toc`
    voll - und genau das steht jetzt im Wert selbst statt in zwei Schluesseln,
    die verschieden heissen und verschieden zaehlen.
    """
    enabled: bool = Field(default=True, description="Whether the chapter appears in this TOC at all")
    max_depth: Optional[int] = Field(default=None, description="Maximum heading depth; None means unlimited")

    def __bool__(self) -> bool:
        """
        A BaseModel is truthy by default, so `if chapter.chapter_toc:` would
        render the local TOC even for `none`. Templates and pipeline both test
        the object directly - make that test mean what it reads like.
        """
        return self.enabled and (self.max_depth is None or self.max_depth > 0)


#: Die drei Schreibweisen, die beide TOC-Schluessel annehmen.
TOC_SCOPE_KEYWORDS = ("none", "full")


def parse_toc_scope(value: Any, key_path: str) -> TocScope:
    """
    Bringt `none`, `full` oder eine Tiefenangabe auf einen TocScope.

    Unbekannte Werte brechen ab. Ein stiller Rueckfall auf den Standard waere
    hier schlecht zu finden: ein vertipptes "fill" ergaebe klaglos ein
    Verzeichnis, dessen Fehlen erst beim Durchblaettern auffiele.
    """
    if isinstance(value, TocScope):
        return value

    if isinstance(value, bool):
        # true/false saehe man die Tiefe nicht an - genau deshalb gibt es die
        # Schluesselwoerter. Ein Wahrheitswert ist hier also keine Abkuerzung,
        # sondern eine Angabe, die die Haelfte der Information unterschlaegt.
        raise ValueError(
            f"{key_path} nimmt keine Wahrheitswerte. "
            f"Schreiben Sie 'none', 'full' oder eine Tiefe (z. B. 2)."
        )

    if isinstance(value, str):
        keyword = value.lower().strip()
        if keyword == "none":
            return TocScope(enabled=False)
        if keyword == "full":
            return TocScope(enabled=True, max_depth=None)
        if keyword.isdigit():
            value = int(keyword)
        else:
            allowed = ", ".join(f"'{k}'" for k in TOC_SCOPE_KEYWORDS)
            raise ValueError(
                f"{key_path} kennt {allowed} oder eine Tiefe als Zahl "
                f"(war: {value!r})."
            )

    if isinstance(value, int):
        if value < 1:
            raise ValueError(
                f"{key_path} braucht eine Tiefe ab 1 (war: {value}). "
                f"Fuer 'kommt nicht vor' schreiben Sie 'none'."
            )
        return TocScope(enabled=True, max_depth=value)

    if isinstance(value, dict):
        return TocScope(**value)

    raise ValueError(
        f"{key_path} kennt 'none', 'full' oder eine Tiefe als Zahl "
        f"(war: {value!r})."
    )


class DocumentConfig(BaseModel):
    """Document-level metadata and global layout switches."""
    model_config = ConfigDict(extra="allow")

    title: str = Field(..., description="Document title")
    subtitle: Optional[str] = Field(default=None, description="Document subtitle")
    summary: Optional[str] = Field(default=None, description="Executive summary / abstract")
    author: Optional[str] = Field(default=None, description="Author name")
    status: Optional[str] = Field(default=None, description="Document status, e.g. 'Entwurf', 'Freigegeben', 'Draft'")
    copyright: Optional[str] = Field(default=None, description="Copyright statement, e.g. '© 2026 Frank Winter'")
    date: Optional[str] = Field(default="auto", description="Date string or 'auto'/'today'")
    # Kein Default-Wert: eine erfundene "1.0.0" liesse sich im Dokument nicht
    # mehr abschalten - jedes Template saehe eine gesetzte Version und druckte
    # sie. Wer eine Version will, schreibt sie hin.
    version: Optional[str] = Field(default=None, description="Version string, e.g. '1.0.0'")
    # Ohne Angabe die Systemsprache: wer nichts hinschreibt, schreibt fast
    # immer in der Sprache, in der sein Rechner mit ihm redet. Ein fest
    # verdrahteter Code waere fuer die Haelfte aller Nutzer schlicht falsch.
    # Wer ein Dokument auf jedem Rechner gleich gebaut haben will, notiert die
    # Sprache - `markpublish init` tut das von sich aus.
    language: str = Field(
        default_factory=default_document_language,
        description="ISO language code, e.g. 'de' or 'en'; defaults to the system language",
    )

    # Global Layout Switches
    cover: bool = Field(default=True, description="Enable cover page")
    # Das grosse Verzeichnis vorn. 'none' laesst es ganz weg, sonst gibt der
    # Wert die Vorgabe fuer die gleichnamige Angabe an den Kapiteln
    document_toc: TocScope = Field(
        default_factory=lambda: TocScope(enabled=True, max_depth=None),
        description="Contribution to the document TOC: 'none', 'full' or a depth",
    )
    # Vorgabe fuer Part-Trennseiten-TOCs. Standard: 'full'.
    part_toc: TocScope = Field(
        default_factory=lambda: TocScope(enabled=True, max_depth=None),
        description="Default local TOC on part divider pages: 'none', 'full' or a depth",
    )
    # Vorgabe fuer Kapitel-Trennseiten-TOCs. Standard: 'full'.
    chapter_toc: TocScope = Field(
        default_factory=lambda: TocScope(enabled=True, max_depth=None),
        description="Default local TOC on chapter divider pages: 'none', 'full' or a depth",
    )
    autonum_style: AutonumStyle = Field(
        default=AutonumStyle.DECIMAL,
        description="Global heading numbering style: decimal, roman, legal, or none",
    )
    autonum_from_level: int = Field(
        default=1,
        ge=1,
        description="Heading level from which numbering starts (1 = h1, 2 = h2, ...)",
    )
    autonum_prefix: Optional[str] = Field(
        default=None,
        description="Optional prefix prepended to numbers (e.g. 'A.' -> A.1, A.2)",
    )
    autonum_reset: bool = Field(
        default=False,
        description="Whether each chapter starts numbering fresh",
    )
    pagenum_reset: bool = Field(
        default=False,
        description="Whether page numbering resets per part or chapter",
    )
    header: bool = Field(default=True, description="Enable running header")
    footer: bool = Field(default=True, description="Enable running footer")

    @field_validator("autonum_style", mode="before")
    @classmethod
    def parse_autonum_style(cls, v: Any) -> AutonumStyle:
        if isinstance(v, AutonumStyle):
            return v
        if isinstance(v, str):
            candidate = str(v).lower().strip()
            for item in AutonumStyle:
                if item.value == candidate:
                    return item
        return AutonumStyle.DECIMAL

    @field_validator("document_toc", mode="before")
    @classmethod
    def parse_document_document_toc(cls, v: Any) -> TocScope:
        if v is None:
            return TocScope(enabled=True, max_depth=None)
        return parse_toc_scope(v, "document.document_toc")

    @field_validator("part_toc", mode="before")
    @classmethod
    def parse_document_part_toc(cls, v: Any) -> TocScope:
        if v is None:
            return TocScope(enabled=True, max_depth=None)
        return parse_toc_scope(v, "document.part_toc")

    @field_validator("chapter_toc", mode="before")
    @classmethod
    def parse_document_chapter_toc(cls, v: Any) -> TocScope:
        if v is None:
            return TocScope(enabled=True, max_depth=None)
        return parse_toc_scope(v, "document.chapter_toc")

    @model_validator(mode="before")
    @classmethod
    def reject_document_level_labels(cls, data: Any) -> Any:
        """
        Statische Texte gehoeren ins Theme, nicht ins Dokument.

        Beides waeren plausible Stellen, an denen jemand sie vermutet -
        `document.i18n` genauso wie `document.labels`, weil die Templates das
        Ergebnis unter `labels.*` sehen. Ohne diesen Riegel wuerde
        `extra: allow` den Block anstandslos schlucken: der Build liefe durch,
        und im PDF staende der Standardtext, ohne jeden Hinweis worauf es
        ankam.
        """
        if not isinstance(data, dict):
            return data

        for key in ("i18n", "labels"):
            if key in data:
                raise ValueError(
                    f"document.{key} gibt es nicht. Statische Texte "
                    "gehoeren in die i18n.yaml des Themes:\n"
                    "  <templates>/<theme>/i18n.yaml          fuer alle Zielformate\n"
                    "  <templates>/<theme>/<pdf|html>/i18n.yaml  nur fuer ein Zielformat\n"
                    "Aufbau: Sprachcode, darunter die Texte. "
                    "Ein eigenes Theme legen Sie mit 'markpublish export-template' an; "
                    "'markpublish labels' zeigt, was am Ende gilt."
                )
        return data


def reject_unknown_keys(data: Any, model: type, where: str) -> Any:
    """
    Bricht bei einem Schluessel ab, den das Modell nicht kennt.

    Fuer Teile und Kapitel gilt das Gegenteil von `document:`: dort sind freie
    Felder eine Zusage -- sie erreichen das Theme und erscheinen im Dokument.
    Hier erreichen sie nichts. Ein geschluckter Schluessel waere also kein
    Feature, sondern ein stiller Verlust.

    Teuer wird das bei den Strukturschluesseln. `break_befor: "divider"` -- ein
    Buchstabe zu wenig -- liesse das Kapitel klaglos mit dem Standardumbruch
    setzen; auffallen wuerde es beim Durchblaettern des fertigen PDFs, wenn
    ueberhaupt. Deshalb steht hier ein Abbruch mit Namensvorschlag statt eines
    Defaults.
    """
    if not isinstance(data, dict):
        return data

    known = set(getattr(model, "model_fields", {}))
    unknown = [key for key in data if key not in known]
    if not unknown:
        return data

    lines = []
    for key in unknown:
        close = difflib.get_close_matches(str(key), sorted(known), n=1, cutoff=0.7)
        hint = f" -- meinten Sie '{close[0]}'?" if close else ""
        lines.append(f"  '{key}'{hint}")

    listed = "\n".join(lines)
    single = len(unknown) == 1
    raise ValueError(
        f"{where} kennt {'diesen Schluessel' if single else 'diese Schluessel'} nicht:\n"
        f"{listed}\n"
        f"Erlaubt sind: {', '.join(sorted(known))}.\n"
        f"Eigene Felder gibt es nur unter 'document:' -- dort erreichen sie das "
        f"Theme und erscheinen im Dokument. Auf einem Kapitel oder Teil bliebe "
        f"ein freies Feld wirkungslos."
    )


class ChapterItem(BaseModel):
    """
    Represents a single chapter (content markdown file).
    """
    file: Optional[str] = Field(default=None, description="Path to markdown file")
    toc_title: Optional[str] = Field(default=None, description="Title for document TOC, part TOC and running headers")
    divider_title: Optional[str] = Field(default=None, description="Title on chapter divider page")
    chapter: Optional[Any] = Field(default=None, description="Legacy/custom field, ignored")
    title: Optional[Any] = Field(default=None, description="Legacy/custom field, ignored")
    subtitle: Optional[str] = Field(default=None, description="Chapter subtitle")
    summary: Optional[str] = Field(default=None, description="Chapter summary")
    break_before: BreakBefore = Field(
        default=BreakBefore.PAGE,
        description="How this chapter is set off: 'page', 'divider' or 'none'",
    )
    document_toc: Optional[TocScope] = Field(
        default=None,
        description="Contribution to the document TOC: 'none', 'full' or a depth; inherited downwards",
    )
    chapter_toc: Optional[TocScope] = Field(
        default=None,
        description="Local TOC on the chapter divider page: 'none', 'full' or a depth",
    )
    autonum_style: Optional[Union[AutonumStyle, str]] = Field(default=None, description="Override numbering style for this chapter")
    autonum_from_level: Optional[int] = Field(default=None, ge=1, description="Start heading level for autonumbering; inherited downwards")
    autonum_prefix: Optional[str] = Field(default=None, description="Optional prefix for generated numbers; inherited downwards")
    autonum_reset: Optional[bool] = Field(default=None, description="Whether to reset counter at chapter start; inherited downwards")
    pagenum_reset: Optional[bool] = Field(default=None, description="Reset page numbers at chapter start")
    # Unterkapitel. Bis eben trug sie `extra: allow` unbemerkt mit -- als rohe
    # Dicts, an jeder Pruefung vorbei: ein Tippfehler in einem Unterkapitel
    # fiel damit nirgends auf. Deklariert werden sie rekursiv geprueft wie
    # die oberste Ebene auch.
    chapters: List["ChapterItem"] = Field(
        default_factory=list, description="Nested sub-chapters"
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def reject_unknown_chapter_keys(cls, data: Any) -> Any:
        return reject_unknown_keys(data, cls, "chapters")

    @field_validator("chapter_toc", mode="before")
    @classmethod
    def parse_chapter_toc(cls, v: Any) -> Optional[TocScope]:
        if v is None:
            return None
        return parse_toc_scope(v, "chapters.chapter_toc")

    @field_validator("document_toc", mode="before")
    @classmethod
    def parse_document_toc(cls, v: Any) -> Optional[TocScope]:
        if v is None:
            return None
        return parse_toc_scope(v, "chapters.document_toc")

    @field_validator("break_before", mode="before")
    @classmethod
    def parse_break_before(cls, v: Any) -> BreakBefore:
        if isinstance(v, BreakBefore):
            return v
        if isinstance(v, str):
            candidate = v.lower().strip()
            for item in BreakBefore:
                if item.value == candidate:
                    return item
        allowed = ", ".join(f"'{item.value}'" for item in BreakBefore)
        raise ValueError(
            f"chapters.break_before kennt nur {allowed} (war: {v!r})."
        )

    @property
    def is_part(self) -> bool:
        return False

    @property
    def display_title(self) -> str:
        return ""


class PartItem(BaseModel):
    """
    Represents an overarching Part / Section containing a flat list of chapters.
    """
    part: Optional[str] = Field(default=None, description="Part name")
    toc_title: Optional[str] = Field(default=None, description="Title for document TOC and running headers")
    divider_title: Optional[str] = Field(default=None, description="Title on part divider page")
    title: Optional[Any] = Field(default=None, description="Legacy/custom field, fallback for part name")
    subtitle: Optional[str] = Field(default=None, description="Part subtitle")
    summary: Optional[str] = Field(default=None, description="Part summary for divider page")
    break_before: Optional[BreakBefore] = Field(
        default=None,
        description="How this part is set off: 'divider', 'page' or 'none' (default: 'divider')",
    )
    document_toc: Optional[TocScope] = Field(
        default=None,
        description="Contribution of this part to the document TOC; 'none' hides the part heading while including chapters",
    )
    part_toc: Optional[TocScope] = Field(
        default=None,
        description="Local TOC on the part divider page: 'none', 'full' or a depth",
    )
    chapter_toc: Optional[TocScope] = Field(
        default=None,
        description="Default chapter TOC for chapters in this part; inherited downwards",
    )
    autonum_style: Optional[Union[AutonumStyle, str]] = Field(default=None, description="Numbering style for this part; inherited downwards")
    autonum_from_level: Optional[int] = Field(default=None, ge=1, description="Start heading level for autonumbering; inherited downwards")
    autonum_prefix: Optional[str] = Field(default=None, description="Optional prefix for generated numbers; inherited downwards")
    autonum_reset: Optional[bool] = Field(default=None, description="Whether to reset counter; inherited downwards")
    pagenum_reset: Optional[bool] = Field(default=None, description="Reset page numbers at the start of this part; inherited downwards")
    chapters: List[ChapterItem] = Field(default_factory=list, description="List of chapters in this part")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def reject_unknown_part_keys(cls, data: Any) -> Any:
        return reject_unknown_keys(data, cls, "parts")

    @model_validator(mode="before")
    @classmethod
    def validate_part_structure(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("part") and not data.get("title"):
                raise ValueError(
                    "Jeder Part in 'parts' muss einen Namen tragen (Schlüssel 'part'). "
                    "Ein unbenannter Block ohne Part-Name ist nicht zulässig."
                )
            if not data.get("part") and data.get("title"):
                data["part"] = data.get("title")
            if "chapters" not in data or not data["chapters"]:
                raise ValueError(
                    f"Der Part '{data.get('part')}' muss mindestens ein Kapitel unter 'chapters' enthalten."
                )
        return data

    @field_validator("document_toc", mode="before")
    @classmethod
    def parse_document_toc(cls, v: Any) -> Optional[TocScope]:
        if v is None:
            return None
        return parse_toc_scope(v, "parts.document_toc")

    @field_validator("part_toc", mode="before")
    @classmethod
    def parse_part_toc(cls, v: Any) -> Optional[TocScope]:
        if v is None:
            return None
        return parse_toc_scope(v, "parts.part_toc")

    @field_validator("chapter_toc", mode="before")
    @classmethod
    def parse_chapter_toc(cls, v: Any) -> Optional[TocScope]:
        if v is None:
            return None
        return parse_toc_scope(v, "parts.chapter_toc")

    @field_validator("break_before", mode="before")
    @classmethod
    def parse_break_before(cls, v: Any) -> Optional[BreakBefore]:
        if v is None:
            return None
        if isinstance(v, BreakBefore):
            return v
        if isinstance(v, str):
            candidate = v.lower().strip()
            for item in BreakBefore:
                if item.value == candidate:
                    return item
        allowed = ", ".join(f"'{item.value}'" for item in BreakBefore)
        raise ValueError(
            f"parts.break_before kennt nur {allowed} (war: {v!r})."
        )

    @property
    def effective_break_before(self) -> BreakBefore:
        if self.break_before is not None:
            return self.break_before
        return BreakBefore.DIVIDER

    @property
    def is_part(self) -> bool:
        return True

    @property
    def display_title(self) -> str:
        return self.toc_title or self.part or (str(self.title) if self.title else "")


class MarkpublishConfig(BaseModel):
    """Root configuration for markpublish."""
    document: DocumentConfig
    theme: str = Field(default="default", description="Selected theme/template name")
    templates_dir: Optional[str] = Field(default=None, description="Optional custom path to shared templates folder")
    parts: List[PartItem] = Field(default_factory=list, description="List of document parts")

    model_config = {
        "extra": "allow"
    }

    @model_validator(mode="before")
    @classmethod
    def reject_chapters_at_root(cls, data: Any) -> Any:
        """
        Der Aufbau hat zwei Stufen: 'parts', darunter 'chapters'.

        Ein 'chapters' auf oberster Ebene ist die naheliegende Vermutung, wenn
        ein Dokument nur aus Kapiteln besteht - und ohne diesen Riegel die
        teuerste: 'extra: allow' schluckt den Schluessel wortlos, 'parts'
        bliebe leer, und heraus kaeme ein Dokument aus Deckblatt und sonst
        nichts. Ein Abbruch mit dem richtigen Aufbau daneben kostet eine
        Minute, ein leeres PDF findet man erst im Druck.
        """
        if not isinstance(data, dict) or "chapters" not in data:
            return data

        raise ValueError(
            "chapters gibt es auf oberster Ebene nicht - Kapitel stehen immer "
            "unter einem Part:\n"
            "  parts:\n"
            '    - title: "Hauptteil"\n'
            "      chapters:\n"
            '        - file: "kapitel/01.md"\n'
            'Ein Part ohne eigene Trennseite bekommt break_before: "none".'
        )

    @property
    def chapters(self) -> List[ChapterItem]:
        """Flache Liste aller Kapitel ueber alle Parts hinweg."""
        all_ch: List[ChapterItem] = []
        for p in self.parts:
            all_ch.extend(p.chapters)
        return all_ch

