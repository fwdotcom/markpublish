import re
from pathlib import Path

import pytest

from markpublish.config.loader import load_config
from markpublish.config.models import ConfigurationError
from markpublish.markdown.engine import MarkdownPipeline

YAML = """\
document:
  title: "T"
  author: "Frank"
  version: "2.2"
  language: de
  custom:
    mail: a@b.de
    count: 3
    verfahren:
      name: "Verfahren X"
parts:
  - part: "P"
    chapters:
      - file: c.md
"""


def _render(tmp_path: Path, markdown: str, yaml: str = YAML):
    if not markdown.startswith("#"):
        markdown = "# H\n\n" + markdown
    (tmp_path / "c.md").write_text(markdown, encoding="utf-8")
    (tmp_path / "markpublish.yaml").write_text(yaml, encoding="utf-8")
    config = load_config(tmp_path / "markpublish.yaml")
    items, toc = MarkdownPipeline(config, base_dir=tmp_path).process_document()
    chapter = items[0]
    while chapter.children:
        chapter = chapter.children[0]
    return chapter.typst_content, toc


def test_document_and_custom_values(tmp_path):
    typst, toc = _render(
        tmp_path,
        "# {{custom.verfahren.name}}\n\n"
        "{{author}}, {{ version }}, {{custom.count}}, [Mail](mailto:{{custom.mail}})\n",
    )
    assert "[Verfahren X]" in typst
    assert "Frank, 2.2, 3," in typst
    assert 'link("mailto:a@b.de")' in typst
    assert toc[0].children[0].title == "Verfahren X"


def test_code_keeps_placeholder(tmp_path):
    typst, _ = _render(tmp_path, "`{{author}}` {{author}}\n\n```\n{{author}}\n```\n")
    assert "`{{author}}` Frank" in typst
    assert "```\n{{author}}\n```" in typst


def test_escaped_placeholder_stays_literal(tmp_path):
    typst, toc = _render(
        tmp_path,
        "# Mit \\{{custom.x}}\n\n"
        "\\{{autor}} {{author}} \\{{ author }}\n\n"
        "`\\{{author}}`\n\n```\n\\{{author}}\n```\n",
    )
    assert "\ue000" not in typst
    assert "{{autor}} Frank {{ author }}" in typst
    assert "`\\{{author}}`" in typst
    assert "```\n\\{{author}}\n```" in typst
    assert toc[0].children[0].title == "Mit {{custom.x}}"


@pytest.mark.parametrize("name", ["autor","custom.missing", "custom.verfahren", "subtitle"])
def test_unknown_placeholder_fails(tmp_path, name):
    with pytest.raises(ConfigurationError, match=r"\{\{" + re.escape(name) + r"\}\}.*c\.md"):
        _render(tmp_path, f"Text {{{{{name}}}}}\n")


@pytest.mark.parametrize("custom", ["[1, 2]", "{a: [1]}", "{a.b: 1}", "{a: null}"])
def test_custom_rejects_invalid_values(tmp_path, custom):
    yaml = YAML.replace("  custom:\n", f"  custom: {custom}\n  ignored:\n")
    with pytest.raises(ValueError, match="document.custom"):
        _render(tmp_path, "Text\n", yaml)


def test_document_fields_use_custom_values(tmp_path):
    yaml = YAML.replace(
        '  title: "T"\n',
        '  title: "{{custom.verfahren.name}}"\n'
        '  summary: "Zugriff auf {{ custom.verfahren.name }}"\n'
        '  department: "Ref. {{custom.count}}"\n',
    )
    doc = load_config(yaml).document
    assert doc.title == "Verfahren X"
    assert doc.summary == "Zugriff auf Verfahren X"
    assert doc.model_extra["department"] == "Ref. 3"


@pytest.mark.parametrize("name", ["author", "title", "custom.nope", "custom.verfahren"])
def test_document_fields_reject_other_placeholders(name):
    yaml = YAML.replace('  title: "T"\n', f'  title: "{{{{{name}}}}}"\n')
    with pytest.raises(ConfigurationError, match=r"\{\{" + re.escape(name) + r"\}\}.*document\.title"):
        load_config(yaml)


ROLES_YAML = YAML.replace(
    "    verfahren:\n",
    "    roles:\n"
    "      owner: {label: Verantwortlich, name: Anna}\n"
    "      admin: {label: Administration, name: Bert}\n"
    "    verfahren:\n",
)


def test_for_repeats_table_rows(tmp_path):
    typst, _ = _render(
        tmp_path,
        "| Rolle | Name | Schlüssel |\n| --- | --- | --- |\n"
        "{% for (role, key) in custom.roles %}\n"
        "| {{role.label}} | {{ role.name }} | {{key}} |\n"
        "{% endfor %}\n",
        ROLES_YAML,
    )
    assert "{%" not in typst
    assert typst.index("Anna") < typst.index("Bert")
    assert "[owner]" in typst and "[admin]" in typst


def test_set_alias_and_nested_loops(tmp_path):
    yaml = ROLES_YAML.replace(
        "      admin: {label: Administration, name: Bert}\n",
        "      admin: {label: Administration, name: Bert}\n"
        "    teams:\n      a: {x: {n: A1}, y: {n: A2}}\n      b: {z: {n: B1}}\n",
    )
    typst, _ = _render(
        tmp_path,
        "{% set roles = custom.roles %}\n"
        "{% set owner = roles.owner %}\n"
        "Zuständig: {{owner.name}}, {{roles.admin.name}}.\n\n"
        "{% for team in custom.teams %}\n"
        "{% for member in team %}\n"
        "- {{member.n}}\n"
        "{% endfor %}\n"
        "{% endfor %}\n",
        yaml,
    )
    assert "Zuständig: Anna, Bert." in typst
    assert re.search(r"A1.*A2.*B1", typst, re.S)


def test_loop_variable_ends_with_loop(tmp_path):
    with pytest.raises(ConfigurationError, match=r"\{\{role\.name\}\}"):
        _render(
            tmp_path,
            "{% for role in custom.roles %}\n{{role.name}}\n{% endfor %}\n\n{{role.name}}\n",
            ROLES_YAML,
        )


def test_statements_in_code_and_escaped_stay_literal(tmp_path):
    typst, _ = _render(
        tmp_path,
        "```\n{% for role in custom.roles %}\n```\n\n"
        "`{% endfor %}` und \\{% set a = b %}\n",
    )
    assert "```\n{% for role in custom.roles %}\n```" in typst
    assert "`{% endfor %}`" in typst
    assert "{% set a = b %}" in typst and "\\{%" not in typst


def test_statements_in_indented_code_and_comments_stay_literal(tmp_path):
    typst, _ = _render(
        tmp_path,
        "Text\n\n    {% raw %} x\n    {% for role in custom.roles %}\n\n"
        "<!-- {% foreach %} -->\n<!--\n{% endfor %}\n-->\n"
        "{% for role in custom.roles %}\n- {{role.name}} <!-- {{role}} -->\n{% endfor %}\n",
        ROLES_YAML,
    )
    assert "{% raw %} x\n{% for role in custom.roles %}" in typst
    assert "Anna" in typst and "Bert" in typst


def test_loop_in_indented_container(tmp_path):
    typst, _ = _render(
        tmp_path,
        "!!! note\n    {% for role in custom.roles %}\n    - {{role.name}}\n    {% endfor %}\n\n"
        "- Liste\n\n    {% for role in custom.roles %}\n    {{role.label}}\n    {% endfor %}\n",
        ROLES_YAML,
    )
    assert "{%" not in typst
    assert "Anna" in typst and "Administration" in typst


def test_loop_over_numeric_keys(tmp_path):
    yaml = YAML.replace("    count: 3\n", "    count: 3\n    years: {2024: {n: A}, 2025: {n: B}}\n")
    typst, _ = _render(
        tmp_path,
        "{% for (year, key) in custom.years %}\n- {{key}}: {{year.n}}\n{% endfor %}\n\n"
        "{{custom.years.2025.n}}\n",
        yaml,
    )
    assert "2024: A" in typst and "2025: B" in typst


def test_loop_in_callout(tmp_path):
    typst, _ = _render(
        tmp_path,
        "> [!NOTE]\n> {% for role in custom.roles %}\n> - {{role.name}}\n> {% endfor %}\n",
        ROLES_YAML,
    )
    assert "Anna" in typst and "Bert" in typst and "{%" not in typst


@pytest.mark.parametrize(
    "markdown, message",
    [
        ("{% for role in custom.roles %}\nx\n", r"line 3: this \{% for %\} has no"),
        ("x\n{% endfor %}\n", r"line 4: \{% endfor %\} without"),
        ("{% foreach role in custom.roles %}\n", r"line 3: \{% foreach"),
        ("Text {% endfor %}\n", "line 3: a statement"),
        ("{% for r in custom.nope %}\n{% endfor %}\n", "line 3: custom.nope has no value"),
        ("{% for r in custom.mail %}\n{% endfor %}\n", "line 3: custom.mail is a single value"),
        ("{% set author = custom.mail %}\n", "line 3: the name author is already"),
    ],
)
def test_statement_errors(tmp_path, markdown, message):
    with pytest.raises(ConfigurationError, match=r"c\.md, " + message):
        _render(tmp_path, markdown, ROLES_YAML)


def test_address_values_become_links(tmp_path):
    yaml = YAML.replace("    count: 3\n", "    count: 3\n    web: https://example.org/x\n")
    typst, _ = _render(
        tmp_path,
        "Mail: {{custom.mail}}, Web: {{custom.web}}, Text: {{author}}.\n\n"
        "[Schreiben]({{custom.web}}) und [{{custom.mail}}](mailto:{{custom.mail}})\n\n"
        "| Kontakt |\n| --- |\n| {{custom.mail}} |\n",
        yaml,
    )
    assert 'Mail: #link("mailto:a@b.de")[a\\@b.de], Web: #link("https://example.org/x")' in typst
    assert ", Text: Frank." in typst
    assert typst.count('link("mailto:a@b.de")') == 3
    assert typst.count("#link") == 5
