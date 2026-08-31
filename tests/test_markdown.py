"""
Tests for Markdown parsing, extensions, and asset resolution.
"""

from pathlib import Path

from markpublish.markdown.assets import rewrite_html_asset_paths
from markpublish.markdown.engine import MarkdownEngine


def test_markdown_extensions():
    engine = MarkdownEngine()

    # Table test
    table_md = """
| Col 1 | Col 2 |
| :--- | :--- |
| Val A | Val B |
"""
    html_table = engine.convert(table_md)
    assert "<table>" in html_table
    assert "Col 1</th>" in html_table
    assert "Val A</td>" in html_table

    # Admonition test
    admonition_md = """
!!! note "Important Title"
    This is an admonition body.
"""
    html_admonition = engine.convert(admonition_md)
    assert 'class="admonition note"' in html_admonition
    assert "Important Title" in html_admonition

    # Code highlighting test
    code_md = """
```python
def test_func():
    return 42
```
"""
    html_code = engine.convert(code_md)
    assert "<code" in html_code
    assert "test_func" in html_code


def test_asset_path_rewriting(tmp_path: Path):
    img_file = tmp_path / "images" / "diagram.png"
    img_file.parent.mkdir(parents=True)
    img_file.write_bytes(b"dummy image data")

    html = '<p><img src="images/diagram.png" alt="Diagram"></p>'
    rewritten = rewrite_html_asset_paths(html, tmp_path)

    # Lokale Assets werden als Data-URI eingebettet, damit die erzeugte HTML-
    # Datei portabel bleibt und nicht auf absolute file://-Pfade zeigt.
    assert "data:image/png;base64," in rewritten
    assert "file://" not in rewritten


def test_asset_rewriting_leaves_remote_urls_alone(tmp_path: Path):
    html = (
        '<img src="https://example.com/a.png">'
        '<img src="data:image/gif;base64,R0lGOD">'
    )
    rewritten = rewrite_html_asset_paths(html, tmp_path)
    assert 'src="https://example.com/a.png"' in rewritten
    assert 'src="data:image/gif;base64,R0lGOD"' in rewritten


def test_github_alerts():
    # Test German localization (default)
    engine_de = MarkdownEngine(language="de")

    md_text_de = """
> [!NOTE]
> Das ist ein Hinweis.

> [!TIP] Individueller Tipp
> Das ist ein Tipp.

> [!IMPORTANT]
> Das ist wichtig.

> [!WARNING]
> Das ist eine Warnung.

> [!CAUTION]
> Das ist Achtung.

> Normales Zitat.
"""
    html_de = engine_de.convert(md_text_de)

    # Check German titles
    assert "Hinweis" in html_de
    assert "Individueller Tipp" in html_de
    assert "Wichtig" in html_de
    assert "Warnung" in html_de
    assert "Achtung" in html_de

    # Check alert classes
    assert 'class="admonition note"' in html_de
    assert 'class="admonition tip"' in html_de
    assert 'class="admonition important"' in html_de
    assert 'class="admonition warning"' in html_de
    assert 'class="admonition caution"' in html_de

    # Test English localization
    engine_en = MarkdownEngine(language="en")
    md_text_en = """
> [!NOTE]
> Note text.
"""
    html_en = engine_en.convert(md_text_en)
    assert "Note" in html_en


