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
| `version` | String | `null` | Version identifier |
| `language` | String | system language | ISO language code (`de`, `en`, …) |
| `cover` | Bool | `true` | Enable the cover page |
| `document_toc` | String/Int | `full` | Default for the document TOC |
| `part_toc` | String/Int | `full` | Default for part divider TOCs |
| `chapter_toc` | String/Int | `full` | Default for chapter divider TOCs |
| `autonum_style` | String | `"decimal"` | Default numbering style (`decimal`, `roman`, `legal`, `none`) |
| `autonum_from_level` | Int | `1` | Default start heading level for numbering |
| `autonum_prefix` | String | `null` | Default prefix for numbers |
| `autonum_reset` | Bool | `false` | Default reset flag |
| `pagenum_reset` | Bool | `false` | Reset page number counter |
| `header` | Bool | `true` | Enable running header |
| `footer` | Bool | `true` | Enable running footer |

## Part properties (`parts`)

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `title` / `part` | String | *required* | Part title (e.g. `"Appendices"`, `"Main"`) |
| `subtitle` | String | `null` | Subtitle for the part divider page |
| `summary` | String | `null` | Abstract for the part divider page |
| `break_before` | String | `"divider"` | `"divider"`, `"page"` or `"none"` |
| `document_toc` | String/Int | `full` | Part contribution to the document TOC |
| `part_toc` | String/Int | `full` | Local TOC on the part divider page |
| `chapter_toc` | String/Int | `full` | Default chapter TOC for chapters in this part |
| `autonum_style` | String | `"decimal"` | Numbering style for this part |
| `autonum_from_level` | Int | `1` | Start heading level for numbering |
| `autonum_prefix` | String | `null` | Optional prefix for generated numbers (e.g. `"A."`) |
| `autonum_reset` | Bool | `false` | Reset counter at part/chapter start |
| `pagenum_reset` | Bool | `false` | Reset page numbering back to 1 at part start |
| `chapters` | List | `[]` | Flat list of chapters in this part |

## Chapter properties (`chapters`)

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `file` | String | `null` | Path to the Markdown file |
| `title` | String | `null` | Overrides the title taken from the file |
| `subtitle` | String | `null` | Subtitle for the chapter divider page |
| `summary` | String | `null` | Abstract for the divider page |
| `break_before` | String | `page` | How the chapter is set off: `page`, `divider` or `none` |
| `document_toc` | String/Int | `full` | Chapter contribution to the front TOC |
| `chapter_toc` | String/Int | `full` | Local TOC on the chapter divider page |
| `autonum_style` | String | `"decimal"` | Numbering style for this chapter |
| `autonum_from_level` | Int | `1` | Start heading level for numbering |
| `autonum_prefix` | String | `null` | Optional prefix for generated numbers (e.g. `"A."` ➔ `A.1`, `A.2`) |
| `autonum_reset` | Bool | `false` | Reset counter at chapter start |
| `pagenum_reset` | Bool | `false` | Reset page numbering back to 1 at chapter start |

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

`document.autonum_style` sets the style for the whole document; `autonum_style` on a chapter or part departs from it and **passes the value down**. Without that inheritance the setting on a part would do nothing: the headings live in the chapter files, not in the part.

`autonum_style: "none"` means **nothing** in that branch carries a number — neither the chapter heading nor the levels below it. There is therefore no restart at 1 either: no count is running inside the branch that could begin again.

The document counter is left untouched. An unnumbered stretch consumes no number:

```yaml
parts:
  - chapters:
      - file: "chapters/01.md"          # 1
  - part: "Appendices"
    autonum_style: "none"           # appendices: no numbers
    chapters:
      - file: "chapters/a.md"
      - file: "chapters/b.md"
  - chapters:
      - file: "chapters/02.md"          # 2, not 4
```

### Numbering from Sub-Headings (`autonum_from_level` & `autonum_prefix`)

For extensive appendices or specialized sections whose main chapter title should remain unnumbered (e.g. *“Appendix A: Reference”*), but whose sub-sections need hierarchical numbering:

- `autonum_from_level: 2` leaves the `h1` chapter heading unnumbered and starts numbering at `h2` (`1`, `2`, ...) and `h3` (`1.1`, `1.2`).
- When `autonum_from_level > 1`, each chapter automatically resets its counter to start afresh.
- `autonum_prefix: "A."` prepends a custom prefix to generated numbers (`A.1`, `A.2`, `A.2.1`).

```yaml
parts:
  - part: "Appendices"
    autonum_from_level: 2           # inherits autonum_style from document
    chapters:
      - file: "chapters/appendix_a.md"
        title: "Appendix A: Reference"
        autonum_prefix: "A."        # A.1, A.2, A.2.1

      - file: "chapters/appendix_b.md"
        title: "Appendix B: FAQ"
        autonum_prefix: "B."        # B.1, B.2, B.2.1
```
