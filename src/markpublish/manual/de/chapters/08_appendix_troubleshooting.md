# Anhang B: Fehlerbehebung & FAQ

Häufige Fragen und Lösungen bei der Dokumentenerstellung.

## WeasyPrint & GTK-Laufzeitumgebung auf Windows

### Problem: `cannot load library 'libgobject-2.0-0'`
WeasyPrint benötigt auf Windows-Systemen die nativen C-Bibliotheken von Pango und GTK.

**Lösung**:
`markpublish` sucht automatisch nach installierten GTK-Umgebungen (wie MSYS2, GTK3-Runtime, darktable oder Inkscape). Sollten diese fehlen, installieren Sie das offizielle GTK3-Runtime-Paket:
- Download: [GTK-for-Windows-Runtime-Environment-Installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer)
- Alternativ via MSYS2: `pacman -S mingw-w64-x86_64-pango`

## Bilder werden im PDF nicht angezeigt

### Problem: Leere Bildrahmen oder fehlende Grafiken
WeasyPrint benötigt gültige relative Pfade oder absolute File-URIs.

**Lösung**:
Geben Sie relative Bildpfade immer relativ zur jeweiligen Markdown-Datei an:
```markdown
![Architekturdiagramm](images/architecture.png)
```
`markpublish` löst relative Pfade automatisch zu absoluten Datei-URIs auf.

## Inhaltsverzeichnis zeigt falsche Seitenzahlen

Das PDF-Rendering erfolgt in mehreren Layout-Durchläufen (Zweipass-Rendering von WeasyPrint). Stellen Sie sicher, dass alle internen Überschriften-IDs eindeutig sind – `markpublish` übernimmt diese Eindeutigkeit automatisch über seinen internen Slug-Generator.

