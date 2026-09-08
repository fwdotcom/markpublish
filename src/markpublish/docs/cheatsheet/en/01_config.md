# markpublish.yaml

Top level: `document`, `theme`, `parts`, optionally `templates_dir`. All paths are relative to the directory of this file. Build with `markpublish build [CONFIG_FILE] [OPTIONS]`.

## Structure

There are exactly two structural tiers. Anything deeper is carried by the Markdown file itself.

```text
markpublish.yaml
├── document:            metadata and global switches
├── theme:               name of the theme
└── parts:               list of sections
     ├── part:           name of the section
     └── chapters:       list of chapters
          └── file:      one Markdown file
               ├── # H1  chapter heading
               ├── ## H2   structure
               └── ### H3  inside the file
```

## document

Metadata and global layout toggles. Only `title` is required.

| Key | Default | Meaning |
| :--- | :--- | :--- |
| `title` | *required* | Document title (cover page, header, filename) |
| `subtitle` | – | Subtitle on the cover page |
| `summary` | – | Summary / abstract on the cover page |
| `author` | – | Author name |
| `date` | `auto` | Date (`auto` or `today` for the build date) |
| `version` | – | Version on the cover page and in the footer |
| `status` | – | Document status (e.g. `Draft`, `Approved`) |
| `copyright` | – | Copyright notice on the cover page |
| `language` | system language | ISO code for static labels (`de`, `en`) |
| `cover` | `false` | Generate a cover page |
| `header` / `footer` | `true` | Running headers and footers |
| `document_toc` | `full` | Main table of contents: `none`, `full` or a depth |
| `part_toc` | `full` | Default for part divider pages: `none`, `full` or a depth |
| `chapter_toc` | `full` | Default for chapter divider pages: `none`, `full` or a depth |
| `autonum_pattern` | *see Numbering* | How numbers are built; slot 1 is the part here |
| `autonum_reset` | `false` | Levels below start again at one when entered |
| `part_label` | from i18n | Word before a part number (`Part`); `""` drops it |
| `chapter_label` | from i18n | Word before a chapter number (`Chapter`); `""` drops it |
| `pagenum_reset` | `false` | Restart page numbering per part or chapter |

Custom fields under `document:` (`department: "R&D"`) reach the theme through the `meta` dictionary (`meta.at("department").value`). Static labels belong in `i18n.yaml`, not here.

## parts

A part brackets chapters and passes settings down to them. Without `break_before` it does not show itself.

| Key | Default | Meaning |
| :--- | :--- | :--- |
| `part` | *required* | Name of the section |
| `chapters` | *required* | List of chapters in this section |
| `toc_title` | `part` | Title in the main table of contents |
| `divider_title` | `part` | Title on the divider page |
| `subtitle` / `summary` | – | Subtitle and summary on the divider page |
| `break_before` | `none` | `divider`, `page` or `none` |
| `document_toc` | inherited | Contribution to the main TOC; `none` hides the part |
| `part_toc` | inherited | Local TOC on its own divider page |
| `chapter_toc` | inherited | Default for the divider pages of its chapters |
| `autonum_pattern` | inherited | Numbers of its chapters; slot 1 is the chapter here |
| `autonum_reset` | inherited | Chapters of this part start again at one |
| `label` | from i18n | Word before its own number |
| `chapter_label` | inherited | Word before the number of each of its chapters (`Appendix`) |
| `pagenum_reset` | inherited | Restart page numbering at the start of the part |

## chapters

A chapter is one Markdown file. Its name comes from that file's `#` heading.

| Key | Default | Meaning |
| :--- | :--- | :--- |
| `file` | *required* | Path to the Markdown file |
| `show_title` | `true` | Show the file's H1 on the content page |
| `toc_title` | file H1 | Title in the table of contents and running header |
| `divider_title` | file H1 | Title on the divider page |
| `subtitle` / `summary` | – | Subtitle and summary on the divider page |
| `break_before` | `page` | `divider`, `page` or `none` |
| `document_toc` | inherited | Contribution to the main TOC (`none`, `full`, depth) |
| `chapter_toc` | inherited | Local TOC on its own divider page |
| `autonum_pattern` | inherited | Numbers *inside* the chapter; slot 1 is the H2 here |
| `autonum_reset` | inherited | Headings of this chapter start again at one |
| `label` | inherited | Word before its own number (`Appendix A: …`) |
| `pagenum_reset` | inherited | Restart page numbering at the start of the chapter |

## Inheritance

Everything marked *inherited* flows from the outside in; the innermost setting wins.

```text
document ─────────────► parts[] ─────────────► chapters[]
  autonum_pattern         autonum_pattern        autonum_pattern
  autonum_reset           autonum_reset          autonum_reset
  document_toc            document_toc           document_toc
  part_toc                part_toc                    –
  chapter_toc             chapter_toc            chapter_toc
  pagenum_reset           pagenum_reset          pagenum_reset
  part_label              label                       –
  chapter_label           chapter_label          label
```

## Numbering

A pattern describes the levels *below* the place it stands — so slot 1 shifts with that place.

```text
  Level            under document      on a part         on a chapter
  ─────────────────────────────────────────────────────────────────────────
  Part               slot 1                  –                  –
  Chapter (H1)       slot 2               slot 1                –
  H2                 slot 3               slot 2             slot 1
  H3                 slot 4               slot 3             slot 2
   ⋮                    ⋮                    ⋮                  ⋮
  H6                 slot 7               slot 6             slot 5
```

**Symbols:** `1` → 1, 2, 3 · `01` → 01, 02 · `a` / `A` → a, b / A, B · `i` / `I` → i, ii / I, II · `_` level without a number · `+` repeats the slot before it for every deeper level. Slots are separated by `|`; everything else in a slot is a literal, reserved characters go in single quotes (`'Article '1`).

```text
  on document   "_|1|.1|+"               part unnumbered · chapter 1 · 1.1
  on document   "I|1|.1|+"               Part I · chapters 1, 2, 3 through
  on a part     "A|.1|+"                 chapter A · A.1 · A.1.1
  on a part     "'Article '1|' ('1')'"   Article 1 · Article 1 (2)
```

Without a setting, `"_|1|.1|+"` applies: parts unnumbered, chapters 1, 1.1, 1.1.1.

The part number does **not** enter the chapter numbers; a part with `document_toc: "none"` gets none and consumes none. A notated `label` steps in front of the heading's number (`Appendix A: Schema`) without reaching the subheadings (`A.1`).
