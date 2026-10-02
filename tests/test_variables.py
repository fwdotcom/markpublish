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
