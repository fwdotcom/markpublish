# Projektkonfiguration mit markpublish.yaml

Die zentrale Steuerungsdatei eines jeden markpublish-Projekts ist die `markpublish.yaml`. Sie definiert das Dokument deklarativ: Metadaten, Layout-Vorgaben, Gliederung und die Zuordnung der Markdown-Dateien zu Kapiteln und Abschnitten.

## Die drei Strukturebenen

markpublish organisiert Dokumente in drei klar voneinander abgegrenzten Ebenen:

```text
document
└── parts (Abschnitte)
    └── chapters (Kapitel)
        └── [Unterkapitel in chapters]
```

### Document (Dokumentebene)

Die oberste Ebene `document:` beschreibt das Gesamtdokument:
* **Metadaten:** Titel, Untertitel, Autoren, Version, Datum, Sprache, Status und Copyright-Hinweise.
* **Layout-Schalter:** Anzeige des Deckblatts (`cover`), Aktivierung von Kopfzeilen (`header`) und Fußzeilen (`footer`).
* **Globale Verzeichnisvorgaben:** Steuerung der Tiefe für das Gesamt-Inhaltsverzeichnis (`document_toc`), Abschnittsverzeichnisse (`part_toc`) und lokale Kapitelverzeichnisse (`chapter_toc`).
* **Nummerierungsregeln:** Vorgaben zur automatischen Nummerierung von Überschriften (`autonum_style`, `autonum_from_level`, `autonum_prefix`).

### Parts (Abschnitte)

Ein Dokument wird durch `parts:` in übergeordnete Abschnitte gegliedert (z. B. „Hauptteil“, „Fallstudien“, „Anhänge“). 
* Ein Abschnitt fasst logisch zusammengehörige Kapitel zusammen.
* Abschnitte können mit Trennseiten (`break_before: "divider"`) oder einfachen Seitenumbrüchen (`break_before: "page"`) eingeleitet werden.
* Auf Abschnittsebene gesetzte Einstellungen (z. B. Verzeichnistiefe oder Nummerierungspräfixe wie `autonum_prefix: "A."`) vererben sich automatisch auf alle darin enthaltenen Kapitel.

### Chapters (Kapitel)

Die Liste `chapters:` innerhalb eines Abschnitts verweist auf die eigentlichen Markdown-Inhaltsdateien:
* Jedes Kapitel besitzt einen Verweis auf die Markdown-Datei (`file:`), einen Titel (`title:`) sowie eine optionale Kurzbeschreibung (`summary:`).
* Kapitel können über das Feld `break_before` steuern, ob vor ihnen eine Trennseite erzeugt wird, ein einfacher Seitenwechsel erfolgt oder der Text nahtlos anschließt.
* Kapitel können hierarchisch geschachtelt werden, indem ein Kapitel selbst wiederum eine Liste von Unterkapiteln (`chapters:`) enthält.

---

## Beispiel einer vollständigen Konfiguration

Das folgende Beispiel zeigt eine praxisnahe, vollständige `markpublish.yaml`:

```yaml
# markpublish.yaml

document:
  title: "Projektbericht Jahresabschluss"
  subtitle: "Analyse, Ergebnisse und Ausblick"
  summary: "Umfassender Gesamtbericht über die Projektphasen des vergangenen Geschäftsjahres."
  author: "Projektgruppe Controlling"
  date: "auto"
  version: "1.2.0"
  language: "de"
  copyright: "© 2026 Musterunternehmen GmbH"

  # Layout-Elemente
  cover: true
  header: true
  footer: true

  # Verzeichnistiefen
  document_toc: 2
  part_toc: 2
  chapter_toc: "none"

  # Nummerierung
  autonum_style: "decimal"
  autonum_from_level: 1

theme: "default"

parts:
  - title: "Hauptteil"
    break_before: "none"
    chapters:
      - file: "chapters/01_einleitung.md"
        title: "Einleitung und Projektziele"
        break_before: "page"

      - file: "chapters/02_analyse.md"
        title: "Marktanalyse und Vorgehen"
        break_before: "page"

      - file: "chapters/03_ergebnisse.md"
        title: "Zentrale Ergebnisse"
        break_before: "divider"

  - title: "Anhänge"
    break_before: "divider"
    autonum_from_level: 2
    autonum_prefix: "A."
    chapters:
      - file: "chapters/anhang_tabellen.md"
        title: "Detailtabellen"

      - file: "chapters/anhang_glossar.md"
        title: "Glossar"
```

Eine vollständige Übersicht aller verfügbaren Schlüssel, Datentypen, Standardwerte und Kombinationsmöglichkeiten für jede der drei Ebenen finden Sie im [Anhang A: Schema-Referenz markpublish.yaml](chapters/07_appendix_yaml_spec.md).
