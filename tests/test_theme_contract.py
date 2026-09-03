"""
Tests fuer die Theme-Vertragspruefung.

Geprueft wird beides: der Parser fuer sich (schnell, viele Faelle) und der
Renderer-Durchlauf (langsam, dafuer echt) -- denn nur letzterer belegt, dass
die Pruefung ueberhaupt aufgerufen wird. Eine Pruefung, die niemand ausloest,
war der Ausgangspunkt dieses Moduls.
"""

from __future__ import annotations

import shutil
import warnings
from pathlib import Path

import pytest

from markpublish.config.loader import load_config
from markpublish.i18n import UndefinedLabelError
from markpublish.markdown.engine import MarkdownPipeline
from markpublish.renderers.base import DocumentContext
from markpublish.renderers.pdf import PDFRenderer
from markpublish.templates.contract import (
    DiagnosisStatus,
    Severity,
    ThemeContractWarning,
    ThemeUsage,
    check_theme_contract,
    diagnose_labels_and_metadata,
    engine_labels,
    parse_sent_arguments,
    parse_theme_contract,
)
from markpublish.templates.resolver import resolve_template_path

# --------------------------------------------------------------------------
# Parser
# --------------------------------------------------------------------------

NESTED_PARENS = '''
#let setup-document(
  title: "",
  authors: (),
  labels: (:),
  accent: rgb("#2563eb"),
  body,
) = { body }
'''


def test_parser_survives_parentheses_inside_the_signature(tmp_path: Path):
    """
    Ein `[^)]*` waere hier nach `authors: ()` fertig und haette die halbe
    Signatur verschluckt -- der Grund fuer den Klammernzaehler.
    """
    (tmp_path / "template.typ").write_text(NESTED_PARENS, encoding="utf-8")
    contract = parse_theme_contract(tmp_path)

    assert contract.parameters["setup-document"] == {
        "title",
        "authors",
        "labels",
        "accent",
    }
    assert contract.accepts_extra["setup-document"] is False


def test_parser_detects_a_sink(tmp_path: Path):
    (tmp_path / "template.typ").write_text(
        '#let setup-document(title: "", ..rest, body) = { body }', encoding="utf-8"
    )
    contract = parse_theme_contract(tmp_path)
    assert contract.accepts_extra["setup-document"] is True


def test_parser_records_whether_a_label_has_a_fallback(tmp_path: Path):
    (tmp_path / "template.typ").write_text(
        '#let f(labels: (:)) = {\n'
        '  [#labels.at("mit", default: "x")]\n'
        '  [#labels.at("ohne")]\n'
        "}",
        encoding="utf-8",
    )
    contract = parse_theme_contract(tmp_path)
    by_key = {ref.key: ref for ref in contract.label_references}

    assert by_key["mit"].has_default is True
    assert by_key["ohne"].has_default is False
    # Die Fundstelle wandert in die Fehlermeldung -- sie muss stimmen.
    assert by_key["ohne"].line == 3


def test_parser_reads_the_real_default_theme():
    """Das mitgelieferte Theme muss der Parser vollstaendig verstehen."""
    contract = parse_theme_contract(resolve_template_path("pdf", "default"))

    for function in ("setup-document", "render-part-divider", "render-chapter-divider"):
        assert contract.declares(function), f"{function} nicht erkannt"
    assert "labels" in contract.parameters["setup-document"]
    assert contract.label_references, "keine Label-Referenzen gefunden"


def test_sent_arguments_are_read_from_the_generated_call():
    main_typ = (
        '#import "template.typ": *\n'
        "#show: doc => setup-document(\n"
        '  title: "T",\n'
        "  authors: (),\n"
        '  labels: (\n    "page": "Seite",\n  ),\n'
        "  doc,\n"
        ")\n"
    )
    sent = parse_sent_arguments(main_typ)
    # 'page' steht innerhalb von labels und ist kein Argument von setup-document.
    assert sent["setup-document"] == {"title", "authors", "labels"}


# --------------------------------------------------------------------------
# Vergleich
# --------------------------------------------------------------------------

def _contract(tmp_path: Path, signature: str):
    (tmp_path / "template.typ").write_text(
        f"#let setup-document({signature}) = {{ body }}", encoding="utf-8"
    )
    return parse_theme_contract(tmp_path)


def test_unknown_parameter_is_an_error(tmp_path: Path):
    report = check_theme_contract(
        _contract(tmp_path, 'title: "", body'),
        {"setup-document": {"title", "status"}},
    )
    assert report.errors and "status" in report.errors[0]


def test_a_sink_absorbs_unknown_parameters(tmp_path: Path):
    report = check_theme_contract(
        _contract(tmp_path, 'title: "", ..rest, body'),
        {"setup-document": {"title", "status"}},
    )
    assert not report.errors


def test_parameter_the_theme_declares_but_nobody_sends_is_fine(tmp_path: Path):
    """Der Default greift -- das ist der Normalfall bei eigenen Erweiterungen."""
    report = check_theme_contract(
        _contract(tmp_path, 'title: "", logo: none, body'),
        {"setup-document": {"title"}},
    )
    assert not report.errors and not report.warnings


def test_missing_function_is_an_error(tmp_path: Path):
    (tmp_path / "template.typ").write_text("#let etwas-anderes() = {}", encoding="utf-8")
    report = check_theme_contract(
        parse_theme_contract(tmp_path), {"setup-document": {"title"}}
    )
    assert report.errors and "setup-document" in report.errors[0]


def test_label_with_fallback_warns_but_does_not_fail(tmp_path: Path):
    (tmp_path / "template.typ").write_text(
        '#let setup-document(labels: (:), body) = { [#labels.at("frei", default: "")] }',
        encoding="utf-8",
    )
    report = check_theme_contract(
        parse_theme_contract(tmp_path), {}, labels={"page": "Seite"}, language="en"
    )
    assert report.warnings and "frei" in report.warnings[0]
    assert not report.missing_labels


def test_label_without_fallback_is_reported_as_missing(tmp_path: Path):
    (tmp_path / "template.typ").write_text(
        '#let setup-document(labels: (:), body) = { [#labels.at("frei")] }',
        encoding="utf-8",
    )
    report = check_theme_contract(
        parse_theme_contract(tmp_path), {}, labels={"page": "Seite"}, language="en"
    )
    assert "frei" in report.missing_labels
    assert not report.warnings


def test_resolved_labels_produce_nothing(tmp_path: Path):
    (tmp_path / "template.typ").write_text(
        '#let setup-document(labels: (:), body) = { [#labels.at("page")] }',
        encoding="utf-8",
    )
    report = check_theme_contract(
        parse_theme_contract(tmp_path), {}, labels={"page": "Seite"}, language="de"
    )
    assert not report


# --------------------------------------------------------------------------
# Renderer -- belegt, dass die Pruefung tatsaechlich laeuft
# --------------------------------------------------------------------------

PROJECT_YAML = """
document:
  title: "Vertragstest"
  language: "en"
  cover: false
  document_toc: "none"
theme: "eigen"
parts:
  - title: "P"
    break_before: "none"
    chapters:
      - file: "a.md"
        title: "A"
"""

MINIMAL_THEME = """
#let setup-document({signature}) = {{
  {body}
  body
}}
#let render-part-divider(..a) = {{}}
#let render-chapter-divider(..a) = {{}}
#let callout(..a, body) = body
#let task-item(..a, body) = body
"""


def _project(tmp_path: Path, signature: str, body: str = "") -> Path:
    (tmp_path / "markpublish.yaml").write_text(PROJECT_YAML, encoding="utf-8")
    (tmp_path / "a.md").write_text("# A\n\nText.\n", encoding="utf-8")
    theme = tmp_path / "templates" / "eigen" / "pdf"
    theme.mkdir(parents=True)
    (theme / "template.typ").write_text(
        MINIMAL_THEME.format(signature=signature, body=body), encoding="utf-8"
    )
    return tmp_path


def _assemble(project: Path) -> str:
    """Der Typst-Quelltext, den markpublish fuer dieses Projekt erzeugt."""
    config = load_config(project / "markpublish.yaml")
    context = DocumentContext(
        config=config,
        content_items=[],
        toc_tree=[],
        template_path=resolve_template_path(
            "pdf", config.theme, config_base_dir=project
        ),
        base_dir=project,
        target="pdf",
    )
    context.content_items, context.toc_tree = MarkdownPipeline(
        config, base_dir=project, labels=context.labels
    ).process_document()
    return PDFRenderer()._assemble_typst_document(context, project)


def _render(project: Path) -> Path:
    config = load_config(project / "markpublish.yaml")
    context = DocumentContext(
        config=config,
        content_items=[],
        toc_tree=[],
        template_path=resolve_template_path(
            "pdf", config.theme, config_base_dir=project
        ),
        base_dir=project,
        target="pdf",
    )
    context.content_items, context.toc_tree = MarkdownPipeline(
        config, base_dir=project, labels=context.labels
    ).process_document()
    out = project / "out.pdf"
    PDFRenderer().render(context, out)
    return out


def test_render_aborts_on_an_outdated_theme(tmp_path: Path):
    """
    Der Fall, der frueher `unexpected argument: status` erzeugt hat.

    Die Signatur nennt absichtlich nur einen Bruchteil der Parameter -- so
    faellt der Test nicht um, sobald ein weiterer hinzukommt.
    """
    project = _project(tmp_path, 'title: "", body')
    with pytest.raises(RuntimeError) as excinfo:
        _render(project)

    message = str(excinfo.value)
    assert "passen nicht zusammen" in message
    assert "nicht deklariert" in message
    assert "setup-document" in message
    assert str(project) in message, "Der Theme-Pfad gehoert in die Meldung"
    # Die Pruefung kennt keine Versionen; sie darf keine Ursache behaupten.
    assert "aelter" not in message and "Version" not in message


def test_render_succeeds_when_the_theme_has_a_sink(tmp_path: Path):
    project = _project(tmp_path, 'title: "", ..rest, body')
    assert _render(project).is_file()


def test_render_warns_about_a_label_that_only_has_a_fallback(tmp_path: Path):
    project = _project(
        tmp_path,
        'title: "", labels: (:), ..rest, body',
        body='[#labels.at("freigabe", default: "")]',
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ThemeContractWarning)
        out = _render(project)

    assert out.is_file(), "Die Warnung darf den Build nicht abbrechen"
    messages = [str(w.message) for w in caught if issubclass(w.category, ThemeContractWarning)]
    assert any("freigabe" in m for m in messages)


def test_render_aborts_on_a_label_without_a_fallback(tmp_path: Path):
    project = _project(
        tmp_path,
        'title: "", labels: (:), ..rest, body',
        body='[#labels.at("freigabe")]',
    )
    with pytest.raises(UndefinedLabelError) as excinfo:
        _render(project)

    message = str(excinfo.value)
    assert "freigabe" in message
    assert "template.typ:" in message, "Die Fundstelle gehoert in die Meldung"


def test_the_shipped_theme_fulfils_its_own_contract(tmp_path: Path):
    """
    Die Pruefung darf das mitgelieferte Theme nicht anfassen.

    Faellt dieser Test, ist entweder ein Parameter in pdf.py hinzugekommen,
    ohne dass template.typ ihn kennt, oder der Parser ist kaputt.
    """
    (tmp_path / "markpublish.yaml").write_text(
        PROJECT_YAML.replace('theme: "eigen"', 'theme: "default"'), encoding="utf-8"
    )
    (tmp_path / "a.md").write_text("# A\n\nText.\n", encoding="utf-8")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ThemeContractWarning)
        assert _render(tmp_path).is_file()

    assert not [w for w in caught if issubclass(w.category, ThemeContractWarning)]


# --------------------------------------------------------------------------
# Diagnose: definiert / gelesen / gesetzt
# --------------------------------------------------------------------------

def _diagnose(theme_dir: Path, defined_keys, document=None):
    """Kurzform: Befunde je Schluessel, wie `markpublish labels` sie berechnet."""
    resolved = {key: {"value": key, "source": "i18n.yaml"} for key in defined_keys}
    rows = diagnose_labels_and_metadata(
        parse_theme_contract(theme_dir), document, resolved
    )
    return {row.key: row for row in rows}


def test_diagnosis_marks_a_label_nobody_reads(tmp_path: Path):
    (tmp_path / "template.typ").write_text(
        '#let setup-document(labels: (:), body) = { [#labels.at("page", default: "")] }',
        encoding="utf-8",
    )
    rows = _diagnose(tmp_path, {"page", "verwaist"})

    assert rows["page"].theme_usage is ThemeUsage.KEY
    assert rows["page"].status is DiagnosisStatus.OK
    assert rows["verwaist"].theme_usage is ThemeUsage.NONE
    assert rows["verwaist"].status is DiagnosisStatus.UNUSED


def test_diagnosis_marks_a_label_that_is_read_but_undefined(tmp_path: Path):
    (tmp_path / "template.typ").write_text(
        '#let setup-document(labels: (:), body) = { [#labels.at("frei")] }',
        encoding="utf-8",
    )
    rows = _diagnose(tmp_path, set())

    assert rows["frei"].theme_usage is ThemeUsage.KEY
    assert rows["frei"].i18n_label is None
    assert rows["frei"].breaks_build, "ohne Fallback bricht der Build ab"
    assert rows["frei"].severity is Severity.ERROR


def test_diagnosis_counts_labels_markpublish_reads_itself(tmp_path: Path):
    """
    `toc_title` steht in keinem `labels.at(...)` des Templates -- markpublish
    liest es und reicht es als Parameter weiter. Ein reiner Textscan wuerde es
    faelschlich als unbenutzt melden und zum Loeschen einladen.
    """
    (tmp_path / "template.typ").write_text(
        '#let setup-document(toc-title: "", body) = { body }', encoding="utf-8"
    )
    rows = _diagnose(tmp_path, {"toc_title"})

    assert rows["toc_title"].theme_usage is not ThemeUsage.NONE
    assert rows["toc_title"].status is DiagnosisStatus.OK


def test_a_label_with_a_fallback_warns_instead_of_breaking(tmp_path: Path):
    """Der Unterschied, auf den es ankommt: mit `default:` laeuft der Build."""
    (tmp_path / "template.typ").write_text(
        '#let setup-document(labels: (:), body) = { [#labels.at("frei", default: "Ersatz")] }',
        encoding="utf-8",
    )
    rows = _diagnose(tmp_path, set())

    assert rows["frei"].breaks_build is False
    assert rows["frei"].severity is Severity.WARNING
    assert rows["frei"].label_fallback == "Ersatz"
    assert rows["frei"].status_detail == "Ersatz"


def test_alert_labels_follow_the_serializer(tmp_path: Path):
    """Ein neuer Callout-Typ soll hier nicht nachgetragen werden muessen."""
    from markpublish.markdown.typst_serializer import TypstSerializer

    known = engine_labels()
    for name in TypstSerializer.CALLOUT_TYPES:
        assert f"alert_{name}" in known


def test_engine_labels_covers_every_label_the_renderer_reads():
    """
    Waechter: liest pdf.py ein weiteres Label, muss es in ENGINE_LABELS stehen
    -- sonst meldet `markpublish labels` es als unbenutzt.
    """
    import re

    source = Path("src/markpublish/renderers/pdf.py").read_text(encoding="utf-8")
    read = set(re.findall(r'labels\.get\(\s*"([a-z_]+)"', source))
    assert read, "keine labels.get()-Aufrufe gefunden - Waechter greift ins Leere"
    assert read <= engine_labels(), f"nicht deklariert: {sorted(read - engine_labels())}"


def test_the_shipped_theme_has_no_gaps():
    """Jedes Label, das gelesen wird, ist im mitgelieferten Theme definiert."""
    from markpublish.config.models import DocumentConfig
    from markpublish.i18n import build_labels

    theme = resolve_template_path("pdf", "default")
    for language in ("de", "en"):
        resolved = {
            key: {"value": value, "source": "i18n.yaml"}
            for key, value in build_labels(language).items()
        }
        rows = diagnose_labels_and_metadata(
            parse_theme_contract(theme),
            DocumentConfig(title="T", language=language),
            resolved,
        )
        gaps = [row.key for row in rows if row.severity is Severity.ERROR]
        assert not gaps, f"{language}: {gaps}"


def test_labels_command_summary_ignores_the_overridden_filter(tmp_path: Path):
    """
    `--overridden` blendet Zeilen aus, darf aber die Bilanz nicht faelschen.

    Vorher rechnete die Zusammenfassung nur ueber die angezeigten Zeilen und
    meldete "jedes Label wird gelesen", obwohl ein verwaistes existierte.
    """
    from typer.testing import CliRunner

    from markpublish.cli import app

    (tmp_path / "markpublish.yaml").write_text(
        PROJECT_YAML.replace('theme: "eigen"', 'theme: "default"').replace(
            'language: "en"', 'language: "de"'
        ),
        encoding="utf-8",
    )
    (tmp_path / "a.md").write_text("# A\n\nText.\n", encoding="utf-8")

    # Ein eigenes verwaistes Label statt eines Produktivlabels: sonst faellt
    # dieser Test um, sobald jemand den Programmstandard aufraeumt.
    (tmp_path / "i18n.yaml").write_text(
        'de:\n  liest_niemand: "Text ohne Leser"\n', encoding="utf-8"
    )

    runner = CliRunner(env={"COLUMNS": "220"})
    plain = runner.invoke(app, ["labels", str(tmp_path / "markpublish.yaml")])
    filtered = runner.invoke(
        app, ["labels", str(tmp_path / "markpublish.yaml"), "--overridden"]
    )

    assert plain.exit_code == 0 and filtered.exit_code == 0
    for result in (plain, filtered):
        assert "liest_niemand" in result.stdout, "verwaistes Label fehlt in der Bilanz"
        assert "vom Theme nicht verwendet" in result.stdout


def test_labels_command_shows_which_layer_supplied_a_text(tmp_path: Path):
    """
    Der Kernzweck des Befehls: sehen, welche Ebene gewonnen hat.

    `chapter_toc_title` steht im Programm *und* im mitgelieferten Theme -- die
    Tabelle muss die Theme-Datei nennen, nicht nur den Text zeigen.
    """
    from typer.testing import CliRunner

    from markpublish.cli import app

    (tmp_path / "markpublish.yaml").write_text(
        PROJECT_YAML.replace('theme: "eigen"', 'theme: "default"').replace(
            'language: "en"', 'language: "de"'
        ),
        encoding="utf-8",
    )
    (tmp_path / "a.md").write_text("# A\n\nText.\n", encoding="utf-8")

    result = CliRunner(env={"COLUMNS": "220"}).invoke(
        app, ["labels", str(tmp_path / "markpublish.yaml")]
    )
    assert result.exit_code == 0
    assert "i18n-Quelle" in result.stdout, "Herkunftsspalte fehlt"
    table = result.stdout.split("Die Kaskade")[0]
    assert "theme" in table, "die ueberschreibende Ebene fehlt"
    assert "mpub" in table, "der Programmstandard wird nicht benannt"
    assert "Auf einen Blick" in table, "der Theme-Text fehlt"
    # Der Fuss loest die Kurznamen auf -- sonst waeren sie nicht nachschlagbar.
    assert "templates" in result.stdout.split("Die Kaskade")[1]


def test_labels_command_names_the_language_block_only_when_it_differs(tmp_path: Path):
    """
    Die Dokumentsprache steht im Kopf der Ausgabe. Sie hinter jeder Quelle zu
    wiederholen waere Laerm -- interessant ist der Sprachblock nur dort, wo er
    abweicht: bei "*" oder beim Rueckfall auf die Fallback-Sprache.
    """
    from typer.testing import CliRunner

    from markpublish.cli import app

    (tmp_path / "markpublish.yaml").write_text(
        PROJECT_YAML.replace('theme: "eigen"', 'theme: "default"').replace(
            'language: "en"', 'language: "de"'
        ),
        encoding="utf-8",
    )
    (tmp_path / "a.md").write_text("# A\n\nText.\n", encoding="utf-8")
    (tmp_path / "i18n.yaml").write_text(
        '"*":\n  ueberall: "Gilt immer"\nde:\n  nur_deutsch: "Nur hier"\n',
        encoding="utf-8",
    )

    result = CliRunner(env={"COLUMNS": "220"}).invoke(
        app, ["labels", str(tmp_path / "markpublish.yaml")]
    )
    assert result.exit_code == 0
    table = result.stdout.split("Die Kaskade")[0]

    assert "(*)" in table, "der sprachunabhaengige Block wird nicht benannt"
    assert "(de)" not in table, "die Dokumentsprache steht schon im Kopf"


def test_labels_command_only_overridden_hides_program_defaults(tmp_path: Path):
    """
    `--overridden` zeigt, was eine Theme-Ebene ersetzt hat -- und sonst nichts.

    `page` kommt unveraendert aus dem Programm, `chapter_toc_title` aus dem
    Theme. Der Filter muss die beiden auseinanderhalten; vorher blendete er
    stattdessen aus, was das Theme nicht liest, und liess damit beide stehen.
    """
    from typer.testing import CliRunner

    from markpublish.cli import app

    (tmp_path / "markpublish.yaml").write_text(
        PROJECT_YAML.replace('theme: "eigen"', 'theme: "default"').replace(
            'language: "en"', 'language: "de"'
        ),
        encoding="utf-8",
    )
    (tmp_path / "a.md").write_text("# A\n\nText.\n", encoding="utf-8")

    result = CliRunner(env={"COLUMNS": "220"}).invoke(
        app, ["labels", str(tmp_path / "markpublish.yaml"), "--overridden"]
    )
    assert result.exit_code == 0
    table = result.stdout.split("Die Kaskade")[0]
    assert "Auf einen Blick" in table, "das ueberschriebene Label fehlt"
    assert "alert_note" not in table, "unveraenderter Programmstandard wird angezeigt"


def test_labels_command_reports_a_theme_without_the_meta_parameter(tmp_path: Path):
    """
    Ein Theme ohne `meta:` bricht beim Bauen ab. Der Diagnosebefehl soll das
    vorher sagen -- er liest den Vertrag ohnehin schon.
    """
    from typer.testing import CliRunner

    from markpublish.cli import app

    theme = tmp_path / "themes" / "alt" / "pdf"
    theme.mkdir(parents=True)
    shutil.copytree(resolve_template_path("pdf", "default"), theme, dirs_exist_ok=True)
    template = theme / "template.typ"
    template.write_text(
        template.read_text(encoding="utf-8").replace("  meta: (:),\n", "", 1),
        encoding="utf-8",
    )

    (tmp_path / "markpublish.yaml").write_text(
        PROJECT_YAML.replace('theme: "eigen"', 'theme: "alt"').replace(
            'language: "en"', 'language: "de"'
        )
        + '\ntemplates_dir: "themes"\n',
        encoding="utf-8",
    )
    (tmp_path / "a.md").write_text("# A\n\nText.\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["labels", str(tmp_path / "markpublish.yaml")])
    assert "meta" in result.stdout
    assert "nicht deklariert" in result.stdout


def test_diagnose_labels_and_metadata_identifies_usage_and_defaults(tmp_path: Path):
    theme_typ = '''
    #let setup-document(meta: (:), labels: (:), body) = {
      let page-lbl = labels.at("page", default: "Seite")
      let custom-lbl = labels.at("my_custom_key")
      for (k, item) in meta {
        item.label
        item.value
      }
      body
    }
    '''
    (tmp_path / "template.typ").write_text(theme_typ, encoding="utf-8")
    contract = parse_theme_contract(tmp_path)

    from markpublish.config.models import DocumentConfig
    doc = DocumentConfig(title="Test", author="Frank", department="F&E")

    resolved_labels = {
        "page": {"value": "Seite", "source": "i18n.yaml"},
        "author": {"value": "Autor", "source": "i18n.yaml"},
    }

    rows = diagnose_labels_and_metadata(contract, doc, resolved_labels)
    by_key = {r.key: r for r in rows}

    # author: dynamisch ueber meta iteriert -> key/wert, Befund OK
    assert by_key["author"].theme_usage is ThemeUsage.BOTH
    assert by_key["author"].i18n_label == "Autor"
    assert by_key["author"].value == "Frank"
    assert by_key["author"].status is DiagnosisStatus.OK

    # department: freies Feld, im Dokument gesetzt, aber kein i18n-Label
    assert by_key["department"].theme_usage is ThemeUsage.BOTH
    assert by_key["department"].value == "F&E"
    assert by_key["department"].status is DiagnosisStatus.LABEL_MISSING
    assert by_key["department"].severity is Severity.WARNING

    # page: nur Label im Theme genutzt, mit Default "Seite"
    assert by_key["page"].theme_usage is ThemeUsage.KEY
    assert by_key["page"].label_fallback == "Seite"
    assert by_key["page"].applies_value is False
    assert by_key["page"].status is DiagnosisStatus.OK

    # my_custom_key: im Theme gefordert OHNE Default und nirgends definiert
    assert by_key["my_custom_key"].theme_usage is ThemeUsage.KEY
    assert by_key["my_custom_key"].breaks_build is True
    assert by_key["my_custom_key"].status is DiagnosisStatus.LABEL_BREAKS


def test_diagnose_labels_and_metadata_detects_unknown_meta_key_without_default(tmp_path: Path):
    theme_typ = '''
    #let setup-document(meta: (:), labels: (:), body) = {
      let client = meta.at("client")
      let with_def = meta.at("optional_info", default: "Standard")
      body
    }
    '''
    (tmp_path / "template.typ").write_text(theme_typ, encoding="utf-8")
    contract = parse_theme_contract(tmp_path)

    from markpublish.config.models import DocumentConfig
    doc = DocumentConfig(title="Test", author="Frank")

    rows = diagnose_labels_and_metadata(contract, doc, {})
    by_key = {r.key: r for r in rows}

    assert by_key["client"].breaks_build is True
    assert by_key["client"].status is DiagnosisStatus.META_KEY_UNKNOWN

    assert by_key["optional_info"].breaks_build is False
    assert by_key["optional_info"].value_fallback == "Standard"


def test_diagnose_does_not_flag_a_core_key_the_document_leaves_empty(tmp_path: Path):
    """
    `meta.at("version")` findet den Schluessel immer -- Kernangaben stehen auch
    dann im Dict, wenn dieses Dokument sie nicht setzt. Typst bricht also nicht
    ab, und ein roter Befund waere ein Fehlalarm.
    """
    (tmp_path / "template.typ").write_text(
        '#let setup-document(meta: (:), body) = { meta.at("version").value \n body }',
        encoding="utf-8",
    )
    from markpublish.config.models import DocumentConfig

    rows = diagnose_labels_and_metadata(
        parse_theme_contract(tmp_path), DocumentConfig(title="Test"), {}
    )
    version = {r.key: r for r in rows}["version"]
    assert version.breaks_build is False
    assert version.status is DiagnosisStatus.VALUE_MISSING


def test_check_theme_contract_aborts_on_missing_meta_key(tmp_path: Path):
    theme_typ = '''
    #let setup-document(meta: (:), body) = {
      meta.at("client")
      body
    }
    '''
    (tmp_path / "template.typ").write_text(theme_typ, encoding="utf-8")
    contract = parse_theme_contract(tmp_path)

    report = check_theme_contract(
        contract=contract,
        sent={"setup-document": {"meta"}},
        meta_keys={"title", "author"},
    )
    assert "client" in report.missing_metadata
    assert not report.missing_labels, "ein Metadatum ist kein Label"

    # Die Fundstelle ist echt, nicht geraten: Zeile 3 der Theme-Datei.
    path, line = report.missing_metadata["client"][0]
    assert path == tmp_path / "template.typ"
    assert line == 3


def test_missing_metadata_message_points_at_the_config_not_the_i18n_file():
    """
    Die Abhilfe muss die sein, die hilft. Vorher lief dieser Fall durch die
    Label-Meldung und riet, den Schluessel in eine i18n.yaml des Themes zu
    schreiben -- was den Build nicht repariert.
    """
    from markpublish.i18n import undefined_metadata_message

    text = undefined_metadata_message(
        "client", [(Path("theme/template.typ"), 12)], known_keys=["title", "clients"]
    )
    assert "markpublish.yaml" in text
    assert "document:" in text
    assert "i18n" not in text
    assert "template.typ:12" in text
    assert "clients" in text, "der aehnliche Schluessel wird genannt"


def test_setup_document_receives_metadata_only_through_meta(tmp_path: Path):
    """
    Eine Angabe, ein Weg. Die frueheren Einzelparameter (title, authors, …)
    werden nicht mehr gesendet -- sonst gaebe es zwei Quellen fuer denselben
    Wert, die auseinanderlaufen koennen.
    """
    (tmp_path / "markpublish.yaml").write_text(
        PROJECT_YAML.replace('theme: "eigen"', 'theme: "default"'), encoding="utf-8"
    )
    (tmp_path / "a.md").write_text("# A\n\nText.\n", encoding="utf-8")

    source = _assemble(tmp_path)
    sent = parse_sent_arguments(source)["setup-document"]

    assert "meta" in sent
    assert not sent & {"title", "subtitle", "authors", "version", "date", "copyright", "status", "summary"}
    assert "language" in sent, "Nicht-Metadaten bleiben Parameter"


def test_a_code_sample_in_the_document_is_not_read_as_a_call(tmp_path: Path):
    """
    Ein Dokument darf ueber markpublish schreiben. Das Handbuch tut es und
    zeigt eine `setup-document(...)`-Signatur im Codeblock -- die Pruefung darf
    daraus keine gesendeten Parameter ableiten.
    """
    (tmp_path / "markpublish.yaml").write_text(
        PROJECT_YAML.replace('theme: "eigen"', 'theme: "default"'), encoding="utf-8"
    )
    (tmp_path / "a.md").write_text(
        "# A\n\n```typst\n#let setup-document(\n  erfundener-parameter: \"\",\n  body\n) = { body }\n```\n",
        encoding="utf-8",
    )

    sent = parse_sent_arguments(_assemble(tmp_path))["setup-document"]
    assert "erfundener-parameter" not in sent


def test_a_project_i18n_names_a_free_metadata_field(tmp_path: Path):
    """
    Freie Felder stehen unter `document:`; ihre Beschriftung gehoert ins
    Projekt. Ohne diese Ebene druckte das Deckblatt den rohen Schluessel.
    """
    (tmp_path / "markpublish.yaml").write_text(
        PROJECT_YAML.replace('theme: "eigen"', 'theme: "default"').replace(
            'language: "en"', 'language: "de"\n  abteilung: "F&E"'
        ),
        encoding="utf-8",
    )
    (tmp_path / "a.md").write_text("# A\n\nText.\n", encoding="utf-8")
    (tmp_path / "i18n.yaml").write_text('de:\n  abteilung: "Abteilung"\n', encoding="utf-8")

    source = _assemble(tmp_path)
    assert '"abteilung": (key: "abteilung", label: "Abteilung"' in source


def test_the_project_level_wins_over_the_theme(tmp_path: Path):
    """Zuletzt gelesen heisst zuletzt gueltig -- das Projekt ist die letzte Ebene."""
    (tmp_path / "markpublish.yaml").write_text(
        PROJECT_YAML.replace('theme: "eigen"', 'theme: "default"').replace(
            'language: "en"', 'language: "de"'
        ),
        encoding="utf-8",
    )
    (tmp_path / "a.md").write_text("# A\n\nText.\n", encoding="utf-8")
    (tmp_path / "i18n.yaml").write_text(
        'de:\n  chapter_toc_title: "Nur hier"\n', encoding="utf-8"
    )

    assert '"chapter_toc_title": "Nur hier"' in _assemble(tmp_path)


def test_metadata_keeps_its_yaml_type_on_the_way_to_typst(tmp_path: Path):
    """
    Ein Wahrheitswert bleibt einer. Sonst stuende "True" auf dem Deckblatt --
    englisch, grossgeschrieben und vom Theme nicht mehr zu reparieren.
    """
    (tmp_path / "markpublish.yaml").write_text(
        PROJECT_YAML.replace('theme: "eigen"', 'theme: "default"').replace(
            'language: "en"', 'language: "de"\n  geprueft: true\n  seiten: 42'
        ),
        encoding="utf-8",
    )
    (tmp_path / "a.md").write_text("# A\n\nText.\n", encoding="utf-8")

    source = _assemble(tmp_path)
    assert "value: true," in source
    assert "value: 42," in source
    assert '"True"' not in source


def test_the_shipped_theme_uses_every_metadata_field_it_prints():
    """
    Waechter gegen einen Fehlalarm, den es schon einmal gab: das Theme las
    Titel, Untertitel und Summary ueber einen Helfer mit variablem Schluessel,
    und `markpublish labels` meldete sie als "ungenutzt" -- obwohl alle drei
    gross auf dem Deckblatt stehen.
    """
    from markpublish.config.models import DocumentConfig

    rows = diagnose_labels_and_metadata(
        parse_theme_contract(resolve_template_path("pdf", "default")),
        DocumentConfig(
            title="T", subtitle="U", summary="Z", author="A",
            version="1", copyright="C", status="S", language="de",
        ),
        {},
    )
    by_key = {row.key: row for row in rows}
    for key in ("title", "subtitle", "summary", "version", "date", "copyright"):
        assert by_key[key].theme_usage is not ThemeUsage.NONE, (
            f"'{key}' steht im Deckblatt, wird aber als ungenutzt gemeldet"
        )
        assert by_key[key].status is not DiagnosisStatus.UNUSED


def test_a_theme_helper_with_a_variable_key_is_not_called_unused(tmp_path: Path):
    """
    Liest ein Theme `meta` ueber einen eigenen Helfer, steht der Schluessel
    nirgends im Quelltext. Dann ist nicht ablesbar, welche Angabe gemeint ist
    -- "ungenutzt" waere eine Behauptung statt eines Befundes.
    """
    (tmp_path / "template.typ").write_text(
        "#let hole(meta, key) = meta.at(key, default: none)\n"
        "#let setup-document(meta: (:), body) = { hole(meta, \"version\") \n body }\n",
        encoding="utf-8",
    )
    from markpublish.config.models import DocumentConfig

    contract = parse_theme_contract(tmp_path)
    assert contract.has_dynamic_meta_access

    rows = diagnose_labels_and_metadata(contract, DocumentConfig(title="T"), {})
    by_key = {row.key: row for row in rows}
    assert by_key["version"].theme_usage is ThemeUsage.VALUE
    assert by_key["version"].status is not DiagnosisStatus.UNUSED


def test_labels_command_with_project_i18n_identifies_project_source_and_ok_status(tmp_path: Path):
    """
    `markpublish labels` erkennt eine projektlokale i18n.yaml als Quelle 'projekt'.
    """
    from typer.testing import CliRunner

    from markpublish.cli import app

    (tmp_path / "markpublish.yaml").write_text(
        """\
document:
  title: "Projekt"
  language: "de"
  department: "F&E"
theme: "default"
parts:
  - title: "P"
    break_before: "none"
    chapters:
      - file: "a.md"
        title: "A"
""",
        encoding="utf-8",
    )
    (tmp_path / "a.md").write_text("# A\n\nText.\n", encoding="utf-8")
    (tmp_path / "i18n.yaml").write_text(
        """\
de:
  department: "Fachabteilung"
""",
        encoding="utf-8",
    )

    runner = CliRunner(env={"COLUMNS": "200"})
    result = runner.invoke(app, ["labels", str(tmp_path / "markpublish.yaml")])
    assert result.exit_code == 0
    assert "department" in result.stdout
    assert "Fachabteilung" in result.stdout
    assert "projekt" in result.stdout
    assert "OK" in result.stdout
