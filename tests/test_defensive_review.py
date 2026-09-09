"""
Defensive regression tests addressing findings from the architecture and security review.
"""

import xml.etree.ElementTree as etree
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from markpublish.cli import app
from markpublish.config.loader import load_config
from markpublish.config.models import MarkpublishConfig
from markpublish.markdown.toc import NumberingContext
from markpublish.markdown.typst_serializer import process_tree_headings_and_toc

runner = CliRunner()


# --------------------------------------------------------------------------
# 1. Top-Level Config Validation (Review Item 2)
# --------------------------------------------------------------------------

def test_toplevel_typo_rejected_with_suggestion():
    """Tippfehler auf oberster Ebene (z.B. theam) werden abgewiesen."""
    bad_raw = {
        "document": {"title": "Test"},
        "theam": "wasdcat",
    }
    with pytest.raises(ValidationError) as excinfo:
        MarkpublishConfig(**bad_raw)

    msg = str(excinfo.value)
    assert "theam" in msg
    assert "theme" in msg


def test_toplevel_unknown_keys_rejected():
    """Beliebige unbekannte Root-Schlüssel werden abgewiesen."""
    bad_raw = {
        "document": {"title": "Test"},
        "custom_plugin_config": 123,
    }
    with pytest.raises(ValidationError) as excinfo:
        MarkpublishConfig(**bad_raw)

    msg = str(excinfo.value)
    assert "custom_plugin_config" in msg


def test_toplevel_chapters_has_specialized_error():
    """'chapters:' auf oberster Ebene gibt die ausfuehrliche Erklaerung."""
    bad_raw = {
        "document": {"title": "Test"},
        "chapters": [{"file": "01.md"}],
    }
    with pytest.raises(ValidationError) as excinfo:
        MarkpublishConfig(**bad_raw)

    msg = str(excinfo.value)
    assert "parts" in msg


def test_valid_toplevel_keys_accepted():
    """Gueltige Root-Schlüssel laufen fehlerfrei durch."""
    valid_raw = {
        "document": {"title": "Test"},
        "theme": "default",
        "templates_dir": "custom_templates",
        "parts": [
            {
                "part": "Hauptteil",
                "chapters": [{"file": "01.md"}],
            }
        ],
    }
    cfg = MarkpublishConfig(**valid_raw)
    assert cfg.theme == "default"
    assert cfg.templates_dir == "custom_templates"
    assert len(cfg.parts) == 1


# --------------------------------------------------------------------------
# 2. Config Loader Error Handling (Review Item 8)
# --------------------------------------------------------------------------

def test_loader_missing_path_raises_filenotfound():
    with pytest.raises(FileNotFoundError):
        load_config(Path("nonexistent_file_path.yaml"))

    with pytest.raises(FileNotFoundError):
        load_config("nonexistent_file_path.yaml")


def test_loader_yaml_list_raises_value_error():
    """Ein YAML-String, der eine Liste ist, wirft ValueError."""
    with pytest.raises(ValueError, match=r"(?i)mapping/dictionary"):
        load_config("- item1\n- item2\n")


def test_loader_yaml_scalar_raises_value_error():
    """Ein YAML-String, der ein Skalar ist, wirft ValueError."""
    with pytest.raises(ValueError, match=r"(?i)mapping/dictionary"):
        load_config("just a plain string with\nnewlines\n")


def test_loader_empty_yaml_raises_value_error():
    """Ein leerer YAML-String wirft ValueError."""
    with pytest.raises(ValueError, match=r"(?i)mapping/dictionary"):
        load_config("")


def test_loader_empty_file_raises_value_error(tmp_path: Path):
    """Eine leere YAML-Datei wirft ValueError."""
    empty_file = tmp_path / "empty.yaml"
    empty_file.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match=r"(?i)mapping/dictionary"):
        load_config(empty_file)


def test_loader_file_with_list_raises_value_error(tmp_path: Path):
    """Eine YAML-Datei mit einer Liste statt Mapping wirft ValueError."""
    list_file = tmp_path / "list.yaml"
    list_file.write_text("- item1\n- item2\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"(?i)mapping/dictionary"):
        load_config(list_file)


# --------------------------------------------------------------------------
# 3. CLI --target html Exits With Code 1 (Review Item 3)
# --------------------------------------------------------------------------

def test_cli_target_html_alone_exits_with_code_1():
    """Wenn nur --target html gewaehlt wird, bricht die CLI mit Fehler ab."""
    res = runner.invoke(app, ["cheatsheet", "--target", "html"])
    assert res.exit_code == 1
    assert "HTML" in res.output or "html" in res.output


# --------------------------------------------------------------------------
# 4. CLI --debug Flag Support (Review Item 7)
# --------------------------------------------------------------------------

def test_cli_debug_flag_accepted():
    """--debug wird von der CLI akzeptiert (bewusst unkommentierter Schalter)."""
    res = runner.invoke(app, ["--debug", "--help"])
    assert res.exit_code == 0

    res_build = runner.invoke(app, ["build", "--debug", "--help"])
    assert res_build.exit_code == 0


# --------------------------------------------------------------------------
# 5. Tree Heading & Slug Collisions (Review Item 5 & 10)
# --------------------------------------------------------------------------

def test_tree_duplicate_heading_slug_collision():
    """Zwei identische Ueberschriften im AST bekommen unterschiedliche Slugs."""
    root = etree.Element("div")
    h1 = etree.SubElement(root, "h2")
    h1.text = "Gleicher Titel"
    h2 = etree.SubElement(root, "h2")
    h2.text = "Gleicher Titel"

    nodes = process_tree_headings_and_toc(root, NumberingContext())
    assert len(nodes) == 2
    assert nodes[0].slug == "gleicher-titel"
    assert nodes[1].slug == "gleicher-titel-1"
    assert nodes[0].slug != nodes[1].slug
    assert h1.attrib["id"] == "gleicher-titel"
    assert h2.attrib["id"] == "gleicher-titel-1"


def test_tree_explicit_id_does_not_collide_with_generated_slug():
    """Eine explizite ID wird vorab reserviert und kollidiert nicht mit generiertem Slug."""
    root = etree.Element("div")
    h1 = etree.SubElement(root, "h2")
    h1.text = "Einleitung"

    h2 = etree.SubElement(root, "h2")
    h2.attrib["id"] = "einleitung"
    h2.text = "Andere Einleitung"

    nodes = process_tree_headings_and_toc(root, NumberingContext())
    assert len(nodes) == 2
    assert nodes[0].slug == "einleitung-1"
    assert nodes[1].slug == "einleitung"
    assert nodes[0].slug != nodes[1].slug
