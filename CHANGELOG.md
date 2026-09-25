# Changelog

All notable changes to **markpublish** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Figure and table captions**: `/// figure-caption` and `/// table-caption` (`pymdownx.blocks.caption`) become numbered Typst figures; `[](#id)` renders a numbered reference ("Figure 1").
- **Lists of figures and tables**: `list_of: figures|tables` as an entry under `chapters:`.
- **Image attributes**: `width`, `height` (aspect ratio kept), `frame` / `noframe` (with or without dot) to override the theme's default.
- **i18n labels**: `figure`, `table`, `list_of_figures`, `list_of_tables`.

### Changed
- Stand-alone images are centered and framed by default (`image-frame-default` in the default theme); inline images stay within their line.
- **Spacing of set-off elements (default theme)**: code blocks, callouts and quotes (`block-spacing`) and figures, tables and images (`figure-spacing`) get more space than paragraphs; the spacing no longer adds up between consecutive elements. Captions sit close to their figure (`caption-gap`).

---

## [2.1.10] - 2026-09-23

### Changed
- **CLI help output cleaned**: Configured `add_completion=False` on the Typer application to suppress shell-completion options (`--install-completion`, `--show-completion`) in `--help`.
- **Project URLs updated (`pyproject.toml`)**: Pointed `Homepage` to the official website (`https://www.markpublish.com`) and `Documentation` to `#manuals`, retaining `Repository` for the GitHub source code.

---

## [2.1.9] - 2026-09-22

### Changed
- **Header and footer typography & spacing (default PDF template)**: Introduced `header-lead` (0.5em), `footer-lead` (0.5em), and `footer-rule-gap` (6pt) tokens for consistent multi-line line spacing and precise divider rule gaps.
- **Bold chapter title in header (default PDF template)**: The running chapter title in the top-right header is now displayed in bold weight (`weight: "bold"`).
- **Init templates with two chapters and cover summary**: Scaffolding (`markpublish init`) now creates two starter chapters in German (`kapitel_1.md`, `kapitel_2.md`) and English (`chapter_1.md`, `chapter_2.md`) with a pre-configured cover summary, improved comments, callouts, and clean configuration examples.

---

## [2.1.8] - 2026-09-22

### Changed
- **Callout boxes set to non-breakable (default PDF template)**: Admonition/callout boxes now use `breakable: false` so title, icon, accent bar, and text remain together on a single page instead of splitting across page breaks.
- **Block quotes styled as callout boxes (default PDF template)**: Markdown block quotes (`>`) use the shared callout box layout with a neutral grey accent bar (`c-quote-bar`, Slate 500) and `breakable: true`, without a title row.

---

## [2.1.7] - 2026-09-22

### Added
- **Example projects (`examples/`)**: Added four complete sample projects in German (`examples/de/`) and English (`examples/en/`) for single-chapter reports and three-chapter guides.

### Changed
- **Single-chapter table of contents**: When a document contains only one chapter in total, the main table of contents omits the redundant chapter line and directly lists subheadings (H2, H3).
- **Single-chapter running headers (default PDF template)**: Top-right running headers suppress the chapter title in single-chapter documents to avoid repeating the document title.
- **Dedicated color token for code (`c-code`)**: Added `c-code` token (Slate 900) to unify syntax coloring for inline code and code blocks.
- **Dedicated color token for link underlines (`c-link-underline`)**: Added `c-link-underline` token (Blue 300) to control link underline styling from the palette.

### Fixed
- **Paragraph spacing inside block quotes (default PDF template)**: Added `quote-spacing` token (1.0em) to tighten spacing inside multi-paragraph quotes.

### Removed
- **Unused `c-primary-light` token**: Removed unused color token from the default palette.

---

## [2.1.6] - 2026-09-21

### Fixed
- **Documentation links in README**: Updated manual and cheat sheet PDF download links in `README.md` to point to `www.markpublish.com/manuals/`.
- **Release workflow wheel management**: Fixed release artifact upload in `.github/workflows/release.yml` by pruning obsolete `.whl` files from earlier releases.

---

## [2.1.5] - 2026-09-21

### Added
- **Landing page & interactive feature showcase (`www/`)**: Redesigned the project website with a 4-card showcase featuring PDF page clippings, vector lightbox zoom, German/English language toggle, and downloads for sample projects and PDFs.
- **Showcase asset build pipeline (`scripts/build_showcase_assets.py`)**: Added an automated script to compile vector SVGs and PNG fallbacks from bundled sample documents (`www/sample/de` and `www/sample/en`).

### Changed
- **Relocated `build_manuals.py`**: Moved documentation build script to `scripts/build_manuals.py` and updated CI workflows and guidelines.
- **GitHub Pages deployment workflow**: Configured `.github/workflows/deploy-pages.yml` to deploy website and documentation on release publication or manual trigger.

### Fixed
- **Leading number escaping in headings & paragraphs**: Escaped leading digits followed by a period (e.g. `1\. `) to prevent Typst from interpreting them as ordered list items in headers.

---

## [2.1.4] - 2026-09-10

### Fixed
- **Table text justification in PDF template**: Tables explicitly disable text justification (`show table: set par(justify: false)`) to prevent overstretched word spacing in narrow columns.
- **Callout icon size & content spacing**: Adjusted callout icon size to 11 pt and title-to-content margin to 7 pt for balanced optical proportions.

---

## [2.1.3] - 2026-09-09

### Added
- **Bundled monospace font (`Noto Sans Mono`)**: Bundled `NotoSansMono-VariableFont_wdth,wght.ttf` under `templates/default/pdf/fonts/` for consistent code rendering across all platforms.
- **Version in quick reference**: Added version display in `markpublish cheatsheet` footer.

### Changed
- **Inline code & code block typography**: Centralized code font tokens (`size-code-block = 8.5pt`, `size-code-inline = 1.0em`, `weight-code-inline = "medium"`).
- **Design tokens consolidation in default template**: Centralized design tokens at top of `template.typ` for colors, strokes, radii, and metrics.
- **Running header column ratio & hyphenation**: Changed header columns to `(1fr, 1fr)` and disabled hyphenation to keep headers strictly two lines high.
- **Unified list and definition list spacing**: Set `list-spacing = 1.2em` across bullet, numbered, task, and definition lists for a consistent vertical rhythm.
- **Document TOC vertical rhythm**: Added spacing (`v(0.85em)`) between part divider titles and chapter lists in table of contents.
- **Cover, divider, and heading typography**: Disabled text justification and hyphenation on headings, cover page titles, and part/chapter dividers.
- **Booktabs table formatting**: Cleaned up default table styling with dedicated top/mid/bottom rules and tabular figures (`number-width: "tabular"`).

---

## [2.1.2] - 2026-09-09

### Fixed
- **Strict root-level configuration validation**: Rejected unknown top-level keys in `MarkpublishConfig` with `did_you_mean` suggestions.
- **Config loader error handling**: Differentiated between missing files and invalid YAML content with explicit error messages.
- **CLI `--target html` exit behavior**: Requesting `--target html` exits with code 1 and an explanatory message.
- **Heading anchor collision handling**: Verified AST slug generation against duplicate titles and explicit anchor collisions.

### Removed
- **v1.x legacy modules**: Removed dormant `assets.py` and `typst_converter.py` along with deprecated tests.

---

## [2.1.1] - 2026-09-08

### Fixed
- **Empty label support**: Setting `part_label: ""`, `chapter_label: ""` or `label: ""` suppresses the label prefix entirely on divider pages and headings.

---

## [2.1.0] - 2026-09-08

### Added
- **`autonum_pattern`**: Added pattern syntax (e.g. `"1|.1|+"`, `"_|1|.1|+"`) to define section and heading numbering across document levels.
- **`label`, `part_label`, `chapter_label`**: Configurable structural labels for parts and chapters via `markpublish.yaml` and the i18n cascade.
- **Numbered parts**: Parts can be numbered via `autonum_pattern` under `document:`.

### Changed
- **`autonum_reset`**: Resets numbering counters for child levels when entering a block.
- **Theme contract**: `render-part-divider` requires a `number:` parameter.
- **Strict label placement**: Validates label placement (`part_label`/`chapter_label` on parent block, `label` on target element).
- **Descriptive pattern errors**: Pattern validation errors indicate the base level where the pattern applies.

### Removed
- **Deprecated numbering keys**: Replaced `autonum_style`, `autonum_from_level`, and `autonum_prefix` with `autonum_pattern`.
- **Redundant chapter keys**: Disallowed unused `title` and `chapter` keys on chapter definitions.
- **`title` alias for parts**: Parts are named exclusively via `part:`.

---

## [2.0.1] - 2026-09-08

### Removed
- **Nested subchapters**: Restricted document structure to two levels (`parts:` → `chapters:`).

---

## [2.0.0] - 2026-09-06

### Added
- **CLI localization (`--ui-lang`, `MARKPUBLISH_UI_LANG`)**: Added German and English interface translations with automatic system language detection.
- **English project scaffold (`markpublish init --lang en`)**: Bundled English project templates and sample documents alongside German.
- **CLI theme override (`--theme`)**: Added `--theme <name>` option to preview themes without modifying `markpublish.yaml`.
- **Chapter title & divider controls**: Added `show_title:` and `divider_title:` options to customize or suppress H1 headings and divider titles.
- **Unified document metadata model (`meta`)**: Grouped document metadata into a structured Typst dictionary for themes.
- **Typed metadata values**: Preserved YAML types (booleans, numbers) when passing metadata to Typst.
- **Project-level i18n**: Added project-level `i18n.yaml` to override labels and define custom metadata captions.
- **Math formula support**: Supported inline (`$...$`) and display (`$$...$$`) math using LaTeX and Typst syntax.
- **Internal heading anchors (`[Text](#slug)`)**: Converted heading references into clickable PDF jump targets.
- **Native Typst AST serializer (`TypstSerializer`)**: Converted Python-Markdown AST directly into well-formed Typst markup.
- **Synchronized headings and TOC**: Synchronized heading numbers and anchors between the syntax tree and table of contents.
- **Local image resolution**: Automatically resolves local Markdown image paths and copies them to the build sandbox.
- **Build diagnostics**: Saves failed Typst sources to `.markpublish/last_failed_build.typ` on compilation errors.
- **Compilation test suite**: Added test suites verifying Typst compilation for formulas, code blocks, and special characters.
- **Enhanced `markpublish labels`**: Displays theme usage, fallback values, and cascade resolution per label.
- **`UndefinedMetadataError`**: Provides descriptive error messages when themes access undefined metadata keys.

### Changed
- **Typst as native PDF compiler**: Replaced WeasyPrint with Typst, removing GTK/Pango dependencies and accelerating builds.
- **Unified single AST pipeline**: Consolidated Markdown processing onto `python-markdown` and `pymdown-extensions`.
- **Full Markdown extension support**: Supported tables, callouts, definition lists, footnotes, task lists, and syntax highlighting.
- **Robust Typst escaping**: Escaped special characters in metadata and Markdown content.
- **Theme contract signature**: Document metadata is passed to `setup-document` via `meta: (:)`.
- **Default `break_before` for parts**: Parts default to `break_before: "none"`; divider pages require `break_before: "divider"`.
- **Default `cover` setting**: Documents default to `cover: false`.
- **Refactored CLI entry point**: CLI entry point resolves `--ui-lang` before importing command definitions.
- **Unified CLI messages**: Consolidated user-facing CLI strings into centralized localization catalogs.
- **Relocated system language detection**: Moved locale detection logic to `markpublish.syslang`.
- **Theme cover metadata ordering**: Themes define metadata field order via `cover-order`.
- **Typst native heading numbering**: Heading numbers use Typst's native numbering property instead of text prefixes.
- **Task list styling**: Rendered task lists with checkboxes only, removing redundant bullet points.
- **Page numbering fixes**: Fixed total page counting across counter resets and decoupled cover page logic.
- **Header & footer controls**: Wired `document.header` and `document.footer` flags to Typst layout.
- **Updated `markpublish labels` output**: Improved cascade source display and override filtering.
- **Strict key validation on parts and chapters**: Rejected unknown keys on parts and chapters with suggestions.
- **Smart `markpublish init` defaults**: Document title defaults to directory name; target directory must be empty.
- **Context-aware `init` command hints**: Displays exact build command with created configuration path.
- **Scaffold placeholders**: Added `{dir}` placeholder for path references in scaffold welcome text.
- **Self-documenting scaffold**: Generated `markpublish.yaml` includes inline comments and recommended options.
- **Multi-language build script**: `build_manuals.py` supports language selection via `--lang`.
- **Streamlined CI/CD matrix**: Removed OS-level GTK/Pango dependencies from CI workflows.

### Fixed
- **Nested subchapter validation**: Validates nested chapters recursively during configuration loading.
- **Raw code theme check fix**: Excluded code blocks from theme contract parameter scanning.
- **Pluralization fix in build script**: Corrected plural forms in build summary messages.
- **Heading orphan prevention**: Headings use `sticky: true` to prevent orphan headings at page bottoms.

### Removed
- **WeasyPrint & GTK dependencies**: Removed WeasyPrint runtime dependencies and configurations.
- **HTML output deprecated**: Removed legacy HTML pipeline to focus exclusively on Typst PDF output.
- **Removed obsolete internal APIs**: Removed `label_overview()` and legacy parameter detection.

---

## [1.0.0] - 2026-09-01

### Added
- **Multi-Format Publishing Pipeline**: Modular compilation from Markdown to print-ready **PDF** (via WeasyPrint & W3C CSS Paged Media) and standalone **HTML**.
- **Declarative YAML Configuration (`markpublish.yaml`)**:
  - Global metadata (`title`, `subtitle`, `author`, `date`, `version`, `language`, `status`, `copyright`).
  - Layout controls: `cover`, `header`, `footer`, `document_toc`, `part_toc`, `chapter_toc`.
  - Numbering controls: `autonum_style`, `autonum_from_level`, `autonum_prefix`, `autonum_reset`, and `pagenum_reset`.
  - Two-tier document structure: **Parts** (`parts:`) divide the document, chapters (`chapters:`) beneath them carry the content.
  - Flexible page-break controls via `break_before` (`page`, `divider`, `none`).
- **Target-Based Template Engine & 3-Tier Resolution**:
  - Hierarchical template resolution: User (`~/.markpublish/templates`) > Project/Workspace (`./templates`) > Package Built-in.
  - Distinct subfolders per theme and target: `templates/<theme>/pdf` and `templates/<theme>/html`.
  - Inlined local assets (SVGs and raster graphics) as portable Data-URIs.
  - Bundled Open Sans variable font embedded into generated PDFs.
- **Cascading Internationalization (i18n)**:
  - 3-level label cascade: Built-in `markpublish/i18n.yaml` > `<theme>/i18n.yaml` > `<theme>/<target>/i18n.yaml`.
  - Native bilingual support for German (`de`) and English (`en`), with regional mapping (`de-AT` -> `de`).
  - Automatic system UI language detection (`detect_system_language()`) via POSIX env vars and Windows Win32 API.
  - Strict compile-time label verification (`validate_label_references`) preventing missing UI labels.
- **Rich CLI (`markpublish` / `mpub`)**:
  - `markpublish build`: Compiles documents to PDF and/or HTML.
  - `markpublish init`: Scaffolds a clean, minimal starting project.
  - `markpublish cheatsheet`: Renders the bundled 2-page quick reference on-demand.
  - `markpublish manual`: Renders the comprehensive official user guide on-demand.
  - `markpublish templates`: Lists available templates and active overrides.
  - `markpublish export-template`: Exports built-in themes into the workspace for customization.
  - `markpublish labels`: Inspects resolved static texts and cascade origins.
- **Build Utilities**:
  - `build_manuals.py`: One command builds all four showcase documents into `www/manuals/`.
