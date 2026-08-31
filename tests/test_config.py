"""
Tests for configuration parsing and data models.
"""

import datetime

from markpublish.config.loader import format_current_date, load_config
from markpublish.config.models import AutonumType, ChapterTOCConfig


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
            "toc": True,
            "autonum_type": "decimal",
        },
        "theme": "default",
        "chapters": [
            {
                "file": "chapters/01.md",
                "title": "Chapter 1",
                "divider_page": True,
                "toc": 2,
            },
            {
                "part": "Appendices",
                "summary": "Appendix section",
                "divider_page": True,
                "autonum": "none",
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
    assert config.document.autonum_type == AutonumType.DECIMAL
    assert len(config.chapters) == 2

    # Check chapter 1
    c1 = config.chapters[0]
    assert c1.title == "Chapter 1"
    assert c1.divider_page is True
    assert isinstance(c1.toc, ChapterTOCConfig)
    assert c1.toc.enabled is True
    assert c1.toc.max_depth == 2

    # Check part
    p = config.chapters[1]
    assert p.is_part is True
    assert p.part == "Appendices"
    assert p.autonum == "none"
    assert len(p.chapters) == 1
    assert p.chapters[0].title == "App A"


def test_load_config_from_yaml_string():
    yaml_text = """
document:
  title: "YAML String Test"
  date: "2026-08-31"
  cover: false
theme: "custom"
chapters:
  - file: "01.md"
"""
    config = load_config(yaml_text)
    assert config.document.title == "YAML String Test"
    assert config.document.date == "2026-08-31"
    assert config.document.cover is False
    assert config.theme == "custom"

