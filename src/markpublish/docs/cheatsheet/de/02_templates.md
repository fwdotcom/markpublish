# Templates und Themes

Alles Sichtbare steckt in einem Theme: Seitenlayout, Stylesheet und statische
Texte. Mitgeliefert wird eines, `default`, in den Varianten `pdf` und `html`.

## Wo ein Theme gesucht wird

Der erste Treffer gewinnt — ein Theme kommt immer aus genau einer Quelle, nie
gemischt.

| Rang | Ort |
| :--- | :--- |
| 1. Benutzer | `~/.markpublish/templates`, sonst das Konfigverzeichnis des Systems |
| 2. Projekt | `templates_dir` in der YAML, `MARKPUBLISH_TEMPLATES_DIR` oder `./templates` |
| 3. Paket | die eingebauten Themes |

`markpublish templates` zeigt, was vorhanden ist und woher es stammt.

## Anpassen

```bash
markpublish export-template default ./templates
```

Kopiert das eingebaute Theme ins Projekt, wo Stufe 2 es beim nächsten Build
aufgreift. Für PDF enthält das Theme die Typst-Vorlage `template.typ`,
optionale Schriftarten in `fonts/` und Grafiken in `assets/`.

## Statische Texte

Labels lösen über vier Ebenen auf; eine tiefere überschreibt nur die Schlüssel,
die sie tatsächlich setzt.

| Ebene | Datei |
| :--- | :--- |
| 1. Programm | `markpublish/i18n.yaml` |
| 2. Theme | `<templates>/<theme>/i18n.yaml` |
| 3. Zielformat | `<templates>/<theme>/<pdf\|html>/i18n.yaml` |
| 4. Projekt | `./i18n.yaml` neben der `markpublish.yaml` |

Jede Datei ist nach Sprachcode gegliedert; der Schlüssel `"*"` gilt für jede
Sprache. Ebene 4 gehört dem Dokument: Sie erlaubt das Überschreiben von Texten
und das Lokalisieren freier Metadatenfelder (`abteilung: "Abteilung"`).
Was geändert wurde, zeigt `markpublish labels --overridden`.
