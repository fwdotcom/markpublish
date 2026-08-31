# Das Template- und Design-System

Das Template-System von `markpublish` ermöglicht vollständige visuelle Anpassbarkeit bei gleichzeitiger Wartbarkeit.

## Target-basierte Verzeichnisstruktur

Templates sind nach dem Ausgabeformat strukturiert:

```
templates/
├── pdf/
│   └── default/
│       ├── layout.html            # HTML-Grundgerüst
│       ├── styles.css             # CSS Paged Media & 2-zeilige Kopf-/Fußzeilen
│       ├── cover.html             # Deckblatt-Template
│       ├── part_divider.html      # Trennseite für übergeordnete Parts
│       ├── chapter_divider.html   # Trennseite für Kapitel mit Mini-TOC
│       └── toc.html               # Globales Inhaltsverzeichnis
└── html/
    └── default/
        ├── layout.html            # Standalone Web-Layout
        ├── styles.css             # Screen/Responsive Stylesheet
        └── ...
```

## Die 3-stufige Auflösungs-Hierarchie

Beim Suchen nach einem Template (z. B. `pdf/default`) gilt folgende strikte Priorität:

```
1. User-Verzeichnis (~/.markpublish/templates/pdf/default/)
   │ (höchste Priorität)
   ▼
2. Gemeinsamer / Projekt-Ordner (<templates_dir>/pdf/default/)
   │
   ▼
3. Paket Built-in (im markpublish Python-Paket)
```

### Konfiguration des gemeinsamen Template-Ordners
Sie können den gemeinsamen Template-Pfad auf 4 Wegen festlegen:
1. **CLI-Parameter**: `markpublish build --templates-dir /pfad/zu/templates`
2. **In `markpublish.yaml`**: `templates_dir: "./custom-templates"`
3. **Umgebungsvariable**: `MARKPUBLISH_TEMPLATES_DIR=/pfad/zu/templates`
4. **Automatischer Fallback**: `./templates` im Projektordner.

## 2-zeilige Kopf- und Fußzeilen

Kopf- und Fußzeilen werden im Template via CSS Paged Media `@page` Margin-Boxes definiert:

```css
@page {
  size: A4;
  margin: 25mm 20mm 25mm 20mm;

  @top-left {
    content: "{{ document.title }}\A" string(current_section);
    font-size: 8pt;
    white-space: pre-wrap;
    border-bottom: 0.5pt solid #cbd5e1;
  }

  @top-right {
    content: "v{{ document.version }}\A{{ document.date }}";
    font-size: 8pt;
    text-align: right;
    white-space: pre-wrap;
    border-bottom: 0.5pt solid #cbd5e1;
  }

  @bottom-left {
    content: "{{ document.author or '' }}\A{{ document.copyright or document.status or '' }}";
    font-size: 8pt;
    white-space: pre-wrap;
    border-top: 0.5pt solid #cbd5e1;
  }

  @bottom-right {
    content: "Seite " counter(page) " von " counter(pages);
    font-size: 8pt;
    text-align: right;
    border-top: 0.5pt solid #cbd5e1;
  }
}
```

