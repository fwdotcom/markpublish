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
        ├── i18n.yaml        # Formatspezifische Beschriftungen des Themes
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
  language: "de",
  show-cover: true,
  show-toc: true,
  toc-title: "Inhaltsverzeichnis",
  meta: (:),
  labels: (:),
  body
) = {
  let title = meta.at("title").value
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

### Das `meta`-Wörterbuch

Sämtliche Dokumentangaben erreichen `setup-document` über das Wörterbuch `meta` — Titel und Version genauso wie ein frei ergänztes `abteilung:`. Eigene Parameter dafür gibt es nicht: zwei Wege zur selben Angabe können auseinanderlaufen. Jeder Eintrag ist ein Datensatz mit vier Feldern:

```typst
meta.at("author")
// -> (key: "author", label: "Autor", value: "Frank Winter", in-grid: true)
```

| Feld | Bedeutung |
|---|---|
| `key` | Der Schlüssel aus der `markpublish.yaml` |
| `label` | Die Beschriftung aus der i18n-Kaskade, oder `none` |
| `value` | Der Wert — **mit seinem Typ**: Text, Zahl, Wahrheitswert oder Liste |
| `in-grid` | `false` für Titel, Untertitel und Summary; sie stehen oben auf dem Deckblatt und gehören nicht noch einmal ins Metadatenraster |

Der Vorteil: Das Theme muss nicht wissen, welche Felder es gibt. Es zählt auf, was da ist — und erreicht damit auch die eigenen Felder, die ein Dokument unter `document:` ergänzt:

```typst
for item in meta.values().filter(it => it.in-grid and it.value != none) {
  [#if item.label != none { item.label } else { item.key }: #item.value]
}
```

### Reihenfolge auf dem Titelblatt

Welche Angabe im Metadatenraster zuerst steht, entscheidet das Theme — eine Zeile in `template.typ`:

```typst
#let cover-order = ("version", "date", "author", "copyright", "status")
```

Schlüssel, die dort nicht vorkommen — Ihre eigenen Felder aus der `markpublish.yaml` —, folgen dahinter in der Reihenfolge der Konfiguration. Ändern Sie die Zeile, ändert sich das Titelblatt; markpublish reicht die Angaben nur weiter und mischt sich nicht ein.

> [!IMPORTANT]
> `meta.at("kunde")` **ohne** `default:` bricht den Build ab, wenn das Dokument den Schlüssel nicht kennt. markpublish meldet das vorher mit Fundstelle und Abhilfe; `markpublish labels` zeigt es ebenfalls an. Wer eine Angabe optional halten will, notiert einen Fallback: `meta.at("kunde", default: (value: ""))`.

Weil der Typ erhalten bleibt, entscheidet das Theme über die Schreibweise. Ein Wahrheitswert wird über die Kaskade formuliert statt als `true` gedruckt:

```typst
#let meta-value(value, labels) = {
  if type(value) == bool {
    if value { labels.at("bool_true", default: "Ja") } else { labels.at("bool_false", default: "Nein") }
  } else if type(value) == array {
    value.map(v => str(v)).join(", ")
  } else {
    str(value)
  }
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

### Die 4-stufige Beschriftungskaskade

Bei der Auflösung eines Textschlüssels (z. B. `toc_title`) sucht markpublish in folgender Reihenfolge – spätere Fundstellen überschreiben frühere:

1. **Paket-Basis (`markpublish/i18n.yaml`):** Vollständige Standardbeschriftungen für alle unterstützten Sprachen.

2. **Theme-Ebene (`<theme>/i18n.yaml`):** Themes können eigene Formulierungen oder Bezeichnungen definieren.

3. **Format-Ebene (`<theme>/pdf/i18n.yaml`):** Formatspezifische Anpassungen des Themes.

4. **Projekt-Ebene (`i18n.yaml` neben der `markpublish.yaml`):** Texte dieses einen Dokuments — mit höchster Priorität.

Die Projekt-Ebene ist der Ort für die Beschriftung eigener Metadatenfelder: Wer unter `document:` ein `abteilung: "F&E"` notiert, schreibt hier `abteilung: "Abteilung"` dazu. Ohne diesen Eintrag druckt das Deckblatt den Schlüssel selbst. Sie können damit auch einen Text des Themes für ein einzelnes Dokument ersetzen, ohne das Theme zu kopieren.

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
