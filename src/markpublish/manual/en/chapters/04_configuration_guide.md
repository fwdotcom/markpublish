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
  language: "en"               # language code for labels and date format

  # Global switches
  cover: true                  # Cover page on/off
  document_toc: 2              # Large TOC, two levels deep
  autonum_type: "decimal"      # "decimal", "roman", "legal", "none"
  chapter_toc: 2               # default for the chapter divider pages
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
        break_before: "none"   # Runs on without a break
```

`markpublish` numbers the sub-chapters consistently as `2.1` and `2.2`. Nesting is recursive — there is no fixed limit on the depth.

Unless told otherwise, every chapter starts at the top of a new page, a sub-chapter too. How far a chapter is set off is governed throughout by `break_before:` (`page`, `divider`, `none`); the values are described in Appendix A.

## Overarching sections (parts / blocks)

For main sections or appendix blocks spanning several chapters, use the `part:` keyword:

```yaml
chapters:
  - part: "Appendices"
    summary: "Supplementary tables and references."
    break_before: "divider"    # Large divider page for the whole appendix
    autonum: "none"            # No leading number
    document_toc: 1            # Appendices enter the TOC by title only
    chapters:
      - file: "chapters/appendix_a.md"
        title: "Appendix A: Reference"
      - file: "chapters/appendix_b.md"
        title: "Appendix B: Glossary"
```

A part carries no text of its own: it groups the chapters below it and gets a divider page. The part title (*"Appendices"* here) is carried into the running header of those pages.
