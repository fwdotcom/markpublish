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
git clone https://github.com/your-username/markpublish.git
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

There is no sample content beyond that, because everything `init` writes is material you delete as soon as you start writing. The reference lives in `markpublish cheatsheet` instead, which stays available after the last scaffold file is gone.

## Looking things up

```bash
markpublish cheatsheet         # two-page reference card
markpublish manual             # this guide
```

Both are rendered from sources shipped inside the package, so they always match the version you have installed. A successful run also confirms that the rendering toolchain works — on Windows, that WeasyPrint found its GTK runtime.

## Building the document

Render with the `build` command:

```bash
# Build PDF (default)
markpublish build

# Build a standalone HTML preview
markpublish build --target html

# Build both in one pass
markpublish build --target all
```

The finished files are written next to the manifest.
