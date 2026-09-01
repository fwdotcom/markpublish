"""
Pydantic data models for markpublish configuration.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class AutonumType(str, Enum):
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
    language: str = Field(default="de", description="ISO language code, e.g. 'de' or 'en'")

    # Global Layout Switches
    cover: bool = Field(default=True, description="Enable cover page")
    toc: bool = Field(default=True, description="Enable global table of contents")
    autonum_type: AutonumType = Field(default=AutonumType.DECIMAL, description="Numbering style")
    header: bool = Field(default=True, description="Enable the running header; its lines are laid out in the theme")
    footer: bool = Field(default=True, description="Enable the running footer; its lines are laid out in the theme")

    # Allow custom extra fields for custom template needs
    model_config = {
        "extra": "allow"
    }

    @field_validator("autonum_type", mode="before")
    @classmethod
    def parse_autonum_type(cls, v: Any) -> AutonumType:
        if isinstance(v, AutonumType):
            return v
        if isinstance(v, str):
            v_lower = v.lower().strip()
            for item in AutonumType:
                if item.value == v_lower:
                    return item
        return AutonumType.DECIMAL

    @model_validator(mode="before")
    @classmethod
    def reject_document_level_labels(cls, data: Any) -> Any:
        """
        `document.i18n` (und der alte Alias `document.labels`) gibt es nicht mehr.

        Statische Texte werden ausschliesslich im Theme definiert. Ein stiller
        Fehlschlag waere hier besonders teuer: `extra: allow` wuerde den Block
        anstandslos schlucken, der Build liefe durch, und im PDF staende
        weiterhin der alte Text - ohne jeden Hinweis worauf es ankam.
        """
        if not isinstance(data, dict):
            return data

        for key in ("i18n", "labels"):
            if key in data:
                raise ValueError(
                    f"document.{key} wird nicht mehr unterstuetzt. Statische Texte "
                    "gehoeren in die i18n.yaml des Themes:\n"
                    "  <templates>/<theme>/i18n.yaml          fuer alle Zielformate\n"
                    "  <templates>/<theme>/<pdf|html>/i18n.yaml  nur fuer ein Zielformat\n"
                    "Der Aufbau ist derselbe wie bisher (Sprachcode, darunter die Texte). "
                    "Ein eigenes Theme legen Sie mit 'markpublish export-template' an; "
                    "'markpublish labels' zeigt, was am Ende gilt."
                )
        return data


class ChapterTOCConfig(BaseModel):
    """Configuration for per-chapter local table of contents."""
    enabled: bool = Field(default=True, description="Enable local chapter TOC")
    max_depth: int = Field(default=3, description="Maximum heading depth for chapter TOC")

    def __bool__(self) -> bool:
        """
        A BaseModel is truthy by default, so `if chapter.toc:` would render the
        local TOC even for `toc: {enabled: false}`. Templates and pipeline both
        test the object directly - make that test mean what it reads like.
        """
        return self.enabled and self.max_depth > 0


class ChapterItem(BaseModel):
    """
    Represents a chapter, sub-chapter, or overarching Part.
    Supports recursive nesting via 'chapters'.
    """
    file: Optional[str] = Field(default=None, description="Path to markdown file")
    title: Optional[str] = Field(default=None, description="Chapter or Part title")
    summary: Optional[str] = Field(default=None, description="Chapter or Part summary")
    part: Optional[str] = Field(default=None, description="If set, declares this item as a Part/Block header")
    # Ein Kapitel beginnt oben auf einer Seite - das ist die Erwartung an ein
    # gesetztes Dokument, nicht die Ausnahme. Wer Fliesstext ueber Kapitel
    # hinweg will (kurze Abschnitte, Merkblaetter), setzt "none"; wer das
    # Kapitel staerker absetzen will, "divider".
    break_before: BreakBefore = Field(
        default=BreakBefore.PAGE,
        description="How this chapter is set off: 'page', 'divider' or 'none'",
    )
    toc: Union[bool, int, ChapterTOCConfig] = Field(default=False, description="Per-chapter TOC (bool, max_depth int, or config)")
    # Begrenzt, wie tief dieser Zweig ins globale Inhaltsverzeichnis einzieht.
    # Gezaehlt wird innerhalb des Kapitels, wie bei `toc`: 1 ist die eigene
    # Ueberschrift, 2 die Ebene darunter. None heisst unbegrenzt.
    toc_depth: Optional[int] = Field(default=None, description="Max heading depth this branch adds to the global TOC")
    autonum: Optional[Union[AutonumType, str]] = Field(default=None, description="Override numbering type for this chapter")
    chapters: List[ChapterItem] = Field(default_factory=list, description="Nested child chapters")

    model_config = {
        "extra": "allow"
    }

    @field_validator("toc", mode="before")
    @classmethod
    def parse_toc(cls, v: Any) -> Union[bool, ChapterTOCConfig]:
        if isinstance(v, bool):
            return ChapterTOCConfig(enabled=v, max_depth=3) if v else False
        if isinstance(v, int):
            return ChapterTOCConfig(enabled=True, max_depth=v)
        if isinstance(v, dict):
            return ChapterTOCConfig(**v)
        if isinstance(v, ChapterTOCConfig):
            return v
        return False

    @field_validator("break_before", mode="before")
    @classmethod
    def parse_break_before(cls, v: Any) -> BreakBefore:
        """
        Unbekannte Werte brechen ab, statt auf den Standard zurueckzufallen.

        Ein stiller Rueckfall waere hier besonders teuer: aus einem vertippten
        "divder" wuerde klaglos ein normaler Seitenumbruch, das Dokument baute
        durch, und die fehlende Trennseite faende man erst beim Durchblaettern
        des fertigen PDFs - ohne jeden Hinweis worauf es ankam.
        """
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

    @field_validator("toc_depth", mode="before")
    @classmethod
    def parse_toc_depth(cls, v: Any) -> Optional[int]:
        """
        `toc_depth: 0` oder negativ waere ein Kapitel, das im Inhaltsverzeichnis
        gar nicht vorkaeme - dafuer gibt es keinen sinnvollen Anwendungsfall,
        und ein stiller Ausschluss waere im fertigen PDF schwer zu finden.
        """
        if v is None:
            return None
        depth = int(v)
        if depth < 1:
            raise ValueError(
                f"chapters.toc_depth muss mindestens 1 sein (war: {depth}). "
                "1 nimmt nur die Kapitelueberschrift ins Inhaltsverzeichnis auf."
            )
        return depth

    @property
    def is_part(self) -> bool:
        """Returns True if this node acts as an overarching Part/Block."""
        return self.part is not None or (self.file is None and self.title is not None and bool(self.chapters))

    @property
    def display_title(self) -> str:
        """Returns the title or part name."""
        return self.part or self.title or ""


class MarkpublishConfig(BaseModel):
    """Root configuration for markpublish."""
    document: DocumentConfig
    theme: str = Field(default="default", description="Selected theme/template name")
    templates_dir: Optional[str] = Field(default=None, description="Optional custom path to shared templates folder")
    chapters: List[ChapterItem] = Field(default_factory=list, description="List of chapters and parts")

    model_config = {
        "extra": "allow"
    }

