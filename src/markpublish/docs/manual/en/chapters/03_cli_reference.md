# Command-Line Interface (CLI)

The command-line interface is the primary way to interact with markpublish. In addition to the main `markpublish` command, the shorthand alias `mpub` is available.

## Command Overview

| Command | Summary |
| :--- | :--- |
| `build` | Compiles the document based on the configuration file. |
| `init` | Creates a new project with a configuration file and starter chapter. |
| `manual` | Renders the official user manual from the installed package. |
| `cheatsheet` | Renders the compact two-page quick reference from the package. |
| `templates` | Lists all available templates and their origin layers. |
| `export-template` | Exports the default theme into the project for customization. |
| `labels` | Shows all resolved text labels and their origin layer in the i18n cascade. |

---

## markpublish build

The `build` command runs the publishing pipeline. It loads the configuration, processes all chapter Markdown files, and compiles the final document.

```bash
markpublish build [CONFIG_FILE] [OPTIONS]
```

### Options

| Option | Default | Description |
| :--- | :--- | :--- |
| `CONFIG_FILE` *(Argument)* | `markpublish.yaml` | Path to the project configuration file. |
| `--target`, `-t` | `pdf` | Output format (`pdf`). |
| `--output`, `-o` | *(automatic)* | Path to output file or destination directory. If the path has no file extension, it is treated as a directory. |
| `--theme` | `None` | Renders with an alternative theme instead of the one specified in the configuration. |
| `--templates-dir` | `None` | Path to a custom templates directory. |

### Details

Without arguments, markpublish looks for `markpublish.yaml` in the current working directory – inside a project folder, running `markpublish build` is sufficient. If a custom path is specified, its directory is treated as the project root: all relative paths in the configuration (chapter files, images, templates) are resolved from that directory, not from your current working directory.

If `--output` is omitted, markpublish writes the file into the project folder. The output filename is derived automatically from the document title (e.g., `my_document.pdf`).

`--templates-dir` expects the container directory, not an individual theme folder. Which theme is used is determined either by the `--theme` command-line option or by `theme:` in `markpublish.yaml` (default: `default`). markpublish combines both settings and looks for `<directory>/<theme>/<target>`:

```text
my-templates/           <- pointed to by --templates-dir
└── corporate/          <- named by theme: in markpublish.yaml
    └── pdf/            <- target format
        ├── template.typ
        └── i18n.yaml
```

The corresponding command is:

```bash
markpublish build --templates-dir my-templates
```

A relative path is resolved relative to the project directory. The same directory can also be configured permanently; markpublish checks these locations in order:

1. `--templates-dir` on the command line
2. `templates_dir:` in `markpublish.yaml`
3. The environment variable `MARKPUBLISH_TEMPLATES_DIR`
4. A `templates/` folder next to the configuration file

The directory determined this way is only one of three tiers searched by markpublish; a template with the same name in your user home directory still takes precedence (see chapter *Theme System and Internationalization*).

Examples:

```bash
# Standard build in current project
markpublish build

# Build with an alternative theme (overrides markpublish.yaml)
markpublish build --theme custom-theme

# Specify custom configuration file and output directory
markpublish build projects/report.yaml --output dist/
```

---

## markpublish init

The `init` command scaffolds a new project quickly. It creates the destination folder (if not yet present), a runnable `markpublish.yaml`, and an initial Markdown chapter.

```bash
markpublish init [DEST_DIR] [OPTIONS]
```

### Options

| Option | Default | Description |
| :--- | :--- | :--- |
| `DEST_DIR` *(Argument)* | `.` *(current directory)* | Target directory in which the project should be initialized. |
| `--title`, `-t` | *(Destination folder name)* | Document title written into the generated configuration. |
| `--lang`, `-l` | *(System language)* | Language of the project template (`en`, `de`). |

### Details

The generated `markpublish.yaml` and starter chapter are copied from built-in templates. You can specify the template language explicitly with `--lang` (e.g., `--lang en`); without this flag, your system language is detected automatically, ensuring the project compiles consistently on any machine.

If the target directory already exists and contains files, `init` aborts with an error message. An existing directory is never overwritten silently; to reinitialize, choose a new directory name or make sure the folder is empty.

Example:

```bash
markpublish init my-manual --lang en --title "System X User Guide"
```

---

## markpublish manual / markpublish cheatsheet

markpublish packages its complete documentation directly within the software. Both commands compile documentation on-demand from the installed package sources – the generated document always reflects the exact installed version.

* `markpublish manual`: Renders this comprehensive user manual.

* `markpublish cheatsheet`: Renders a compact two-page reference.

```bash
markpublish manual [OPTIONS]
markpublish cheatsheet [OPTIONS]
```

### Options

| Option | Default | Description |
| :--- | :--- | :--- |
| `--lang`, `-l` | *(System language)* | Document language (`en`, `de`). |
| `--target`, `-t` | `pdf` | Output format (`pdf`). |
| `--output`, `-o` | `.` *(current directory)* | Output destination path. |
| `--theme` | `None` | Renders with an alternative theme instead of the default theme. |
| `--templates-dir` | `None` | Path to a custom templates directory. |

### Details

If no `--lang` option is provided, markpublish detects your operating system language. If no translation exists for that language, markpublish falls back to the document's default language.

Example:

```bash
# Render the English user manual in the current directory
markpublish manual --lang en

# Render the German cheat sheet
markpublish cheatsheet --lang de
```

---

## markpublish templates

Lists all templates available across your system and project, clearly indicating precedence when multiple templates share the same name.

```bash
markpublish templates [OPTIONS]
```

### Options

| Option | Default | Description |
| :--- | :--- | :--- |
| `--target`, `-t` | `None` | Filters the list by output format (`pdf`). |
| `--templates-dir` | `None` | Additional template search directory. |

### Details

Outputs a structured table showing the theme name, origin layer (User, Common, or Package), and a status indicator showing which theme would be activated during a build.

---

## markpublish export-template

Exports a packaged theme into a local directory so it can be customized or used as the foundation for your own corporate design.

```bash
markpublish export-template [THEME] [DEST_DIR] [OPTIONS]
```

### Options

| Option | Default | Description |
| :--- | :--- | :--- |
| `THEME` *(Argument)* | `default` | Name of the theme to export. |
| `DEST_DIR` *(Argument)* | `templates` | Destination directory for exported template files. |
| `--target`, `-t` | `all` | Target format to export (`pdf` or `all`). |

### Details

During export, the Typst template files (`template.typ`) and the accompanying `i18n.yaml` label file are copied into the target directory. When a theme is located inside the project's `templates/` directory, markpublish automatically picks it up during builds.

Example:

```bash
# Export the default theme into the local ./templates directory
markpublish export-template default ./templates
```

---

## markpublish labels

Displays a detailed report of all static text labels (such as "Table of Contents", "Chapter", "Page X of Y") for the project's selected document language, along with their resolution layer in the cascade.

```bash
markpublish labels [CONFIG_FILE] [OPTIONS]
```

### Options

| Option | Default | Description |
| :--- | :--- | :--- |
| `CONFIG_FILE` *(Argument)* | `markpublish.yaml` | Path to the project configuration file. |
| `--target`, `-t` | `pdf` | Target format whose label cascade should be inspected. |
| `--theme` | `None` | Inspects the label cascade for an alternative theme. |
| `--templates-dir` | `None` | Custom templates directory. |
| `--overridden` | `False` | Displays only labels that have been overridden by a theme or project layer. |

### Details

This command is the primary diagnostic tool when developing themes or configuring documents. Before running a build, it verifies that all metadata fields, text labels, and theme function signatures match up completely.

The report is structured into eight columns:

| Column | Description |
| :--- | :--- |
| **Key** | Name of the metadata or text label key (e.g., `title`, `author`, `toc_title`, or custom fields like `department`). |
| **Theme Usage** | How the theme references this key: `key` (as a label identifier), `value` (as content value), `key/value` (both), or `-` (unused by theme). |
| **Label** | Resolved text string from the i18n cascade for this key. Missing required labels are highlighted in red. |
| **i18n Source** | Cascade layer providing the label (`mpub`, `theme`, `target`, `project`). Layers that override defaults are highlighted in green. |
| **Label Fallback** | Fallback text defined inside the theme if the label does not exist in any i18n layer. |
| **Value** | Content value defined in the document configuration (`document:`). |
| **Value Fallback** | Fallback value defined in the theme if the field is omitted in the document. |
| **Status** | Diagnostic assessment: `OK`, `unused`, `Missing label`, `Value not set`, or critical errors in red that would prevent compilation. |

The identifiers in the **i18n Source** column represent:

| Value | Source File |
| :--- | :--- |
| `mpub` | Built-in package default, `markpublish/i18n.yaml` |
| `theme` | `<theme>/i18n.yaml` |
| `target` | `<theme>/<target>/i18n.yaml` |
| `project` | `i18n.yaml` placed next to your `markpublish.yaml` |

Green highlights mark layers that define custom values compared to the package default – the `--overridden` flag limits the output to these rows. Rows that would cause a build failure always remain visible: a filter that hides fatal errors would defeat diagnostic safety.

Language codes appear in parentheses only when they deviate from the active document language: `(*)` denotes a language-independent key, while `(en)` indicates a fallback language resolution. At the bottom of the output, full paths to all four cascade layers are displayed along with their availability status.

**Pre-Build Signature Validation and Summary:**  
`markpublish labels` also validates the theme's Typst template directly against the parameter call markpublish will execute during rendering. If the theme fails to declare required parameters (such as `meta: (:)`), `labels` reports the signature error immediately. A summary at the bottom of the output provides a clean tally of fatal errors, warnings, and unused fields.

---

## Global Options and Environment Variables

The following options and environment variables control markpublish globally:

| Option / Variable | Description |
| :--- | :--- |
| `--version`, `-v` | Prints the installed version of markpublish and exits. |
| `--help` | Displays built-in CLI help and option summaries in the terminal. |
| `--ui-lang` | Interface language for terminal output during this invocation (`en`, `de`). |
| `MARKPUBLISH_UI_LANG` | Environment variable to permanently set the terminal interface language. |
| `MARKPUBLISH_TEMPLATES_DIR` | Environment variable pointing to a global custom templates directory. |

markpublish resolves the user interface language in the following order of precedence:
1. The `--ui-lang` CLI option
2. The `MARKPUBLISH_UI_LANG` environment variable
3. The operating system's UI language (Windows display language or POSIX variables `LC_ALL`, `LANG`)
4. English (`en`) as the default fallback

*(Note: The interface language controls only terminal messages and CLI help. The typesetting language, hyphenation, and date formatting of the generated PDF document are controlled completely independently by `language:` in `markpublish.yaml`.)*

```bash
# Force terminal output to English for this command
markpublish --ui-lang en build
```

