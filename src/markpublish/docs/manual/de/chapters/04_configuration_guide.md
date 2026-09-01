# Konfigurations-Leitfaden

Die Datei `markpublish.yaml` ist das zentrale Steuerungsdokument jeder Publikation. Sie gliedert sich in drei Teile: `document` für Metadaten und globale Schalter, `theme` für die Auswahl des Designs und `chapters` für den Aufbau des Dokuments.

## Das `document`-Objekt

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

### Automatische Datumsauflösung

Wird `date: "auto"` oder `date: "today"` angegeben, setzt `markpublish` das aktuelle Datum im passenden Sprachformat ein:

- `language: "de"` → `31.08.2026`
- `language: "en"` → `2026-08-31`

### Zusätzliche Metadatenfelder

Beliebige zusätzliche Schlüssel (z. B. `status: "Entwurf"`, `department: "IT-Architektur"`) können frei definiert werden und stehen in allen Jinja2-Templates über `document.<feldname>` zur Verfügung.

## Kapitel definieren

Ein einfaches Kapitel wird mit `file:`, optionalem `title:` und `summary:` angegeben:

```yaml
chapters:
  - file: "chapters/01_intro.md"
    title: "Einleitung"
    summary: "Zielsetzung des Leitfadens."
    break_before: "divider"    # Eigene Trennseite vor dem Kapitel
    chapter_toc: "none"        # Kein kapitelweises Mini-TOC
```

Alle Pfade sind relativ zur `markpublish.yaml`, nicht zum Arbeitsverzeichnis der Shell.

## Hierarchische Unterkapitel

Um ein Unterkapitel zu definieren, rücken Sie einfach weitere Kapitel unter `chapters:` ein:

```yaml
chapters:
  - file: "chapters/02_architecture.md"
    title: "Systemarchitektur"
    break_before: "divider"
    chapter_toc: 2             # Mini-TOC bis Überschriftstiefe 2
    chapters:
      - file: "chapters/02_1_backend.md"
        title: "Backend Services"
      - file: "chapters/02_2_frontend.md"
        title: "Frontend Client"
        break_before: "none"   # Läuft ohne Umbruch weiter
```

`markpublish` nummeriert die Unterkapitel automatisch konsistent als `2.1` und `2.2`. Die Verschachtelung ist rekursiv — eine feste Obergrenze für die Tiefe gibt es nicht.

Ohne Angabe beginnt jedes Kapitel oben auf einer neuen Seite, auch ein Unterkapitel. Wie weit ein Kapitel abgesetzt wird, steuert durchgehend `break_before:` (`page`, `divider`, `none`); die Werte sind in Anhang A beschrieben.

## Übergeordnete Abschnitte (Parts / Blöcke)

Für Hauptabschnitte oder Anhangsblöcke, die mehrere Kapitel umfassen, verwenden Sie das Schlüsselwort `part:`:

```yaml
chapters:
  - part: "Anhänge"
    summary: "Ergänzende Tabellen und Referenzen."
    break_before: "divider"    # Große Trennseite für den gesamten Anhang
    autonum: "none"            # Keine vorangestellte Ziffer
    document_toc: 1            # Anhänge nur mit Titel ins Inhaltsverzeichnis
    chapters:
      - file: "chapters/appendix_a.md"
        title: "Anhang A: Referenz"
      - file: "chapters/appendix_b.md"
        title: "Anhang B: Glossar"
```

Ein Part trägt selbst keinen Text: er gruppiert die Kapitel unter sich und bekommt eine eigene Trennseite. Der Part-Titel (hier *"Anhänge"*) wird automatisch in die laufende Kopfzeile der Einzelseiten übernommen.
