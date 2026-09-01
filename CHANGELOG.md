# Changelog

All notable changes to **markpublish** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

