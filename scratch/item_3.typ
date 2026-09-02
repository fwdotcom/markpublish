#import "template.typ": *

#show: doc => setup-document(
  title: "markpublish Benutzerhandbuch",
  subtitle: "Moderne PDF- und HTML-Dokumentenerstellung aus Markdown",
  authors: ("Frank Winter",),
  version: "1.0.0",
  date: "02.09.2026",
  copyright: "© 2026 Frank Winter",
  language: "de",
  show-cover: true,
  summary: "Dieses Handbuch bietet eine praxisorientierte Anleitung und vollständige Referenz zur Konfiguration, Template-Anpassung und Dokumentengenerierung mit markpublish.",
  show-toc: true,
  toc-title: "Inhaltsverzeichnis",
  toc-depth: 2,
  labels: (
    version: "Version",
    date: "Datum",
    author: "Autor",
    copyright: "Copyright",
  ),
  doc,
)

#render-chapter-divider(title: "Konfigurations-Leitfaden", subtitle: "", summary: "Deklarative Definition von Dokumentenmetadaten, Kapiteln und Hierarchien.", tag: "Kapitel 4")

= Konfigurations-Leitfaden <konfigurations-leitfaden>

Die Datei `markpublish.yaml` ist das zentrale Steuerungsdokument jeder Publikation.

== Das `document`-Objekt <das-document-objekt>

Unter `document:` werden alle globalen Metadaten und Schalter hinterlegt:

```yaml
document:
  title: "markpublish Benutzerhandbuch"
  subtitle: "Moderne PDF- und HTML-Dokumentenerstellung"
  summary: "Kurze Zusammenfassung für Deckblatt und Metadaten."
  author: "Frank Winter"
  organisation: "WASDCAT Games"
  date: "auto"                 # "auto" (Tagesdatum) oder festes Datum "2026-08-31"
  version: "1.0.0"             # optional - ohne Angabe entfällt das Feld
  language: "de"               # Beschriftungen und Datumsformat; ohne Angabe die Systemsprache

  # Globale Schalter
  cover: true                  # Deckblatt an/aus
  document_toc: 2              # Großes Verzeichnis, zwei Ebenen tief
  autonum_style: "decimal"     # "decimal", "roman", "legal", "none"
  chapter_toc: 2               # Vorgabe für die Kapitel-Trennseiten
  header: true                 # Laufende Kopfzeile
  footer: true                 # Laufende Fußzeile
```

=== Automatische Datumsauflösung <automatische-datumsaufloesung>

Wird `date: "auto"` oder `date: "today"` angegeben, setzt `markpublish` das aktuelle Datum im passenden Sprachformat ein:

- `language: "de"` → `31.08.2026`
- `language: "en"` → `2026-08-31`

=== Zusätzliche Metadatenfelder <zusaetzliche-metadatenfelder>

Beliebige zusätzliche Schlüssel (z. B. `status: "Entwurf"`, `department: "IT-Architektur"`) können frei definiert werden und stehen in allen Jinja2-Templates über `document.<feldname>` zur Verfügung.

== Kapitel definieren <kapitel-definieren>

Ein einfaches Kapitel wird mit `file:`, optionalem `title:` und `summary:` angegeben:

```yaml
parts:
  - title: "Hauptteil"
    break_before: "none"
    chapters:
      - file: "chapters/01_intro.md"
        title: "Einleitung"
        summary: "Zielsetzung des Leitfadens."
        break_before: "divider"    # Eigene Trennseite vor dem Kapitel
        chapter_toc: "none"        # Kein kapitelweises Mini-TOC
```

Ein Kapitel steht immer unter einem Part — `chapters:` auf oberster Ebene weist `markpublish` mit einem Hinweis auf den richtigen Aufbau zurück. Der nächste Abschnitt erklärt, warum.

Alle Pfade sind relativ zur `markpublish.yaml`, nicht zum Arbeitsverzeichnis der Shell.

== Dokumentaufbau in 2 Stufen: Parts und Kapitel <dokumentaufbau-in-2-stufen-parts-und-kapitel>

`markpublish` organisiert Dokumente in einer klaren 2-stufigen Struktur:

+ *Stufe 1 — Parts (`parts:`):* Gliedert das Dokument in logische Hauptabschnitte (z. B. Hauptteil, Anhänge, Bände). Jeder Part besitzt einen Namen (`title:` oder `part:`).
+ *Stufe 2 — Kapitel (`chapters:`):* Die eigentlichen Inhaltsdateien (*.md) unter dem jeweiligen Part.
+ *Binnenstruktur (`##`, `###`):* Wird direkt im Markdown formatiert.

```yaml
parts:
  - title: "Hauptteil"         # Hauptabschnitt
    break_before: "none"       # Keine Part-Trennseite für den Hauptteil
    document_toc: "none"       # 'Hauptteil' erscheint nicht im TOC; Kapitel direkt gelistet
    chapters:
      - file: "chapters/01_intro.md"
        title: "Einführung"
      - file: "chapters/02_usage.md"
        title: "Nutzung"

  - title: "Anhänge"           # Gliedernder Abschnitt mit Trennseite & TOC-Rubrik
    summary: "Ergänzende Tabellen und Referenzen."
    break_before: "divider"
    autonum_from_level: 2
    document_toc: 2
    chapters:
      - file: "chapters/appendix_a.md"
        title: "Anhang A: Referenz"
        autonum_prefix: "A."
      - file: "chapters/appendix_b.md"
        title: "Anhang B: Glossar"
        autonum_prefix: "B."
```

Ein benannter Part gruppiert seine Kapitel, erhält auf Wunsch eine Trennseite und steht als gliedernde Rubrik im Inhaltsverzeichnis (wenn nicht mit `document_toc: "none"` ausgeblendet). Alle Kapitel stehen typografisch bündig auf derselben primären Fluchtlinie.

