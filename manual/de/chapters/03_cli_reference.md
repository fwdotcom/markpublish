# Die CLI-Befehle

`markpublish` bietet eine schlanke, intuitive Befehlszeilenschnittstelle (CLI), die über `markpublish` oder die Kurzform `mpub` aufgerufen werden kann.

## Befehlsübersicht

| Befehl | Kurzbeschreibung |
| :--- | :--- |
| `markpublish build` | Kompiliert das Dokument zu PDF und/oder HTML |
| `markpublish init` | Erzeugt ein neues Projekt mit Beispieldateien |
| `markpublish templates` | Listet alle gefundenen Templates und deren Quellen auf |
| `markpublish export-template` | Exportiert ein Template zur individuellen Anpassung |

## `markpublish build`

Kompiliert eine `markpublish.yaml`-Konfiguration.

```bash
markpublish build [CONFIG_FILE] [OPTIONEN]
```

### Argumente & Optionen:
- `CONFIG_FILE` *(optional, Standard: `markpublish.yaml`)*: Pfad zur YAML-Datei.
- `--target / -t` *(Standard: `pdf`)*: Zielformat (`pdf`, `html` oder `all`).
- `--output / -o`: Benutzerdefinierter Ausgabepfad (Datei oder Verzeichnis).
- `--templates-dir`: Spezifischer Pfad zu einem gemeinsamen Template-Verzeichnis.

### Beispiele:
```bash
# Standard-Build aus aktuellem Verzeichnis
markpublish build

# HTML-Version in ein bestimmtes Zielverzeichnis ausgeben
markpublish build markpublish.yaml -t html -o dist/

# Benutzerdefiniertes Template-Verzeichnis nutzen
markpublish build --templates-dir /shared/company-templates
```

## `markpublish init`

Initialisiert ein neues Projektverzeichnis.

```bash
markpublish init [ZIELORDNER] [--title "Titel"]
```

## `markpublish templates`

Zeigt eine tabellarische Übersicht aller Templates auf dem System und deren Prioritätsstatus:

```bash
markpublish templates
markpublish templates --target pdf
```

## `markpublish export-template`

Kopiert das eingebaute Standard-Template in Ihr lokales Arbeitsverzeichnis:

```bash
markpublish export-template default templates
```

