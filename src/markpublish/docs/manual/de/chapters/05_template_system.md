# Templates und Mehrsprachigkeit

markpublish trennt Inhalt und Gestaltung strikt voneinander: Die Textinhalte entstehen in Markdown, während das visuelle Erscheinungsbild, die Typografie und das Seitenlayout über Typst-Templates gesteuert werden. Ergänzt wird dieses System durch eine flexible Kaskade zur Mehrsprachigkeit (i18n).

## Die Auflösungshierarchie für Themes

Wenn markpublish nach einem Theme sucht (angegeben über das Kommandozeilen-Flag `--theme`, die Einstellung `theme:` in der Konfigurationsdatei oder den Standard `default`), durchsucht der Resolver folgende Ebenen der Reihe nach (der erste Treffer gewinnt):

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

### Was auf dem Titelblatt erscheint

Das Metadatenraster des Deckblatts zeigt nicht alles, was unter `document:` steht, sondern genau die Angaben, die das Theme dafür vorsieht – im mitgelieferten Standard-Theme sind das Version, Datum, Autor, Copyright und Status, in dieser Reihenfolge. Titel, Untertitel und Zusammenfassung stehen ohnehin groß darüber.

Ein eigenes Feld aus der `markpublish.yaml` erreicht das Theme, wird aber erst gedruckt, wenn das Theme es ausdrücklich aufführt. Wer `abteilung:` oder `kunde:` auf dem Deckblatt haben möchte, exportiert sich das Theme (siehe unten) und ergänzt dort eine Zeile; die Beschriftung dazu kommt aus der `i18n.yaml` des Projekts.

Welche Felder ein Theme tatsächlich abholt, zeigt `markpublish labels`: Ein Feld, das kein Theme verwendet, erscheint dort mit dem Befund *ungenutzt*.

## Eigene Themes erstellen und anpassen

Der einfachste und sicherste Weg zur Erstellung eines eigenen Corporate Designs ist der Export des integrierten Standard-Themes:

```bash
markpublish export-template default ./templates --target pdf
```

Dieser Befehl kopiert das Standard-Theme vollständig in das lokale Verzeichnis `templates/default/`. Sie können die Dateien anschließend direkt bearbeiten, Schriften anpassen, Farben ändern oder Ihr Firmenlogo einbinden. markpublish greift beim nächsten `build` automatisch auf Ihre angepasste Projektvorlage zu.

Die Layoutdatei `template.typ` ist in der Satzsprache Typst geschrieben und im Standard-Theme durchgehend kommentiert. Wer sie über Farben und Schriften hinaus umbauen möchte, findet die vollständige Sprachreferenz unter [https://typst.app/docs](https://typst.app/docs).

---

## Mehrsprachigkeit und Textkaskade (i18n)

Professionelle Dokumente enthalten eine Vielzahl statischer Texte, die nicht aus den Markdown-Kapiteln stammen, sondern vom Template erzeugt werden – beispielsweise „Inhaltsverzeichnis“, „Kapitel“, „Seite X von Y“ oder Hinweise im Deckblatt.

markpublish verwaltet diese Texte über ein Kaskadensystem in `i18n.yaml`-Dateien.

### Die vierstufige Beschriftungskaskade

Bei der Auflösung eines Textschlüssels (z. B. `toc_title`) sucht markpublish in folgender Reihenfolge – spätere Fundstellen überschreiben frühere:

1. **Paket-Basis (`markpublish/i18n.yaml`):** Vollständige Standardbeschriftungen für alle unterstützten Sprachen.

2. **Theme-Ebene (`<theme>/i18n.yaml`):** Themes können eigene Formulierungen oder Bezeichnungen definieren.

3. **Format-Ebene (`<theme>/pdf/i18n.yaml`):** Formatspezifische Anpassungen des Themes.

4. **Projekt-Ebene (`i18n.yaml` neben der `markpublish.yaml`):** Texte dieses einen Dokuments – mit höchster Priorität.

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
