# markpublish

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Modern PDF Document Publishing from Markdown

markpublish typesets structured Markdown chapters into print-ready PDFs.
Structure, metadata and design live in a single `markpublish.yaml` —
everything else is your text.

- **One manifest instead of a command line full of options**: title, cover,
  tables of contents, headers and footers, order of chapters.
- **Parts and chapters with divider pages**: with subtitle, summary and a
  local table of contents of their own — configurable per level.
- **Themes in Typst**: `markpublish export-template default ./templates` puts
  the default theme into your project and the next build picks up your
  version. The font ships with the theme, so output does not depend on the
  machine.
- **Markdown that does more**: GitHub-style alerts, footnotes, task lists,
  definition lists, math, syntax highlighting.
- **Bilingual both ways**: the document language drives labels and
  hyphenation, the interface language follows your system (`--ui-lang`).
- **Self-documenting**: `markpublish cheatsheet` and `markpublish manual`
  render the reference and the manual from the installed package — always
  matching the version you are running.

## Manual

| | Deutsch | English |
| :--- | :--- | :--- |
| Handbuch · Manual | [Benutzerhandbuch (PDF)](https://github.com/fwdotcom/markpublish/blob/main/manual/markpublish_benutzerhandbuch.pdf) | [User Manual (PDF)](https://github.com/fwdotcom/markpublish/blob/main/manual/markpublish_user_manual.pdf) |
| Kurzreferenz · Quick reference | [Kurzreferenz (PDF)](https://github.com/fwdotcom/markpublish/blob/main/manual/markpublish_kurzreferenz.pdf) | [Quick Reference (PDF)](https://github.com/fwdotcom/markpublish/blob/main/manual/markpublish_quick_reference.pdf) |

All four are typeset with markpublish itself.

## Installation

```bash
pip install markpublish

# create a project
markpublish init my-project

# build the PDF
markpublish build my-project/markpublish.yaml      
```

(requires Python 3.10 or newer)

## Lizenz · License

MIT © 2026 Frank Winter —
[LICENSE](https://github.com/fwdotcom/markpublish/blob/main/LICENSE)
