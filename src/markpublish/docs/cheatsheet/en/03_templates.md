# Templates and Themes

Everything visible is controlled by a theme: typography, page layout, and static
text. The built-in default theme `default` is provided for PDF.

## Where Themes Are Located

The first match wins — a theme is always loaded from exactly one source location
and never merged across multiple locations. Which theme is used is determined
by the `--theme` command-line option or the `theme:` setting in `markpublish.yaml`
(default: `default`).

| Rank | Location |
| :--- | :--- |
| 1. User | `~/.markpublish/templates/<theme>/` or user-specific AppData directory |
| 2. Project | `--templates-dir` on CLI, `templates_dir:` in YAML, `MARKPUBLISH_TEMPLATES_DIR`, or `./templates/<theme>/` |
| 3. Package | Built-in standard theme `default` |

`markpublish templates` lists all templates available on the system along with their resolution rank and origin.

## Customizing a Theme

```bash
markpublish export-template default ./templates
```

This command copies the built-in theme files into your project directory, where
resolution rank 2 automatically discovers and uses them on the next build.
For PDF output, a theme directory contains:

* `template.typ`: Main Typst layout template defining page geometry, headers, footers, and styles
* `i18n.yaml`: Shared label definitions and localized strings across the theme
* `pdf/i18n.yaml`: Format-specific label definitions and string overrides for PDF
* `fonts/`: Optional custom font files (.ttf, .otf) loaded by Typst
* `assets/`: Image assets, logos, and vector icons

## Static Labels (i18n)

Labels resolve through a four-stage cascade; a lower level overrides only
the keys it explicitly defines:

| Level | File |
| :--- | :--- |
| 1. Application | `markpublish/i18n.yaml` (application default strings) |
| 2. Theme | `<templates>/<theme>/i18n.yaml` |
| 3. Target format | `<templates>/<theme>/pdf/i18n.yaml` |
| 4. Project | `./i18n.yaml` next to `markpublish.yaml` |

Each file is organized by language code (`de:`, `en:`); the key `"*"` applies
to all languages. Level 4 belongs to the project: it allows overriding labels
and localizing custom metadata fields (`department: "Department"`).
Use `markpublish labels --overridden` or `markpublish labels --theme <theme>`
to inspect the cascade before building.

## Key CLI Commands

| Command | Key Options | Description |
| :--- | :--- | :--- |
| `markpublish build` | `--theme`, `--target`, `-o`, `--templates-dir` | Compile document to PDF |
| `markpublish init` | `[TARGET]`, `--title`, `--lang` | Set up a minimal starter project |
| `markpublish cheatsheet` | `--lang`, `--theme`, `-o`, `--templates-dir` | Generate this quick reference as PDF |
| `markpublish manual` | `--lang`, `--theme`, `-o`, `--templates-dir` | Generate the complete user manual |
| `markpublish templates` | `--target`, `--templates-dir` | List templates and lookup rank |
| `markpublish export-template` | `[THEME]`, `[TARGET]`, `--target` | Export template files for customization |
| `markpublish labels` | `--theme`, `--target`, `--templates-dir`, `--overridden` | Inspect static labels and metadata |

