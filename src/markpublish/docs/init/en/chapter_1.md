# Welcome to markpublish

Congratulations, your new markpublish project is ready.

The project follows a clean two-tier architecture: `markpublish.yaml` manages document structure, metadata, and styling, while Markdown files provide your actual content.

## Building the PDF

Switch to your new project directory and compile the document:

```bash
cd {dir}
markpublish build
```

markpublish transforms your Markdown via a high-performance Typst pipeline into a print-ready PDF.

## Chapter Structure

Your project is preconfigured with two starter chapters (`chapter_1.md` and `chapter_2.md`):

```yaml
parts:
  - part: "Main Part"
    chapters:
      - file: "chapter_1.md"
        break_before: "divider"
        show_title: false
      - file: "chapter_2.md"
        break_before: "divider"
        show_title: false
```

To add more chapters, create a new `.md` file and list its path under `chapters:`.

## Documentation & Reference

markpublish includes built-in reference guides accessible straight from your terminal:

```bash
markpublish cheatsheet    # Compact cheat sheet covering all YAML configuration keys
markpublish manual        # Comprehensive official user manual
```
