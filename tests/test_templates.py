"""
Tests for template resolution and hierarchy.
"""

from pathlib import Path
import pytest

from markpublish.templates.resolver import (
    get_package_templates_dir,
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


def test_resolve_template_precedence(tmp_path: Path):
    # Create custom common template directory
    custom_templates = tmp_path / "templates"
    custom_pdf_default = custom_templates / "pdf" / "default"
    custom_pdf_default.mkdir(parents=True)
    custom_layout = custom_pdf_default / "layout.html"
    custom_layout.write_text("<!-- Custom Common Template -->", encoding="utf-8")

    # Resolve with custom templates dir
    resolved = resolve_template_path(
        target="pdf",
        theme="default",
        custom_templates_dir=custom_templates,
    )
    assert resolved == custom_pdf_default
    assert (resolved / "layout.html").read_text(encoding="utf-8") == "<!-- Custom Common Template -->"


def test_list_templates():
    templates = list_templates()
    assert len(templates) >= 2
    targets = {t["target"] for t in templates}
    themes = {t["theme"] for t in templates}
    assert "pdf" in targets
    assert "html" in targets
    assert "default" in themes

