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

#render-chapter-divider(title: "Installation & Schnellstart", subtitle: "", summary: "Schritt-für-Schritt-Anleitung zur Installation und Erstellung des ersten Dokuments.", tag: "Kapitel 2")

= Installation & Schnellstart <installation-schnellstart>

In diesem Kapitel erfahren Sie, wie Sie `markpublish` installieren und in weniger als zwei Minuten Ihr erstes Dokument kompilieren.

== Voraussetzungen <voraussetzungen>

`markpublish` benötigt *Python 3.10 oder neuer*. Es läuft nativ unter:

- *Windows* (10, 11, Server)
- *macOS* (Intel und Apple Silicon)
- *Linux* (Debian, Ubuntu, Fedora, Arch, etc.)

== Installation via pip <installation-via-pip>

Installieren Sie das Paket über den Python-Paketmanager:

```bash
pip install markpublish
```

Für Entwickler oder zur Installation aus dem Quellcode:

```bash
git clone https://github.com/fwdotcom/markpublish.git
cd markpublish
pip install -e ".[dev]"
```

== Erstes Projekt initialisieren <erstes-projekt-initialisieren>

Verwenden Sie den Befehl `init`, um eine neue Dokumentenstruktur zu erzeugen:

```bash
markpublish init mein-leitfaden --title "Mein Leitfaden"
cd mein-leitfaden
```

Der Befehl legt einen bewusst minimalen Stumpf an — zwei Dateien, direkt im Zielordner:

```
mein-leitfaden/
├── markpublish.yaml          # Das Dokumenten-Manifest
└── next-steps.md             # Ein Kapitel, zum Ersetzen gedacht
```

== Nachschlagen <nachschlagen>

```bash
# zweiseitige Kurzreferenz
markpublish cheatsheet [--lang CODE] [--target pdf|html|all] [--output PFAD] [--theme NAME]

# dieses Handbuch
markpublish manual [--lang CODE] [--target pdf|html|all] [--output PFAD] [--theme NAME]
```

Beide werden aus Quellen gerendert, die im Paket mitgeliefert werden — sie passen also immer zur installierten Version. Ein erfolgreicher Lauf ist zugleich der Nachweis, dass die Rendering-Kette funktioniert; unter Windows also, dass WeasyPrint seine GTK-Laufzeit findet.

Ohne `--lang` entscheidet die Sprache Ihres Systems; gibt es dafür keine Übersetzung, erscheint die englische. Der Parameter wählt die *Quelle* des Handbuchs, nicht bloß die Beschriftungen der Oberfläche.

== Dokument erstellen <dokument-erstellen>

Rendern Sie Ihr Dokument mit dem `build`-Befehl:

```bash
# PDF aus dem aktuellen Projektverzeichnis erstellen
markpublish build

# HTML-Ausgabe erzeugen
markpublish build --target html

# Sowohl PDF als auch HTML in einem Durchgang bauen
markpublish build --target all
```

Die fertigen Dateien werden direkt im Projektordner abgelegt.

