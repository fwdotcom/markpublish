<style>
/* Eine Referenzkarte ist absichtlich dichter gesetzt als Fliesstext: nur so
   bleiben beide Seiten vollstaendig. Der Block gilt nur fuer dieses Dokument -
   auf eigene Builds hat er keine Wirkung. Farben, Schrift und Rahmen kommen
   weiterhin aus dem Theme, hier wird ausschliesslich die Dichte geregelt.

   Beide Uebersetzungen tragen denselben Block, bemessen an der laengeren:
   deutscher Satz braucht fuer dieselbe Aussage rund ein Sechstel mehr Platz.
   Wer hier lockerer setzt, verliert die zweite Seite - in einer Sprache. */
.chapter-body table { margin: 0.4em 0; font-size: 8.5pt; }
.chapter-body th, .chapter-body td { padding: 0.9mm 2.2mm; }
.chapter-body h1 { margin-top: 0; margin-bottom: 0.3em; }
.chapter-body h2 { margin-top: 0.75em; margin-bottom: 0.15em; }
.chapter-body p { margin: 0.35em 0; }
.chapter-body pre { margin: 0.4em 0; }
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
| `language` | system language | Picks the label set, else `en` |
| `cover` / `header` / `footer` | `true` | Cover page, running header and footer |
| `document_toc` | `full` | Large TOC: `none`, `full` or a depth |
| `chapter_toc` | `none` | Small divider-page TOCs: same three forms |
| `autonum_style` | `decimal` | `decimal`, `roman`, `legal`, `none` |

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
| `chapter_toc` | `none` | Small TOC on this chapter's divider page |
| `document_toc` | `full` | This chapter's share of the TOC at the front |
| `chapters` | `[]` | Nested children |

Both TOC keys take `none`, `full` or a depth, counted from the chapter's own
heading. `document_toc: 1` lists the chapter but none of its sub-headings; set
it on a part to flatten every appendix at once. `document_toc`, `autonum`, and `autonum_from_level` (e.g. `2` for numbering sub-headings with optional `autonum_prefix`) are inherited downwards, `chapter_toc` falls back to `document.chapter_toc`.
