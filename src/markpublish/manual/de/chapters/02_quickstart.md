# Installation & Schnellstart

In diesem Kapitel erfahren Sie, wie Sie `markpublish` installieren und in weniger als zwei Minuten Ihr erstes Dokument kompilieren.

## Voraussetzungen

`markpublish` benötigt **Python 3.10 oder neuer**. Es läuft nativ unter:
- **Windows** (10, 11, Server)
- **macOS** (Intel und Apple Silicon)
- **Linux** (Debian, Ubuntu, Fedora, Arch, etc.)

## Installation via pip

Installieren Sie das Paket über den Python-Paketmanager:

```bash
pip install markpublish
```

Für Entwickler oder zur Installation aus dem Quellcode:

```bash
git clone https://github.com/your-username/markpublish.git
cd markpublish
pip install -e ".[dev]"
```

## Erstes Projekt initialisieren

Verwenden Sie den Befehl `init`, um eine neue Dokumentenstruktur zu erzeugen:

```bash
markpublish init mein-leitfaden --title "Mein Leitfaden"
cd mein-leitfaden
```

Der Befehl legt einen bewusst minimalen Stumpf an — zwei Dateien, direkt im
Zielordner:

```
mein-leitfaden/
├── markpublish.yaml          # Das Dokumenten-Manifest
└── next-steps.md             # Ein Kapitel, zum Ersetzen gedacht
```

Mehr Beispielinhalt gibt es nicht, denn alles, was `init` schreibt, löschen Sie
beim ersten echten Kapitel wieder. Die Referenz liegt deshalb nicht im Stumpf,
sondern in `markpublish cheatsheet` — dort bleibt sie auch dann verfügbar, wenn
die letzte Stumpfdatei verschwunden ist.

## Nachschlagen

```bash
markpublish cheatsheet         # zweiseitige Kurzreferenz
markpublish manual             # dieses Handbuch
markpublish manual --lang de   # Handbuch auf Deutsch
markpublish manual --lang en   # Handbuch auf Englisch
```

Beide werden aus Quellen gerendert, die im Paket mitgeliefert werden — sie
passen also immer zur installierten Version. Ein erfolgreicher Lauf ist zugleich
der Nachweis, dass die Rendering-Kette funktioniert; unter Windows also, dass
WeasyPrint seine GTK-Laufzeit findet.

Der Parameter `--lang` waehlt die Sprachquelle des Handbuchs, nicht nur die
Beschriftungen der Oberflaeche.

## Dokument erstellen

Rendern Sie Ihr Dokument mit dem `build`-Befehl:

```bash
# PDF erstellen (Standard)
markpublish build

# HTML-Vorschau erzeugen
markpublish build --target html

# Sowohl PDF als auch HTML in einem Durchgang bauen
markpublish build --target all
```

Die fertigen Dateien werden direkt im Projektordner abgelegt.

