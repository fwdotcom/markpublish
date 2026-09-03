"""
Tests for configuration parsing and data models.
"""

import datetime

from markpublish.config.loader import format_current_date, load_config
from markpublish.config.models import AutonumStyle, BreakBefore, TocScope


def test_format_current_date():
    today = datetime.date.today()
    assert format_current_date("de") == today.strftime("%d.%m.%Y")
    assert format_current_date("en") == today.strftime("%Y-%m-%d")


def test_load_config_from_dict():
    raw = {
        "document": {
            "title": "Test Title",
            "subtitle": "Test Subtitle",
            "author": "Test Author",
            "status": "Freigegeben",
            "copyright": "© 2026 Frank Winter",
            "date": "auto",
            "version": "2.0.0",
            "language": "de",
            "cover": True,
            "document_toc": "full",
            "autonum_style": "decimal",
        },
        "theme": "default",
        "parts": [
            {
                "title": "Main",
                "break_before": "none",
                "document_toc": "none",
                "chapters": [
                    {
                        "file": "chapters/01.md",
                        "title": "Chapter 1",
                        "break_before": "divider",
                        "chapter_toc": 2,
                    },
                ],
            },
            {
                "part": "Appendices",
                "summary": "Appendix section",
                "break_before": "divider",
                "autonum_style": "none",
                "chapters": [
                    {
                        "file": "chapters/app_a.md",
                        "title": "App A",
                    }
                ],
            },
        ],
    }

    config = load_config(raw)
    assert config.document.title == "Test Title"
    assert config.document.subtitle == "Test Subtitle"
    assert config.document.status == "Freigegeben"
    assert config.document.copyright == "© 2026 Frank Winter"
    assert config.document.date == datetime.date.today().strftime("%d.%m.%Y")
    assert config.document.autonum_style == AutonumStyle.DECIMAL
    assert len(config.parts) == 2
    assert len(config.chapters) == 2

    # Check chapter 1 in main part
    main_part = config.parts[0]
    assert len(main_part.chapters) == 1
    c1 = main_part.chapters[0]
    assert c1.title == "Chapter 1"
    assert c1.break_before is BreakBefore.DIVIDER
    assert isinstance(c1.chapter_toc, TocScope)
    assert c1.chapter_toc.enabled is True
    assert c1.chapter_toc.max_depth == 2

    # Check part
    p = config.parts[1]
    assert p.is_part is True
    assert p.part == "Appendices"
    assert p.autonum_style == AutonumStyle.NONE
    assert len(p.chapters) == 1
    assert p.chapters[0].title == "App A"


def test_load_config_from_yaml_string():
    yaml_text = """\

document:
  title: "YAML String Test"
  date: "2026-08-31"
  cover: false
theme: "custom"
parts:
  - title: "Hauptteil"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "01.md"
"""
    config = load_config(yaml_text)
    assert config.document.title == "YAML String Test"
    assert config.document.date == "2026-08-31"
    assert config.document.cover is False
    assert config.theme == "custom"


def test_parts_must_have_name():
    """Ein Part ohne title/part wirft einen Validierungsfehler."""
    import pytest
    from pydantic import ValidationError

    raw_invalid = {
        "document": {"title": "Test"},
        "parts": [
            {
                "chapters": [{"file": "01.md"}]
            }
        ]
    }
    with pytest.raises(ValidationError, match="Jeder Part in 'parts' muss einen Namen tragen"):
        load_config(raw_invalid)

    raw_valid = {
        "document": {"title": "Test"},
        "parts": [
            {
                "title": "Hauptteil",
                "chapters": [{"file": "01.md"}]
            }
        ]
    }
    config = load_config(raw_valid)
    assert len(config.parts) == 1
    assert config.parts[0].title == "Hauptteil"


def test_pagenum_reset_configuration():
    """Prueft, dass pagenum_reset auf Part- und Kapitel-Ebene korrekt geladen wird."""
    raw = {
        "document": {"title": "Test"},
        "parts": [
            {
                "title": "Hauptteil",
                "chapters": [{"file": "01.md"}]
            },
            {
                "title": "Anhänge",
                "pagenum_reset": True,
                "chapters": [
                    {"file": "app.md", "pagenum_reset": False}
                ]
            }
        ]
    }
    config = load_config(raw)
    assert config.parts[0].pagenum_reset is None
    assert config.parts[1].pagenum_reset is True
    assert config.parts[1].chapters[0].pagenum_reset is False


def test_part_and_chapter_naming_and_title_tolerance():
    """
    Prueft die Vereinheitlichung auf 'part' und 'chapter':
    - 'part' ist der primaere Schluessel fuer Abschnitte.
    - 'chapter' ist der Bezeichner fuer Kapitel.
    - 'title' auf Part oder Chapter wird wie ein Custom-Feld toleriert (kein Fehler).
    """
    raw = {
        "document": {"title": "Testdoc"},
        "parts": [
            {
                "part": "Erster Abschnitt",
                "title": "Ignorierter Part-Titel",
                "chapters": [
                    {
                        "file": "01.md",
                        "chapter": "Einstieg",
                        "title": "Ignorierter Kapitel-Titel",
                    }
                ],
            },
            {
                # Legacy: nur title auf Part ohne part-Schluessel
                "title": "Zweiter Abschnitt",
                "chapters": [{"file": "02.md"}],
            },
        ],
    }
    config = load_config(raw)
    p0 = config.parts[0]
    assert p0.part == "Erster Abschnitt"
    assert p0.display_title == "Erster Abschnitt"
    assert p0.chapters[0].chapter == "Einstieg"

    p1 = config.parts[1]
    assert p1.part == "Zweiter Abschnitt"
    assert p1.display_title == "Zweiter Abschnitt"
    assert p1.chapters[0].chapter is None



