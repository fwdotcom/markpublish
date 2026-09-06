# Appendix B: Troubleshooting and FAQ

This appendix offers actionable guidance for typical issues during the publishing process along with answers to frequently asked questions.

## Diagnosing Compilation Errors

If a compilation run aborts due to an error from the Typst engine, markpublish automatically saves the fully generated Typst source code in your working directory:

```text
.markpublish/last_failed_build.typ
```

### Troubleshooting Procedure

1. Open `.markpublish/last_failed_build.typ` in any text editor.

2. Search for the keyword, variable name, or text snippet cited in the error message.

3. The surrounding context directly reveals which Markdown chapter or formatting block triggered the issue.

---

## Common Causes and Solutions

### Images or Graphics Not Found

**Problem:** Typst aborts with a message such as `image not found`.

**Solution:**

* Paths to images in Markdown (e.g., `![Diagram](images/architecture.png)`) are always resolved **relative to the respective Markdown file**.
* If `01_chapter.md` is located in `chapters/`, the `images/` folder must either reside in `chapters/images/` or be referenced as `../images/architecture.png`.
* markpublish automatically copies local image files to the internal build directory during compilation.

### Invalid Indentation in Configuration (YAML)

**Problem:** markpublish reports `Configuration error: mapping values are not allowed here` or `YAML parsing error` on startup.

**Solution:**

* YAML is strict regarding indentation. Always use **two spaces** for indentation and never tabs.
* Ensure list markers (`-`) and nested keys are aligned consistently.

### Customizing Static Text Labels (i18n)

**Problem:** A generated string (such as "Table of Contents" or "Chapter") should be reworded or is missing in a new language.

**Solution:**

* Run `markpublish labels` to display all resolved text variables and their cascade layer.
* Add or override the desired keys either in a project-local `i18n.yaml` (next to `markpublish.yaml`) or in your theme's `i18n.yaml`.

### Fonts and Font Families

**Problem:** Font-related error messages or unexpected font appearance.

**Solution:**

* The standard theme uses the bundled **Open Sans** font family; manual font installation on your operating system is not required.
* For custom themes, you can place font files (`.ttf`, `.otf`) directly into your theme's `pdf/fonts/` folder. markpublish automatically includes theme fonts in the search path.

### Missing Metadata Field (UndefinedMetadataError)

**Problem:** The build halts with the message `Metadata '...' is queried by theme but not defined in document`.

**Solution:**

* The theme queries a field via `meta.at("key")` that is not defined under `document:` in `markpublish.yaml` and has no fallback in the theme.
* Add the missing field under `document:` in your `markpublish.yaml` (custom fields are permitted without restriction), or define a fallback value in the theme: `meta.at("key", default: (value: none)).value`.

### Missing Text Label (UndefinedLabelError)

**Problem:** The build halts with the message `Label '...' is referenced in template but not defined in any i18n layer`.

**Solution:**

* The template accesses a label via `labels.at("...")` that is not defined in any layer of the cascade for the active document language.
* Add the key under the appropriate language code (e.g., `en:`) in an `i18n.yaml` file in your project directory or theme.

### Theme Signature Mismatch

**Problem:** `markpublish labels` or the build reports that the theme and function signature do not match.

**Solution:**

* The Typst function `setup-document` in `template.typ` does not declare all required parameters.
* markpublish delivers all metadata packaged in the dictionary `meta: (:)`. Ensure your theme declares this parameter: `#let setup-document(..., meta: (:), labels: (:), body) = { ... }` (or accepts `..rest`).

### Rejection of Unknown Keys (unknown_key)

**Problem:** markpublish aborts with a message such as `chapters does not recognize key: 'break_befor' -- did you mean 'break_before'?`.

**Solution:**

* At section (`parts:`) and chapter (`chapters:`) levels, markpublish strictly rejects unknown keys to catch typos early. Check the reported key; custom metadata fields are exclusively permitted under `document:`.

### Target Directory on init is Not Empty

**Problem:** `markpublish init` aborts with `Destination directory ... already exists and is not empty`.

**Solution:**

* `init` never overwrites existing files. Choose a new directory name or empty the directory before initialization.

---

## Frequently Asked Questions (FAQ)

### What is the difference between interface language and document language?

markpublish strictly separates the CLI language from the document typesetting language:

* **Interface language (`--ui-lang`, `MARKPUBLISH_UI_LANG`):** Controls the language of terminal error messages, help texts, and diagnostic tables (`en` or `de`). Without this flag, your system language applies.
* **Document language (`language:` in `markpublish.yaml`):** Governs typography, hyphenation, date formatting, and fixed text labels (such as "Table of Contents" or "Chapter") in the output PDF. A terminal in one language can effortlessly compile documents in another.

### How do I prevent a divider page before a chapter?

By default, a chapter starts on a new page with `break_before: "page"`. To attach a chapter seamlessly without a page break, set `break_before: "none"` in the chapter definition.

### Why does my section not appear anywhere in the document?

Sections (`parts:`) default to `break_before: "none"`: they group chapters, occupy no page, and do not appear in the table of contents. To make a section visible, specify:

```yaml
parts:
  - part: "Appendices"
    break_before: "divider"   # styled divider page
```

With `break_before: "page"`, the section receives a heading on a fresh page instead of a divider page.

### How can I restart page numbering for each chapter?

Set `pagenum_reset: true` at the document or chapter level in `markpublish.yaml`. markpublish automatically resets the page number to 1 at chapter start and computes total page counts consistently.

### Are hyperlinks exported as clickable links in the PDF?

Yes. Both internal references (from the table of contents or footnotes) and external web links (written in Markdown as `[Link text](URL)`) are generated as native, clickable PDF hyperlinks.

