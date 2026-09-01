# Markdown Features & Syntax

`markpublish` ships a capable Markdown engine with full support for modern documentation elements.

## Code blocks & syntax highlighting

Source code is highlighted by Pygments:

```python
from markpublish.config.loader import load_config
from markpublish.markdown.engine import MarkdownPipeline

# Load the manifest
config = load_config("markpublish.yaml")
print(f"Building: {config.document.title}")
```

## Tables

Tables are rendered with a clean zebra pattern and protection against page breaks:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `title` | String | *required* | Main title of the document |
| `author` | String | `None` | Author name |
| `status` | String | `None` | Document status (e.g. "Released", "Draft") |
| `copyright` | String | `None` | Copyright notice (e.g. "© 2026 Frank Winter") |
| `version` | String | `null` | Version identifier. Without it the field disappears from the cover page; when set, it appears in the footer to the left of the date |

## GitHub-style callouts (alerts)

`markpublish` supports the common **GitHub alert syntax** with five semantic types. The icons come straight from the template:

> [!NOTE]
> An informative note with a blue accent and a matching info icon.

> [!TIP]
> Use `markpublish build --target all` to produce PDF and HTML in one pass.

> [!IMPORTANT]
> Callout titles are localised automatically from the document language
> (*Hinweis*, *Tipp*, *Wichtig*, *Warnung*, *Achtung* in German).

> [!WARNING]
> With relative image paths, make sure they are relative to the Markdown file
> that references them.

> [!CAUTION]
> Malformed YAML indentation aborts the build while parsing the manifest.

> [!TIP] A title of your own
> After the alert type you may give an individual title, which replaces the
> default label.

The classic `!!! note` syntax remains supported as well.

## Task lists

- [x] Initialise the project
- [x] Write the chapters
- [ ] Publish the document
