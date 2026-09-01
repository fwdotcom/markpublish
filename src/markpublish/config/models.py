"""
Pydantic data models for markpublish configuration.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from markpublish.i18n import default_document_language


class AutonumStyle(str, Enum):
    DECIMAL = "decimal"    # 1, 1.1, 1.1.1
    ROMAN = "roman"        # I, I.1, I.1.1
    LEGAL = "legal"        # 1., 1.1., 1.1.1.
    NONE = "none"          # No automatic numbering


# Alias fuer Abwaertskompatibilitaet
AutonumType = AutonumStyle


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
    header: bool = Field(default=True, description="Enable running header")
    footer: bool = Field(default=True, description="Enable running footer")

    # Allow custom extra fields for custom template needs
    model_config = {
        "extra": "allow"
    }

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

        if "autonum_type" in data and "autonum_style" not in data:
            data["autonum_style"] = data.pop("autonum_type")

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


class ChapterItem(BaseModel):
    """
    Represents a single chapter (content markdown file).
    """
    file: Optional[str] = Field(default=None, description="Path to markdown file")
    title: Optional[str] = Field(default=None, description="Chapter title")
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

    model_config = {
        "extra": "allow"
    }

    @model_validator(mode="before")
    @classmethod
    def map_legacy_autonum(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "autonum" in data and "autonum_style" not in data:
                data["autonum_style"] = data.pop("autonum")
        return data

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
        return self.title or ""


class PartItem(BaseModel):
    """
    Represents an overarching Part / Section containing a flat list of chapters.
    """
    title: Optional[str] = Field(default=None, description="Part title")
    part: Optional[str] = Field(default=None, description="Alternative key for part title")
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
    chapters: List[ChapterItem] = Field(default_factory=list, description="List of chapters in this part")

    model_config = {
        "extra": "allow"
    }

    @model_validator(mode="before")
    @classmethod
    def validate_part_structure(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "autonum" in data and "autonum_style" not in data:
                data["autonum_style"] = data.pop("autonum")
            if not data.get("part") and not data.get("title"):
                raise ValueError(
                    "Jeder Part in 'parts' muss einen Namen tragen (Schlüssel 'title' oder 'part'). "
                    "Ein unbenannter Block ohne Titel ist nicht zulässig."
                )
            if "chapters" not in data or not data["chapters"]:
                raise ValueError(
                    f"Der Part '{data.get('title') or data.get('part')}' muss mindestens ein Kapitel unter 'chapters' enthalten."
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
        return self.title or self.part or ""


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
    def normalize_parts_and_chapters(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # Wenn 'chapters' auf Root-Ebene angegeben ist (Legacy-Migration)
        if "chapters" in data and ("parts" not in data or not data["parts"]):
            raw_chapters = data.get("chapters", [])
            parts_list: List[Dict[str, Any]] = []
            current_main_chapters: List[Any] = []

            for item in raw_chapters:
                if isinstance(item, dict) and ("part" in item or "title" in item and "chapters" in item and not item.get("file")):
                    if current_main_chapters:
                        parts_list.append({"title": "Hauptteil", "break_before": "none", "document_toc": "none", "chapters": current_main_chapters})
                        current_main_chapters = []
                    parts_list.append(item)
                else:
                    current_main_chapters.append(item)

            if current_main_chapters:
                parts_list.append({"title": "Hauptteil", "break_before": "none", "document_toc": "none", "chapters": current_main_chapters})

            data["parts"] = parts_list

        return data

    @property
    def chapters(self) -> List[ChapterItem]:
        """Flache Liste aller Kapitel ueber alle Parts hinweg."""
        all_ch: List[ChapterItem] = []
        for p in self.parts:
            all_ch.extend(p.chapters)
        return all_ch

