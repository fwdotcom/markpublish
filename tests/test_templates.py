"""
Tests for template resolution and hierarchy.
"""

from pathlib import Path

import pytest

from markpublish.templates.resolver import (
    list_templates,
    resolve_template_path,
)


def test_resolve_package_templates():
    pdf_default = resolve_template_path("pdf", "default")
    assert pdf_default.exists()
    assert (pdf_default / "layout.html").is_file()
    assert (pdf_default / "styles.css").is_file()

    html_default = resolve_template_path("html", "default")
    assert html_default.exists()
    assert (html_default / "layout.html").is_file()
    assert (html_default / "styles.css").is_file()


def test_package_templates_use_theme_target_layout():
    """Das Verzeichnis heisst <theme>/<target>, nicht <target>/<theme>."""
    pdf_default = resolve_template_path("pdf", "default")
    assert pdf_default.name == "pdf"
    assert pdf_default.parent.name == "default"


def test_resolve_template_precedence(tmp_path: Path):
    # Create custom common template directory in the current layout
    custom_templates = tmp_path / "templates"
    custom_pdf_default = custom_templates / "default" / "pdf"
    custom_pdf_default.mkdir(parents=True)
    custom_layout = custom_pdf_default / "layout.html"
    custom_layout.write_text("<!-- Custom Common Template -->", encoding="utf-8")

    resolved = resolve_template_path(
        target="pdf",
        theme="default",
        custom_templates_dir=custom_templates,
    )

    assert resolved == custom_pdf_default
    assert (resolved / "layout.html").read_text(encoding="utf-8") == "<!-- Custom Common Template -->"


def test_resolve_unknown_theme_lists_current_layout(tmp_path: Path):
    with pytest.raises(FileNotFoundError) as exc:
        resolve_template_path("pdf", "gibtsnicht", custom_templates_dir=tmp_path)
    # Der Fehlertext soll den Pfad zeigen, den man anlegen muss.
    assert "gibtsnicht" in str(exc.value)
    assert str(Path("gibtsnicht") / "pdf") in str(exc.value)


def test_list_templates():
    templates = list_templates()
    assert len(templates) >= 2
    targets = {t["target"] for t in templates}
    themes = {t["theme"] for t in templates}
    assert "pdf" in targets
    assert "html" in targets
    assert "default" in themes
