# Introduction & Architecture

Welcome to the **markpublish User Guide**. `markpublish` is a modern, open-source publishing tool that turns plain Markdown files into professionally typeset **PDF publications** and **HTML previews**.

## Motivation & Goals

Most documentation tools either demand a complex LaTeX setup or stop at plain HTML pages. `markpublish` combines the simplicity of Markdown with the typographic precision of **CSS Paged Media** through the [WeasyPrint](https://weasyprint.org/) engine.

### Key benefits at a glance:
- **Modular chapters**: every chapter lives in its own Markdown file.
- **Hierarchical structure**: sub-chapters nest to any depth, with overarching sections (*parts*) above them.
- **Declarative control**: one manifest (`markpublish.yaml`) governs content, metadata and layout.
- **W3C CSS Paged Media**: exact control over `@page` margins, multi-line running headers and footers, page numbers and divider pages.
- **Extensible pipeline**: a clean separation between parser, renderer and template layers.

## The Processing Pipeline

The architecture of `markpublish` follows a staged process:

1. **Configuration loader (`config.loader`)**: reads the YAML structure, validates data types and resolves dynamic values (for example `date: auto`).
2. **Template resolver (`templates.resolver`)**: finds the theme for the target format along a three-level priority (*user* > *common/workspace* > *package*).
3. **Markdown & TOC engine (`markdown.engine`)**: parses Markdown with extended features (callouts, tables, Pygments syntax highlighting), assigns consistent heading numbers (`1.1`, `1.2`) and builds the tables of contents.
4. **Renderers (`renderers.pdf` & `renderers.html`)**: hand the rendered HTML and CSS to WeasyPrint for PDF export, or write standalone, responsive HTML.
