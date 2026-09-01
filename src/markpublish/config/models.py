"""
Pydantic data models for markpublish configuration.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional, Union

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
    # Wert die Vorgabe fuer die gleichnamige Angabe an den Kapiteln.
    document_toc: TocScope = Field(
        default_factory=lambda: TocScope(enabled=True),
        description="Document TOC: 'none', 'full' or a depth; root for the chapters' document_toc",
    )
    autonum_style: AutonumStyle = Field(default=AutonumStyle.DECIMAL, description="Numbering style ('decimal', 'roman', 'legal', 'none')")
    autonum_from_level: int = Field(default=1, ge=1, description="Start heading level for autonumbering (default: 1)")
    autonum_prefix: Optional[str] = Field(default=None, description="Optional prefix for generated numbers")
    autonum_reset: bool = Field(default=False, description="Reset numbering counter per chapter")
    # Vorgabe fuer das kleine Verzeichnis auf den Kapitel-Trennseiten. Steht zu
    # `chapters.chapter_toc` wie `autonum_style` zu `chapters.autonum_style`: hier die
    # Wurzel, dort der Einzelfall. Ohne sie wiederholt ein Dokument mit zehn
    # Kapiteln zehnmal dieselbe Zeile.
    chapter_toc: TocScope = Field(
        default_factory=lambda: TocScope(enabled=False),
        description="Default for chapters' divider-page TOC: 'none', 'full' or a depth",
    )
    header: bool = Field(default=True, description="Enable the running header; its lines are laid out in the theme")
    footer: bool = Field(default=True, description="Enable the running footer; its lines are laid out in the theme")

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
            v_lower = v.lower().strip()
            for item in AutonumStyle:
                if item.value == v_lower:
                    return item
        return AutonumStyle.DECIMAL

    @field_validator("document_toc", mode="before")
    @classmethod
    def parse_document_document_toc(cls, v: Any) -> TocScope:
        return parse_toc_scope(v, "document.document_toc")

    @field_validator("chapter_toc", mode="before")
    @classmethod
    def parse_document_chapter_toc(cls, v: Any) -> TocScope:
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
    # Das kleine Verzeichnis auf der Trennseite. Standard: keins.
    chapter_toc: Optional[TocScope] = Field(
        default=None,
        description="Local TOC on the chapter divider page: 'none', 'full' or a depth",
    )
    # Der Beitrag zum grossen Verzeichnis vorn im Dokument. Standard: voll.
    # None heisst "nicht gesetzt" und erbt vom Part bzw. Elternkapitel - deshalb
    # Optional statt eines Defaults, sonst waere "geerbt" von "ausdruecklich
    # voll" nicht zu unterscheiden.
    document_toc: Optional[TocScope] = Field(
        default=None,
        description="Contribution to the document TOC: 'none', 'full' or a depth; inherited downwards",
    )
    autonum_style: Optional[Union[AutonumStyle, str]] = Field(default=None, description="Override numbering style for this chapter")
    autonum_from_level: Optional[int] = Field(default=None, ge=1, description="Start heading level for autonumbering; inherited downwards")
    autonum_prefix: Optional[str] = Field(default=None, description="Optional prefix for generated numbers; inherited downwards")
    autonum_reset: Optional[bool] = Field(default=None, description="Whether to reset counter at chapter start; inherited downwards")
    chapters: List[ChapterItem] = Field(default_factory=list, description="Nested child chapters")

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
        # None heisst "nicht gesetzt" - erst die Pipeline entscheidet daraus
        # geerbt oder voll. Das ist kein Wert, den jemand hinschreibt.
        if v is None:
            return None
        return parse_toc_scope(v, "chapters.document_toc")

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

