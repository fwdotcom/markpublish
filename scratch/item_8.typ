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

#pagebreak()

= Anhang B: Fehlerbehebung & FAQ <anhang-b-fehlerbehebung-faq>

Häufige Fragen, Fehlermeldungen und Lösungen bei der Dokumentenerstellung.

#table(
  columns: 3,
  align: (left, left, left),
  table.header([* Problem / Fehlermeldung *], [* Mögliche Ursache *], [* Lösung *]),
  [`cannot load library 'libgobject-2.0-0'`], [WeasyPrint benötigt auf Windows die C-Bibliotheken von Pango und GTK.], [GTK3-Runtime installieren (#link("https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer")[GTK-Installer]) oder MSYS2: `pacman -S mingw-w64-x86_64-pango`. Schnelle Alternative: `--target html` rendert ohne WeasyPrint.],
  [Leere Bildrahmen / fehlende Grafiken im PDF], [Bildpfad ist falsch oder absolut statt relativ notiert.], [Pfade immer relativ zur jeweiligen Markdown-Datei angeben (z. B. `images/diag.png`). markpublish bettet Grafiken bis 12 MB als Data-URI ein.],
  [Inhaltsverzeichnis: Falsche Seitenzahlen], [Manuell vergebene Heading-IDs kollidieren im Zweipass-Rendering.], [Automatische Eindeutigkeit von markpublish nutzen oder manuell vergebene Anker (`{#id}`) prüfen.],
  [`Label 'x' is used in template but defined in no i18n level`], [Ein Theme verwendet einen statischen Textschlüssel, der in keiner `i18n.yaml` deklariert ist.], [Schlüssel in `<theme>/i18n.yaml` für alle Sprachen oder unter `*` eintragen. Gültige Texte mit `markpublish labels` prüfen.],
  [`cheatsheet` oder `manual` ignoriert Arbeitsordner-Theme], [Eingebaute Referenzen nutzen standardmäßig das robuste Built-in-Theme.], [Mit `--theme <name>` explizit das Rendern im eigenen Theme anfordern.],
)

