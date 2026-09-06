# Willkommen bei markpublish

Herzlichen Glückwunsch, Sie haben Ihr neues markpublish-Projekt erstellt.

Es besteht aus zwei Dateien: `markpublish.yaml` und diesem Kapitel.

## PDF erstellen

Zum Test der PDF-Erstellung:

```bash
cd Test                              # das neu erstellte Projekt-Verzeichnis
markpublish build                       # PDF erstellen
```

## Weitere Kapitel hinzufügen

Erstellen Sie eine neue Markdown-Datei und tragen Sie sie unter `chapters:` in der
`markpublish.yaml` einen weiteren `file:`-Schlüssel ein. Pfade gelten relativ zur Konfigurationsdatei:

```yaml
parts:
  - part: "Hauptteil"
    chapters:
      - file: "welcome.md"
      - file: "ihre_neue_md_datei.md"
```

## Nachschlagen

Weitere Informationen entnehmen Sie dem Handbuch oder der Schnellreferenz. Beides können Sie mit markpublish direkt über die Kommandozeile erstellen:

```bash
markpublish cheatsheet                  # Kompakte Schnellreferenz ausgeben
markpublish manual                      # Ausführliches Benutzerhandbuch ausgeben
```

Für Informationen zum aktuellen Entwicklungsstand schauen Sie gern auf https://github.com/fwdotcom/markpublish vorbei. Viel Freude bei der Dokumentenerstellung mit markpublish!

Frank Winter

