"""
Tests for CLI commands.
"""

from pathlib import Path

import pytest
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
    assert (project_dir / "next-steps.md").is_file()

    # 2. Test build HTML
    build_html_res = runner.invoke(app, ["build", str(project_dir / "markpublish.yaml"), "--target", "html"])
    assert build_html_res.exit_code == 0
    assert (project_dir / "cli_test_doc.html").is_file()

    # 3. Test build PDF
    build_pdf_res = runner.invoke(app, ["build", str(project_dir / "markpublish.yaml"), "--target", "pdf"])
    assert build_pdf_res.exit_code == 0
    assert (project_dir / "cli_test_doc.pdf").is_file()


def test_cli_init_stays_minimal(tmp_path: Path):
    """
    Der Stumpf ist bewusst zwei Dateien - kein chapters/-Verzeichnis, keine
    Beispielkapitel. Wer hier etwas hinzufuegt, sollte es begruenden koennen:
    alles, was init erzeugt, loescht der Nutzer beim ersten echten Kapitel
    wieder. Die Referenz liegt in 'markpublish cheatsheet'.
    """
    project_dir = tmp_path / "stub"
    assert runner.invoke(app, ["init", str(project_dir)]).exit_code == 0

    created = sorted(p.name for p in project_dir.iterdir())
    assert created == ["markpublish.yaml", "next-steps.md"]

    # Der Verweis auf das Cheat Sheet ist der einzige Grund, warum der Stumpf
    # so klein sein darf - faellt er weg, steht der Nutzer ohne Referenz da.
    assert "markpublish cheatsheet" in (project_dir / "markpublish.yaml").read_text(encoding="utf-8")
    assert "markpublish cheatsheet" in (project_dir / "next-steps.md").read_text(encoding="utf-8")


def test_cli_cheatsheet_renders_into_the_working_directory(tmp_path: Path, monkeypatch):
    """
    Die Quelle liegt im Paket, das Ergebnis muss im Arbeitsverzeichnis landen -
    site-packages ist oft schreibgeschuetzt, und dort wuerde ohnehin niemand
    nach seinem PDF suchen.
    """
    monkeypatch.chdir(tmp_path)

    res = runner.invoke(app, ["cheatsheet", "--target", "html"])
    assert res.exit_code == 0, res.stdout

    assert len(list(tmp_path.glob("*.html"))) == 1

    # Kein Quelltext im Projekt des Nutzers - nur das fertige Dokument.
    assert not list(tmp_path.glob("*.md"))
    assert not list(tmp_path.glob("*.yaml"))


def test_cli_cheatsheet_stays_two_pages(tmp_path: Path, monkeypatch):
    """
    Zwei Seiten sind die ganze Idee: Seite 1 die markpublish.yaml, Seite 2 die
    Theme-Grundlagen. Waechst der Inhalt darueber hinaus, ist es keine
    Referenzkarte mehr - dann muss gekuerzt werden, nicht der Test angepasst.
    """
    pypdfium2 = pytest.importorskip("pypdfium2")
    monkeypatch.chdir(tmp_path)

    res = runner.invoke(app, ["cheatsheet", "--target", "pdf"])
    assert res.exit_code == 0, res.stdout

    produced = list(tmp_path.glob("*.pdf"))
    assert len(produced) == 1

    pdf = pypdfium2.PdfDocument(str(produced[0]))
    try:
        assert len(pdf) == 2
    finally:
        pdf.close()


def test_cli_cheatsheet_ignores_a_broken_project_theme(tmp_path: Path, monkeypatch):
    """
    Die Referenz muss gerade dann rendern, wenn im Arbeitsverzeichnis ein
    eigenes, noch unfertiges Theme liegt - sonst faellt sie in dem Moment aus,
    in dem jemand nachschlagen will, wie Themes funktionieren.
    """
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["export-template", "default", "./templates"]).exit_code == 0
    (tmp_path / "templates" / "default" / "html" / "layout.html").write_text(
        "<html><body>{{ labels.does_not_exist }}</body></html>", encoding="utf-8"
    )

    res = runner.invoke(app, ["cheatsheet", "--target", "html"])
    assert res.exit_code == 0, res.stdout

    # Ausdruecklich angefordert, greift die normale Aufloesung wieder - und
    # das kaputte Theme schlaegt durch.
    broken = runner.invoke(app, ["cheatsheet", "--target", "html", "--theme", "default"])
    assert broken.exit_code != 0


def test_cli_manual_renders_in_both_languages(tmp_path: Path, monkeypatch):
    """
    Das Handbuch wird in beiden gepflegten Sprachen ausgeliefert. Bricht eine
    davon, faellt es sonst erst auf, wenn jemand sie anfordert.
    """
    monkeypatch.chdir(tmp_path)

    for lang in ("en", "de"):
        res = runner.invoke(app, ["manual", "--lang", lang, "--target", "html"])
        assert res.exit_code == 0, f"{lang}: {res.stdout}"

    # Zwei Sprachen, zwei verschieden benannte Ergebnisse - der Dateiname kommt
    # aus dem Titel, und der ist uebersetzt.
    assert len(list(tmp_path.glob("*.html"))) == 2


def test_cli_manual_defaults_to_english(tmp_path: Path, monkeypatch):
    """
    Ohne --lang gilt DEFAULT_DOC_LANGUAGE. Das ist Englisch, weil CLI-Hilfe und
    README es auch sind - ein deutsches Dokument ohne Vorwarnung waere fuer die
    Mehrheit der Nutzer die Ueberraschung.
    """
    monkeypatch.chdir(tmp_path)

    assert runner.invoke(app, ["manual", "--target", "html"]).exit_code == 0

    produced = list(tmp_path.glob("*.html"))
    assert len(produced) == 1
    assert "user_guide" in produced[0].name


def test_cli_manual_says_so_when_a_language_is_missing(tmp_path: Path, monkeypatch):
    """
    Eine nicht gepflegte Sprache faellt zurueck - aber sichtbar. Still auf
    Englisch auszuweichen hiesse, ein Dokument auszuliefern, das aussieht als
    waere es uebersetzt worden.
    """
    monkeypatch.chdir(tmp_path)

    res = runner.invoke(app, ["manual", "--lang", "fr", "--target", "html"])
    assert res.exit_code == 0, res.stdout
    assert "fr" in res.stdout
    assert "de" in res.stdout and "en" in res.stdout, "die verfuegbaren Sprachen werden genannt"
    assert len(list(tmp_path.glob("*.html"))) == 1


def test_bundled_documents_declare_the_languages_they_ship(tmp_path: Path):
    """
    Der Sprachordner ist die einzige Quelle der Wahrheit: liegt eine Uebersetzung
    im Paket, muss sie auch auffindbar sein - und umgekehrt.
    """
    from markpublish.cli import _available_doc_languages, get_bundled_doc_dir

    assert _available_doc_languages("manual") == ["de", "en"]
    assert _available_doc_languages("cheatsheet") == ["en"]

    # Jede gemeldete Sprache hat auch wirklich Kapitel neben ihrem Manifest.
    for name in ("manual", "cheatsheet"):
        for lang in _available_doc_languages(name):
            base = get_bundled_doc_dir(name) / lang
            assert (base / "markpublish.yaml").is_file()
            assert list(base.rglob("*.md")), f"{name}/{lang} hat keine Kapitel"


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


def test_cli_export_template_brings_the_theme_level_i18n(tmp_path: Path):
    """
    Die i18n.yaml der Theme-Ebene liegt neben den Zielformat-Ordnern, nicht
    darin. Ohne sie exportiert man ein Theme und ausgerechnet die Datei, in der
    die statischen Texte definiert werden, bliebe im Paket zurueck.
    """
    dest = tmp_path / "exported_templates"
    res = runner.invoke(app, ["export-template", "default", str(dest)])
    assert res.exit_code == 0
    assert (dest / "default" / "i18n.yaml").is_file()
    assert (dest / "default" / "pdf" / "i18n.yaml").is_file()
    assert (dest / "default" / "html" / "i18n.yaml").is_file()


def test_cli_export_template_keeps_an_edited_i18n(tmp_path: Path):
    """Ein zweiter Export darf die eigenen Texte nicht ueberschreiben."""
    dest = tmp_path / "exported_templates"
    assert runner.invoke(app, ["export-template", "default", str(dest)]).exit_code == 0

    edited = dest / "default" / "i18n.yaml"
    edited.write_text('de:\n  part: "Abschnitt"\n', encoding="utf-8")

    assert runner.invoke(app, ["export-template", "default", str(dest)]).exit_code == 0
    assert edited.read_text(encoding="utf-8") == 'de:\n  part: "Abschnitt"\n'

