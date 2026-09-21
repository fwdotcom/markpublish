# Introduction & System Architecture

markpublish transforms structured Markdown files into publication-grade documents. Structure, metadata, and styling are governed centrally in `markpublish.yaml` — everything else remains clean prose.

> [!NOTE]
> The native Typst typesetting engine delivers book-grade printing, automatic hyphenation, and consistent typography without external LaTeX or Pandoc chains.

## Modular Structure
Documents can be organized into parts, chapters, and divider pages. Each file remains pure Markdown, while the central manifest handles chapter ordering and automatic numbering.

