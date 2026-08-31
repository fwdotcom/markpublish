# Das Template- und Design-System

Das Template-System von `markpublish` ermöglicht vollständige visuelle Anpassbarkeit bei gleichzeitiger Wartbarkeit.

## Theme-basierte Verzeichnisstruktur

Templates sind nach Theme gruppiert, darunter liegt das Ausgabeformat. So gehören
alle Dateien eines Designs zusammen und ein Theme lässt sich als Ganzes kopieren,
weitergeben oder versionieren:

```
templates/
└── default/                       # Theme-Name
    ├── pdf/
    │   ├── layout.html            # HTML-Grundgerüst
    │   ├── styles.css             # CSS Paged Media & 2-zeilige Kopf-/Fußzeilen
    │   ├── cover.html             # Deckblatt-Template
    │   ├── part_divider.html      # Trennseite für übergeordnete Parts
    │   ├── chapter_divider.html   # Trennseite für Kapitel mit Mini-TOC
    │   └── toc.html               # Globales Inhaltsverzeichnis
    └── html/
        ├── layout.html            # Standalone Web-Layout
        ├── styles.css             # Screen/Responsive Stylesheet
        └── ...
```

> [!NOTE]
> Bis einschließlich Version 0.1 lag die Struktur umgekehrt (`templates/pdf/default`).
> Templates im alten Layout werden weiterhin gefunden, `markpublish templates` markiert
> sie in der Spalte *Layout* und gibt einen Hinweis aus. Verschieben Sie sie bei
> Gelegenheit — die alte Auflösung entfällt in einer künftigen Version.

## Die 3-stufige Auflösungs-Hierarchie

Beim Suchen nach einem Template (z. B. `default/pdf`) gilt folgende strikte Priorität:

```
1. User-Verzeichnis (~/.markpublish/templates/default/pdf/)
   │ (höchste Priorität)
   ▼
2. Gemeinsamer / Projekt-Ordner (<templates_dir>/default/pdf/)
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

## Statische Texte und Sprache

Die festen Beschriftungen in den Templates — Überschrift des Inhaltsverzeichnisses,
Kapitel-Marken, Cover-Labels, Seitenzahl-Fußzeile — stehen nicht im Template selbst,
sondern in einer Übersetzungstabelle. Ausgewählt wird sie über `document.language`:

```yaml
document:
  title: "User Guide"
  language: "en"      # steuert Beschriftungen, Callout-Titel und Datumsformat
```

Mitgeliefert sind `de` und `en`. Regionale Formen werden zugeordnet (`de-AT` → `de`),
eine unbekannte Sprache fällt auf Englisch zurück.

### Verfügbare Schlüssel

| Schlüssel | `de` | `en` |
| :--- | :--- | :--- |
| `toc_title` | Inhaltsverzeichnis | Table of Contents |
| `toc_sidebar` | Inhalt | Contents |
| `chapter_toc_title` | Inhalt dieses Kapitels | In this chapter |
| `chapter` | Kapitel | Chapter |
| `part` | Teil | Part |
| `author` | Autor | Author |
| `status` | Status | Status |
| `version` | Version | Version |
| `date` | Datum | Date |
| `copyright` | Copyright | Copyright |
| `page` | Seite | Page |
| `page_of` | von | of |
| `alert_note` | Hinweis | Note |
| `alert_tip` | Tipp | Tip |
| `alert_important` | Wichtig | Important |
| `alert_warning` | Warnung | Warning |
| `alert_caution` | Achtung | Caution |

### Einzelne Texte überschreiben

Unter `document.labels` lässt sich jeder Schlüssel gezielt ersetzen, ohne ein Template
anzufassen:

```yaml
document:
  language: "de"
  labels:
    chapter_toc_title: "Auf dieser Seite"
    part: "Abschnitt"
```

Dieselbe Stelle dient dazu, eine noch nicht mitgelieferte Sprache vollständig selbst zu
setzen — die Tabelle wird geschichtet: Englisch als Basis, darüber die Dokumentsprache,
darüber `labels`. Ein fehlender Eintrag erzeugt deshalb nie einen leeren Text.

> [!TIP]
> In eigenen Templates greifen Sie mit `{{ labels.chapter }}` auf die Tabelle zu — auch
> in `styles.css`, das durch dieselbe Jinja-Umgebung läuft. So ist die Fußzeile
> `"{{ labels.page }} " counter(page) " {{ labels.page_of }} " counter(pages)` gebaut.

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

