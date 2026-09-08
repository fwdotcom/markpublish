# Project Configuration with markpublish.yaml

The central control file for every markpublish project is `markpublish.yaml`. It configures the document declaratively: metadata, layout specifications, structural hierarchy, and the mapping of Markdown files to chapters and parts.

## The Three Structural Tiers

markpublish organizes documents across three clearly defined levels:

```text
document
└── parts (Sections)
    └── chapters (Chapters)
```

The configuration goes no deeper than this. Within a chapter, the Markdown file
itself carries the structure, using `##`, `###` and so on.

### Document (Document Level)

The top-level `document:` key describes the document as a whole:

Metadata
: Title, subtitle, authors, version, date, language, status, and copyright notices.

Layout Toggles
: Cover page display (`cover`), header activation (`header`), and footer activation (`footer`).

Global Table of Contents Settings
: Depth controls for the global table of contents (`document_toc`), part-level tables of contents (`part_toc`), and local chapter tables of contents (`chapter_toc`).

> [!IMPORTANT] No Booleans in TOC Switches
> The switches `document_toc`, `part_toc`, and `chapter_toc` do **not** accept Booleans (`true` or `false`). Use `"full"` (full depth), `"none"` (no TOC), or a positive integer starting at `1` for the maximum heading depth (e.g., `2`). Writing `document_toc: false` aborts validation with a clear error message.

Numbering Rules
: Settings for automatic numbering (`autonum_pattern`, `autonum_reset`).

#### Custom Metadata Fields

Under `document:`, **arbitrary custom fields** are permitted beyond the standard keys. They are forwarded to the theme, but are not printed automatically:

```yaml
document:
  title: "Project Report"
  department: "Controlling"
  client: "Acme Corporation"
  reviewed: true
```

The metadata block on the cover page only displays fields that the active theme specifically arranges – in the built-in standard theme, these are version, date, author, copyright, and status. A custom field is only displayed when a theme explicitly requests it (see chapter *Theme System and Internationalization*).

> [!NOTE] Why not automatically?
> If every arbitrary field landed unprompted on the cover page, so would every typo: `departmnet: "Controlling"` would create an unwanted line on the title page. Controlling the title page layout remains the theme's responsibility.

Three essential things to keep in mind:

* **Unused fields are reported by `markpublish labels`.** Any field not referenced by a theme appears with the status *unused* and is listed in the summary at the bottom – this is exactly where mistyped keys stand out. Checking `labels` before your first build saves time.

* **Labels come from the i18n cascade.** When a theme prints the field, it needs a label string; if none is found, the cover page prints the key itself – e.g. `department` instead of `Department`. To define labels, create an `i18n.yaml` file next to your `markpublish.yaml`:

  ```yaml
  # i18n.yaml in the project root
  en:
    department: "Department"
    client: "Client"
    reviewed: "Reviewed"
  ```

  This file is the final stage of the cascade and overrides both application and theme defaults (see chapter *Theme System and Internationalization*).

* **Types are preserved.** A `true` is a boolean value, not raw text: the cover page typesets `Yes` or `No` (or `Ja` / `Nein`) depending on the document language. These strings are looked up as `bool_true` and `bool_false` in the i18n cascade.

### Parts (Sections)

A document is organized into high-level sections via `parts:` (e.g., "Main Part", "Case Studies", "Appendices"):

* A document must always be structured using `parts:`; a flat `chapters:` list at the top level is rejected.

* A part groups logically related chapters together.

* By default, a part produces no separate page (`break_before: "none"`): it groups its chapters and passes down its settings, but occupies no page and does not appear in the table of contents. With `break_before: "divider"`, it receives a styled divider page; with `break_before: "page"`, it receives a heading on a fresh page.

* Settings defined at the part level (such as TOC depth or an `autonum_pattern`) are automatically inherited by all chapters contained within.

* Under `parts:`, only declared configuration keys are allowed. Unknown keys (such as `break_befor`) are rejected with fuzzy suggestions to prevent unnoticed misconfigurations.

### Chapters (Chapters)

The `chapters:` list within a part references the actual Markdown content files:

* Each chapter points to its Markdown file (`file:`). Authors can write their Markdown files naturally starting with a `#` heading.

* **`show_title:`** (`true` or `false`, default: `true`) controls whether the file's `#` heading should be rendered on the content page. If a divider page precedes the chapter (`break_before: "divider"`), setting `show_title: false` prevents the title from repeating on the next page – the content page then starts directly with the introductory text or the first subheading.

* Optional keys **`toc_title:`** (for tables of contents and headers) and **`divider_title:`** (for divider pages) allow defining distinct alternative titles (e.g., a concise short form in the table of contents versus an extensive title on the chapter page). When omitted, both inherit the file's `#` heading.

* When generating a divider page (`break_before: "divider"`) or listing the chapter in the table of contents, at least one `#` heading or the corresponding title key (`divider_title` / `toc_title`) must exist; otherwise, the build aborts with an informative error message.

* Chapters can control via `break_before` whether a divider page is generated, a simple page break occurs, or content flows seamlessly.

---

## Example of a Complete Configuration

The following example demonstrates a realistic, complete `markpublish.yaml`:

```yaml
# markpublish.yaml

document:
  title: "Annual Project Report"
  subtitle: "Analysis, Results, and Outlook"
  summary: "Comprehensive report covering the project phases of the past fiscal year."
  author: "Controlling Working Group"
  date: "auto"
  version: "1.2.0"
  language: "en"
  copyright: "© 2026 Acme Corporation"

  # Layout elements
  cover: true
  header: true
  footer: true

  # TOC depths
  document_toc: 2
  part_toc: 2
  chapter_toc: "none"

  # Numbering: slot 1 is the part, slot 2 the chapter, slot 3 the H2
  autonum_pattern: "_|1|.1|+"

theme: "default"

parts:
  - part: "Main Part"
    break_before: "none"
    chapters:
      - file: "chapters/01_introduction.md"
        break_before: "page"

      - file: "chapters/02_analysis.md"
        # Concise title for TOC when file H1 is long:
        toc_title: "Market Analysis"
        break_before: "page"

      - file: "chapters/03_results.md"
        break_before: "divider"

  - part: "Appendices"
    break_before: "divider"
    # On a part, slot 1 is the chapter: '_' leaves it unnumbered and the
    # H2 below start at 1 - afresh in every chapter.
    autonum_pattern: "_|1|.1|+"
    autonum_reset: true
    chapters:
      - file: "chapters/appendix_tables.md"

      - file: "chapters/appendix_glossary.md"
```

A complete reference of all available keys, data types, default values, and valid combinations for each of the three tiers can be found in **Appendix A: markpublish.yaml Schema Specification** at the end of this manual.

