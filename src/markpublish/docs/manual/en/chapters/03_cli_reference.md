# The CLI Commands

`markpublish` offers a small, predictable command-line interface, reachable as `markpublish` or the short form `mpub`.

## Command overview

| Command | Summary |
| :--- | :--- |
| `markpublish init` | Creates a minimal project stub (two files) |
| `markpublish cheatsheet` | Renders the two-page reference card |
| `markpublish manual` | Renders this user guide |
| `markpublish build` | Compiles a document to PDF and/or HTML |
| `markpublish templates` | Lists every template found and where it came from |
| `markpublish export-template` | Copies a template out for customisation |
| `markpublish labels` | Shows the resolved static texts and their origin |

## `markpublish init`

Creates a minimal project stub: a `markpublish.yaml` and one chapter, `next-steps.md`, both directly in the target directory. No `chapters/` folder, no sample chapters.

```bash
markpublish init [DIRECTORY] [--title "Title"]
```

The stub is deliberately small, because it exists to be deleted — at the latest when you write your first real chapter. The reference therefore does not live in the stub but in `markpublish cheatsheet`; both generated files point at it. Cover page and table of contents are switched off, because a one-page draft needs neither.

## `markpublish cheatsheet`

Renders the bundled reference card: page 1 the keys of `markpublish.yaml`, page 2 the essentials of themes and templates.

```bash
markpublish cheatsheet [--lang CODE] [--target pdf|html|all] [--output PATH] [--theme NAME]
```

## `markpublish manual`

Renders this guide.

```bash
markpublish manual [--lang CODE] [--target pdf|html|all] [--output PATH] [--theme NAME]
```

### Shared behaviour of the two document commands

Both sources ship inside the package and are rendered on every call. The result therefore always matches the version you have installed, and a successful run doubles as proof that the rendering toolchain works — on Windows, that WeasyPrint found its GTK runtime. Only the finished document is written, into the current directory; no source files ever land in your project.

| Option | Default | Notes |
| :--- | :--- | :--- |
| `--lang`, `-l` | system language | Which translation to render. `markpublish manual --lang de` |
| `--target`, `-t` | `pdf` | `pdf`, `html` or `all` |
| `--output`, `-o` | current directory | File or directory |
| `--theme` | built-in | Render with a theme of your own |

`--lang` selects the **source**, not just the labels — each translation carries its own `language:` and therefore pulls in the matching static texts by itself.

Given no language, your system decides. These two documents address the person at the keyboard rather than an audience, so their language is the best guess available. Where no translation exists, the English one appears without comment — nothing was asked for. An explicit `--lang fr`, by contrast, is reported, rather than silently wrapping an English frame around a French expectation.

Without `--theme` or `--templates-dir`, both commands deliberately ignore user and project themes and render with the built-in one. Otherwise a `templates/` folder in your working directory — created with `export-template` and still half-finished — would drag the reference down with it: one missing label would abort the build at exactly the moment somebody wants to look up how labels work.

If the PDF path is unavailable for want of GTK, `--target html` produces the same document without WeasyPrint.

## `markpublish build`

Compiles a `markpublish.yaml` configuration.

```bash
markpublish build [CONFIG_FILE] [OPTIONS]
```

### Arguments & options
- `CONFIG_FILE` *(optional, default `markpublish.yaml`)*: path to the YAML file.
- `--target / -t` *(default `pdf`)*: target format (`pdf`, `html` or `all`).
- `--output / -o`: custom output path (file or directory).
- `--templates-dir`: explicit path to a shared templates directory.

### Examples
```bash
# Default build from the current directory
markpublish build

# Write the HTML version into a specific directory
markpublish build markpublish.yaml -t html -o dist/

# Use a shared templates directory
markpublish build --templates-dir /shared/company-templates
```

> [!NOTE]
> There is no `--lang` on `build`. A document's language belongs in its own
> `markpublish.yaml`, next to `title` and `author`: it states which language the
> document is *written in*. Overriding it from the command line would only swap
> the seventeen static labels around unchanged prose.

## `markpublish templates`

Shows every template on the system in a table, together with its priority:

```bash
markpublish templates
markpublish templates --target pdf
```

## `markpublish export-template`

Copies the built-in theme into your working directory:

```bash
markpublish export-template default templates
```

## `markpublish labels`

Shows which static text applies in the end, and which level of the label cascade it came from. Useful as soon as a theme brings its own texts and it stops being obvious which level wins.

```bash
markpublish labels                          # all keys, target PDF
markpublish labels --target html            # cascade for the HTML output
markpublish labels --overridden             # only overridden texts
markpublish labels path/to/markpublish.yaml
```

### Arguments & options

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `config_file` | Path | `markpublish.yaml` | Path to the configuration file |
| `--target`, `-t` | String | `pdf` | Target format whose cascade is shown (`pdf` or `html`) |
| `--templates-dir` | Path | – | Alternative templates directory |
| `--overridden` | Flag | off | Only show texts the theme changes |

The *Source* column names the level: `i18n.yaml (en)` for the program default, or the path of a theme or target `i18n.yaml`. Below the table, markpublish lists which files were searched for overrides and which of them exist.

> [!TIP]
> `--overridden` answers the most common question directly: *what in this project
> deviates from the default at all?*
