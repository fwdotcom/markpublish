# Appendix A: YAML Schema Reference

A complete overview of every configuration option in `markpublish.yaml`.

## Document properties (`document`)

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `title` | String | *required* | Title of the publication |
| `subtitle` | String | `null` | Subtitle |
| `summary` | String | `null` | Abstract for the cover page |
| `author` | String | `null` | Author name |
| `status` | String | `null` | Document status (e.g. "Draft", "Released") |
| `copyright` | String | `null` | Copyright notice (e.g. "© 2026 Frank Winter") |
| `date` | String | `"auto"` | A date, or `"auto"` for today |
| `version` | String | `null` | Version identifier. Without it the field disappears from the cover page; when set, it appears in the footer to the left of the date |
| `language` | String | `"de"` | ISO language code (`de`, `en`, …). Governs template labels, callout titles and date format |
| `cover` | Bool | `true` | Enable the cover page |
| `toc` | Bool | `true` | Enable the global table of contents |
| `autonum_type` | String | `"decimal"` | `"decimal"`, `"roman"`, `"legal"`, `"none"` |
| `header` | Bool | `true` | Enable the running header (its layout lives in the theme) |
| `footer` | Bool | `true` | Enable the running footer (its layout lives in the theme) |

## Chapter and part properties (`chapters`)

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `file` | String | `null` | Path to the Markdown file |
| `title` | String | `null` | Overrides the title taken from the file |
| `summary` | String | `null` | Abstract for the divider page |
| `part` | String | `null` | Declares an overarching part |
| `break_before` | String | `page` | How the chapter is set off: `page`, `divider` or `none`. PDF only — the bundled HTML theme has neither pages nor divider pages |
| `toc` | Bool/Int | `false` | Local chapter TOC (e.g. `2` for maximum depth). It appears on the divider page, so PDF only as well |
| `toc_depth` | Int | `null` | Limits how deep this branch enters the global table of contents |
| `autonum` | String | `null` | Local override of the numbering style |
| `chapters` | List | `[]` | Nested sub-chapters |

### `break_before` — how a chapter is set off

One key with three values, not two independent switches:

| Value | Effect |
| :--- | :--- |
| `page` | Default. The chapter starts at the top of a new page |
| `divider` | A divider page of its own precedes the chapter |
| `none` | The chapter runs on in the text flow |

That it is *one* key has a reason: the three values are one axis, not three questions. As two booleans you could write down "divider page, but no page break" — a state that does not exist, because a divider page always breaks. A setting you can write down and that does nothing is a source of error with no upside.

`page` is what a typeset document is expected to do. If you want short sections to run on — leaflets, reference cards, tightly set appendices — put `break_before: "none"` on the individual chapter; the setting can also be overridden in the front matter of the Markdown file.

With `divider`, the chapter's own break and the divider page's break fall in the same place and merge into one — no blank sheet appears. Before the first chapter the rule does not apply.

An unknown value aborts the build instead of quietly falling back to `page`: a mistyped `divder` would otherwise become an ordinary page break without complaint, and you would find the missing divider page only when leafing through the finished PDF.

### `toc_depth` — keeping appendices flat in the table of contents

Depth counts within the chapter, exactly as it does for `toc`: depth 1 is the chapter heading itself, depth 2 the level below it. `toc_depth: 1` therefore puts the chapter into the global table of contents but none of its sub-headings.

The value is inherited downwards: set on a part, it applies to every chapter below it, and a chapter passes it on to its sub-chapters. For the most common case — an appendix whose internal structure only bloats the table of contents — one line is enough:

```yaml
  - part: "Appendices"
    toc_depth: 1
    chapters:
      - file: "chapters/07_appendix_yaml_spec.md"
        title: "Appendix A: YAML Schema Reference"
      - file: "chapters/08_appendix_troubleshooting.md"
        title: "Appendix B: Troubleshooting"
```

The prose is untouched: the sub-headings remain in the chapter, numbering and anchors included. Only the table of contents is shortened. A sub-chapter keeps its own entry — the depth is inherited relative to each chapter, not applied across the combined list.
