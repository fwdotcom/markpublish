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

Die festen Beschriftungen — Überschrift des Inhaltsverzeichnisses, Kapitel-Marken,
Cover-Labels, Seitenzahl-Fußzeile, Callout-Titel — stehen nicht im Template, sondern in
`i18n.yaml`-Dateien. Welche Sprache gilt, bestimmt `document.language`:

```yaml
document:
  title: "User Guide"
  language: "en"      # steuert Beschriftungen, Callout-Titel und Datumsformat
```

Mitgeliefert sind `de` und `en`. Regionale Formen werden zugeordnet (`de-AT` → `de`),
eine unbekannte Sprache fällt auf Englisch zurück.

> [!NOTE]
> **i18n** bezeichnet die Quellen — die Dateien und den YAML-Eintrag, jeweils über alle
> Sprachen. **labels** ist das daraus aufgelöste Ergebnis für *ein* Dokument in *einer*
> Sprache: das, was im Template unter `{{ labels.chapter }}` ankommt.

### Die 4-stufige i18n-Kaskade

Alle vier Ebenen sind **identisch aufgebaut**: Sprachcode auf oberster Ebene, darunter
die Texte. Jede tiefere Ebene überschreibt die höher liegende — und zwar **nur die
Schlüssel, die sie tatsächlich setzt**. Alles andere bleibt, wie es weiter oben steht:

```
1. Programm      markpublish/i18n.yaml
   │             vollständig, de + en
   ▼
2. Theme         <templates>/<theme>/i18n.yaml
   │             gilt für alle Zielformate des Themes
   ▼
3. Zielformat    <templates>/<theme>/<target>/i18n.yaml
   │             nur für PDF bzw. nur für HTML
   ▼
4. Dokument      document.i18n in der markpublish.yaml
                 höchste Priorität
```

Ebene 1 ist die einzige, die vollständig sein muss. Sie legt zusätzlich Englisch unter
die Dokumentsprache, damit jeder Schlüssel garantiert auflöst. Die Ebenen 2–4 sind
reine Overrides.

> [!IMPORTANT]
> Die Ebenen 2–4 greifen **nur für die gewählte Sprache**. Ein Theme, das einen
> `en:`-Block definiert, verändert eine deutsche Ausgabe nicht — sonst würden englische
> Theme-Texte in fremdsprachige Dokumente durchschlagen.

### Das gemeinsame Format

```yaml
# templates/mytheme/i18n.yaml
de:
  part: "Abschnitt"
  chapter_toc_title: "Auf dieser Seite"
en:
  part: "Section"
  chapter_toc_title: "On this page"
```

Der Sonderschlüssel `"*"` gilt für **jede** Sprache und wird vor dem sprachspezifischen
Block angewendet — für Begriffe, die unabhängig von der Dokumentsprache gleich heißen:

```yaml
"*":
  version: "Rev."       # in jeder Sprache "Rev."
de:
  part: "Abschnitt"
```

Wer nur eine Sprache pflegt, darf die Sprachebene auch weglassen; die flache Form ist
gleichbedeutend mit `"*"`:

```yaml
part: "Abschnitt"       # entspricht:  "*":\n  part: "Abschnitt"
```

Regionale Blöcke schlagen den Basis-Block: bei `language: "de-AT"` gewinnt `de-at:`
über `de:`. Fehlt eine `i18n.yaml`, ist das kein Fehler — ein Theme ohne eigene Texte
ist der Normalfall. Ist sie vorhanden, aber fehlerhaft, bricht der Build mit Angabe der
Datei ab, statt still die Standardtexte zu verwenden.

### Beispiel: PDF und HTML unterschiedlich beschriften

```
templates/mytheme/
├── i18n.yaml            de: chapter: "Kapitel"
├── pdf/
│   └── i18n.yaml        de: chapter: "Kap."      ← nur im PDF
└── html/
    └── i18n.yaml        (leer → erbt "Kapitel")
```

Das mitgelieferte Theme `default` bringt alle drei Dateien als **auskommentiertes
Muster** mit: `templates/default/i18n.yaml`, `default/pdf/i18n.yaml` und
`default/html/i18n.yaml`. Sie sind bewusst wirkungslos — das Standard-Theme soll exakt
wie der Programmstandard aussprechen. Kommentieren Sie aus, was Sie ändern möchten.

### Ebene 4: Texte für ein einzelnes Dokument

In der `markpublish.yaml` unter `document.i18n`, mit demselben Aufbau:

```yaml
document:
  language: "de"
  i18n:
    de:
      part: "Abschnitt"
      chapter_toc_title: "Auf einen Blick"
```

Genau so ist dieses Handbuch konfiguriert — die Trennseiten zeigen deshalb *Auf einen
Blick* statt *Inhalt dieses Kapitels* und der Anhang-Block *Abschnitt* statt *Teil*.

Dieselbe Stelle dient dazu, eine noch nicht mitgelieferte Sprache vollständig selbst zu
setzen.

### Die aufgelöste Tabelle ansehen

Bei vier Ebenen ist nicht immer offensichtlich, woher ein Text kommt. `markpublish
labels` zeigt das Ergebnis samt Herkunft:

```bash
markpublish labels                       # alle Schlüssel, Ziel PDF
markpublish labels --target html         # Kaskade für die HTML-Ausgabe
markpublish labels --overridden          # nur das, was von Ebene 2-4 kommt
```

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

Eine neue Sprache legen Sie an, indem Sie in `markpublish/i18n.yaml` einen
vollständigen Block ergänzen — oder, ohne das Paket anzufassen, auf Ebene 2–4 alle
Schlüssel unter dem gewünschten Sprachcode setzen.

> [!TIP]
> In eigenen Templates greifen Sie mit `{{ labels.chapter }}` auf das Ergebnis zu — auch
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

