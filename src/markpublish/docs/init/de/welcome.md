# Willkommen bei markpublish

Herzlichen Glückwunsch, Sie haben Ihr neues markpublish-Projekt initialisiert.

Es besteht aus zwei Dateien: `markpublish.yaml` und diesem Kapitel.

## PDF erstellen

Zum Test der PDF-Erstellung:

```bash
cd {title}
markpublish build                       # PDF erstellen
```

## Nachschlagen

Sie können mit markpublish das Handbuch und eine Schnellreferenz direkt über die Kommandozeile erstellen lassen:

```bash
markpublish cheatsheet                  # Kompakte Schnellreferenz ausgeben
markpublish manual                      # Ausführliches Benutzerhandbuch ausgeben
```

Erstellt eine übersichtliche Referenzkarte aller Konfigurationsschlüssel, Themes
und Vorlagen bzw. das ausführliche Benutzerhandbuch als PDF.

## Weitere Kapitel hinzufügen

Erstellen Sie eine neue Markdown-Datei und tragen Sie sie unter `chapters:` in der
`markpublish.yaml` einen weiteren `file:`-Parameter ein. Pfade gelten relativ zur Konfigurationsdatei:

```yaml
parts:
  - part: "Hauptteil"
    break_before: "none"
    chapters:
      - file: "next-steps.md"
      - file: "ihre_md_datei.md"
```

Ein Dokument besitzt immer zwei Ebenen: `parts:` gliedert, `chapters:` trägt den Inhalt.

## Design und Theme anpassen

```bash
markpublish export-template default ./templates
```

Kopiert das Standard-Theme in Ihr Projekt, wo markpublish es beim nächsten Build
automatisch aufgreift.

