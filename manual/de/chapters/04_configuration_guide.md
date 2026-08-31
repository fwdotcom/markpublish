# Konfigurations-Leitfaden

Die Datei `markpublish.yaml` ist das zentrale Steuerungsdokument jeder Publikation. Sie gliedert sich in Metadaten, Template-Einstellungen und Kapiteldefinitionen.

## Das `document`-Objekt

Unter `document:` werden alle globalen Metadaten und Schalter hinterlegt:

```yaml
document:
  title: "markpublish Benutzerhandbuch"
  subtitle: "Moderne PDF- und HTML-Dokumentenerstellung"
  summary: "Kurze Zusammenfassung für Deckblatt und Metadaten."
  author: "Frank Winter"
  organisation: "WASDCAT Games"
  date: "auto"                    # "auto" (Tagesdatum) oder festes Datum "2026-08-31"
  version: "1.0.0"               # optional - ohne Angabe entfällt das Feld
  language: "de"                 # Sprachcode für Silbentrennung & Formatierung

  # Globale Schalter
  cover: true                    # Deckblatt an/aus
  toc: true                      # Globales Inhaltsverzeichnis
  autonum_type: "decimal"        # "decimal", "roman", "legal", "none"
  header: true                   # Laufende Kopfzeile
  footer: true                   # Laufende Fußzeile
```

### Automatische Datumsauflösung
Wird `date: "auto"` oder `date: "today"` angegeben, generiert `markpublish` automatisch das aktuelle Datum im passenden Sprachformat:
- `language: "de"` $\rightarrow$ `31.08.2026`
- `language: "en"` $\rightarrow$ `2026-08-31`

### Zusätzliche Metadatenfelder
Beliebige zusätzliche Schlüssel (z. B. `status: "Entwurf"`, `department: "IT-Architektur"`) können frei definiert werden und stehen in allen Jinja2-Templates über `document.<feldname>` zur Verfügung.

