# Templates und Mehrsprachigkeit

markpublish trennt Inhalt und Gestaltung strikt voneinander: Die Textinhalte entstehen in Markdown, während das visuelle Erscheinungsbild, die Typografie und das Seitenlayout über Typst-Templates gesteuert werden. Ergänzt wird dieses System durch eine flexible Kaskade zur Mehrsprachigkeit (i18n).

## Die Auflösungshierarchie für Themes

Wenn markpublish nach einem Theme sucht (angegeben über `theme:` in der Konfigurationsdatei oder den Standard `default`), durchsucht der Resolver folgende Ebenen der Reihe nach (der erste Treffer gewinnt):

1. **Benutzer-Vorlagen (`user`):**  
   Vorlagen im Home-Verzeichnis des aktuellen Benutzers (`~/.markpublish/templates/<theme>/`) bzw. im benutzerspezifischen AppData-Verzeichnis. Dies ermöglicht autorenweite Standardvorlagen über alle Projekte hinweg.
2. **Projekt- / Vorlagen-Verzeichnis (`common`):**  
   Vorlagen im Projektordner (`./templates/<theme>/`) oder in einem explizit über `templates_dir:` in der `markpublish.yaml`, über das Kommandozeilen-Flag `--templates-dir` oder die Umgebungsvariable `MARKPUBLISH_TEMPLATES_DIR` festgelegten Verzeichnis.
3. **Paket-Vorlagen (`package`):**  
   Das mitgelieferte Standard-Theme `default`. Es dient als verlässlicher Fallback, wenn auf Benutzer- oder Projektebene keine Vorlage gefunden wird.

## Aufbau eines Themes

Ein vollständiges markpublish-Theme besitzt folgende Verzeichnisstruktur:

```text
templates/
└── mein-theme/
    ├── i18n.yaml            # Übergreifende Beschriftungen des Themes
    └── pdf/
        ├── template.typ     # Typst-Layoutvorlage für das PDF
        ├── i18n.yaml        # Formatspezifische Beschriftungen (höchste Priorität)
        ├── fonts/           # Optionale Schriftdateien (z. B. .ttf, .otf)
        └── assets/          # Statische Grafiken, Logos und Icons
            └── icons/
```

### Typst als Layout-Engine

Typst ist eine moderne, hochperformante Satz- und Programmiersprache für Dokumente. Sie bietet mächtige Funktionen für Seitenränder, Kopf- und Fußzeilen, Farbwelten, Schriftdefinitionen und mathematischen Formelsatz.

* **Weiterführende Typst-Dokumentation:**  
  Eine vollständige Einführung in alle Möglichkeiten von Typst (Gestaltungselemente, Funktionen, Regeln und Typografie) finden Sie in der offiziellen Dokumentation unter [https://typst.app/docs](https://typst.app/docs).

### Exemplarischer Aufbau einer template.typ

Die Datei `template.typ` definiert das Gesamterscheinungsbild des Dokuments. Ein Auszug zeigt die grundlegende Struktur unter Verwendung moderner Typst-Kontexte (`context`):

```typst
// template.typ (Auszug)

#let setup-document(
  title: "",
  subtitle: "",
  authors: (),
  version: "",
  date: "",
  labels: (:),
  body
) = {
  // Grundlegende Seiteneigenschaften
  set page(
    paper: "a4",
    margin: (top: 2.5cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
    header: context {
      // Individuelle Kopfzeilengestaltung
      text(9pt, fill: rgb("#64748b"))[#title]
    },
    footer: context {
      // Seitennummerierung über aktuelle Labels
      let page_num = counter(page).display()
      let page_label = labels.at("page", default: "Seite")
      align(center)[#text(9pt)[#page_label #page_num]]
    }
  )

  // Grundschriftart und Absatzgestaltung
  set text(font: "Open Sans", size: 10pt, lang: "de")
  set par(justify: true, leading: 0.65em)

  body
}
```

## Eigene Themes erstellen und anpassen

Der einfachste und sicherste Weg zur Erstellung eines eigenen Corporate Designs ist der Export des integrierten Standard-Themes:

```bash
markpublish export-template default ./templates --target pdf
```

Dieser Befehl kopiert das Standard-Theme vollständig in das lokale Verzeichnis `templates/default/`. Sie können die Dateien anschließend direkt bearbeiten, Schriften anpassen, Farben ändern oder Ihr Firmenlogo einbinden. markpublish greift beim nächsten `build` automatisch auf Ihre angepasste Projektvorlage zu.

---

## Mehrsprachigkeit und Textkaskade (i18n)

Professionelle Dokumente enthalten eine Vielzahl statischer Texte, die nicht aus den Markdown-Kapiteln stammen, sondern vom Template erzeugt werden – beispielsweise „Inhaltsverzeichnis“, „Kapitel“, „Seite X von Y“ oder Hinweise im Deckblatt.

markpublish verwaltet diese Texte über ein Kaskadensystem in `i18n.yaml`-Dateien.

### Die 3-stufige Beschriftungskaskade

Bei der Auflösung eines Textschlüssels (z. B. `toc_title`) sucht markpublish in folgender Reihenfolge – spätere Fundstellen überschreiben frühere:

1. **Paket-Basis (`markpublish/i18n.yaml`):** Vollständige Standardbeschriftungen für alle unterstützten Sprachen.
2. **Theme-Ebene (`<theme>/i18n.yaml`):** Themes können eigene Formulierungen oder Bezeichnungen definieren.
3. **Format-Ebene (`<theme>/pdf/i18n.yaml`):** Formatspezifische Anpassungen mit höchster Priorität.

### Aufbau der i18n.yaml

Eine `i18n.yaml` enthält strukturierte Übersetzungen je Sprachkürzel:

```yaml
de:
  toc_title: "Inhaltsverzeichnis"
  chapter: "Kapitel"
  part: "Abschnitt"
  page: "Seite"
  page_of: "von"
  version: "Version"
  author: "Autor"

en:
  toc_title: "Table of Contents"
  chapter: "Chapter"
  part: "Part"
  page: "Page"
  page_of: "of"
  version: "Version"
  author: "Author"
```

### Spracherkennung und Validierung

Die Sprache eines Dokuments wird in der `markpublish.yaml` über den Schlüssel `language:` (z. B. `language: "de"`) festgelegt. Fehlt dieser Eintrag, ermittelt markpublish automatisch die Systemsprache des Autors.

Mit dem CLI-Befehl `markpublish labels` können Sie jederzeit prüfen, welche Beschriftungen für Ihr Projekt aktiv sind und aus welcher Datei sie stammen.
