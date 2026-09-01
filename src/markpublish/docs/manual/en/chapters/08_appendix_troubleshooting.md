# Appendix B: Troubleshooting & FAQ

Common questions, error messages, and fixes when producing documents.

| Issue / Error Message | Possible Cause | Solution |
| :--- | :--- | :--- |
| `cannot load library 'libgobject-2.0-0'` | WeasyPrint requires native Pango and GTK C-libraries on Windows. | Install GTK3 runtime ([GTK-Installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer)) or MSYS2: `pacman -S mingw-w64-x86_64-pango`. Quick alternative: `--target html` renders without WeasyPrint. |
| Missing graphics / empty image frames | Image path is broken or absolute instead of relative. | Always specify paths relative to the referring Markdown file (e.g. `images/diag.png`). markpublish inlines graphics up to 12 MB as data URIs. |
| Table of Contents shows wrong page numbers | Manually specified heading IDs collide during two-pass rendering. | Rely on markpublish's automatic slug generator or check custom anchors (`{#id}`). |
| `Label 'x' is used in template but defined in no i18n level` | A theme uses a static text key not defined in any `i18n.yaml` level. | Define the key in `<theme>/i18n.yaml` for all languages or under `*`. Inspect active labels with `markpublish labels`. |
| `cheatsheet` or `manual` ignores working directory theme | Built-in reference documents render with the stable default theme by default. | Use `--theme <name>` to explicitly enforce rendering in your custom theme. |

