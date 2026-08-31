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
- 📑 **2-Line Headers & Footers**: Cleanly designed inside templates and automatically populated from document metadata.
- 🔢 **Autonumbering & TOC**:
  - Global TOC reflecting chapter depth and heading levels.
  - Per-chapter local TOCs with configurable `max_depth`.
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

This creates a starter directory with `markpublish.yaml` and sample chapters.

### 2. Build PDF and HTML
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
  version: "1.0.0"
  language: "de"                 # Localization and hyphenation

  # Layout Toggles
  cover: true                    # Enable cover page
  toc: true                      # Global table of contents
  autonum_type: "decimal"        # "decimal" (1, 1.1), "roman", "legal", "none"
  header: true                   # Enable 2-line header (defined in template)
  footer: true                   # Enable 2-line footer (defined in template)

# Template selection
theme: "default"
templates_dir: "./templates"     # Optional: custom shared templates directory

# Chapters & Overarching Parts
chapters:
  # Level 1 Chapter
  - file: "chapters/01_introduction.md"
    title: "Introduction"
    summary: "Scope and motivation."
    divider_page: true           # Dedicated divider/separator page
    toc: false

  # Level 1 Chapter with Nested Sub-chapters
  - file: "chapters/02_architecture.md"
    title: "Core Architecture"
    summary: "System components and flows."
    divider_page: true
    toc: 2                       # Local chapter TOC up to depth 2
    chapters:
      # Level 2 (2.1)
      - file: "chapters/02_1_backend.md"
        title: "Backend Services"
        divider_page: false
        
      # Level 2 (2.2)
      - file: "chapters/02_2_frontend.md"
        title: "Frontend Application"
        divider_page: false

  # Overarching Part / Section (e.g. Appendices)
  - part: "Appendices"
    summary: "Glossary and reference tables."
    divider_page: true           # Dedicated Part separator page
    autonum: "none"
    chapters:
      - file: "chapters/appendix_a.md"
        title: "Appendix A: Glossary"
        divider_page: false
```

---

## Template System

Templates are organized by target format:
```
templates/
├── pdf/
│   └── default/
│       ├── layout.html          # Jinja2 layout
│       ├── styles.css           # CSS Paged Media (@page, @top-left, @bottom-right)
│       ├── cover.html           # Cover page
│       ├── part_divider.html    # Part separator page
│       ├── chapter_divider.html # Chapter separator page & local TOC
│       └── toc.html             # Global TOC
└── html/
    └── default/
        └── ...
```

### Template Resolution Order:
When rendering `pdf` with theme `default`:
1. **User directory**: `~/.markpublish/templates/default/pdf/` (or OS config dir)
2. **Common / Project directory**: `<templates_dir>/default/pdf/` (configured via `--templates-dir`, YAML `templates_dir`, `MARKPUBLISH_TEMPLATES_DIR`, or `./templates`)
3. **Package built-ins**: Embedded inside `markpublish`.


### Static texts and language

Fixed labels in the templates (table of contents heading, chapter tags, cover labels,
page footer, callout titles) come from a translation table selected by
`document.language`. `de` and `en` ship with the package; regional forms map onto them
(`de-AT` -> `de`) and an unknown language falls back to English.

```yaml
document:
  language: "en"
  labels:                      # optional, overrides single keys
    chapter_toc_title: "On this page"
```

The layering is English -> document language -> `labels`, so a missing entry never
renders as an empty string. `document.labels` is also the way to supply a language the
table does not cover yet, without touching a template. In custom templates the table is
reachable as `{{ labels.chapter }}` -- including inside `styles.css`, which is rendered
through the same Jinja environment.

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
| `markpublish templates` | Lists available templates across User, Common, and Package sources |
| `markpublish export-template [theme]` | Copies a built-in template to project directory |

---

## License

MIT License. See [LICENSE](LICENSE) for details.

