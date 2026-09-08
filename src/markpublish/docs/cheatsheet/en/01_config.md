# markpublish.yaml

Top level of the configuration file: `document`, `theme`, `parts`, optional `templates_dir`. All paths are relative to the directory containing this file. Build using: `markpublish build [CONFIG_FILE] [OPTIONS]`.

## document

Metadata and global layout toggles. Only `title` is required.

| Key | Default | Description |
| :--- | :--- | :--- |
| `title` | *Required* | Document title (cover page, header, filename) |
| `subtitle` | – | Subtitle on the cover page |
| `summary` | – | Summary / abstract on the cover page |
| `author` | – | Author name (cover page) |
| `date` | `auto` | Date on the cover page (`auto` or `today` for build date) |
| `version` | – | Version number on the cover page and in the footer |
| `status` | – | Document status on the cover page (e.g. `Draft`, `Approved`) |
| `copyright` | – | Copyright notice on the cover page |
| `language` | System locale | ISO language code for static labels (`de`, `en`) |
| `cover` | `false` | Generate cover page (`true` or `false`) |
| `header` | `true` | Enable running headers (`true` or `false`) |
| `footer` | `true` | Enable footers (`true` or `false`) |
| `document_toc` | `full` | Main table of contents: `none`, `full`, or depth as integer |
| `part_toc` | `full` | Default for part divider pages: `none`, `full`, or depth |
| `chapter_toc` | `full` | Default for chapter divider pages: `none`, `full`, or depth |
| `autonum_style` | `decimal` | Heading numbering style: `decimal`, `roman`, `legal`, `none` |
| `autonum_from_level` | `1` | Starting heading level to number (1 = H1, 2 = H2, ...) |
| `autonum_prefix` | – | Prefix for heading numbers (e.g. `A.` for A.1) |
| `autonum_reset` | `false` | Reset heading numbering counter for each chapter |
| `pagenum_reset` | `false` | Reset page numbering for each part or chapter |

Custom metadata fields under `document:` (e.g. `department: "R&D"`, `project: "Alpha"`)
are forwarded to the theme via the `meta` dictionary (`meta.at("field").value`)
and rendered if supported by the theme. Static labels belong in
`i18n.yaml`, not in `document:`.

## parts and chapters

Exactly two hierarchy levels: `parts:` structures sections, `chapters:` holds the content. Page titles
are derived from the markdown file's H1; table of contents and divider titles can be
configured individually.

| Key | Level | Default | Description |
| :--- | :--- | :--- | :--- |
| `part` | Part | *Required* | Name of the section |
| `chapters` | Part | *Required* | List of chapters in this section |
| `file` | Chapter | *Required* | Path to markdown file (relative to config) |
| `show_title` | Chapter | `true` | Show file H1 on content page (`false` hides it) |
| `toc_title` | Part / Chapter | File H1 / `part` | Title for main table of contents and headers |
| `divider_title` | Part / Chapter | `part` / File H1 | Title on the divider page |
| `subtitle` | Part / Chapter | – | Subtitle on the divider page |
| `summary` | Part / Chapter | – | Short description on the divider page |
| `break_before` | Part / Chapter | `none` / `page` | Page break: `divider` (divider page), `page`, or `none` |
| `document_toc` | Part / Chapter | inherited | Contribution to main TOC (`none`, `full`, depth) |
| `part_toc` | Part | inherited | Local TOC on part divider page |
| `chapter_toc` | Part / Chapter | inherited | Local TOC on chapter divider page |
| `autonum_style` | Part / Chapter | inherited | Local numbering style (`decimal`, `roman`, `legal`, `none`) |
| `autonum_from_level` | Part / Chapter | inherited | Level at which numbering begins |
| `autonum_prefix` | Part / Chapter | inherited | Prefix for numbers in this section |
| `autonum_reset` | Part / Chapter | inherited | Reset numbering counter at start of section/chapter |
| `pagenum_reset` | Part / Chapter | inherited | Reset page numbering at start |

`document_toc: 1` lists a chapter without its subheadings; set at the part level,
it flattens all contained chapters at once. Options marked *inherited* inherit their
default value from `document` through the part to the chapter – the more specific
setting wins.

