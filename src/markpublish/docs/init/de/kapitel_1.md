# Willkommen bei markpublish

Herzlichen Glückwunsch, Ihr neues markpublish-Projekt ist eingerichtet.

Das Projekt folgt einem zweistufigen Aufbau: In der Konfigurationsdatei `markpublish.yaml` definieren Sie Metadaten, Theme und Gliederung, während die Markdown-Dateien den Inhalt tragen.

## Erstes PDF erstellen

Wechseln Sie in das Projektverzeichnis und starten Sie die Kompilierung:

```bash
cd {dir}
markpublish build
```

markpublish übersetzt Ihre Inhalte über eine Typst-Pipeline direkt in ein druckreifes PDF-Dokument.

## Kapitelstruktur

Ihr Dokument ist bereits mit zwei Beispielkapiteln (`kapitel_1.md` und `kapitel_2.md`) vorkonfiguriert:

```yaml
parts:
  - part: "Hauptteil"
    chapters:
      - file: "kapitel_1.md"
        break_before: "divider"
        show_title: false
      - file: "kapitel_2.md"
        break_before: "divider"
        show_title: false
```

Weitere Kapitel fügen Sie hinzu, indem Sie eine neue `.md`-Datei anlegen und diese unter `chapters:` eintragen.

## Dokumentation und Nachschlagen

markpublish bringt integrierte Referenzdokumente mit, die Sie direkt über das Terminal aufrufen können:

```bash
markpublish cheatsheet    # Kompakte Schnellreferenz zu allen YAML-Schlüsseln
markpublish manual        # Ausführliches offizielles Benutzerhandbuch
```
