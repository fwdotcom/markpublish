<style>
/* Eine Referenzkarte ist absichtlich dichter gesetzt als Fliesstext: nur so
   bleiben beide Seiten vollstaendig. Der Block gilt nur fuer dieses Dokument -
   auf eigene Builds hat er keine Wirkung. Farben, Schrift und Rahmen kommen
   weiterhin aus dem Theme, hier wird ausschliesslich die Dichte geregelt.

   Beide Uebersetzungen tragen denselben Block, bemessen an der laengeren:
   deutscher Satz braucht fuer dieselbe Aussage rund ein Sechstel mehr Platz.
   Wer hier lockerer setzt, verliert die zweite Seite - in einer Sprache.

   8pt in den Tabellen ist die Untergrenze. Waechst das Schema weiter, ist
   nicht die Schrift das Stellrad, sondern der Inhalt: die vollstaendige
   Referenz steht in Anhang A des Handbuchs, hier nur, was man staendig
   nachschlaegt. */
.chapter-body table { margin: 0.4em 0; font-size: 8pt; }
.chapter-body th, .chapter-body td { padding: 0.7mm 2.0mm; }
.chapter-body h1 { margin-top: 0; margin-bottom: 0.3em; }
.chapter-body h2 { margin-top: 0.75em; margin-bottom: 0.15em; }
.chapter-body p { margin: 0.35em 0; }
.chapter-body pre { margin: 0.4em 0; }
</style>

# markpublish.yaml

Top level: `document`, `theme`, `parts`, optionally `templates_dir`. Paths are
relative to this file. Build with `markpublish build [file] -t pdf|html|all`.

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
| `part_toc` / `chapter_toc` | `full` | Divider-page TOCs, same three forms |
| `autonum_style` | `decimal` | `decimal`, `roman`, `legal`, `none` |
| `autonum_from_level` | `1` | Heading level numbering starts at |
| `autonum_reset` / `pagenum_reset` | `false` | Restart the counter or the page number |

Also `summary` (cover), `status`, `copyright` (footer). Unknown keys are handed
to the theme as `{{ document.your_key }}`.

## parts and chapters

Exactly two levels: `parts:` divides, `chapters:` carries the content. Chapters
do **not** nest further — depth comes from the headings in the file.

| Key | Applies to | Notes |
| :--- | :--- | :--- |
| `title` / `part` | part | Name of the part, required |
| `chapters` | part | Flat list of chapters, at least one |
| `file` | chapter | Path to a Markdown file |
| `title` / `subtitle` / `summary` | both | Override what the file says |
| `break_before` | both | `page`, `divider` (separator page) or `none` |
| `document_toc` | both | Share of the TOC at the front |
| `part_toc` / `chapter_toc` | part / chapter | TOC on the divider page |
| `autonum_*`, `pagenum_reset` | both | As under `document`, but local |

`document_toc: 1` lists a chapter but none of its sub-headings; set it on a
part to flatten every appendix at once. `autonum_*` and `document_toc` are
inherited from `document` through the part to the chapter — the deeper wins.
