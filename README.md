# markpublish

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**markpublish** is a modern, modular, and extensible publishing tool for Markdown documents. It compiles structured Markdown chapters into print-ready **PDFs** (powered by [WeasyPrint](https://weasyprint.org/) and W3C CSS Paged Media) and standalone **HTML** previews, fully configured via a clean YAML manifest.

---

## Key Features

- 📄 **WeasyPrint PDF Engine**: Native support for CSS Paged Media (`@page`, `@top-left`, `@top-right`, `@bottom-left`, `@bottom-right`, page counters, leaders, target counters).
- 🌐 **Multi-Format Pipeline**: First-class support for **PDF** and **HTML** (extensible architecture for EPUB, DOCX).
- ⚙️ **Declarative YAML Configuration**: Configure metadata, covers, TOCs, headers, and footers in `markpublish.yaml`.
- 📁 **Modular Chapters & Parts**: Split your content into separate `.md` files, organize them hierarchically, and group them under overarching **Parts** (e.g. *Appendices*).
- 🎨 **Target-Based Template Hierarchy**:
  - `templates/<theme>/pdf` and `templates/<theme>/html`
  - 3-tier resolution: **User directory** > **Common/Project folder** > **Package built-ins**.
- 🔤 **Bundled font**: Open Sans ships with the theme as a variable font and is embedded into the PDF, so output does not depend on what is installed on the build machine.
- 📑 **Running Headers & Footers**: Real markup in the page margins via CSS running elements -- any number of lines, per-line styling, columns top-aligned.
- 🔢 **Autonumbering & TOC**:
  - Global TOC reflecting chapter depth and heading levels.
  - Per-chapter local TOCs with configurable `max_depth` (rendered on the PDF divider page).
  - Configurable autonumbering schemes (`decimal`, `roman`, `legal`, `none`).
- 💻 **Cross-Platform**: Works seamlessly on Linux, macOS, and Windows.

---

## Installation

```bash
pip install markpublish
```

For development:
```bash
git clone https://github.com/your-username/markpublish.git
cd markpublish
pip install -e ".[dev]"
```

---

## Quickstart

### 1. Initialize a new project
```bash
markpublish init my-book --title "My Architecture Guide"
cd my-book
```

This creates a minimal stub: `markpublish.yaml` plus one chapter, both directly
in the directory. It is meant to be replaced by your own content.

### 2. Look things up
```bash
markpublish cheatsheet [--lang de|en]   # two-page reference card
markpublish manual     [--lang de|en]   # the full user guide
```

`cheatsheet` renders a two-page reference -- every key of `markpublish.yaml` on
page one, themes and templates on page two. `manual` renders the complete user
guide. Both ship in German and English, their sources inside the package, and
are rendered on demand -- so they describe the version you actually have rather
than whatever was current when someone last rebuilt a PDF, and a successful run
also confirms that the rendering toolchain works.

`--lang` selects the source, not just the labels: each translation carries its
own `language:` and pulls in the matching static texts by itself. Without it,
your system language decides; where no translation exists, English appears.

### 3. Build PDF and HTML
```bash
# Build PDF
markpublish build

# Build standalone HTML
markpublish build --target html

# Build both PDF and HTML
markpublish build --target all
```

---

## Configuration Reference (`markpublish.yaml`)

```yaml
# Document Metadata & Layout
document:
  title: "Cloud Architecture Guide"
  subtitle: "Best Practices & Standards"
  summary: "Comprehensive guide for modern enterprise cloud environments."
  author: "Frank Mustermann"
  date: "auto"                    # "auto" for current date, or "2026-08-31"
  version: "1.0.0"              # optional; omitted -> no version on the cover
  language: "de"                 # Localization and hyphenation; omit it and
                                 # your system language applies

  # Layout Toggles
  cover: true                    # Enable cover page
  document_toc: 2                # Large TOC, two levels deep
  autonum_type: "decimal"        # "decimal" (1, 1.1), "roman", "legal", "none"
  chapter_toc: 2                 # Default for the chapters' divider-page TOC
  header: true                   # Enable running header (laid out in the theme)
  footer: true                   # Enable running footer (laid out in the theme)

# Template selection
theme: "default"
templates_dir: "./templates"     # Optional: custom shared templates directory

# Chapters & Overarching Parts
chapters:
  # Level 1 Chapter
  - file: "chapters/01_introduction.md"
    title: "Introduction"
    summary: "Scope and motivation."
    break_before: "divider"      # Dedicated divider/separator page
    chapter_toc: "none"

  # Level 1 Chapter with Nested Sub-chapters
  - file: "chapters/02_architecture.md"
    title: "Core Architecture"
    summary: "System components and flows."
    break_before: "divider"
    chapter_toc: 2               # Local chapter TOC up to depth 2
    chapters:
      # Level 2 (2.1)
      - file: "chapters/02_1_backend.md"
        title: "Backend Services"

      # Level 2 (2.2)
      - file: "chapters/02_2_frontend.md"
        title: "Frontend Application"
        break_before: "none"     # Runs on from the previous chapter

  # Overarching Part / Section (e.g. Appendices)
  - part: "Appendices"
    summary: "Glossary and reference tables."
    break_before: "divider"      # Dedicated Part separator page
    autonum: "none"
    document_toc: 1              # Appendices enter the front TOC by title only
    chapters:
      - file: "chapters/appendix_a.md"
        title: "Appendix A: Glossary"
```

`break_before` decides how far a chapter is set off from the one before it, on a
single axis: `page` (the default) starts it at the top of a fresh page,
`divider` gives it a separator page of its own, and `none` lets it run on.

A document has two tables of contents and one key each, written the same way in
the `document` block and on a chapter: `document_toc` for the large one at the
front, `chapter_toc` for the small ones on the divider pages. Under `document`
they set the default, on a chapter they override it. Both take `none`, `full` or
a depth counted from the chapter's own heading, so `document_toc: 1` contributes
the chapter title and nothing below it.

`document_toc` and `autonum` are inherited downwards, which is why one line on
the `Appendices` part flattens every appendix at once -- and why `autonum:
"none"` there leaves the whole appendix unnumbered without consuming a chapter
number. `chapter_toc` is not chained; it falls back to `document.chapter_toc`,
so the common case is one line at the top instead of one per chapter.

---

## Template System

Templates are organized by theme first, then by target format:
```
templates/
└── default/
  ├── pdf/
  │   ├── layout.html          # Jinja2 layout
  │   ├── styles.css           # CSS Paged Media (@page, @top-left, @bottom-right)
  │   ├── cover.html           # Cover page
  │   ├── part_divider.html    # Part separator page
  │   ├── chapter_divider.html # Chapter separator page & local TOC (PDF only)
  │   └── toc.html             # Global TOC
  └── html/
    └── ...
```

### Template Resolution Order:
When rendering `pdf` with theme `default`:
1. **User directory**: `~/.markpublish/templates/default/pdf/` (or OS config dir)
2. **Common / Project directory**: `<templates_dir>/default/pdf/` (configured via `--templates-dir`, YAML `templates_dir`, `MARKPUBLISH_TEMPLATES_DIR`, or `./templates`)
3. **Package built-ins**: Embedded inside `markpublish`.


### Static texts and language

Fixed labels (table of contents heading, chapter tags, cover labels, page footer,
callout titles) live in `i18n.yaml` files rather than in the templates. The language
comes from `document.language`; `de` and `en` ship with the package, regional forms map
onto them (`de-AT` -> `de`), and an unknown language falls back to English. Leave the key
out and the system language applies -- `markpublish init` writes it down, so a document
builds the same on every machine.

*i18n* is the source data across all languages; *labels* is what it resolves to for one
document in one language, i.e. what a template sees as `{{ labels.chapter }}`.

Three levels, all built the same way -- language code, then key/text. Each level
overrides the one above it, and only for the keys it actually sets:

| Level | Location |
| :--- | :--- |
| 1 | `markpublish/i18n.yaml` (complete, `de` + `en`) |
| 2 | `<templates>/<theme>/i18n.yaml` |
| 3 | `<templates>/<theme>/<target>/i18n.yaml` |

Levels 2 and 3 always come from the **one** theme the template resolution picked
(user > project > package); a project theme does not inherit the texts of the
package theme of the same name. A document cannot override texts -- give it its
own theme (`markpublish export-template`) instead.

```yaml
# any of the three levels
"*":                       # applies to every language
  version: "Rev."
de:
  part: "Abschnitt"
en:
  part: "Section"
```

A flat mapping without the language level is shorthand for `"*"`. Levels 2 and 3 apply
**only to the selected language**, so a theme's English block never leaks into German
output. Level 1 additionally layers English underneath the document language, so every
program text always resolves. A missing `i18n.yaml` is fine; a malformed one aborts the
build naming the file.

#### Free labels

A theme may define keys the program knows nothing about -- for the static texts of the
template itself -- and read them back with `{{ labels.imprint_title }}`. There is no
program default to fall back on for those, so the rule is strict: a label written in a
template must resolve in the cascade, otherwise the build **aborts** and names the key,
the file and line that used it, the document language, and the `i18n.yaml` files that
were searched. Keep every language of a free label filled in, or put it under `"*"`.
An empty string in a finished PDF goes unnoticed; an abort does not.

The bundled `default` theme ships all three template-side files as commented patterns,
and `markpublish export-template` copies them along with the templates.

Run `markpublish labels [--target html] [--overridden]` to see the resolved table and
which level supplied each value.

### Exporting Templates for Customization:
```bash
markpublish export-template default
```

---

## CLI Commands

| Command | Description |
| :--- | :--- |
| `markpublish build [config.yaml]` | Builds PDF/HTML outputs (`-t pdf`, `-t html`, `-t all`) |
| `markpublish init [path]` | Scaffolds a new project with chapters and configuration |
| `markpublish cheatsheet` | Renders the two-page reference card (`--lang`, `--target`) |
| `markpublish manual` | Renders the full user guide (`--lang`, `--target`) |
| `markpublish templates` | Lists available templates across User, Common, and Package sources |
| `markpublish export-template [theme]` | Copies a built-in template to project directory |
| `markpublish labels` | Shows the resolved static texts and their cascade origin |

---

## License

MIT License. See [LICENSE](LICENSE) for details.

