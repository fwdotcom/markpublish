# Theme System and Internationalization

markpublish strictly separates content from presentation: text content is written in Markdown, while the visual appearance, typography, and page layouts are controlled via Typst templates. This architecture is complemented by a flexible cascade for internationalization (i18n).

## Theme Resolution Hierarchy

When markpublish searches for a theme (specified via the `--theme` CLI flag, the `theme:` configuration setting, or the `default` fallback), the resolver searches through the following locations in order (the first match wins):

1. **User Templates (`user`):**  
   Templates in the current user's home directory (`~/.markpublish/templates/<theme>/`) or platform-specific AppData directory. This allows author-wide default templates across all projects.

2. **Project / Common Directory (`common`):**  
   Templates in the project directory (`./templates/<theme>/`) or in a directory explicitly configured via `templates_dir:` in `markpublish.yaml`, the `--templates-dir` CLI flag, or the `MARKPUBLISH_TEMPLATES_DIR` environment variable.

3. **Package Templates (`package`):**  
   The built-in default theme (`default`). It serves as a reliable fallback whenever no template is found at the user or project level.

## Theme Structure

A complete markpublish theme has the following directory layout:

```text
templates/
└── my-theme/
    ├── i18n.yaml            # Cross-format theme text labels
    └── pdf/
        ├── template.typ     # Typst layout template for PDF
        ├── i18n.yaml        # Format-specific theme text labels
        ├── fonts/           # Optional font files (e.g., .ttf, .otf)
        └── assets/          # Static graphics, logos, and icons
            └── icons/
```

### The Theme Contract (`setup-document` and `meta`)

The core of `template.typ` is the Typst function `setup-document`. It receives layout switches, text labels, and all document metadata from markpublish:

```typst
#let setup-document(
  language: "en",
  show-cover: true,
  show-toc: true,
  toc-title: "Table of Contents",
  toc-depth: 3,
  show-header: true,
  show-footer: true,
  meta: (:),
  labels: (:),
  body,
) = {
  // ...
}
```

> [!IMPORTANT] Metadata Delivery via `meta`
> markpublish delivers all document metadata packaged as a structured Typst dictionary `meta: (:)`. Every theme must declare this parameter in `setup-document` (or accept `..rest`). If the parameter is missing, `markpublish labels` flags it as a signature mismatch error before the build begins.

Inside the Typst template, access individual metadata fields by key:

```typst
let title = meta.at("title").value
let subtitle = meta.at("subtitle").value
let version = meta.at("version").value
```

Custom or optional metadata fields should always be queried with a safe fallback:

```typst
let department = meta.at("department", default: (value: none)).value
```

If a theme queries a field without `default:` that is not defined in the configuration, compilation aborts with an informative `UndefinedMetadataError`. The error cites the exact file line in the theme and references `markpublish.yaml`.

### What Appears on the Title Page (`cover-fields`)

The metadata grid on the cover page does not automatically display everything under `document:`; it shows precisely the fields designated by the theme – in the built-in standard theme, these are version, date, author, copyright, and status. Title, subtitle, and summary are typeset as distinct header blocks above.

Which fields appear on the cover page is determined inside the theme by the `cover-fields` function:

```typst
#let cover-fields(meta) = (
  meta.at("version", default: none),
  meta.at("date", default: none),
  meta.at("author", default: none),
  meta.at("copyright", default: none),
  meta.at("status", default: none),
)
```

To display `department:` or `client:` on the cover page, export the theme (see below) and add a line to `cover-fields`. The accompanying label is looked up in the project's `i18n.yaml`.

### Typed Metadata Values

Metadata preserves its native YAML data type on its way to Typst:
* Integers, floats, and strings remain numbers and strings.
* `reviewed: true` arrives as a native Typst boolean. The standard theme formats this automatically using the label keys `bool_true` ("Yes") and `bool_false` ("No") from the i18n cascade.
* Lists are formatted cleanly with comma separation.

Which fields a theme actually consumes can be inspected with `markpublish labels`: any field ignored by the theme is flagged as *unused*.

## Creating and Customizing Themes

The fastest and safest way to develop your own corporate design is to export the built-in standard theme:

```bash
markpublish export-template default ./templates --target pdf
```

This command copies the complete default theme into the local directory `templates/default/`. You can then edit the files directly, customize fonts, adjust color palettes, or embed your company logo. markpublish automatically uses your customized project template on subsequent `build` commands.

The `template.typ` layout file is written in the Typst typesetting language and comprehensively commented in the default theme. For advanced modifications beyond colors and fonts, the official language documentation is available at [https://typst.app/docs](https://typst.app/docs).

---

## Internationalization and the Text Cascade (i18n)

Professional documents require various static text strings that do not originate from chapter Markdown files but are generated by the template – such as "Table of Contents", "Chapter", "Page X of Y", or labels on the title page.

markpublish manages these strings through a cascading system of `i18n.yaml` files.

### The Four-Tier Label Cascade

When resolving a text label (e.g., `toc_title`), markpublish traverses the following layers in order – later entries override earlier ones:

1. **Package Base (`markpublish/i18n.yaml`):** Comprehensive default strings for all supported languages.

2. **Theme Level (`<theme>/i18n.yaml`):** Themes can supply their own terminology or design phrasing.

3. **Format Level (`<theme>/pdf/i18n.yaml`):** Format-specific text customizations for the theme.

4. **Project Level (`i18n.yaml` next to `markpublish.yaml`):** Document-specific texts with highest priority.

The project level is where custom metadata fields are labeled: if you specify `department: "R&D"` under `document:`, write `department: "Department"` into the project's `i18n.yaml`. Without this entry, the cover page falls back to printing the raw key name. You can also override any theme text for an individual project without modifying the theme itself.

### Structure of i18n.yaml

An `i18n.yaml` file contains translations grouped by language code:

```yaml
en:
  toc_title: "Table of Contents"
  chapter: "Chapter"
  part: "Part"
  page: "Page"
  page_of: "of"
  version: "Version"
  author: "Author"

de:
  toc_title: "Inhaltsverzeichnis"
  chapter: "Kapitel"
  part: "Abschnitt"
  page: "Seite"
  page_of: "von"
  version: "Version"
  author: "Autor"
```

### Language Detection and Validation

The document language is set in `markpublish.yaml` via the `language:` key (e.g., `language: "en"`). If omitted, markpublish automatically detects your operating system language.

You can run `markpublish labels` at any time to inspect all active text labels for your project and verify which file provided each string.

