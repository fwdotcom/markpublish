# Architektur- und Implementierungsdokumentation: markpublish

Ein modernes, modulares und erweiterbares Open-Source-Publishing-Tool für Markdown-Dokumente mit WeasyPrint (PDF) und HTML-Unterstützung, konfigurierbar über YAML, mit flexibler Template-Hierarchie, getrennten Kapiteldateien und Part/Block-Oberstrukturen.

---

## 1. Übersicht & Zielsetzung

`markpublish` ist ein CLI- und Python-Framework, um aus strukturierten Markdown-Dateien hochwertige Dokumente (PDFs, HTML-Websites/Previews) zu generieren.

### Kernmerkmale:
- **WeasyPrint-Engine**: Native Nutzung von W3C CSS Paged Media (`@page`, Margin-Boxes, Counter, Seitenumbrüche, Running Elements).
- **Theme-basierte Templates**: Gliederung nach Theme, darunter das Zielformat (`templates/<theme>/pdf`, `templates/<theme>/html`).
- **3-stufige Template-Auflösung**:
  1. *User-Verzeichnis*: `~/.markpublish/templates/<theme>/<target>/`
  2. *Gemeinsamer Ordner*: `<templates_dir>/<theme>/<target>/` (konfigurierbar via CLI, YAML `templates_dir`, ENV `MARKPUBLISH_TEMPLATES_DIR` oder Default `./templates`)
  3. *Paket-Templates*: Built-in in `markpublish`
  - *Priorität*: User vor Common/Projekt vor Paket.
- **Hierarchische Kapitel & Parts**:
  - Unterstützung einzelner `.md`-Dateien je Kapitel.
  - Verschachtelung (`chapters:` innerhalb von Kapiteln) für automatische Unterkapitel (`1.1`, `1.2`).
  - Übergeordnete Parts/Blöcke (`part: "Anhänge"`) mit eigener Trennseite und Wiederholung in Kopf-/Fußzeilen.
- **Trennseiten & Deckblatt**:
  - `cover: true/false`
  - `break_before: page|divider|none` je Kapitel oder Part.
- **Inhaltsverzeichnisse (TOC)**:
  - Globales TOC (Baumstruktur aus Kapitelhierarchie).
  - Lokales Kapitel-TOC (`toc: true` oder `toc: 2` mit maximaler Tiefe).
- **2-zeilige Kopf- und Fußzeilen**:
  - Layout und Design liegen vollständig im Template (HTML/CSS) und werden aus Metadaten gespeist (`document.title`, `document.version`, `document.date`, `document.author`, `chapter.title`, `part.title`).
- **Plattformunabhängig**: Voll kompatibel mit Linux, macOS und Windows.

---

## 2. YAML-Konfigurationsschema (`markpublish.yaml`)

```yaml
# markpublish.yaml

document:
  title: "Architektur- und Designleitfaden"
  subtitle: "Best Practices für moderne Cloud-Systeme"
  summary: "Dieses Dokument beschreibt die Architekturrichtlinien, Sicherheitsstandards und Deployment-Strategien für verteilte Anwendungen."
  author: "Frank Mustermann"
  date: "auto"                    # Konkretes Datum (z. B. "2026-08-31") oder "auto" / "today"
  version: "1.0.0"
  language: "de"                 # Lokalisierung (z.B. Datumsformat, "Seite X von Y", Trennung)
  
  # Layout & Schalter
  cover: true                    # Deckblatt an/aus (true/false)
  toc: true                      # Globales Inhaltsverzeichnis (Tiefe aus Hierarchie)
  autonum_type: "decimal"        # "decimal" (1, 1.1), "roman", "legal", "none"
  header: true                   # Kopfzeile an/aus (Layout liegt im Template)
  footer: true                   # Fußzeile an/aus (Layout liegt im Template)

# Template-Konfiguration
theme: "default"                 # Name des Templates
templates_dir: "./templates"     # Optional: Konfigurierbarer Pfad zum gemeinsamen Template-Ordner

# Kapitel- und Part-Definitionen
chapters:
  # Normales Kapitel auf oberster Ebene
  - file: "chapters/01_introduction.md"
    title: "Einleitung & Motivation"
    summary: "Überblick über die Ziele und den Kontext des Projekts."
    break_before: "divider"      # page (Standard) | divider | none
    toc: false                   # Kein lokales Kapitel-TOC

  # Hauptkapitel mit Unterkapiteln (Hierarchie durch Einrückung)
  - file: "chapters/02_architecture.md"
    title: "Systemarchitektur"
    summary: "Detaillierte Darstellung der Kernkomponenten."
    break_before: "divider"
    toc: 2                       # Lokales Kapitel-TOC bis Tiefe 2
    chapters:
      - file: "chapters/02_1_backend.md"
        title: "Backend Services"
      - file: "chapters/02_2_frontend.md"
        title: "Frontend Client"

  # Weiteres Hauptkapitel
  - file: "chapters/03_security.md"
    title: "Sicherheit & Compliance"
    break_before: "divider"

  # ============================================================
  # OBERSTER BLOCK / PART (z. B. "Anhänge")
  # ============================================================
  - part: "Anhänge"              # Übergeordneter Block/Part
    summary: "Ergänzende Spezifikationen, Glossar und Referenztabellen."
    break_before: "divider"      # Eigene Trennseite "Anhänge" vor dem Block
    autonum: "none"              # Keine Ziffer für diesen Block
    chapters:
      - file: "chapters/appendix_glossar.md"
        title: "Anhang A: Glossar"
      - file: "chapters/appendix_tables.md"
        title: "Anhang B: Referenztabellen"
```

---

## 3. Template-Architektur

### 3.1 Ordnerstruktur
```
templates/
├── pdf/
│   └── default/
│       ├── layout.html            # Jinja2 Hauptlayout für WeasyPrint PDF
│       ├── styles.css             # CSS Paged Media (@page, 2-zeilige Kopf-/Fußzeilen)
│       ├── cover.html             # PDF Deckblatt
│       ├── part_divider.html      # Part Trennseite
│       ├── chapter_divider.html   # Kapitel Trennseite (mit Summary & lokalem TOC)
│       └── toc.html               # Globales Inhaltsverzeichnis
└── html/
    └── default/
        ├── layout.html            # Standalone Web/Preview HTML
        ├── styles.css             # Responsive Screen-CSS
        ├── cover.html             # Hero/Header-Bereich
        ├── part_divider.html      # Part-Separator im Web
        ├── chapter_divider.html   # Kapitel-Header
        └── toc.html               # Interaktives Seiten-TOC
```

### 3.2 2-zeilige Kopf- und Fußzeilen
- **Kopfzeile**:
  - `@top-left`: Zeile 1: `document.title`, Zeile 2: `current-part` / `current-chapter`
  - `@top-right`: Zeile 1: `v{{ document.version }}`, Zeile 2: `{{ document.date }}`
- **Fußzeile**:
  - `@bottom-left`: Zeile 1: `{{ document.author }}`, Zeile 2: Status/Vertraulichkeitsvermerk
  - `@bottom-right`: Zeile 1: `Seite counter(page) von counter(pages)`, Zeile 2: Kurztitel

---

## 4. CLI Schnittstelle

- `markpublish init [path]` – Initialisiert ein neues Projektverzeichnis.
- `markpublish build [config.yaml] [-t pdf|html|all] [-o output_dir] [--templates-dir dir]` – Rendert Ausgabedateien.
- `markpublish template list [-t pdf|html]` – Zeigt alle verfügbaren Templates und deren Ursprung an.
- `markpublish template export <theme> [target_dir] [-t pdf|html]` – Exportiert ein Template zur Anpassung.

