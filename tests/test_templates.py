"""
Tests for template resolution and hierarchy.
"""

import warnings
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

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        resolved = resolve_template_path(
            target="pdf",
            theme="default",
            custom_templates_dir=custom_templates,
        )

    assert resolved == custom_pdf_default
    assert (resolved / "layout.html").read_text(encoding="utf-8") == "<!-- Custom Common Template -->"


def test_legacy_layout_still_resolves_but_warns(tmp_path: Path):
    """Bestehende Templates im alten <target>/<theme> bleiben nutzbar."""
    custom_templates = tmp_path / "templates"
    legacy = custom_templates / "pdf" / "mytheme"
    legacy.mkdir(parents=True)
    (legacy / "layout.html").write_text("<!-- legacy -->", encoding="utf-8")

    with pytest.warns(DeprecationWarning, match="alten Layout"):
        resolved = resolve_template_path(
            target="pdf",
            theme="mytheme",
            custom_templates_dir=custom_templates,
        )
    assert resolved == legacy


def test_current_layout_wins_over_legacy(tmp_path: Path):
    """Liegt ein Theme in beiden Layouts vor, gewinnt das neue."""
    base = tmp_path / "templates"
    current = base / "mytheme" / "pdf"
    legacy = base / "pdf" / "mytheme"
    for d in (current, legacy):
        d.mkdir(parents=True)
        (d / "layout.html").write_text(d.as_posix(), encoding="utf-8")

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        resolved = resolve_template_path("pdf", "mytheme", custom_templates_dir=base)
    assert resolved == current


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
    assert all(t["layout"] == "current" for t in templates)


def test_list_templates_flags_legacy_layout(tmp_path: Path):
    base = tmp_path / "templates"
    legacy = base / "html" / "altes-theme"
    legacy.mkdir(parents=True)
    (legacy / "styles.css").write_text("/* legacy */", encoding="utf-8")

    rows = list_templates(custom_templates_dir=base)
    match = [r for r in rows if r["theme"] == "altes-theme"]
    assert match, "Template im alten Layout wird nicht gelistet"
    assert match[0]["layout"] == "legacy"
    assert match[0]["target"] == "html"
