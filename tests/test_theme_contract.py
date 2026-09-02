"""
Tests fuer die Theme-Vertragspruefung.

Geprueft wird beides: der Parser fuer sich (schnell, viele Faelle) und der
Renderer-Durchlauf (langsam, dafuer echt) -- denn nur letzterer belegt, dass
die Pruefung ueberhaupt aufgerufen wird. Eine Pruefung, die niemand ausloest,
war der Ausgangspunkt dieses Moduls.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from markpublish.config.loader import load_config
from markpublish.i18n import UndefinedLabelError
from markpublish.markdown.engine import MarkdownPipeline
from markpublish.renderers.base import DocumentContext
from markpublish.renderers.pdf import PDFRenderer
from markpublish.templates.contract import (
    ThemeContractWarning,
    check_theme_contract,
    engine_labels,
    label_overview,
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
# Uebersicht definiert / gelesen
# --------------------------------------------------------------------------

def test_overview_marks_a_label_nobody_reads(tmp_path: Path):
    (tmp_path / "template.typ").write_text(
        '#let setup-document(labels: (:), body) = { [#labels.at("page", default: "")] }',
        encoding="utf-8",
    )
    rows = {
        row.key: row
        for row in label_overview(parse_theme_contract(tmp_path), {"page", "verwaist"})
    }

    assert rows["page"].defined and rows["page"].used
    assert rows["verwaist"].defined and not rows["verwaist"].used


def test_overview_marks_a_label_that_is_read_but_undefined(tmp_path: Path):
    (tmp_path / "template.typ").write_text(
        '#let setup-document(labels: (:), body) = { [#labels.at("frei")] }',
        encoding="utf-8",
    )
    rows = {row.key: row for row in label_overview(parse_theme_contract(tmp_path), set())}

    assert not rows["frei"].defined
    assert rows["frei"].used
    assert rows["frei"].breaks_build, "ohne Fallback bricht der Build ab"


def test_overview_counts_labels_markpublish_reads_itself(tmp_path: Path):
    """
    `toc_title` steht in keinem `labels.at(...)` des Templates -- markpublish
    liest es und reicht es als Parameter weiter. Ein reiner Textscan wuerde es
    faelschlich als unbenutzt melden und zum Loeschen einladen.
    """
    (tmp_path / "template.typ").write_text(
        '#let setup-document(toc-title: "", body) = { body }', encoding="utf-8"
    )
    rows = {
        row.key: row
        for row in label_overview(parse_theme_contract(tmp_path), {"toc_title"})
    }
    assert rows["toc_title"].used
    assert rows["toc_title"].readers == {"markpublish"}


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
    from markpublish.i18n import build_labels

    contract = parse_theme_contract(resolve_template_path("pdf", "default"))
    for language in ("de", "en"):
        resolved = build_labels(language)
        gaps = [
            row.key
            for row in label_overview(contract, set(resolved))
            if row.used and not row.defined
        ]
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

    runner = CliRunner()
    plain = runner.invoke(app, ["labels", str(tmp_path / "markpublish.yaml")])
    filtered = runner.invoke(
        app, ["labels", str(tmp_path / "markpublish.yaml"), "--overridden"]
    )

    assert plain.exit_code == 0 and filtered.exit_code == 0
    for result in (plain, filtered):
        assert "toc_sidebar" in result.stdout, "verwaistes Label fehlt in der Bilanz"
        assert "wird von niemandem gelesen" in result.stdout
