# Project Report: Digital Publishing Pipelines

The automated production of high-quality technical documentation is a vital requirement for modern software engineering teams. Traditional publication toolchains often lead to fragmented source repositories, inconsistent typography, and significant manual post-processing. This report outlines the experience and performance gains achieved by introducing a unified publication pipeline powered by **markpublish**.

## Background and Motivation

In distributed software projects, architectural documentation, operation manuals, and project reports are authored organically in Markdown. Previous conversion approaches relying on heavyweight LaTeX toolchains or browser-based HTML-to-PDF converters exhibited notable shortcomings:

- **Inconsistent Typesetting:** Fragile page breaks, inaccurate hyphenation rules, and missing font metrics.
- **Heavyweight Dependencies:** Containerized environments exceeding 2 GB in download size and high execution latency.
- **Fragmented Metadata:** Lack of a centralized manifest for document metadata, version tracking, and cover page layout.

> [!NOTE]
> The primary objective was establishing a lightweight, cross-platform publishing pipeline capable of compiling reproducible, print-ready PDFs directly from Git repositories without external binary dependencies.

## Solution Comparison and Evaluation

During a four-week benchmark evaluation, three common document production workflows were analyzed against key operational criteria:

| Evaluation Criterion | Office Export | LaTeX / Pandoc | markpublish (Typst) |
| :--- | :--- | :--- | :--- |
| **Version Control (Git)** | Inadequate (binary diffs) | Excellent (plain text) | Optimal (Markdown & YAML) |
| **Compilation Latency** | Manual / Slow | Moderate (multiple passes) | Sub-second (< 1s) |
| **Setup Overhead** | Proprietary suite | High (> 2 GB toolchain) | Minimal (`pip install markpublish`) |
| **Typography Standard** | Variable / Inconsistent | High, but complex | Publication-grade & deterministic |
| **CI/CD Integration** | Complex workarounds | Well-established | Native and lightweight |

The empirical findings confirmed that combining a native Typst typesetting engine with a structured Markdown workflow significantly accelerates document delivery and guarantees typographic consistency.

## Architectural Pillars

Three core architectural conventions were established across the project:

### Separation of Concerns
All presentation rules, chapter sequences, and document metadata reside exclusively in `markpublish.yaml`. Markdown files focus entirely on semantic content without inline styling hacks.

### Deterministic Rendering
By bundling standard typefaces (`Open Sans`) directly within the default theme, page layouts and line wraps remain completely identical across Windows, macOS, and Linux CI runners.

### Continuous Quality Verification
Every documentation update submitted via pull request triggers automated schema validation and PDF compilation. Artifacts are only approved when all automated checks succeed.

## Conclusion and Roadmap

Adopting **markpublish** decreased document maintenance overhead by over 60 percent. Engineering teams benefit from familiar Markdown syntax, while stakeholders receive polished, publication-ready reports. Future milestones include integrating automated nightly builds for central technical documentation repositories.
