# Installation & Quickstart

This chapter shows how to install `markpublish` and compile your first document in under two minutes.

## Requirements

`markpublish` needs **Python 3.10 or newer**. It runs natively on:
- **Windows** (10, 11, Server)
- **macOS** (Intel and Apple Silicon)
- **Linux** (Debian, Ubuntu, Fedora, Arch, …)

## Installing with pip

Install the package with the Python package manager:

```bash
pip install markpublish
```

For development, or to install from source:

```bash
git clone https://github.com/frankwinter/markpublish.git
cd markpublish
pip install -e ".[dev]"
```

## Initialising your first project

Use the `init` command to create a new document:

```bash
markpublish init my-guide --title "My Guide"
cd my-guide
```

It creates a deliberately minimal stub — two files, directly in the directory:

```
my-guide/
├── markpublish.yaml          # The document manifest
└── next-steps.md             # One chapter, meant to be replaced
```

## Looking things up

```bash
# two-page reference card
markpublish cheatsheet [--lang de|en]

# this guide
markpublish manual [--lang de|en]
```

Both are rendered from sources shipped inside the package, so they always match the version you have installed. A successful run also confirms that the rendering toolchain works — on Windows, that WeasyPrint found its GTK runtime.

Without `--lang` your system language decides; where no translation exists, the English one appears. The parameter selects the **source**, not merely the interface labels.

## Building the document

Render with the `build` command:

```bash
# Build a PDF from the current project directory
markpublish build

# Produce the HTML output
markpublish build --target html

# Build both in one pass
markpublish build --target all
```

The finished files are written next to the manifest.
