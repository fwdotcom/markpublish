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

#render-chapter-divider(title: "Markdown-Features & Syntax", subtitle: "", summary: "Tabellen, Admonitions/Callouts, Pygments Syntax-Highlighting und Tasklisten.", tag: "Kapitel 6")

= Markdown-Features & Syntax <markdown-features-syntax>

`markpublish` beinhaltet eine leistungsfähige Markdown-Engine mit voller Unterstützung moderner Dokumentations-Elemente.

== Code-Blöcke & Syntax Highlighting <code-bloecke-syntax-highlighting>

Quellcode wird durch Pygments hervorgehoben:

```python
from markpublish.config.loader import load_config
from markpublish.markdown.engine import MarkdownPipeline

# Manifest laden
config = load_config("markpublish.yaml")
print(f"Building: {config.document.title}")
```

== Tabellen <tabellen>

Tabellen werden mit sauberem CSS-Zebramuster und Seitenumbruchschutz gerendert:

#table(
  columns: 4,
  align: (left, left, left, left),
  table.header([* Parameter *], [* Typ *], [* Standard *], [* Beschreibung *]),
  [`title`], [String], [_Pflicht_], [Haupttitel des Dokuments],
  [`author`], [String], [`None`], [Name des Autors],
  [`status`], [String], [`None`], [Dokumentstatus (z.B. "Freigegeben", "Draft")],
  [`copyright`], [String], [`None`], [Copyright-Vermerk (z.B. "© 2026 Frank Winter")],
  [`version`], [String], [`null`], [Versionskennung. Ohne Angabe entfällt das Feld auf dem Deckblatt; ist sie gesetzt, steht sie in der Fußzeile links neben dem Datum],
)

== GitHub-Style Callout-Boxen (Alerts) <github-style-callout-boxen-alerts>

`markpublish` unterstützt die gängige *GitHub-Alert-Syntax* mit fünf semantischen Typen. Die Icons stammen dabei direkt aus dem Template:

#callout(type: "note", title: [Hinweis])[
Dies ist eine informative Notiz mit blauem Akzent und passendem Info-Icon.
]

#callout(type: "tip", title: [Tipp])[
Nutzen Sie `markpublish build --target all`, um PDF und HTML parallel in einem Durchgang zu erstellen.
]

#callout(type: "important", title: [Wichtig])[
GitHub-Callouts werden automatisch anhand der Dokumentensprache lokalisiert (z. B. _Hinweis_, _Tipp_, _Wichtig_, _Warnung_, _Achtung_).
]

#callout(type: "warning", title: [Warnung])[
Achten Sie bei relativen Bildpfaden darauf, dass diese relativ zur jeweiligen Markdown-Datei liegen.
]

#callout(type: "caution", title: [Achtung])[
Fehlerhafte YAML-Einrückungen führen zu Abbruchfehlern beim Parsen des Manifests.
]

#callout(type: "tip", title: [Eigener Titel])[
Sie können nach dem Alert-Typ auch einen individuellen Titel angeben, der die Standardbeschriftung überschreibt.
]

Alternativ wird auch weiterhin die klassische `!!! note`-Syntax unterstützt.

== Tasklisten <tasklisten>

- #task-item(checked: true)[Projekt initialisieren]
- #task-item(checked: true)[Kapitel schreiben]
- #task-item(checked: false)[Dokument veröffentlichen]

