# Templates und Mehrsprachigkeit

markpublish trennt Inhalt und Gestaltung strikt voneinander: Die Textinhalte entstehen in Markdown, während das visuelle Erscheinungsbild, die Typografie und das Seitenlayout über Typst-Templates gesteuert werden. Ergänzt wird dieses System durch eine flexible Kaskade zur Mehrsprachigkeit (i18n).

## Die 3-stufige Auflösungshierarchie

Wenn markpublish nach einem Theme sucht (angegeben über `theme:` in der Konfigurationsdatei oder den Standard `default`), durchsucht es drei Ebenen in fester Reihenfolge:

1. **Projekt-Vorlagen (`./templates/<theme>/`):**  
   Vorlagen im Projektordner haben höchste Priorität. Liegt hier ein Theme, wird dieses verwendet. Dies ermöglicht projektspezifische Layouts, die direkt mit dem Repository versioniert werden können.
2. **Benutzer-Vorlagen (`~/.markpublish/templates/<theme>/`):**  
   Vorlagen im Home-Verzeichnis des aktuellen Benutzers. Ideal für persönliche Dokumentvorlagen, die über mehrere Projekte hinweg zur Verfügung stehen sollen.
3. **Paket-Vorlagen (Integrierte Standard-Themes):**  
   Das mitgelieferte Standard-Theme `default`. Es dient als verlässliche Basis und Fallback, wenn auf Benutzer- oder Projektebene keine Vorlage gefunden wird.

*Benutzerdefinierter Vorlagenpfad:*  
Zusätzlich kann über den Schlüssel `templates_dir:` direkt in der `markpublish.yaml` oder über den Kommandozeilen-Parameter `--templates-dir` ein beliebiger alternativer Ordner angegeben werden, der die Suche anführt.

## Aufbau eines Themes

Ein vollständiges markpublish-Theme besitzt folgende Verzeichnisstruktur:

```text
templates/
└── mein-theme/
    ├── i18n.yaml            # Übergreifende Beschriftungen des Themes
    └── pdf/
        ├── template.typ     # Typst-Layoutvorlage für das PDF
        └── i18n.yaml        # Formatspezifische Beschriftungen (höchste Kaskaden-Priorität)
```

### Typst als Layout-Engine

Typst ist eine moderne, hochperformante Satz- und Programmiersprache für Dokumente. Sie bietet mächtige Funktionen für Seitenränder, Kopf- und Fußzeilen, Farbwelten, Schriftdefinitionen und mathematischen Formelsatz.

* **Weiterführende Typst-Dokumentation:**  
  Eine vollständige Einführung in alle Möglichkeiten von Typst (Gestaltungselemente, Funktionen, Regeln und Typografie) finden Sie in der offiziellen Dokumentation unter [https://typst.app/docs](https://typst.app/docs).

### Exemplarischer Aufbau einer template.typ

Die Datei `template.typ` definiert das Gesamterscheinungsbild des Dokuments. Ein Auszug zeigt die grundlegende Struktur:

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
    header: locate(loc => {
      // Individuelle Kopfzeilengestaltung
      text(9pt, fill: rgb("#64748b"))[#title]
    }),
    footer: locate(loc => {
      // Seitennummerierung: Seite X von Y
      let page_num = counter(page).at(loc).first()
      align(center)[#text(9pt)[#page_num]]
    })
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
markpublish export-template default ./templates
```

Dieser Befehl kopiert das Standard-Theme vollständig in das lokale Verzeichnis `templates/default/`. Sie können die Dateien anschließend direkt bearbeiten, Schriften anpassen, Farben ändern oder Ihr Firmenlogo einbinden. markpublish greift beim nächsten `build` automatisch auf Ihre angepasste Projektvorlage zu.

---

## Mehrsprachigkeit und Textkaskade (i18n)

Professionelle Dokumente enthalten eine Vielzahl statischer Texte, die nicht aus den Markdown-Kapiteln stammen, sondern vom Template erzeugt werden – beispielsweise „Inhaltsverzeichnis“, „Kapitel“, „Seite X von Y“ oder Hinweise im Deckblatt.

markpublish verwaltet diese Texte über ein Kaskadensystem in `i18n.yaml`-Dateien.

### Die 3-stufige Beschriftungskaskade

Bei der Auflösung eines Textschlüssels (z. B. `table_of_contents`) sucht markpublish in folgender Reihenfolge – spätere Fundstellen überschreiben frühere:

1. **Paket-Basis (`markpublish/i18n.yaml`):** Vollständige Standardbeschriftungen für alle unterstützten Sprachen.
2. **Theme-Ebene (`<theme>/i18n.yaml`):** Themes können eigene Formulierungen oder Bezeichnungen definieren.
3. **Format-Ebene (`<theme>/pdf/i18n.yaml`):** Formatspezifische Anpassungen.

### Aufbau der i18n.yaml

Eine `i18n.yaml` enthält strukturierte Übersetzungen je Sprachkürzel:

```yaml
de:
  table_of_contents: "Inhaltsverzeichnis"
  chapter: "Kapitel"
  part: "Abschnitt"
  page_x_of_y: "Seite {x} von {y}"
  version: "Version"
  author: "Autor"

en:
  table_of_contents: "Table of Contents"
  chapter: "Chapter"
  part: "Part"
  page_x_of_y: "Page {x} of {y}"
  version: "Version"
  author: "Author"
```

### Spracherkennung und Validierung

Die Sprache eines Dokuments wird in der `markpublish.yaml` über den Schlüssel `language:` (z. B. `language: "de"`) festgelegt. Fehlt dieser Eintrag, ermittelt markpublish automatisch die Systemsprache des Autors.

Mit dem CLI-Befehl `markpublish labels` können Sie jederzeit prüfen, welche Beschriftungen für Ihr Projekt aktiv sind und aus welcher Datei sie stammen.
