"""
Pydantic data models for markpublish configuration.
"""

from __future__ import annotations

import difflib
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from markpublish.i18n import default_document_language
from markpublish.markdown.pattern import compile_pattern
from markpublish.ui import t, tn

#: Vorgabe fuer das ganze Dokument: Parts ohne Nummer, Kapitel 1, 1.1, 1.1.1.
DEFAULT_AUTONUM_PATTERN = "_|1|.1|+"


def check_pattern(value: Any, scope: str) -> Any:
    """
    Uebersetzt das Pattern einmal probeweise, damit ein Fehler beim Laden faellt.

    Erst beim Setzen der ersten Ueberschrift abzubrechen hiesse: das halbe
    Dokument ist schon gebaut, und die Meldung steht zwischen Fortschritts-
    zeilen statt neben der Zeile, die sie verursacht hat.
    """
    compile_pattern(value, scope)
    return value


def keep_explicit_none(data: Any, key: str) -> Any:
    """
    Haelt `autonum_pattern:` ohne Wert von einem fehlenden Schluessel getrennt.

    YAML liefert fuer beide `None`, gemeint ist aber das Gegenteil: der
    fehlende Schluessel erbt, der leere schaltet ab. Der notierte Fall wird
    deshalb auf die Zeichenkette gebracht, die er meint.
    """
    if isinstance(data, dict) and key in data and data[key] is None:
        data = dict(data)
        data[key] = "none"
    return data


class ConfigurationError(ValueError):
    """Raised when a configuration or document structure rule is violated."""
    pass


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
            t("err.config.toc_bool", key_path=key_path)
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
                t("err.config.toc_value", key_path=key_path, allowed=allowed, value=repr(value))
            )

    if isinstance(value, int):
        if value < 1:
            raise ValueError(
                t("err.config.toc_depth", key_path=key_path, value=value)
            )
        return TocScope(enabled=True, max_depth=value)

    if isinstance(value, dict):
        return TocScope(**value)

    raise ValueError(
        t("err.config.toc_kind", key_path=key_path, value=repr(value))
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
    # Aus, solange es niemand einschaltet. Ein Deckblatt ist eine Entscheidung
    # ueber das Dokument, keine Grundausstattung - wer ein paar Seiten Markdown
    # setzt, bekaeme sonst ein Titelblatt, das er nicht bestellt hat, und
    # muesste erst herausfinden, welcher Schluessel es wieder wegnimmt.
    cover: bool = Field(default=False, description="Enable cover page")
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
    # Slot 1 ist hier der Part, Slot 2 das Kapitel, Slot 3 die h2. Die Vorgabe
    # ueberspringt den Part: die wenigsten Dokumente nummerieren ihn.
    autonum_pattern: Optional[str] = Field(
        default=DEFAULT_AUTONUM_PATTERN,
        description="Numbering pattern; slot 1 is the part, slot 2 the chapter",
    )
    autonum_reset: bool = Field(
        default=False,
        description="Whether the levels below start again at one",
    )
    # Wie die Ebenen darunter heissen. Ohne Angabe die Woerter aus der
    # i18n-Kaskade; notiert erscheinen sie zusaetzlich vor der Ueberschrift.
    part_label: Optional[str] = Field(
        default=None, description="Word naming a part, e.g. 'Teil'; default from the i18n cascade"
    )
    chapter_label: Optional[str] = Field(
        default=None, description="Word naming a chapter, e.g. 'Kapitel'; default from the i18n cascade"
    )
    pagenum_reset: bool = Field(
        default=False,
        description="Whether page numbering resets per part or chapter",
    )
    header: bool = Field(default=True, description="Enable running header")
    footer: bool = Field(default=True, description="Enable running footer")

    @field_validator("autonum_pattern")
    @classmethod
    def validate_autonum_pattern(cls, v: Any) -> Any:
        return check_pattern(v, "document")

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
    def keep_explicit_pattern_none(cls, data: Any) -> Any:
        return keep_explicit_none(data, "autonum_pattern")

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
                    t("err.config.document_unknown", key=key)
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
        hint = t("err.config.did_you_mean", candidate=close[0]) if close else ""
        lines.append(f"  '{key}'{hint}")

    listed = "\n".join(lines)
    raise ValueError(
        tn("err.config.unknown_key", len(unknown), where=where)
        + "\n"
        + listed
        + "\n"
        + t("err.config.unknown_key.allowed", allowed=", ".join(sorted(known)))
        + "\n"
        + t("err.config.unknown_key.hint")
    )


class ChapterItem(BaseModel):
    """
    Represents a single chapter (content markdown file).
    """
    file: Optional[str] = Field(default=None, description="Path to markdown file")
    toc_title: Optional[str] = Field(default=None, description="Title for document TOC, part TOC and running headers")
    divider_title: Optional[str] = Field(default=None, description="Title on chapter divider page")
    show_title: bool = Field(default=True, description="Whether to render the markdown H1 heading on the content page")
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
    # Slot 1 ist hier die h2: ein Kapitel beschreibt, was in ihm steht, nicht
    # seine eigene Nummer -- die gehoert seinem Part.
    autonum_pattern: Optional[str] = Field(default=None, description="Numbering pattern for this chapter; slot 1 is h2")
    autonum_reset: Optional[bool] = Field(default=None, description="Whether the levels below start again at one")
    label: Optional[str] = Field(default=None, description="Word naming this chapter, e.g. 'Anhang'")
    pagenum_reset: Optional[bool] = Field(default=None, description="Reset page numbers at chapter start")
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def reject_unknown_chapter_keys(cls, data: Any) -> Any:
        """
        Ein 'chapters' *im* Kapitel bekommt eine eigene Meldung.

        Ueber den allgemeinen Weg liefe es auf "unbekannter Schluessel
        'chapters' -- meinten Sie 'chapter'?" hinaus, und 'chapter' ist ein
        Alt-Feld, das nichts tut. Der Vorschlag schickte also genau in die
        falsche Richtung. Verschachtelte Kapitel gab es frueher; sie sind
        ersatzlos entfallen, und das gehoert in die Meldung.
        """
        if isinstance(data, dict):
            if "chapters" in data:
                raise ValueError(t("err.config.chapters_nested"))
            for key in ("chapter_label", "part_label"):
                if key in data:
                    raise ValueError(t("err.config.label_scope", key=key))
        data = keep_explicit_none(data, "autonum_pattern")
        return reject_unknown_keys(data, cls, "chapters")

    @field_validator("autonum_pattern")
    @classmethod
    def validate_autonum_pattern(cls, v: Any) -> Any:
        return check_pattern(v, "chapter")

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
            t("err.config.break_before", key_path="chapters.break_before", allowed=allowed, value=repr(v))
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
    subtitle: Optional[str] = Field(default=None, description="Part subtitle")
    summary: Optional[str] = Field(default=None, description="Part summary for divider page")
    break_before: Optional[BreakBefore] = Field(
        default=None,
        description="How this part is set off: 'divider', 'page' or 'none' (default: 'none')",
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
    # Slot 1 ist hier das Kapitel: ein Part beschreibt seine Kapitel, nicht
    # seine eigene Nummer -- die kommt aus dem document-Pattern.
    autonum_pattern: Optional[str] = Field(default=None, description="Numbering pattern for this part; slot 1 is the chapter")
    autonum_reset: Optional[bool] = Field(default=None, description="Whether the levels below start again at one")
    label: Optional[str] = Field(default=None, description="Word naming this part, e.g. 'Teil'")
    chapter_label: Optional[str] = Field(default=None, description="Word naming each chapter of this part, e.g. 'Anhang'")
    pagenum_reset: Optional[bool] = Field(default=None, description="Reset page numbers at the start of this part; inherited downwards")
    chapters: List[ChapterItem] = Field(default_factory=list, description="List of chapters in this part")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def reject_unknown_part_keys(cls, data: Any) -> Any:
        if isinstance(data, dict) and "part_label" in data:
            raise ValueError(t("err.config.label_scope", key="part_label"))
        data = keep_explicit_none(data, "autonum_pattern")
        return reject_unknown_keys(data, cls, "parts")

    @field_validator("autonum_pattern")
    @classmethod
    def validate_autonum_pattern(cls, v: Any) -> Any:
        return check_pattern(v, "part")

    @model_validator(mode="before")
    @classmethod
    def validate_part_structure(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("part"):
                raise ValueError(
                    t("err.config.part_needs_name")
                )
            if "chapters" not in data or not data["chapters"]:
                raise ValueError(
                    t("err.config.part_needs_chapters", part=data.get("part"))
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
            t("err.config.break_before", key_path="parts.break_before", allowed=allowed, value=repr(v))
        )

    @property
    def effective_break_before(self) -> BreakBefore:
        """
        Ohne Angabe gliedert ein Part, ohne sich selbst zu zeigen.

        Eine Trennseite als Vorgabe hiess: wer 'parts:' nur benutzt, weil der
        Aufbau sie verlangt - zwei Stufen, eine davon oft nur eine Klammer um
        die Kapitel -- bekam eine ganze Seite dafuer, die er nicht notiert
        hatte. Wer eine will, schreibt sie hin; das ist eine Zeile.
        """
        if self.break_before is not None:
            return self.break_before
        return BreakBefore.NONE

    @property
    def is_part(self) -> bool:
        return True

    @property
    def display_title(self) -> str:
        return self.toc_title or self.part or ""


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
            t("err.config.chapters_toplevel")
        )

    @property
    def chapters(self) -> List[ChapterItem]:
        """Flache Liste aller Kapitel ueber alle Parts hinweg."""
        all_ch: List[ChapterItem] = []
        for p in self.parts:
            all_ch.extend(p.chapters)
        return all_ch

