# Templates and themes

Everything visual lives in a theme: page layout, stylesheet and static texts.
markpublish ships one, `default`, with a `pdf` and an `html` variant.

## Where a theme is looked up

First hit wins -- a theme always comes from exactly one place, never merged.

| Order | Location |
| :--- | :--- |
| 1. User | `~/.markpublish/templates`, else the OS config directory |
| 2. Project | `templates_dir` in the YAML, `MARKPUBLISH_TEMPLATES_DIR`, or `./templates` |
| 3. Package | the built-in themes |

`markpublish templates` lists what is available and where it was found.

## Customising

```bash
markpublish export-template default ./templates
```

Copies the built-in theme into your project, where step 2 picks it up on the
next build. A theme holds `layout.html`, `styles.css`, `cover.html`,
`toc.html`, `chapter_divider.html`, `part_divider.html` and `i18n.yaml`.
Markup and stylesheet both run through Jinja2 and see `document`,
`content_items`, `toc_tree` and `labels`.

## Static texts

Labels resolve through three layers; a later one overrides only the keys it
actually sets.

| Layer | File |
| :--- | :--- |
| 1. Program | `markpublish/i18n.yaml` |
| 2. Theme | `<templates>/<theme>/i18n.yaml` |
| 3. Target | `<templates>/<theme>/<pdf\|html>/i18n.yaml` |

Each file is keyed by language code; the key `"*"` applies to every language.
A document cannot override labels -- that is what a theme is for. See what a
theme changed with `markpublish labels --overridden`.
