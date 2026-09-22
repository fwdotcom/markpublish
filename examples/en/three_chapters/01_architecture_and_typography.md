# Foundations & Typography

A publication-grade typesetting system relieves authors of tedious layout decisions while maintaining uncompromising aesthetic and structural precision. **markpublish** bridges the gap between universal, readable Markdown syntax and the typographic fidelity of modern book printing.

## Separation of Presentation and Content

In technical documentation engineering, decoupling semantic text from styling logic is crucial for long-term maintainability. When formatting commands are interspersed within prose, reuse decreases and automated verification becomes difficult[^1].

[^1]: See also the guidelines on digital accessibility and structured information architecture under ISO/IEC 26514.

Systems like markpublish implement this separation through two core pillars:

1. **Semantic Sources:** Authors write standard Markdown files (`.md`) utilizing structured elements such as sections, bulleted lists, blockquotes, and tables.
2. **Declarative Manifest:** A central configuration file (`markpublish.yaml`) defines global page geometry, margins, typographic scale, running headers, and chapter ordering.

> [!NOTE]
> Centralizing design logic in the theme and manifest keeps source text entirely portable. The exact same source tree can be rendered as a technical whitepaper, an internal specification, or an interactive web publication without modifying content files.

## Microtypography and Layout Geometry

Superior typesetting relies on consistent visual rhythm and balanced typographic color. The underlying Typst engine computes line wraps using dynamic optimization algorithms that eliminate orphans and widows across page breaks.

Key architectural concepts include:

AST (Abstract Syntax Tree)
: The hierarchical structural tree into which incoming Markdown elements are parsed before being translated into Typst layout primitives.

Page Geometry
: The deliberate ratio between the printed text block and surrounding white margins, calculated according to classic European book design proportions.

Running Headers
: Dynamic header and footer elements indicating the active document title, section group, and page numbers on alternating recto and verso pages.

> [!TIP]
> The default theme bundles the complete `Open Sans` font family (Regular, Italic, SemiBold, and Bold) directly within the package distribution, ensuring identical line wrapping and page pagination on every operating system.

### Heading Hierarchy Conventions

Headings not only provide visual pacing, but also define a navigable structural tree. markpublish automatically synchronizes heading numbering across all levels with the document table of contents and any localized chapter navigation. Manual numbering in Markdown source text is therefore unnecessary and discouraged.

