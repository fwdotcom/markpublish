# Installation and Quickstart

This chapter outlines the fastest path from installation to your first rendered PDF document.

## Prerequisites

markpublish requires a standard Python environment:

* **Python version:** 3.10 or newer

* **Operating system:** Windows, macOS, or Linux

## Installation

Install markpublish via Python's package manager `pip`:

```bash
pip install markpublish
```

After installation, the `markpublish` command (along with the shorthand alias `mpub`) is ready in your terminal. You can verify the installation by checking the version:

```bash
markpublish --version
```

## Steps to Your First Build

Setting up a new document project takes just a few quick steps:

### Initialize a New Project

The `init` command creates a new project directory with a minimal, runnable starter template:

```bash
markpublish init my-document
```

If the specified directory already exists and is not empty, `init` safely aborts to prevent accidental overwriting of existing files.

This command creates a folder named `my-document/` with the following structure:

```text
my-document/
├── markpublish.yaml
└── welcome.md
```

### Build Your First PDF

You can build the PDF directly from the parent directory by passing the path to the configuration file (which `init` displays as a recommendation upon completion):

```bash
markpublish build my-document/markpublish.yaml
```

Alternatively, switch into the newly created folder and trigger the build there:

```bash
cd my-document
markpublish build
```

markpublish parses `markpublish.yaml`, processes all referenced Markdown files, and compiles the document.

### Open the Document

The generated PDF is placed directly inside your project folder:

```text
my-document/
└── my_document.pdf
```

*(Note: The output filename is automatically derived from the document title configured in `markpublish.yaml` – spaces and hyphens are converted to underscores. Without `--title`, the new project takes the directory name, so `my-document` becomes `my_document.pdf`.)*

Open the file in any PDF viewer to inspect the result. The document features the formatted starter chapter complete with header, footer, and typographic styling.

