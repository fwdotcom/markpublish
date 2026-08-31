"""
Pydantic data models for markpublish configuration.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class AutonumType(str, Enum):
    DECIMAL = "decimal"    # 1, 1.1, 1.1.1
    ROMAN = "roman"        # I, I.1, I.1.1
    LEGAL = "legal"        # 1., 1.1., 1.1.1.
    NONE = "none"          # No automatic numbering


class DocumentConfig(BaseModel):
    """Document-level metadata and global layout switches."""
    title: str = Field(..., description="Document title")
    subtitle: Optional[str] = Field(default=None, description="Document subtitle")
    summary: Optional[str] = Field(default=None, description="Executive summary / abstract")
    author: Optional[str] = Field(default=None, description="Author name")
    status: Optional[str] = Field(default=None, description="Document status, e.g. 'Entwurf', 'Freigegeben', 'Draft'")
    copyright: Optional[str] = Field(default=None, description="Copyright statement, e.g. '© 2026 Frank Winter'")
    date: Optional[str] = Field(default="auto", description="Date string or 'auto'/'today'")
    version: Optional[str] = Field(default="1.0.0", description="Version string")
    language: str = Field(default="de", description="ISO language code, e.g. 'de' or 'en'")
    labels: Dict[str, str] = Field(
        default_factory=dict,
        description="Overrides for static template texts, e.g. {toc_title: 'Contents'}. "
                    "See markpublish.i18n.LABELS for the available keys.",
    )

    # Global Layout Switches
    cover: bool = Field(default=True, description="Enable cover page")
    toc: bool = Field(default=True, description="Enable global table of contents")
    autonum_type: AutonumType = Field(default=AutonumType.DECIMAL, description="Numbering style")
    header: bool = Field(default=True, description="Enable 2-line header")
    footer: bool = Field(default=True, description="Enable 2-line footer")

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
    divider_page: bool = Field(default=False, description="Insert a dedicated separator/divider page")
    toc: Union[bool, int, ChapterTOCConfig] = Field(default=False, description="Per-chapter TOC (bool, max_depth int, or config)")
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

