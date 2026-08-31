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

Dieser Befehl erstellt die folgende Verzeichnisstruktur:

```
mein-leitfaden/
├── markpublish.yaml          # Das Dokumenten-Manifest
└── chapters/                 # Markdown-Kapiteldateien
    ├── 01_introduction.md
    ├── 02_architecture.md
    ├── 02_1_details.md
    └── 03_appendix.md
```

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

