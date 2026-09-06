# Changelog

All notable changes to **markpublish** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

## [2.0.0] - 2026-09-06

### Added
- **The program speaks your language (`--ui-lang`, `MARKPUBLISH_UI_LANG`)**: Help texts, status lines and error messages are available in English and German, and markpublish follows your system language without being asked. This is the *interface* language and has nothing to do with `language:` in the markpublish.yaml, which decides what the PDF says — a German user typesetting an English document now gets English headings in the document and German messages in the terminal. Resolution, nearest to the call wins: `--ui-lang` → `MARKPUBLISH_UI_LANG` → the system (POSIX variables, or the Windows display language) → English. A regional form falls back to its base language (`de-AT` → `de`); a language with no catalogue falls back to English rather than being guessed at. Deliberately absent from the cascade: the markpublish.yaml — the terminal language belongs to a person's working environment, not to the repository. Texts live in `markpublish/locale/<language>.yaml`, one flat file per language.
- **An English project scaffold (`markpublish init --lang en`)**: `docs/init/en` ships alongside the German one — configuration and welcome chapter, comments and prose translated, and `language: "en"` set in the configuration, so the built document carries English labels ("Table of Contents", "CHAPTER", ISO date) rather than English text under German ones. Without `--lang`, `init` follows the system language as before; it now has somewhere to go when that language is English. The manual and the quick reference ship in both languages as well.
- **A theme without touching the document (`--theme`)**: `build`, `cheatsheet`, `manual` and `labels` take `--theme <name>` and use it for that one run, ahead of `theme:` in the markpublish.yaml. Trying a theme on a document no longer means editing the document, and the bundled reference can be rendered in your own theme without a project at all.
- **`show_title:` and `divider_title:` on a chapter**: `show_title: false` keeps the file's H1 off the content page — the counterpart to a chapter that already carries its title on a divider page, where it would otherwise stand twice. `divider_title:` sets what that divider page says wherever it should differ from the heading; `toc_title:` does the same for the table of contents and the running header.
- **Unified Document Metadata Model (`meta`)**: All document metadata is grouped into a structured Typst dictionary passed to `setup-document`. Each entry is a record — `(key, label, value, in-grid)` — so a theme can enumerate the metadata instead of knowing every field by name. Custom fields under `document:` reach the cover page without a schema change.
- **Typed metadata values**: Values keep their YAML type on the way to Typst. A `reviewed: true` arrives as a Typst boolean, and the theme words it through the cascade (`bool_true` / `bool_false`, new in `i18n.yaml`) instead of printing Python's `True`.
- **Project level in the i18n cascade**: An `i18n.yaml` next to `markpublish.yaml` is now the last and winning level. It is where a document names the captions of its own free metadata fields (`abteilung: "F&E"` under `document:` → `abteilung: "Abteilung"`), and it can override a theme text for a single document without forking the theme.
- **Formulas**: LaTeX math between single dollars runs inline, between double dollars as a displayed block, and Typst's own math syntax is accepted as well. Fractions, roots, sums, integrals and greek letters are normalised on the way and set by Typst rather than pictured.
- **Anchor links inside the document (`[Text](#slug)`)**: A link to a heading becomes a real jump target in the PDF. Only slugs that exist in the finished document are labelled — a link to a heading that is not there would otherwise abort the Typst compilation instead of simply not jumping anywhere.
- **Native Typst AST Serializer (`TypstSerializer`)**: A dedicated, robust ElementTree-to-Typst serializer converting Python-Markdown trees directly into clean, well-formed Typst markup.
- **Synchronized AST Numbering & TOC**: Headings, autoincrement numbers, and slugs are calculated and injected directly into the syntax tree, ensuring 100% synchronization between document headings and the table of contents.
- **Local Image Resolution & Isolation**: Local image paths referenced in Markdown chapters are resolved relative to the chapter source and automatically copied to the build directory (`images/`), avoiding sandbox path restrictions.
- **Build Diagnostics**: In case of a Typst compilation error, the complete generated Typst source is saved to `.markpublish/last_failed_build.typ` for immediate troubleshooting.
- **Real Compilation Test Suite**: Added `tests/test_typst_compile_cases.py` and `tests/test_typst_serializer.py`, verifying real Typst compilation for prices ($5), programming languages (C#), HTML-like tags, special characters, and extensions.
- **Enhanced `markpublish labels` diagnostics**: The table now shows theme usage (`key`, `wert`, `key/wert`), the fallback a theme has notated, the document value, and a per-key diagnosis. It also reports a theme whose `setup-document` does not declare an argument markpublish sends — before the build, not during it.
- **`UndefinedMetadataError`**: A theme reading a metadata key the document does not define now aborts with its own message, naming the exact file and line in the theme and pointing at `document:` in `markpublish.yaml`. Previously this ran through the label message and advised editing an `i18n.yaml`, which does not fix it.

### Changed
- **Typst as Native PDF Compiler**: Replaced WeasyPrint and W3C CSS Paged Media with **Typst**, eliminating all native C/GTK/Pango runtime dependencies while accelerating PDF builds by an order of magnitude (~1.3s for 30+ pages).
- **Single Markdown Pipeline**: Replaced the previous dual regex/HTML pipeline with a unified single AST pipeline powered by `python-markdown` and `pymdown-extensions`.
- **Full Markdown Extension Support**: Restored complete support for all 16 standard markdown extensions (tables with column alignment, GitHub alerts/callouts, definition lists, footnotes, task lists, smart quotes, and pygments code blocks).
- **Robust Typst String Escaping**: Full escaping of metadata and content strings (`\`, `"`, `$`, `#`, `@`, `~`, backticks) preventing syntax errors on special characters.
- **`part:` names a part, a chapter names itself**: `part:` is the key that carries a part's name (`title:` there is tolerated as the legacy spelling and still supplies it). A chapter takes its name from its own H1, with `toc_title:` and `divider_title:` overriding it where needed; `chapter:` and `title:` on a chapter are accepted for compatibility and ignored.
- **Breaking: theme contract signature**: Document metadata now reaches a theme *only* through `meta`. The individual parameters `title`, `subtitle`, `authors`, `version`, `date`, `copyright`, `status` and `summary` are no longer sent; `setup-document` must accept `meta: (:)` (or use `..rest`) and read them as `meta.at("title").value`. Two routes to the same value could drift apart, and every new field would otherwise have had to decide whether it also gets a parameter.
- **Breaking: `break_before:` on a part defaults to `"none"`**: A part without the key no longer produces a divider page. It brackets its chapters and passes its settings down, but takes no page of its own and therefore does not appear in the document TOC either. The two-level structure (`parts:` → `chapters:`) is mandatory, so a part is often just a bracket the format demands — and it billed a full page for it that nobody had asked for. Notate `break_before: "divider"` for the designed divider page, or `"page"` for a heading on a fresh page. Chapters are unchanged: they still default to `"page"`.
- **`cover:` defaults to `false`**: A cover page is a decision about the document, not standard equipment. Whoever typesets a few pages of Markdown got a title page they had not ordered and first had to find out which key removes it again. Set `cover: true` to get one; documents that already notate the key are unaffected.
- **Console scripts run through `markpublish.entry:main`**: `markpublish` and `mpub` no longer point at `markpublish.cli:app` directly. The wrapper reads `--ui-lang` from the command line and sets the language *before* importing the CLI, because Typer evaluates `help=` at import time — resolving it any later would leave `--ui-lang de --help` printing English help. Importing `markpublish.cli:app` yourself still works and takes the language from the environment and the system.
- **The interface no longer speaks two languages at once**: the CLI shell was English while the messages underneath it were German — a mistyped key in a chapter produced an English `Error:` in front of a German sentence. Every user-facing text now goes through one catalogue, and both languages are complete. A test walks the sources and fails on any user-facing string still written at the call site, so the next one cannot creep back in.
- **`clean_locale` and `detect_system_language` moved to `markpublish.syslang`**: the document language and the interface language both need to know what the system speaks, and the interface catalogue supplies the messages the document i18n raises — leaving the detection in `i18n.py` would have been a circular import. Both names remain importable from `markpublish.i18n`.
- **Cover metadata order lives in the theme**: `cover-order` in `template.typ` decides the order of the metadata grid; keys it does not list — your own fields — follow behind in configuration order. The shipped order is unchanged (version, date, author, copyright, status), but it is now one editable line in the theme rather than a side effect of a constant in `i18n.py`.
- **Heading numbers**: Headings carry their number in Typst's `numbering` property instead of inside the heading text. Running headers therefore show the plain chapter title, and no acronym (`API`, `CLI`) is mistaken for a numeral.
- **Task lists without bullet markers**: Task lists are rendered with only the checkbox and text, eliminating the redundant preceding bullet point (`•`). Sub-lines in multiline tasks remain cleanly aligned.
- **Physical Page Count & Layout Refinement**: Fixed `pagenum_reset` page counting (accurate total page count across counter resets via `<doc-end>`) and decoupled cover page detection (`<cover-page>`) from page number checks.
- **Header & Footer Controls**: `document.header` and `document.footer` configuration flags are now wired directly into `setup-document` in Typst.
- **`markpublish labels` shows the cascade again**: The `i18n-Quelle` column names the level that supplied each text — `mpub`, `theme`, `target`, `projekt` — and highlights the ones a theme or the project overrode. The language block is appended only where it differs from the document language (`(*)`, or a fall back to English). The footer resolves the short names to full paths. `--overridden` filters for exactly those overrides again — it had come to mean "hide what the theme does not read".
- **`markpublish labels` summary**: Warnings are counted and reported; the all-clear line appears only when there is genuinely nothing to report.
- **Unknown keys on `parts:` and `chapters:` are rejected**: Both accepted any field and dropped it — including `break_befor` instead of `break_before`, which silently set the chapter with the default break. Unknown keys now abort with the closest declared name as a suggestion. Free fields remain available under `document:`, where they reach the theme.
- **`markpublish init` names the document after its folder**: Without `--title`, the new project is titled after the target directory (`markpublish init mein-dokument` → `mein-dokument`, built as `mein-dokument.pdf`) instead of the fixed placeholder `New Document`. The folder name is the one thing the user has already named at that point; a placeholder was wrong in nearly every project and surfaced late — not only on the cover, but in the output file name. `--title` still wins, and only a drive root (where the directory has no name) falls back to `New Document`.
- **`init` refuses a target that is not empty**: A directory that already holds files aborts the run, naming the path, instead of quietly writing past whatever is there. Scattering a configuration and a chapter into an existing project is superfluous at best and the silent loss of a file of the same name at worst; the way out is a different directory, not a switch that permits the loss. An existing but empty directory is fine — nothing can be lost there.
- **`init` hands you the build command that actually works**: The closing hint now names the configuration just created — `markpublish build Test\markpublish.yaml` instead of a bare `markpublish build`, which looks for a markpublish.yaml in the working directory and, after `init <folder>`, finds the wrong one or none at all. A path containing spaces comes quoted; initializing the working directory itself keeps the short form.
- **A second placeholder in the scaffold, `{dir}`**: the target folder, which is what the commands in the welcome chapter need (`cd Test`), while `{title}` stays the document title. The two part ways as soon as `--title` is given, and the welcome chapter used to print the title as a folder name.
- **The scaffold explains itself**: the generated `markpublish.yaml` now carries comments on every key it sets, shows the most useful optional ones commented out with their defaults, and opens the chapter with a divider page (`break_before: "divider"` plus `show_title: false`, so the heading does not appear twice).
- **The `init` scaffold costs no divider page**: Its single part brackets its single chapter and takes no page of its own — the generated configuration does not notate `break_before` on the part at all and relies on the new default (the chapter below it notates one on purpose). What the scaffold *shows* remains a matter of taste and stays in the template; what it *structures* does not.
- **`build_manuals.py` selects languages with `--lang`**: `de,en` by default, `all` for every shipped translation, and the summary marks which documents this run actually wrote — a file it did not touch is reported as unchanged instead of passing for current.
- **Streamlined CI/CD Matrix**: Completely removed Pango, GTK, Homebrew, and MSYS2 pacman installation steps from `.github/workflows/ci.yml` and `release.yml`, resulting in fast, portable wheel-based CI across Ubuntu, macOS, and Windows.

### Fixed
- **Nested sub-chapters are validated**: `chapters:` inside a chapter was carried along as an undeclared extra, so its contents passed unchecked — a typo in a sub-chapter reached nothing and was reported nowhere. It is now a declared field, validated recursively like the top level.
- **A code sample is no longer read as a call**: The theme-contract check scanned the whole generated Typst source, so a ```` ```typst ```` block in a chapter — the manual has one showing `setup-document(...)` — was taken for a real call and produced phantom "undeclared parameter" errors. Raw blocks are now excluded.
- **"1 Dokumente aktualisiert"**: `build_manuals.py` counted in a single plural form, so a run that wrote one document reported it in the plural. Counted messages now carry `.one` and `.other` forms and are selected through `tn()`.
- **Headings no longer stand alone at the foot of a page**: A heading whose text began on the next page is now carried over with it. Typst's built-in heading is a sticky block, but the default theme's `show heading:` rule replaces that output and so had to reproduce the property by hand. The heading text now sits in `block(..., sticky: true)` — placed inside `text(...)` and taking `above`/`below` from `par.spacing`, so every spacing value stays where it was: as a paragraph in the flow the heading carried its own paragraph spacing, resolved at the heading's font size (1.5em is 27pt at 18pt, not 15pt). Measured across the manual, all heading positions are unchanged down to the first affected page; six orphaned headings are resolved and the document grows by the one page that content displaces.

### Removed
- **WeasyPrint & GTK Dependencies**: Removed `weasyprint`, `cffi`, and native GTK runtime installers.
- **Obsolete Fontconfig Configuration**: Deleted `src/markpublish/data/fonts.conf`.
- **HTML Output Pipeline**: Temporarily removed HTML output rendering (`--target html`) and HTML Jinja2 templates to concentrate fully on top-quality Typst PDF publishing. The `--target` switch informs the user gracefully.
- **`label_overview()` / `LabelUsage`**: Superseded by `diagnose_labels_and_metadata()`, which the CLI actually uses.
- **Legacy parameter detection in the theme contract**: The heuristic that guessed which core fields a theme set through its own parameters is gone with the parameters themselves.

---

## [1.0.0] - 2026-09-01

### Added
- **Multi-Format Publishing Pipeline**: Modular compilation from Markdown to print-ready **PDF** (via WeasyPrint & W3C CSS Paged Media) and standalone **HTML**.
- **Declarative YAML Configuration (`markpublish.yaml`)**:
  - Global metadata (`title`, `subtitle`, `author`, `date`, `version`, `language`, `status`, `copyright`).
  - Layout controls: `cover`, `header`, `footer`, `document_toc`, `part_toc`, `chapter_toc`.
  - Numbering controls: `autonum_style`, `autonum_from_level`, `autonum_prefix`, `autonum_reset`, and `pagenum_reset`.
  - Two-tier document structure: **Parts** (`parts:`) divide the document, chapters (`chapters:`) beneath them carry the content; depth inside a chapter comes from its own headings.
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
  - `build_manuals.py`: One command builds all four showcase documents — German and English, PDF and HTML — into `manual/`.

