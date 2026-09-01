# Anhang B: Fehlerbehebung & FAQ

Häufige Fragen und Lösungen bei der Dokumentenerstellung.

## WeasyPrint & GTK-Laufzeitumgebung auf Windows

### Problem: `cannot load library 'libgobject-2.0-0'`

WeasyPrint benötigt auf Windows-Systemen die nativen C-Bibliotheken von Pango und GTK.

**Lösung**:
`markpublish` sucht automatisch nach installierten GTK-Umgebungen (wie MSYS2, GTK3-Runtime, darktable oder Inkscape). Sollten diese fehlen, installieren Sie das offizielle GTK3-Runtime-Paket:

- Download: [GTK-for-Windows-Runtime-Environment-Installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer)
- Alternativ via MSYS2: `pacman -S mingw-w64-x86_64-pango`

Wenn Sie nur schnell etwas nachlesen wollen: `--target html` rendert ganz ohne WeasyPrint — auch `markpublish cheatsheet --target html` und `markpublish manual --target html`.

## Bilder werden im PDF nicht angezeigt

### Problem: Leere Bildrahmen oder fehlende Grafiken

WeasyPrint benötigt gültige relative Pfade oder absolute File-URIs.

**Lösung**:
Geben Sie relative Bildpfade immer relativ zu der Markdown-Datei an, die sie einbindet:

```markdown
![Architekturdiagramm](images/architecture.png)
```

`markpublish` bettet relative Grafiken automatisch als portable Data-URIs ein (und nutzt für Dateien über 12 MB absolute Datei-URIs).

## Inhaltsverzeichnis zeigt falsche Seitenzahlen

Das PDF-Rendering erfolgt in mehreren Layout-Durchläufen (Zweipass-Rendering von WeasyPrint). Stellen Sie sicher, dass alle internen Überschriften-IDs eindeutig sind — `markpublish` übernimmt diese Eindeutigkeit automatisch über seinen internen Slug-Generator.

## Ein Build bricht mit einem Label-Namen ab

```
Label 'imprint_title' is used in the template but defined in no i18n level.
```

Ein Theme verwendet einen statischen Text, der in keiner Ebene der i18n-Kaskade auflöst. Der Abbruch ist Absicht und die bessere Alternative zum stillen Leerstring: ein leerer Text im fertigen PDF fällt niemandem auf, ein Abbruch schon.

**Lösung**: Definieren Sie den Schlüssel in der `i18n.yaml` des Themes — unter jeder Sprache, die Sie ausliefern, oder unter `"*"`, wenn er überall gleich lauten soll. Was aktuell auflöst, zeigt `markpublish labels`.

## `markpublish cheatsheet` oder `manual` schlägt fehl, nachdem ich ein Theme bearbeitet habe

Beide Befehle rendern bewusst im mitgelieferten Theme und ignorieren ein `templates/`-Verzeichnis im Arbeitsordner — genau damit ein halbfertiges Theme die Referenz nicht mit sich reißen kann. Wer sie *doch* im eigenen Theme sehen will, verlangt das ausdrücklich mit `--theme NAME`; dann schlägt ein defektes Theme durch, was der Sinn des Nachfragens ist.
