# Templates und Themes

Alles Sichtbare steckt in einem Theme: Typografie, Seitenlayout und statische
Texte. Mitgeliefert wird das Standard-Theme `default` für PDF.

## Wo ein Theme gesucht wird

Der erste Treffer gewinnt — ein Theme kommt immer aus genau einer Quelle, nie
gemischt. Welches Theme verwendet wird, bestimmt das Kommandozeilen-Flag `--theme`
oder die Einstellung `theme:` in der `markpublish.yaml` (Standard: `default`).

| Rang | Ort |
| :--- | :--- |
| 1. Benutzer | `~/.markpublish/templates/<theme>/` bzw. benutzerspezifisches AppData-Verzeichnis |
| 2. Projekt | `--templates-dir` auf der CLI, `templates_dir:` in der YAML, `MARKPUBLISH_TEMPLATES_DIR` oder `./templates/<theme>/` |
| 3. Paket | Mitgeliefertes Standard-Theme `default` |

`markpublish templates` zeigt, welche Vorlagen auf dem System vorhanden sind und woher sie stammen.

## Anpassen eines Themes

```bash
markpublish export-template default ./templates
```

Kopiert das eingebaute Theme ins Projekt, wo Rang 2 es beim nächsten Build
automatisch aufgreift. Für PDF enthält das Theme:

* `template.typ`: Hauptlayout-Vorlage in Typst
* `i18n.yaml`: Übergreifende Beschriftungen des Themes
* `pdf/i18n.yaml`: Formatspezifische Beschriftungen für PDF
* `fonts/`: Optionale Schriftarten (.ttf, .otf)
* `assets/`: Grafiken, Logos und Icons

## Statische Texte (i18n)

Labels lösen über eine vierstufige Kaskade auf; eine tiefere Ebene überschreibt
nur die Schlüssel, die sie tatsächlich setzt:

| Ebene | Datei |
| :--- | :--- |
| 1. Programm | `markpublish/i18n.yaml` (Standardtexte der Anwendung) |
| 2. Theme | `<templates>/<theme>/i18n.yaml` |
| 3. Zielformat | `<templates>/<theme>/pdf/i18n.yaml` |
| 4. Projekt | `./i18n.yaml` neben der `markpublish.yaml` |

Jede Datei ist nach Sprachcode gegliedert (`de:`, `en:`); der Schlüssel `"*"` gilt
für jede Sprache. Ebene 4 gehört dem Projekt: Sie erlaubt das Überschreiben von
Texten und das Lokalisieren freier Metadatenfelder (`abteilung: "Abteilung"`).
Mit `markpublish labels --overridden` bzw. `markpublish labels --theme <theme>`
prüfen Sie die Kaskade vor dem Bauen.

## Wichtige CLI-Befehle

| Befehl | Wichtige Optionen | Bedeutung |
| :--- | :--- | :--- |
| `markpublish build` | `--theme`, `--target`, `-o`, `--templates-dir` | Dokument nach PDF oder HTML kompilieren |
| `markpublish init` | `[ZIEL]`, `--title`, `--lang` | Minimales Starterprojekt einrichten |
| `markpublish cheatsheet` | `--lang`, `--theme`, `-o`, `--templates-dir` | Diese Schnellreferenz als PDF erzeugen |
| `markpublish manual` | `--lang`, `--theme`, `-o`, `--templates-dir` | Vollständiges Benutzerhandbuch erzeugen |
| `markpublish templates` | `--target`, `--templates-dir` | Vorlagen und Auflösungsrang auflisten |
| `markpublish export-template` | `[THEME]`, `[ZIEL]`, `--target` | Vorlagendateien zur Anpassung exportieren |
| `markpublish labels` | `--theme`, `--target`, `--templates-dir`, `--overridden` | Statische Texte und Metadaten analysieren |

