# Configuration Guide

`markpublish.yaml` is the control document of every publication. It falls into three parts: `document` for metadata and global switches, `theme` for choosing the design, and `chapters` for the structure of the document.

## The `document` object

Everything global — metadata and layout switches — lives under `document:`:

```yaml
document:
  title: "markpublish User Guide"
  subtitle: "Modern PDF and HTML publishing"
  summary: "Short abstract for the cover page and metadata."
  author: "Frank Winter"
  organisation: "WASDCAT Games"
  date: "auto"                 # "auto" (today) or a fixed date "2026-08-31"
  version: "1.0.0"             # optional - omit it and the field disappears
  language: "en"               # labels and date format; defaults to the system language

  # Global switches
  cover: true                  # Cover page on/off
  document_toc: 2              # Large TOC, two levels deep
  autonum_style: "decimal"     # "decimal", "roman", "legal", "none"
  chapter_toc: 2               # Default for the chapter divider pages
  header: true                 # Running header
  footer: true                 # Running footer
```

### Automatic date resolution

With `date: "auto"` or `date: "today"`, markpublish inserts the current date in the format matching the document language:

- `language: "de"` → `31.08.2026`
- `language: "en"` → `2026-08-31`

### Additional metadata fields

Any extra key (`status: "Draft"`, `department: "IT Architecture"`, …) may be defined freely and is available in every Jinja2 template as `document.<name>`.

## Defining a chapter

A plain chapter is given as `file:`, with optional `title:` and `summary:`:

```yaml
chapters:
  - file: "chapters/01_intro.md"
    title: "Introduction"
    summary: "What this guide sets out to do."
    break_before: "divider"    # Its own divider page ahead of the chapter
    chapter_toc: "none"        # No per-chapter mini TOC
```

All paths are relative to `markpublish.yaml`, not to the shell's working directory.

## Hierarchical sub-chapters

To define a sub-chapter, simply indent further chapters under `chapters:`:

```yaml
chapters:
  - file: "chapters/02_architecture.md"
    title: "System Architecture"
    break_before: "divider"
    chapter_toc: 2             # Mini TOC down to heading depth 2
    chapters:
      - file: "chapters/02_1_backend.md"
        title: "Backend Services"
      - file: "chapters/02_2_frontend.md"
        title: "Frontend Client"
```

## Document Structure in 2 Tiers: Parts and Chapters

`markpublish` strictly separates document organisation (YAML) from content structure (Markdown):

1. **Tier 1 — Parts (`parts:`):** Organises the document into major logical sections (e.g. Main Body, Appendices, Volumes). Every part must have a name (`title:` or `part:`).
2. **Tier 2 — Chapters (`chapters:`):** The actual content files (*.md) belonging to each part.
3. **Internal Structure (`##`, `###`):** Formatted directly in Markdown.

```yaml
parts:
  - title: "Main"              # Main section
    break_before: "none"       # No part divider page for the main part
    document_toc: "none"       # 'Main' is not listed in TOC; chapters appear directly
    chapters:
      - file: "chapters/01_intro.md"
        title: "Introduction"
      - file: "chapters/02_usage.md"
        title: "Usage"

  - title: "Appendices"        # Section with divider page & TOC rubric
    summary: "Supplementary tables and references."
    break_before: "divider"
    autonum_from_level: 2
    document_toc: 2
    chapters:
      - file: "chapters/appendix_a.md"
        title: "Appendix A: Reference"
        autonum_prefix: "A."
      - file: "chapters/appendix_b.md"
        title: "Appendix B: Glossary"
        autonum_prefix: "B."
```

A named part groups its chapters, optionally receives a divider page, and appears as a structural category in the table of contents (unless omitted via `document_toc: "none"`). All chapters align to the same primary baseline.
