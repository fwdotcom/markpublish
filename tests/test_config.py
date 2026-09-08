"""
Tests for configuration parsing and data models.
"""

import datetime

from markpublish.config.loader import format_current_date, load_config
from markpublish.config.models import (
    BreakBefore,
    ChapterItem,
    PartItem,
    TocScope,
)


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
            "autonum_pattern": "_|1|.1|+",
        },
        "theme": "default",
        "parts": [
            {
                "part": "Main",
                "break_before": "none",
                "document_toc": "none",
                "chapters": [
                    {
                        "file": "chapters/01.md",
                        "toc_title": "Chapter 1",
                        "break_before": "divider",
                        "chapter_toc": 2,
                    },
                ],
            },
            {
                "part": "Appendices",
                "summary": "Appendix section",
                "break_before": "divider",
                "autonum_pattern": "none",
                "chapters": [
                    {
                        "file": "chapters/app_a.md",
                        "toc_title": "App A",
                        "label": "Appendix",
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
    assert config.document.autonum_pattern == "_|1|.1|+"
    assert len(config.parts) == 2
    assert len(config.chapters) == 2

    # Check chapter 1 in main part
    main_part = config.parts[0]
    assert len(main_part.chapters) == 1
    c1 = main_part.chapters[0]
    assert c1.toc_title == "Chapter 1"
    assert c1.break_before is BreakBefore.DIVIDER
    assert isinstance(c1.chapter_toc, TocScope)
    assert c1.chapter_toc.enabled is True
    assert c1.chapter_toc.max_depth == 2

    # Check part
    p = config.parts[1]
    assert p.is_part is True
    assert p.part == "Appendices"
    assert p.autonum_pattern == "none"
    assert len(p.chapters) == 1
    assert p.chapters[0].toc_title == "App A"
    assert p.chapters[0].label == "Appendix"


def test_load_config_from_yaml_string():
    yaml_text = """\

document:
  title: "YAML String Test"
  date: "2026-08-31"
  cover: false
theme: "custom"
parts:
  - part: "Hauptteil"
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
    with pytest.raises(ValidationError, match="Every part in 'parts' must carry a name"):
        load_config(raw_invalid)

    raw_valid = {
        "document": {"title": "Test"},
        "parts": [
            {
                "part": "Hauptteil",
                "chapters": [{"file": "01.md"}]
            }
        ]
    }
    config = load_config(raw_valid)
    assert len(config.parts) == 1
    assert config.parts[0].part == "Hauptteil"


def test_nested_chapters_are_rejected():
    """
    'chapters' in einem Kapitel bricht ab - mit eigener Meldung.

    Ueber die allgemeine Unbekannter-Schluessel-Pruefung liefe der Vorschlag
    auf das Alt-Feld 'chapter' hinaus, das nichts tut. Verschachtelte Kapitel
    sind ersatzlos entfallen, und genau das muss dastehen.
    """
    import pytest
    from pydantic import ValidationError

    raw = {
        "document": {"title": "Test"},
        "parts": [
            {
                "part": "Hauptteil",
                "chapters": [
                    {
                        "file": "01.md",
                        "chapters": [{"file": "02.md"}],
                    }
                ],
            }
        ],
    }
    with pytest.raises(ValidationError, match="chapters does not exist inside a chapter"):
        load_config(raw)


def test_pagenum_reset_configuration():
    """Prueft, dass pagenum_reset auf Part- und Kapitel-Ebene korrekt geladen wird."""
    raw = {
        "document": {"title": "Test"},
        "parts": [
            {
                "part": "Hauptteil",
                "chapters": [{"file": "01.md"}]
            },
            {
                "part": "Anhänge",
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


def test_a_block_is_named_by_exactly_one_key():
    """
    Der Part heisst 'part', das Kapitel nimmt seinen Namen aus der
    '#'-Ueberschrift. 'title' war an beiden Stellen ein Relikt - am Kapitel
    wirkungslos, am Part ein zweiter Weg zu demselben Wert. Zwei Schreibweisen
    fuer dieselbe Angabe laufen frueher oder spaeter auseinander.
    """
    import pytest
    from pydantic import ValidationError

    config = load_config({
        "document": {"title": "Testdoc"},
        "parts": [{"part": "Erster Abschnitt", "chapters": [{"file": "01.md"}]}],
    })
    assert config.parts[0].display_title == "Erster Abschnitt"

    with pytest.raises(ValidationError, match="must carry a name"):
        load_config({
            "document": {"title": "T"},
            "parts": [{"title": "Zweiter Abschnitt", "chapters": [{"file": "02.md"}]}],
        })

    for key in ("title", "chapter"):
        with pytest.raises(ValidationError, match="does not know this key"):
            load_config({
                "document": {"title": "T"},
                "parts": [{"part": "P", "chapters": [{"file": "01.md", key: "X"}]}],
            })


def test_a_label_key_names_the_level_below_and_belongs_further_out():
    """
    'part_label' und 'chapter_label' geben die Ebene darunter vor. An dem
    Block, den sie selbst benennen sollen, heisst der Schluessel 'label' --
    und die Meldung sagt das, statt auf ein aehnlich geschriebenes Feld zu
    raten.
    """
    import pytest
    from pydantic import ValidationError

    cases = [
        {"part": "P", "part_label": "Teil", "chapters": [{"file": "01.md"}]},
        {"part": "P", "chapters": [{"file": "01.md", "chapter_label": "Anhang"}]},
        {"part": "P", "chapters": [{"file": "01.md", "part_label": "Teil"}]},
    ]
    for part in cases:
        with pytest.raises(ValidationError, match="belongs on"):
            load_config({"document": {"title": "T"}, "parts": [part]})

    # An der richtigen Stelle gehen beide durch.
    config = load_config({
        "document": {"title": "T", "part_label": "Teil", "chapter_label": "Kapitel"},
        "parts": [{
            "part": "P",
            "label": "Teil",
            "chapter_label": "Anhang",
            "chapters": [{"file": "01.md", "label": "Exkurs"}],
        }],
    })
    assert config.document.part_label == "Teil"
    assert config.parts[0].chapter_label == "Anhang"
    assert config.parts[0].chapters[0].label == "Exkurs"


def test_break_before_defaults_are_quiet():
    """
    Ohne Angabe zeigt sich ein Part gar nicht, ein Kapitel beginnt auf neuer Seite.

    Eine Trennseite als Vorgabe fuer Parts hiess: wer 'parts:' nur benutzt,
    weil der Aufbau zwei Stufen verlangt, bekam eine ganze Seite fuer eine
    Klammer, die er nicht notiert hatte. Wer eine Trennseite will, schreibt
    sie hin.
    """
    klammer = PartItem(part="Nur eine Klammer", chapters=[ChapterItem(file="01.md")])
    assert klammer.effective_break_before is BreakBefore.NONE
    assert ChapterItem(file="01.md").break_before is BreakBefore.PAGE

    # Notiert man den Schluessel, gilt er unveraendert.
    notiert = PartItem(part="P", break_before="divider", chapters=[ChapterItem(file="01.md")])
    assert notiert.effective_break_before is BreakBefore.DIVIDER

    config = load_config(
        {
            "document": {"title": "T"},
            "parts": [{"part": "Hauptteil", "chapters": [{"file": "01.md"}]}],
        }
    )
    assert config.parts[0].effective_break_before is BreakBefore.NONE
    assert config.parts[0].chapters[0].break_before is BreakBefore.PAGE
