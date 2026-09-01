<style>
/* Eine Referenzkarte ist absichtlich dichter gesetzt als Fliesstext: nur so
   bleiben beide Seiten vollstaendig. Der Block gilt nur fuer dieses Dokument -
   auf eigene Builds hat er keine Wirkung. Farben, Schrift und Rahmen kommen
   weiterhin aus dem Theme, hier wird ausschliesslich die Dichte geregelt. */
.chapter-body table { margin: 0.5em 0; font-size: 8.5pt; }
.chapter-body th, .chapter-body td { padding: 1.1mm 2.5mm; }
.chapter-body h1 { margin-top: 0; margin-bottom: 0.3em; }
.chapter-body h2 { margin-top: 0.9em; margin-bottom: 0.2em; }
.chapter-body p { margin: 0.45em 0; }
.chapter-body pre { margin: 0.5em 0; }
</style>

# markpublish.yaml

Three top-level keys: `document`, `theme`, `chapters`. All paths are relative
to this file. Build with `markpublish build [file] --target pdf|html|all`.

## document

Metadata and the global layout switches. Only `title` is required.

| Key | Default | Notes |
| :--- | :--- | :--- |
| `title` / `subtitle` | *title required* | Cover, running header, output filename |
| `author` | – | Cover |
| `date` / `version` | `auto` / – | `auto` or `today` for the build date |
| `language` | `de` | Picks the label set; falls back to `en` |
| `cover` / `toc` | `true` | Cover page and global table of contents |
| `autonum_type` | `decimal` | `decimal`, `roman`, `legal`, `none` |
| `header` / `footer` | `true` | Running header and footer |

Also available: `summary` (abstract on the cover), `status`, `copyright`
(footer). Unknown keys are handed to the theme as `{{ document.your_key }}`.

## chapters

Chapters, sub-chapters and parts. Nesting is recursive.

| Key | Default | Notes |
| :--- | :--- | :--- |
| `file` | – | Path to a Markdown file |
| `title` | – | Overrides the heading for TOC and header |
| `part` | – | Makes the item a part header, not a chapter |
| `break_before` | `page` | `page`, `divider` (own separator page) or `none` |
| `toc` | `false` | Local TOC: `true`, a depth as integer, or a map |
| `toc_depth` | – | How deep this branch enters the global TOC |
| `chapters` | `[]` | Nested children |

Depth counts from the chapter's own heading, so `toc_depth: 1` puts the chapter
into the global table of contents but none of its sub-headings -- set it on a
part to flatten every appendix at once; sub-chapters inherit it. Also available:
`summary` and `autonum`.
