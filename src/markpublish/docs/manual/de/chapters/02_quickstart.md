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

Mit dem Befehl `init` legt markpublish ein neues Projektverzeichnis mit einer minimalen, lauffähigen Startstruktur an:

```bash
markpublish init mein-dokument
```

Dieser Befehl erzeugt einen neuen Ordner `mein-dokument/` mit folgender Grundstruktur:

```text
mein-dokument/
├── markpublish.yaml
└── welcome.md
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

markpublish liest die Konfigurationsdatei `markpublish.yaml`, verarbeitet die referenzierten Markdown-Dateien und kompiliert das Dokument.

### Dokument öffnen

Das generierte PDF befindet sich nun direkt in Ihrem Projektverzeichnis:

```text
mein-dokument/
└── mein_dokument.pdf
```

*(Hinweis: Der Dateiname der Ausgabe leitet sich automatisch aus dem in der `markpublish.yaml` hinterlegten Dokumententitel ab – Leerzeichen und Bindestriche werden dabei zu Unterstrichen. Ohne `--title` trägt das neue Dokument den Namen des Projektordners, hier also `mein-dokument` $\rightarrow$ `mein_dokument.pdf`.)*

Öffnen Sie die Datei mit einem beliebigen PDF-Betrachter, um das Ergebnis zu begutachten. Das Dokument enthält die formatierte Einstiegsseite mit Kopf- und Fußzeilen.
