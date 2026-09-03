# Nächste Schritte

Dieses Projekt besteht aus zwei Dateien: `markpublish.yaml` und diesem Kapitel.
Ersetzen Sie beide durch Ihren eigenen Inhalt -- sobald Sie schreiben, wird der
Inhalt dieser Datei nicht mehr benötigt.

## PDF erstellen

```bash
markpublish build                 # PDF via Typst erstellen
```

## Nachschlagen

```bash
markpublish cheatsheet
```

Erstellt eine kompakte zweiseitige Referenz: alle Schlüssel der `markpublish.yaml`
auf Seite 1, Themes und Vorlagen auf Seite 2.

## Weitere Kapitel hinzufügen

Erstellen Sie eine neue Markdown-Datei und tragen Sie sie unter `chapters:` in der
`markpublish.yaml` ein. Pfade gelten relativ zur Konfigurationsdatei:

```yaml
parts:
  - part: "Hauptteil"
    break_before: "none"
    chapters:
      - file: "next-steps.md"
      - file: "chapters/01_einleitung.md"
```

Ein Dokument besitzt immer zwei Ebenen: `parts:` gliedert, `chapters:` trägt den Inhalt.

## Design und Theme anpassen

```bash
markpublish export-template default ./templates
```

Kopiert das Standard-Theme in Ihr Projekt, wo markpublish es beim nächsten Build
automatisch aufgreift.

