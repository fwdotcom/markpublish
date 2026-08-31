"""
Tests for CLI commands.
"""

from pathlib import Path

from typer.testing import CliRunner

from markpublish.cli import app

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "markpublish version" in result.stdout


def test_cli_init_and_build(tmp_path: Path):
    project_dir = tmp_path / "my_project"

    # 1. Test init
    init_res = runner.invoke(app, ["init", str(project_dir), "--title", "CLI Test Doc"])
    assert init_res.exit_code == 0
    assert (project_dir / "markpublish.yaml").is_file()
    assert (project_dir / "chapters" / "01_introduction.md").is_file()

    # 2. Test build HTML
    build_html_res = runner.invoke(app, ["build", str(project_dir / "markpublish.yaml"), "--target", "html"])
    assert build_html_res.exit_code == 0
    assert (project_dir / "cli_test_doc.html").is_file()

    # 3. Test build PDF
    build_pdf_res = runner.invoke(app, ["build", str(project_dir / "markpublish.yaml"), "--target", "pdf"])
    assert build_pdf_res.exit_code == 0
    assert (project_dir / "cli_test_doc.pdf").is_file()


def test_cli_templates_list():
    res = runner.invoke(app, ["templates"])
    assert res.exit_code == 0
    assert "pdf" in res.stdout
    assert "default" in res.stdout


def test_cli_export_template(tmp_path: Path):
    dest = tmp_path / "exported_templates"
    res = runner.invoke(app, ["export-template", "default", str(dest)])
    assert res.exit_code == 0
    assert (dest / "default" / "pdf" / "layout.html").is_file()
    assert (dest / "default" / "html" / "layout.html").is_file()

