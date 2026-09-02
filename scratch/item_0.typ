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

#render-chapter-divider(title: "Einführung & Architektur", subtitle: "", summary: "Überblick über Zielsetzung, Kernkonzepte und die modulare Verarbeitungs-Pipeline.", tag: "Kapitel 1")

= Einführung & Architektur <einfuehrung-architektur>

Willkommen beim *markpublish Benutzerhandbuch*. `markpublish` ist ein modernes, quelloffenes Publishing-Werkzeug, das aus einfachen Markdown-Dateien professionell gesetzte *PDF-Publikationen* und *HTML-Vorschauen* erzeugt.

== Motivation & Zielsetzung <motivation-zielsetzung>

Viele Dokumentationswerkzeuge erfordern entweder komplexe LaTeX-Setups oder beschränken sich auf reine HTML-Webseiten. `markpublish` verbindet die Einfachheit von Markdown mit der typografischen Präzision von *CSS Paged Media* über die #link("https://weasyprint.org/")[WeasyPrint]-Engine.

=== Kernvorteile auf einen Blick: <kernvorteile-auf-einen-blick>

- *Modulare Kapitel*: Jedes Kapitel wird als separate Markdown-Datei gepflegt.
- *Zweistufige Gliederung*: Übergeordnete Abschnitte (_Parts_) über den Kapiteln; die Tiefe innerhalb eines Kapitels kommt aus dessen Überschriften.
- *Deklarative Steuerung*: Ein zentrales Manifest (`markpublish.yaml`) steuert Inhalt, Metadaten und Layout.
- *W3C CSS Paged Media*: Exakte Kontrolle über `@page`-Ränder, mehrzeilige Kopf- und Fußzeilen, Seitenzahlen und Trennseiten.
- *Erweiterbare Pipeline*: Saubere Trennung zwischen Parser, Renderer und Template-Ebenen.

== Die Verarbeitungs-Pipeline <die-verarbeitungs-pipeline>

Die Architektur von `markpublish` folgt einem mehrstufigen Prozess:

+ *Konfigurations-Lader (`config.loader`)*: Liest die YAML-Struktur ein, validiert Datentypen und löst dynamische Variablen (z. B. `date: auto`) auf.
+ *Template-Resolver (`templates.resolver`)*: Sucht nach der 3-stufigen Priorität (_User_ \> _Common/Workspace_ \> _Package_) nach dem passenden Theme für das Zielformat.
+ *Markdown- & TOC-Engine (`markdown.engine`)*: Parst Markdown mit erweiterten Erweiterungen (Callouts, Tabellen, Pygments-Syntax-Highlighting), vergibt konsistente Überschriftennummern (`1.1`, `1.2`) und baut Inhaltsverzeichnisse auf.
+ *Renderer (`renderers.pdf` & `renderers.html`)*: Übergibt die gerenderten HTML- und CSS-Fragmente an WeasyPrint für den PDF-Export oder speichert eigenständiges, responsives HTML.

