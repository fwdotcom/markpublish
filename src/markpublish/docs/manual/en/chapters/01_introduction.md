# Introduction

## Motivation and Objectives

Markdown is the leading format for technical documentation, notes, and project reports. Its strength lies in simplicity and readability in plain text. However, when these texts need to be turned into high-quality, print-ready reports, manuals, or whitepapers, traditional tools quickly reach their limits. Authors often face time-consuming manual post-processing in word processing or desktop publishing software.

**markpublish** closes this gap: it automatically transforms structured Markdown files via a simple yet powerful configuration into typographically refined, professionally designed PDF documents.

The goal of markpublish is to provide developers, technical writers, and authors with a seamless publishing workflow. Content is written in plain Markdown, while markpublish takes full control over layout, document structure, divider pages, numbering, tables of contents, and typography.

## Core Features

markpublish focuses on document quality, speed, and reliability:

* **Modern Typesetting Quality with Typst:** Powered by the innovative Typst typesetting engine, documents feature outstanding typographical precision, balanced margins, and aesthetic layouts.

* **Blazing Compilation Speed:** Even comprehensive documents with dozens of pages, illustrations, and tables compile in about one to two seconds.

* **Simple Installation and Portability:** As a standard Python package, markpublish runs cross-platform on Windows, macOS, and Linux without complicated dependencies.

* **Declarative Configuration:** A single file (`markpublish.yaml`) controls the entire publishing project.

* **Multi-Tier Document Architecture:** Clear distinction between high-level sections (*Parts*) and content chapters (*Chapters*) with flexible divider page control.

* **Precise Tables of Contents and Numbering:** Fully automated generation of document-wide, part-level, and chapter-level tables of contents, alongside customizable chapter and heading numbering.

* **Comprehensive Markdown Extensions:** Built-in support for GitHub-style callout boxes (admonitions), tables, definition lists, footnotes, task lists, and syntax-highlighted code blocks.

* **Cascading Internationalization (i18n):** Integrated support for multilingual documents and themes (static text labels such as Table of Contents, Chapter, page numbers) through a four-tier cascade. Furthermore, the command-line interface (CLI) is fully bilingual (English and German) and automatically adapts to your operating system's language.

## Architecture Overview

markpublish operates along a clean processing pipeline:

1. **Configuration and Document Analysis:** markpublish reads `markpublish.yaml`, validates all settings, and constructs the hierarchy of parts and chapters.

2. **Content Processing:** Chapter Markdown files are parsed via an ElementTree AST pipeline and converted directly into clean Typst markup by a native Typst serializer (`TypstSerializer`). Headings and tables of contents are synchronized at the AST level, link targets are resolved, and local image paths are automatically isolated for the build.

3. **Template Assembly:** The selected theme (by default the built-in standard theme) provides layout definitions. Document metadata (packaged in a typed `meta` dictionary), headers, footers, divider pages, and body content are mapped directly into the Typst environment.

4. **PDF Compilation:** The Typst engine compiles the assembled document directly into a finished PDF file in a single, highly efficient run. If an error occurs, the generated Typst source code is saved to `.markpublish/last_failed_build.typ` for immediate debugging.

