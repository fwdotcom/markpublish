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
| `language` | String | system language | ISO language code (`de`, `en`, …). Governs template labels, callout titles and date format |
| `cover` | Bool | `true` | Enable the cover page |
| `document_toc` | String/Int | `full` | The large TOC: `none`, `full` or a depth. Default for the chapters |
| `autonum_type` | String | `"decimal"` | `"decimal"`, `"roman"`, `"legal"`, `"none"`. Root for `chapters.autonum` |
| `chapter_toc` | String/Int | `none` | The small TOCs: `none`, `full` or a depth. Default for the chapters |
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
| `chapter_toc` | String/Int | `none` | The small TOC on this chapter's divider page. PDF only as well |
| `document_toc` | String/Int | `full` | This chapter's contribution to the large TOC at the front. Inherited downwards |
| `autonum` | String | `null` | Numbering style for this branch. Inherited downwards |
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

### `chapter_toc` and `document_toc` — two tables of contents, one vocabulary

A document has two tables of contents, and each has a pair of keys — one for the default, one for the individual case:

| Table of contents | Default under `document:` | On a chapter |
| :--- | :--- | :--- |
| The **large** one at the front | `document_toc` | `document_toc` |
| The **small** one on a divider page | `chapter_toc` | `chapter_toc` |

All four take the same three forms:

| Value | Meaning |
| :--- | :--- |
| `none` | Does not appear in this table of contents at all |
| `full` | Every level |
| *number* | Down to this depth, counted from the chapter heading |

Depth counts **within the chapter**: 1 is the chapter heading itself, 2 the level below it. `document_toc: 1` therefore puts the chapter into the large TOC but none of its sub-headings. `chapter_toc: 2` lists exactly the level below the chapter heading on the divider page.

For the common case, two lines in the `document` block are enough:

```yaml
document:
  document_toc: 2       # large TOC, two levels deep
  chapter_toc: 2        # small ones likewise
```

`document_toc: "none"` leaves the large table out entirely; the per-chapter settings are then moot.

### Inheritance

`document_toc` is inherited downwards: set on a part, it applies to every chapter below it, and a chapter passes it on to its sub-chapters. For the most common case — an appendix whose internal structure only bloats the table of contents — one line is enough:

```yaml
  - part: "Appendices"
    document_toc: 1
    chapters:
      - file: "chapters/07_appendix_yaml_spec.md"
        title: "Appendix A: YAML Schema Reference"
      - file: "chapters/08_appendix_troubleshooting.md"
        title: "Appendix B: Troubleshooting"
```

An individual chapter beats what it inherited — including back to `full`. That is exactly why the keyword exists: without it you would have to write an arbitrarily large number to say "everything after all".

`chapter_toc` is **not** passed from chapter to sub-chapter. It describes the divider page of this one chapter, and every chapter has its own; without a value of its own, `document.chapter_toc` simply applies.

### What is shortened, and what is not

The prose is untouched: the sub-headings remain in the chapter, numbering and anchors included. Only the table of contents is shortened. A sub-chapter keeps its own entry — the depth is inherited relative to each chapter, not applied across the combined list.

An unknown value aborts the build. Booleans are rejected too: a `true` would not show the depth — that is exactly what `full` is for.

## Numbering

`document.autonum_type` sets the style for the whole document; `autonum` on a chapter or part departs from it and **passes the value down**. Without that inheritance the setting on a part would do nothing: the headings live in the chapter files, not in the part.

`autonum: "none"` means **nothing** in that branch carries a number — neither the chapter heading nor the levels below it. There is therefore no restart at 1 either: no count is running inside the branch that could begin again.

The document counter is left untouched. An unnumbered stretch consumes no number:

```yaml
chapters:
  - file: "chapters/01.md"          # 1
  - part: "Appendices"
    autonum: "none"                 # appendices: no numbers
    chapters:
      - file: "chapters/a.md"
      - file: "chapters/b.md"
  - file: "chapters/02.md"          # 2, not 4
```
