# The Template and Design System

The template system of `markpublish` allows complete visual customisation while staying maintainable.

## Theme-based directory structure

Templates are grouped by theme, with the output format underneath. Everything belonging to one design therefore stays together, and a theme can be copied, shared or versioned as a whole:

```
templates/
└── default/                       # Theme name
    ├── pdf/
    │   ├── layout.html            # HTML skeleton
    │   ├── styles.css             # CSS Paged Media, header and footer
    │   ├── fonts/                 # Bundled font (Open Sans, variable) + OFL.txt
    │   ├── cover.html             # Cover page template
    │   ├── part_divider.html      # Divider page for overarching parts
    │   ├── chapter_divider.html   # Chapter divider page with mini TOC
    │   └── toc.html               # Global table of contents
    └── html/
        ├── layout.html            # Standalone web layout
        ├── styles.css             # Screen/responsive stylesheet
        └── ...
```

## The three-level resolution hierarchy

When looking for a template (say `default/pdf`), this strict priority applies:

```
1. User directory (~/.markpublish/templates/default/pdf/)
   │ (highest priority)
   ▼
2. Common / project folder (<templates_dir>/default/pdf/)
   │
   ▼
3. Package built-in (inside the markpublish Python package)
```

### Configuring the common templates folder

There are four ways to set the shared template path:

1. **CLI parameter**: `markpublish build --templates-dir /path/to/templates`
2. **In `markpublish.yaml`**: `templates_dir: "./custom-templates"`
3. **Environment variable**: `MARKPUBLISH_TEMPLATES_DIR=/path/to/templates`
4. **Automatic fallback**: `./templates` in the project folder.

## Static texts and language

The fixed labels — table-of-contents heading, chapter marks, cover labels, page-number footer, callout titles — are not in the template but in `i18n.yaml` files. Which language applies is decided by `document.language`:

```yaml
document:
  title: "User Guide"
  language: "en"      # governs labels, callout titles and date format
```

`de` and `en` ship with markpublish. Regional forms are mapped (`de-AT` to `de`), and an unknown language falls back to English.

> [!NOTE]
> **i18n** refers to the sources — the files and the YAML entry, across all
> languages. **labels** is the result resolved from them for *one* document in
> *one* language: what arrives in the template as `{{ labels.chapter }}`.

### The three-level i18n cascade

All three levels are built **identically**: language code at the top, texts underneath. Each deeper level overrides the one above it — and only **the keys it actually sets**. Everything else stays as it stands further up:

```
1. Program      markpublish/i18n.yaml
   │            complete, de + en
   ▼
2. Theme        <templates>/<theme>/i18n.yaml
   │            applies to every target format of the theme
   ▼
3. Target       <templates>/<theme>/<target>/i18n.yaml
                PDF only, or HTML only
```

Level 1 is the only one that must be complete. It additionally places English beneath the document language, so that every program text is guaranteed to resolve. Levels 2 and 3 are pure overrides.

Static texts are defined **in the theme only**. There is no document level: `document.i18n` in `markpublish.yaml` is rejected, with a pointer to the theme file. To change the texts of a document, give it its own theme — `markpublish export-template` creates one.

> [!IMPORTANT]
> Levels 2 and 3 always come from **exactly one** theme: which one applies is
> decided beforehand by template resolution (user > project > package). A project
> theme does **not** inherit the texts of the package theme of the same name —
> only that one theme is merged with the program default.

> [!IMPORTANT]
> Levels 2 and 3 apply **only to the chosen language**. A theme that defines an
> `en:` block does not change a German output — otherwise English theme texts
> would bleed into documents written in other languages.

### The shared format

```yaml
# templates/mytheme/i18n.yaml
de:
  part: "Abschnitt"
  chapter_toc_title: "Auf dieser Seite"
en:
  part: "Section"
  chapter_toc_title: "On this page"
```

The special key `"*"` applies to **every** language and takes effect before the language-specific block — for terms that should read the same regardless of the document language:

```yaml
"*":
  version: "Rev."       # "Rev." in every language
de:
  part: "Abschnitt"
```

If you maintain only one language, the language level may be omitted. The flat form means the same as putting the keys under `"*"`:

```yaml
part: "Section"
```

Regional blocks beat the base block: with `language: "de-AT"`, `de-at:` wins over `de:`. A missing `i18n.yaml` is not an error — a theme without its own texts is the normal case. If one exists but is malformed, the build aborts naming the file, rather than quietly falling back to the defaults.

### Example: labelling PDF and HTML differently

```
templates/mytheme/
├── i18n.yaml            en: chapter: "Chapter"
├── pdf/
│   └── i18n.yaml        en: chapter: "Ch."       (PDF only)
└── html/
    └── i18n.yaml        (empty, inherits "Chapter")
```

The bundled `default` theme ships all three files as a **commented-out pattern**: `templates/default/i18n.yaml`, `default/pdf/i18n.yaml` and `default/html/i18n.yaml`. They are deliberately inert — the default theme should read exactly like the program default. Uncomment what you want to change. `markpublish export-template` copies these files along, including the theme-level `i18n.yaml`, which sits next to the target folders rather than inside them.

### Free labels: a template's own texts

A theme may define **its own keys**, which the program does not know — for the static texts of the template itself. The structure is the same, and so is the access:

```yaml
# templates/mytheme/i18n.yaml
de:
  imprint_title: "Impressum"
  disclaimer: "Alle Angaben ohne Gewähr."
en:
  imprint_title: "Imprint"
  disclaimer: "All information without guarantee."
```

```html
<!-- templates/mytheme/html/layout.html -->
<footer>{{ labels.imprint_title }}</footer>
```

> [!WARNING]
> For free labels there is **no program default** that could step in. A strict
> rule therefore applies: a label a template writes down **must** resolve
> somewhere in the cascade. If it does not, the build aborts and names the key,
> the location with line number, the document language and the files searched:
>
> ```
> Label 'imprint_title' is used in the template but defined in no i18n level.
>   Document language: en
>   Found at:
>     templates/mytheme/html/layout.html:108
>   Searched in:
>     templates/mytheme/html/i18n.yaml  (present)
>     templates/mytheme/i18n.yaml       (present)
>     markpublish/i18n.yaml             (present)
> ```
>
> So maintain every language you ship, or put the key under `"*"`. An empty text
> in a finished PDF goes unnoticed — an abort does not.

What is checked are the template sources, not the render pass: a label in a branch this particular document never traverses is reported too. `styles.css` counts as well, since it runs through the same Jinja environment.

### Inspecting the resolved table

With three levels it is not always obvious where a text comes from. `markpublish labels` shows the result together with its origin:

```bash
markpublish labels                       # all keys, target PDF
markpublish labels --target html         # cascade for the HTML output
markpublish labels --overridden          # only what comes from the theme
```

### Available keys

| Key | `de` | `en` |
| :--- | :--- | :--- |
| `toc_title` | Inhaltsverzeichnis | Table of Contents |
| `toc_sidebar` | Inhalt | Contents |
| `chapter_toc_title` | Inhalt dieses Kapitels | In this chapter |
| `chapter` | Kapitel | Chapter |
| `part` | Teil | Part |
| `author` | Autor | Author |
| `status` | Status | Status |
| `version` | Version | Version |
| `date` | Datum | Date |
| `copyright` | Copyright | Copyright |
| `page` | Seite | Page |
| `page_of` | von | of |
| `alert_note` | Hinweis | Note |
| `alert_tip` | Tipp | Tip |
| `alert_important` | Wichtig | Important |
| `alert_warning` | Warnung | Warning |
| `alert_caution` | Achtung | Caution |

The `alert_*` titles are produced while parsing Markdown, not later in the template — the cascade is handed through to that point, so an `alert_note` set in the theme takes effect in the callout as well.

To add a new language, complete a block in `markpublish/i18n.yaml` — or, without touching the package, set every key under the desired language code on level 2 or 3.

> [!TIP]
> In your own templates you reach the result with `{{ labels.chapter }}` — in
> `styles.css` too, which runs through the same Jinja environment. That is how
> the footer is built:
> `"{{ labels.page }} " counter(page) " {{ labels.page_of }} " counter(pages)`.

## Running headers and footers

Header and footer are **running elements**: a block in `layout.html` is given `position: running(name)`, which takes it out of the text flow; the `@page` rule then places it into the margin box with `content: element(name)`.

The difference from a `content:` string matters: the margin box thereby holds **real markup**. Any number of lines becomes possible, each with its own formatting — a string knows only one formatting for everything.

```html
<!-- layout.html -->
<div class="page-header-runner">
  <div class="hf-left">
    <div class="hf-doc-title">{{ document.title }}</div>
    <div class="hf-doc-subtitle">{{ document.subtitle }}</div>
  </div>
  <div class="hf-right"><span class="hf-section"></span></div>
</div>
```

```css
/* styles.css */
.page-header-runner {
  position: running(pageheader);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;    /* right column stays at the top */
}
.hf-doc-title { font-weight: 700; }
.hf-section::before { content: string(current-section); }

@page {
  @top-left {
    content: element(pageheader);
    width: 100%;
    vertical-align: top;
    margin-top: 12mm;          /* distance to the paper edge */
    padding-bottom: 0;
    border-bottom: 0.5pt solid #cbd5e1;
    margin-bottom: 12mm;       /* distance to the content */
  }
}
```

### Geometry

From the paper edge inwards:

```
Edge -- margin -- lines (top-aligned) -- rule -- margin -- content
        12 mm                                    12 mm
```

Both distances are deliberately equal: a header sitting tightly above the text reads as part of the type area rather than as page furniture.

Both columns sit in a flex container with `align-items: flex-start`. The right column therefore begins at the height of the **first** left-hand line, even when there are three lines on the left and only one on the right.

> [!IMPORTANT]
> The distance to the content comes from `margin-bottom`, not `padding-bottom`.
> In CSS the border sits **outside** the padding — a `padding-bottom` would push
> the rule away from the text and press it against the content. The opposite is
> wanted: rule right at the text, space after it.

> [!WARNING]
> A margin box **does not push the content**. Its height is capped by the page
> margin; extra lines run off the page instead of shrinking the type area. The
> page margin is therefore computed in `styles.css` from the number of lines:
>
> ```
> margin-top = edge distance + lines x line height + rule width + content distance
> ```
>
> If you add a line in `layout.html`, adjust `hf_header_lines` or
> `hf_footer_lines` in `styles.css` accordingly.

### What the default theme puts there

```
Header      Document title (bold)                       Chapter title
            Subtitle

Footer      Copyright                     Version 1.0.0 | 2026-09-01
                                                     Page X of Y
```

Subtitle and version are optional. Without a subtitle the header has a single line and the type area moves up accordingly. Without a version it disappears together with its separator — the footer then shows only the date, and the field is absent from the cover page entirely.

The chapter title comes from `string(current-section)`, which the chapter `<article>` sets via `string-set`; `counter(page)` works inside the running element just as it does in a margin box. The switches `document.header` and `document.footer` hide the respective block; on cover and divider pages it is switched off anyway.
