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

    # 2. Test build HTML shows notice
    build_html_res = runner.invoke(app, ["build", str(project_dir / "markpublish.yaml"), "--target", "html"])
    assert build_html_res.exit_code == 0
    assert "HTML output is currently not implemented" in build_html_res.stdout

    # 3. Test build PDF
    build_pdf_res = runner.invoke(app, ["build", str(project_dir / "markpublish.yaml"), "--target", "pdf"])
    assert build_pdf_res.exit_code == 0
    assert (project_dir / "cli_test_doc.pdf").is_file()


def test_cli_build_treats_non_existing_output_without_suffix_as_directory(tmp_path: Path):
    project_dir = tmp_path / "my_project"

    init_res = runner.invoke(app, ["init", str(project_dir), "--title", "Output Dir Test"])
    assert init_res.exit_code == 0

    out_dir = tmp_path / "dist"
    build_res = runner.invoke(
        app,
        ["build", str(project_dir / "markpublish.yaml"), "--target", "pdf", "--output", str(out_dir)],
    )
    assert build_res.exit_code == 0, build_res.stdout

    assert out_dir.is_dir(), "--output ohne Endung soll als Zielverzeichnis gelten"
    assert (out_dir / "output_dir_test.pdf").is_file()


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

    res = runner.invoke(app, ["cheatsheet"])
    assert res.exit_code == 0, res.stdout

    assert len(list(tmp_path.glob("*.pdf"))) == 1

    # Kein Quelltext im Projekt des Nutzers - nur das fertige Dokument.
    assert not list(tmp_path.glob("*.md"))
    assert not list(tmp_path.glob("*.yaml"))


@pytest.mark.skip(reason="Cheatsheet page count is flexible")
@pytest.mark.parametrize("lang", ["de", "en"])
def test_cli_cheatsheet_stays_two_pages(tmp_path: Path, monkeypatch, lang):
    """
    Zwei Seiten sind die ganze Idee: Seite 1 die markpublish.yaml, Seite 2 die
    Theme-Grundlagen. Waechst der Inhalt darueber hinaus, ist es keine
    Referenzkarte mehr - dann muss gekuerzt werden, nicht der Test angepasst.

    Beide Sprachen einzeln: deutscher Satz braucht mehr Platz, die Karte kippt
    also zuerst dort - und zwar unbemerkt, wenn nur Englisch gemessen wird.
    """
    pypdfium2 = pytest.importorskip("pypdfium2")
    monkeypatch.chdir(tmp_path)

    res = runner.invoke(app, ["cheatsheet", "--lang", lang, "--target", "pdf"])
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
    (tmp_path / "templates" / "default" / "pdf" / "template.typ").write_text(
        "INVALID TYPST SYNTAX # # # { { {", encoding="utf-8"
    )

    res = runner.invoke(app, ["cheatsheet"])
    assert res.exit_code == 0, res.stdout

    # Ausdruecklich angefordert, greift die normale Aufloesung wieder - und
    # das kaputte Theme schlaegt durch.
    broken = runner.invoke(app, ["cheatsheet", "--theme", "default"])
    assert broken.exit_code != 0


def test_cli_manual_renders_in_every_shipped_language(tmp_path: Path, monkeypatch):
    """
    Jede mitgelieferte Uebersetzung muss durchlaufen. Bricht eine, faellt es
    sonst erst auf, wenn jemand sie anfordert.

    Gefragt wird das Paket, nicht eine Liste hier: welche Sprachen es gibt,
    entscheidet der Inhalt von docs/manual/.
    """
    from markpublish.cli import _available_doc_languages

    monkeypatch.chdir(tmp_path)
    shipped = _available_doc_languages("manual")
    assert shipped, "kein mitgeliefertes Handbuch gefunden"

    for lang in shipped:
        res = runner.invoke(app, ["manual", "--lang", lang])
        assert res.exit_code == 0, f"{lang}: {res.stdout}"

    # Je Sprache ein eigener Dateiname - er kommt aus dem uebersetzten Titel.
    assert len(list(tmp_path.glob("*.pdf"))) == len(shipped)


def test_cli_cheatsheet_renders_in_declared_languages(tmp_path: Path, monkeypatch):
    """Wie beim Handbuch: alle deklarierten Sprachen muessen durchlaufen."""
    monkeypatch.chdir(tmp_path)

    from markpublish.cli import _available_doc_languages
    shipped = _available_doc_languages("cheatsheet")

    for lang in shipped:
        res = runner.invoke(app, ["cheatsheet", "--lang", lang])
        assert res.exit_code == 0, f"{lang}: {res.stdout}"

    assert len(list(tmp_path.glob("*.pdf"))) == len(shipped)


@pytest.mark.parametrize(
    "system_locale,expected",
    [
        ("de_DE.UTF-8", "benutzerhandbuch"),
        # Regionale Form ohne eigene Uebersetzung: die Basissprache greift.
        ("de_AT", "benutzerhandbuch"),
    ],
)
def test_cli_manual_follows_the_system_language(
    tmp_path: Path, monkeypatch, system_locale, expected
):
    """
    Ohne --lang entscheidet die Systemsprache. Die mitgelieferten Dokumente
    richten sich an die Person vor dem Rechner, nicht an ein Publikum - deren
    Sprache ist die beste verfuegbare Vermutung.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LANGUAGE", system_locale)

    assert runner.invoke(app, ["manual"]).exit_code == 0

    produced = list(tmp_path.glob("*.pdf"))
    assert len(produced) == 1
    assert expected in produced[0].name


def test_cli_cheatsheet_follows_the_system_language(tmp_path: Path, monkeypatch):
    """
    Dieselbe Erkennung an der Kurzreferenz, die in beiden Sprachen vorliegt --
    seit das Handbuch nur noch auf Deutsch mitgeliefert wird, ist sie das
    Dokument, an dem sich der englische Weg noch pruefen laesst.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LANGUAGE", "en_US.UTF-8")

    assert runner.invoke(app, ["cheatsheet"]).exit_code == 0

    produced = list(tmp_path.glob("*.pdf"))
    assert len(produced) == 1
    assert "benutzer" not in produced[0].name.lower()


def test_cli_manual_falls_back_silently_for_an_unshipped_system_language(
    tmp_path: Path, monkeypatch
):
    """
    Erkennung, die danebengreift, bleibt still: verlangt wurde nichts, und ein
    Hinweis bei jedem Aufruf waere Laerm. Der Unterschied zum ausdruecklichen
    --lang ist Absicht.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LANGUAGE", "fr_FR.UTF-8")

    res = runner.invoke(app, ["manual"])
    assert res.exit_code == 0, res.stdout

    assert len(list(tmp_path.glob("*.pdf"))) == 1
    assert "not available in" not in res.stdout, (
        "Ein Hinweis gehoert nur zum ausdruecklichen --lang, nicht zur Erkennung"
    )


def test_cli_manual_says_so_when_a_language_is_missing(tmp_path: Path, monkeypatch):
    """
    Eine nicht gepflegte Sprache faellt zurueck - aber sichtbar. Still auf
    Englisch auszuweichen hiesse, ein Dokument auszuliefern, das aussieht als
    waere es uebersetzt worden.
    """
    monkeypatch.chdir(tmp_path)

    res = runner.invoke(app, ["manual", "--lang", "fr"])
    assert res.exit_code == 0, res.stdout
    assert "fr" in res.stdout
    assert "de" in res.stdout and "en" in res.stdout, "die verfuegbaren Sprachen werden genannt"
    assert len(list(tmp_path.glob("*.pdf"))) == 1


def test_cli_target_html_shows_notice(tmp_path: Path, monkeypatch):
    """
    --target html stuerzt nicht ab, sondern gibt einen freundlichen Hinweis aus.
    """
    monkeypatch.chdir(tmp_path)
    res = runner.invoke(app, ["manual", "--target", "html"])
    assert res.exit_code == 0, res.stdout
    assert "HTML output is currently not implemented" in res.stdout
    assert len(list(tmp_path.glob("*.html"))) == 0


def test_bundled_documents_declare_the_languages_they_ship(tmp_path: Path):
    """
    Der Sprachordner ist die einzige Quelle der Wahrheit: liegt eine Uebersetzung
    im Paket, muss sie auch auffindbar sein - und umgekehrt.
    """
    from markpublish.cli import _available_doc_languages, get_bundled_doc_dir

    # Alle Dokumente werden auf Deutsch gepflegt; englische Fassungen
    # entstehen daraus, wenn die deutsche freigegeben ist.
    assert _available_doc_languages("manual") == ["de"]
    assert _available_doc_languages("cheatsheet") == ["de"]
    assert _available_doc_languages("init") == ["de"]

    # Jede gemeldete Sprache hat auch wirklich Kapitel neben ihrem Manifest.
    for name in ("manual", "cheatsheet", "init"):
        for lang in _available_doc_languages(name):
            base = get_bundled_doc_dir(name) / lang
            assert (base / "markpublish.yaml").is_file()
            assert list(base.rglob("*.md")), f"{name}/{lang} hat keine Kapitel"


def test_cli_init_lang_de(tmp_path: Path):
    """Prueft, dass init mit Sprachschalter die deutsche Vorlage kopiert."""
    p_de = tmp_path / "proj_de"
    res_de = runner.invoke(app, ["init", str(p_de), "--lang", "de", "--title", "Mein Dokument"])
    assert res_de.exit_code == 0
    yaml_de = (p_de / "markpublish.yaml").read_text(encoding="utf-8")
    assert 'title: "Mein Dokument"' in yaml_de
    assert 'language: "de"' in yaml_de
    assert 'part: "Hauptteil"' in yaml_de
    assert 'next-steps.md' in yaml_de
    steps_de = (p_de / "next-steps.md").read_text(encoding="utf-8")
    assert "# Nächste Schritte" in steps_de


def test_cli_init_uses_system_language(tmp_path: Path, monkeypatch):
    """Prueft, dass init ohne --lang die Systemsprache zur Vorlagenauswahl nutzt."""
    monkeypatch.setenv("LC_ALL", "de_DE.UTF-8")
    p = tmp_path / "proj_sys"
    res = runner.invoke(app, ["init", str(p), "--title", "System Doc"])
    assert res.exit_code == 0
    yaml_text = (p / "markpublish.yaml").read_text(encoding="utf-8")
    assert 'language: "de"' in yaml_text
    assert 'part: "Hauptteil"' in yaml_text


def test_cli_templates_list():
    res = runner.invoke(app, ["templates"])
    assert res.exit_code == 0
    assert "pdf" in res.stdout
    assert "default" in res.stdout


def test_cli_export_template(tmp_path: Path):
    dest = tmp_path / "exported_templates"
    res = runner.invoke(app, ["export-template", "default", str(dest)])
    assert res.exit_code == 0
    assert (dest / "default" / "pdf" / "template.typ").is_file()


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


def test_cli_export_template_keeps_an_edited_i18n(tmp_path: Path):
    """Ein zweiter Export darf die eigenen Texte nicht ueberschreiben."""
    dest = tmp_path / "exported_templates"
    assert runner.invoke(app, ["export-template", "default", str(dest)]).exit_code == 0

    edited = dest / "default" / "i18n.yaml"
    edited.write_text('de:\n  part: "Abschnitt"\n', encoding="utf-8")

    assert runner.invoke(app, ["export-template", "default", str(dest)]).exit_code == 0
    assert edited.read_text(encoding="utf-8") == 'de:\n  part: "Abschnitt"\n'


def test_cli_export_template_rejects_unknown_target(tmp_path: Path):
    dest = tmp_path / "exported_templates"
    res = runner.invoke(app, ["export-template", "default", str(dest), "--target", "invalid_target"])
    assert res.exit_code == 1
    assert "Unknown target 'invalid_target'" in res.stdout

