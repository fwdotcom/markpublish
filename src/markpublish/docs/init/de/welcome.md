# Willkommen bei markpublish

Herzlichen Glückwunsch, Sie haben Ihr neues markpublish-Projekt erstellt.

Es besteht aus zwei Dateien: `markpublish.yaml` und diesem Kapitel in `welcome.md`.

## PDF erstellen

Wechseln Sie in das neu erstellte Projekt-Verzeichnis und bauen Sie das PDF:

```bash
cd {dir}
markpublish build
```

## Weitere Kapitel hinzufügen

Erstellen Sie eine neue Markdown-Datei und tragen Sie sie mit einem weiteren
`file:`-Schlüssel unter `chapters:` in die `markpublish.yaml` ein. Pfade gelten
relativ zur Konfigurationsdatei:

```yaml
parts:
  - part: "Hauptteil"
    chapters:
      - file: "welcome.md"
      - file: "ihre_neue_md_datei.md"
```

Nach dem nächsten `markpublish build` steht das neue Kapitel im PDF – in der Reihenfolge, in der die Dateien unter `chapters:` stehen.

## Nachschlagen

Weitere Informationen entnehmen Sie dem Handbuch oder der Schnellreferenz. Beide können Sie mit markpublish direkt über die Kommandozeile erstellen:

```bash
markpublish cheatsheet                  # Kompakte Schnellreferenz ausgeben
markpublish manual                      # Ausführliches Benutzerhandbuch ausgeben
```

Für Informationen zum aktuellen Entwicklungsstand besuchen Sie https://github.com/fwdotcom/markpublish. Viel Freude bei der Dokumentenerstellung mit markpublish!
