# Installation und Schnellstart

Dieses Kapitel beschreibt den direkten Weg von der Installation bis zum ersten fertig erstellten PDF-Dokument.

## Voraussetzungen

Für den Betrieb von markpublish wird eine funktionierende Python-Installation benötigt:

* **Python-Version:** 3.10 oder neuer
* **Betriebssystem:** Windows, macOS oder Linux

## Installation

markpublish wird komfortabel über den Python-Paketmanager `pip` installiert:

```bash
pip install markpublish
```

Nach Abschluss der Installation steht der Befehl `markpublish` (sowie das kurze Alias `mpub`) im Terminal zur Verfügung. Die erfolgreiche Bereitstellung lässt sich mit folgendem Aufruf prüfen:

```bash
markpublish --version
```

## Schritte bis zum ersten Build

Die Erstellung eines neuen Dokumentenprojekts erfolgt in wenigen einfachen Schritten:

### Neues Projekt initialisieren

Mit dem Befehl `init` legt markpublish ein neues Projektverzeichnis mit einer lauffähigen Beispielstruktur an:

```bash
markpublish init mein-dokument
```

Dieser Befehl erzeugt einen neuen Ordner `mein-dokument/` mit folgender Grundstruktur:

```text
mein-dokument/
├── markpublish.yaml
└── chapters/
    └── 01_einleitung.md
```

### In das Projektverzeichnis wechseln

Wechseln Sie in das neu angelegte Verzeichnis:

```bash
cd mein-dokument
```

### Erstes PDF erstellen

Starten Sie den Veröffentlichungsprozess direkt aus dem Projektverzeichnis heraus:

```bash
markpublish build
```

markpublish liest die Konfigurationsdatei `markpublish.yaml`, verarbeitet die Kapitel im Ordner `chapters/` und erstellt das Dokument.

### Dokument öffnen

Das generierte PDF befindet sich nun im Unterordner `dist/`:

```text
dist/
└── mein-dokument.pdf
```

Öffnen Sie die Datei mit einem beliebigen PDF-Betrachter, um das Ergebnis zu begutachten. Das Dokument enthält bereits ein gestaltetes Deckblatt, ein Inhaltsverzeichnis, Kopf- und Fußzeilen sowie das erste formatierte Kapitel.
