# Appendix B: Troubleshooting & FAQ

Common questions and fixes when producing documents.

## WeasyPrint & the GTK runtime on Windows

### Problem: `cannot load library 'libgobject-2.0-0'`

On Windows, WeasyPrint needs the native C libraries of Pango and GTK.

**Fix**:
`markpublish` looks for installed GTK environments automatically (MSYS2, GTK3 Runtime, darktable, Inkscape). If none is present, install the official GTK3 runtime package:

- Download: [GTK-for-Windows-Runtime-Environment-Installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer)
- Or via MSYS2: `pacman -S mingw-w64-x86_64-pango`

If you only need to read something quickly, `--target html` renders without WeasyPrint at all — including `markpublish cheatsheet --target html` and `markpublish manual --target html`.

## Images do not appear in the PDF

### Problem: empty image frames or missing graphics

WeasyPrint needs valid relative paths or absolute file URIs.

**Fix**:
Always give image paths relative to the Markdown file that references them:

```markdown
![Architecture diagram](images/architecture.png)
```

`markpublish` resolves relative paths to absolute file URIs automatically.

## The table of contents shows wrong page numbers

PDF rendering happens in several layout passes (WeasyPrint's two-pass rendering). Make sure all internal heading IDs are unique — `markpublish` guarantees this through its internal slug generator.

## A build aborts naming a label

```
Label 'imprint_title' is used in the template but defined in no i18n level.
```

A theme uses a static text that resolves in no level of the i18n cascade. This is deliberate rather than a silent empty string: an empty text in a finished PDF goes unnoticed, an abort does not.

**Fix**: define the key in the theme's `i18n.yaml`, under every language you ship, or under `"*"` if it should read the same everywhere. `markpublish labels` shows what currently resolves.

## `markpublish cheatsheet` or `manual` fails after I edited a theme

Both commands deliberately render with the built-in theme and ignore a `templates/` folder in your working directory — precisely so that a half-finished theme cannot take the reference down with it. If you *want* to see them in your own theme, ask for it explicitly with `--theme NAME`; then a broken theme will surface, which is the point of asking.
