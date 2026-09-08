# markpublish.yaml Schema Specification

This appendix provides the complete specification of all configuration options supported in `markpublish.yaml`.

---

## Document Level (document)

The `document:` section defines global metadata, layout switches, table of contents depths, and numbering styles for the entire document.

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `title` | String | *(Required)* | Document title (appears on cover page, header, and metadata). |
| `subtitle` | String | `None` | Document subtitle. |
| `summary` | String | `None` | Executive summary or abstract (printed on cover page). |
| `author` | String | `None` | Author or organization name. |
| `status` | String | `None` | Document lifecycle status (e.g., "Draft", "Approved", "Confidential"). |
| `copyright` | String | `None` | Copyright notice (e.g., "© 2026 Frank Winter"). |
| `date` | String | `"auto"` | Document date. Set to `"auto"` or `"today"` to use current date. |
| `version` | String | `None` | Version identifier (e.g., `"2.0.0"`). Only printed when explicitly set. |
| `language` | String | *(System language)* | ISO language code (e.g., `"en"` or `"de"`). Governs hyphenation and UI strings. |
| `cover` | Boolean | `false` | Controls whether a styled cover page is generated. |
| `header` | Boolean | `true` | Enables or disables running headers throughout the document. |
| `footer` | Boolean | `true` | Enables or disables running footers (including page numbering). |
| `document_toc` | Scope | `"full"` | Depth for the main table of contents (`"none"`, `"full"`, or integer $\ge 1$). |
| `part_toc` | Scope | `"full"` | Default depth for local tables of contents on part divider pages. |
| `chapter_toc` | Scope | `"full"` | Default depth for local tables of contents on chapter divider pages. |
| `autonum_pattern` | String | *see below* | How numbers are built; slot 1 is the part, slot 2 the chapter. `none` switches numbering off. |
| `autonum_reset` | Boolean | `false` | Makes the levels below start again at one when this block is entered. |
| `part_label` | String | from i18n | Word naming a part (e.g. `"Part"`). |
| `chapter_label` | String | from i18n | Word naming a chapter (e.g. `"Chapter"`). |
| `pagenum_reset` | Boolean | `false` | Restarts page numbering at page 1 for each part or chapter. |

> [!NOTE] Custom Metadata Fields under `document:`
> Beyond standard fields, arbitrary custom metadata fields can be added under `document:` (e.g., `department: "R&D"`, `reviewed: true`). They are delivered typed into the theme (`meta: (:)`).
>
> Static text translations (`document.i18n` or `document.labels`) are not permitted here and cause validation to fail – localization belongs exclusively in `i18n.yaml` files within the cascade.

---

## Global Project Settings

Directly at the top level of `markpublish.yaml` (alongside `document:` and `parts:`), the following settings can be configured:

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `theme` | String | `"default"` | Name of the active theme. |
| `templates_dir` | String | `None` | Optional custom directory path containing theme templates. |

### Numbering Patterns

`autonum_pattern` describes how numbers are built, as a chain of slots separated by `|`. Slot 1 belongs to the first level *below* the place the pattern stands: under `document:` that is the part, on a part the chapter, on a chapter the H2. A pattern therefore never describes the level it is written at.

| Symbol | Result |
| :--- | :--- |
| `1` | 1, 2, 3 … |
| `01`, `001` | 01, 02 … or 001, 002 … (fixed width) |
| `a` / `A` | a, b, c … / A, B, C … |
| `i` / `I` | i, ii, iii … / I, II, III … |
| `_` | level stays unnumbered |
| `+` | repeats the slot before it for every deeper level |

Everything else in a slot is a literal and needs no quoting; only a reserved character meant literally goes into single quotes (`'Article '1`). A malformed pattern aborts the build.

```text
  "_|1|.1|+"        part unnumbered, chapter 1, section 1.1   (default)
  "I|1|.1|+"        part I, II … chapters count straight through
  "'Appendix 'A|.1" Appendix A, Appendix A.1
```

A notated `label` puts the word in front of the number of the heading and its table-of-contents entry: `A` becomes `Appendix A: `. The subheadings are untouched and keep counting `A.1`, `A.2` — which is why the word belongs in this key and not in the pattern. The separator comes from the i18n cascade (`label_separator`).

The part number does not enter the chapter numbers: it appears on the divider page and in the table of contents, not in front of every chapter. A part with `document_toc: "none"` gets no number and consumes none.

---

## Section Level (parts)

The `parts:` list subdivides the document into high-level sections. A part groups chapters together and passes down its settings.

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `part` | String | *(Required)* | Section name (e.g., "Main Part", "Appendices"). |
| `toc_title` | String | `None` | Optional title override for TOC and headers (default: `part`). |
| `divider_title` | String | `None` | Optional title override on the section divider page (default: `part`). |
| `subtitle` | String | `None` | Section subtitle (appears on divider page). |
| `summary` | String | `None` | Section summary (appears on divider page). |
| `break_before` | String | `"none"` | Break behavior: `"divider"` (divider page), `"page"` (heading on new page), or `"none"` (structural grouping only, no dedicated page). |
| `document_toc` | Scope | `None` | Overrides this section's contribution to the main TOC. |
| `part_toc` | Scope | `None` | Controls the local table of contents on the section divider page. |
| `chapter_toc` | Scope | `None` | Propagates chapter TOC settings down to all chapters in this part. |
| `autonum_pattern` | String | `None` | Numbers for this part; slot 1 is the chapter here. |
| `autonum_reset` | Boolean | `None` | Makes the chapters of this part start again at one. |
| `label` | String | from i18n | Word naming this part. |
| `chapter_label` | String | inherited | Word for every chapter of this part (e.g. `"Appendix"`). |
| `pagenum_reset` | Boolean | `None` | Resets page numbering to 1 at the start of this section. |
| `chapters` | List | *(Required)* | List of content chapters in this part (at least 1 entry). |

---

## Chapter Level (chapters)

The `chapters:` list specifies the content files. Chapters always sit directly under an entry of `parts:`.

The chapter heading on the content page is determined by default by the file's leading `#` heading (suppressible via `show_title: false`). For tables of contents and divider pages, two explicit title overrides are available:

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `file` | String | `None` | Relative path to the Markdown file (e.g., `"chapters/01_intro.md"`). |
| `show_title` | Boolean | `true` | Controls whether the file's `#` heading is printed on the content page. |
| `toc_title` | String | `None` | Title for tables of contents and headers. Default: file H1. |
| `divider_title` | String | `None` | Title on chapter divider pages (`break_before: "divider"`). Default: file H1. |
| `subtitle` | String | `None` | Chapter subtitle (appears on divider pages). |
| `summary` | String | `None` | Short summary (used on divider pages). |
| `break_before` | String | `"page"` | Page break behavior: `"page"` (new page), `"divider"` (divider page), or `"none"`. |
| `document_toc` | Scope | `None` | Contribution of this chapter to the main TOC (`"none"`, `"full"`, integer). |
| `chapter_toc` | Scope | `None` | Local table of contents on this chapter's divider page. |
| `autonum_pattern` | String | `None` | Numbers inside this chapter; slot 1 is the H2 here. The chapter's own number comes from its part. |
| `autonum_reset` | Boolean | `None` | Makes the headings of this chapter start again at one. |
| `label` | String | inherited | Word naming this chapter (e.g. `"Excursus"`). |
| `pagenum_reset` | Boolean | `None` | Resets page numbering to 1 at the start of this chapter. |

> [!IMPORTANT]
> Under `parts:` and `chapters:`, **only** the keys listed above are allowed. Any unrecognized key halts compilation and provides fuzzy spelling suggestions – catching mistakes like `break_befor` before chapters are rendered with incorrect breaks. Custom metadata fields belong exclusively under `document:`.

---

## Table of Contents Scope Controls

The table of contents settings `document_toc`, `part_toc`, and `chapter_toc` accept the following values:

| Value | Description |
| :--- | :--- |
| `"none"` | Disables the table of contents completely or excludes the item. |
| `"full"` | Includes all heading levels without depth limitation. |
| Positive Integer (e.g., `1`, `2`, `3`) | Limits TOC depth strictly to the specified number of heading levels. |

> [!WARNING] No Booleans Allowed
> Boolean values (`true` or `false`) are invalid for TOC scope switches and trigger a `ConfigurationError`. To disable a table of contents, always specify `"none"`.

