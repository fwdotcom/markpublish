# Kommandozeilen-Schnittstelle (CLI)

Die Kommandozeile ist die primäre Schnittstelle zur Arbeit mit markpublish. Neben dem Hauptbefehl `markpublish` steht das kurze Alias `mpub` zur Verfügung.

## Befehlsübersicht

| Befehl | Kurzbeschreibung |
| :--- | :--- |
| `build` | Kompiliert das Dokument auf Basis der Konfigurationsdatei. |
| `init` | Erstellt ein neues Projekt mit Konfigurationsdatei und Beispielkapitel. |
| `manual` | Rendert das offizielle Benutzerhandbuch aus dem installierten Paket. |
| `cheatsheet` | Rendert die kompakte zweiseitige Kurzreferenz aus dem Paket. |
| `templates` | Listet alle verfügbaren Templates und deren Herkunftsebenen auf. |
| `export-template` | Exportiert das Standard-Theme zur individuellen Anpassung in das Projekt. |
| `labels` | Zeigt alle aufgelösten Textbeschriftungen und deren Herkunftsebene (i18n) an. |

---

## markpublish build

Der Befehl `build` führt den Veröffentlichungsprozess aus. Er liest die Konfiguration ein, verarbeitet alle Markdown-Dateien der Kapitel und kompiliert das fertige Dokument.

```bash
markpublish build [CONFIG_FILE] [OPTIONEN]
```

### Optionen

| Option | Default | Bedeutung |
| :--- | :--- | :--- |
| `CONFIG_FILE` *(Argument)* | `markpublish.yaml` | Pfad zur Projekt-Konfigurationsdatei. |
| `--target`, `-t` | `pdf` | Ausgabeformat (`pdf`). |
| `--output`, `-o` | *(automatisch)* | Pfad zur Zieldatei oder zum Zielverzeichnis. Endet der Pfad ohne Dateiendung, wird er als Verzeichnis behandelt. |
| `--templates-dir` | `None` | Pfad zu einem benutzerdefinierten Vorlagen-Verzeichnis. |

### Erläuterungen

Wird kein `--output` angegeben, erzeugt markpublish die Datei im selben Verzeichnis wie die Konfigurationsdatei (standardmäßig im Projektordner). Der Dateiname leitet sich automatisch aus dem Dokumententitel ab (z. B. `mein_dokument.pdf`).

Beispiele:

```bash
# Standard-Build im aktuellen Projekt
markpublish build

# Anderes Konfigurationsfile und Ausgabeordner festlegen
markpublish build projekte/bericht.yaml --output dist/
```

---

## markpublish init

Der Befehl `init` dient dem schnellen Aufsetzen eines neuen Projekts. Er erzeugt das Verzeichnis (sofern noch nicht vorhanden), eine lauffähige `markpublish.yaml` sowie ein erstes Markdown-Kapitel.

```bash
markpublish init [ZIELORDNER] [OPTIONEN]
```

### Optionen

| Option | Default | Bedeutung |
| :--- | :--- | :--- |
| `ZIELORDNER` *(Argument)* | `.` *(aktueller Ordner)* | Zielverzeichnis, in dem das Projekt initialisiert werden soll. |
| `--title`, `-t` | `New Document` | Titel des neuen Dokuments in der erzeugten Konfiguration. |

### Erläuterungen

Die erzeugte `markpublish.yaml` enthält eine minimale, übersichtliche Konfiguration. Die Systemsprache des Autors wird automatisch ermittelt und in die Konfiguration eingetragen, sodass das Projekt auf jedem Rechner konsistent kompiliert.

Beispiel:

```bash
markpublish init mein-handbuch --title "Benutzerhandbuch System X"
```

---

## markpublish manual / markpublish cheatsheet

markpublish bringt seine vollständige Dokumentation direkt im Paket mit. Beide Befehle erzeugen die Dokumentation on-demand aus den installierten Quellen – das Ergebnis beschreibt somit immer exakt die aktuell installierte Version.

* `markpublish manual`: Rendert dieses umfassende Benutzerhandbuch.
* `markpublish cheatsheet`: Rendert eine kompakte Schnellreferenz.

```bash
markpublish manual [OPTIONEN]
markpublish cheatsheet [OPTIONEN]
```

### Optionen

| Option | Default | Bedeutung |
| :--- | :--- | :--- |
| `--lang`, `-l` | *(Systemsprache)* | Sprachauswahl des Dokuments (z. B. `de` oder `en`). |
| `--target`, `-t` | `pdf` | Ausgabeformat (`pdf`). |
| `--output`, `-o` | `.` *(aktueller Ordner)* | Zielpfad für das generierte Dokument. |
| `--theme` | `None` | Render-Vorgabe mit einem alternativen Theme anstelle des Standard-Themes. |
| `--templates-dir` | `None` | Pfad zu einem benutzerdefinierten Vorlagen-Verzeichnis. |

### Erläuterungen

Wird beim Aufruf von `manual` oder `cheatsheet` keine Sprache mit `--lang` angegeben, ermittelt markpublish automatisch die Sprache Ihres Betriebssystems. Ist für diese Sprache keine Übersetzung vorhanden, wird auf die erste im Paket vorhandene Sprache zurückgegriffen (beim Handbuch derzeit `de`).

Für eigene Dokumente gilt: Die Sprachwahl (`language: "de"`) in der `markpublish.yaml` steuert die statischen Textvariablen (wie „Inhaltsverzeichnis“, „Kapitel“, „Seite X von Y“). Diese müssen vom verwendeten Theme in dessen `i18n.yaml` bereitgestellt bzw. unterstützt werden.

Beispiel:

```bash
# Deutsches Benutzerhandbuch im aktuellen Ordner erzeugen
markpublish manual --lang de

# Englische Kurzreferenz erzeugen
markpublish cheatsheet --lang en
```

---

## markpublish templates

Listet alle im System und Projekt verfügbaren Vorlagen auf und zeigt übersichtlich an, welche Vorlage im Falle von Namensgleichheiten Vorrang hat.

```bash
markpublish templates [OPTIONEN]
```

### Optionen

| Option | Default | Bedeutung |
| :--- | :--- | :--- |
| `--target`, `-t` | `None` | Filtert die Anzeige nach Zielformat (`pdf`). |
| `--templates-dir` | `None` | Zusätzliches Vorlagen-Verzeichnis, das in die Suche einbezogen werden soll. |

### Erläuterungen

Die Ausgabe erfolgt als tabellarische Übersicht mit Angabe von Theme-Name, Herkunftsebene (User, Common oder Package) und einem Status-Indikator, welches Theme bei einem Build aktiv verwendet wird.

---

## markpublish export-template

Exportiert ein mitgeliefertes Theme aus dem markpublish-Paket in ein lokales Verzeichnis, damit es nach eigenen Wünschen angepasst oder als Vorlage für ein eigenes Corporate Design verwendet werden kann.

```bash
markpublish export-template [THEME] [ZIELVERZEICHNIS] [OPTIONEN]
```

### Optionen

| Option | Default | Bedeutung |
| :--- | :--- | :--- |
| `THEME` *(Argument)* | `default` | Name des zu exportierenden Themes. |
| `ZIELVERZEICHNIS` *(Argument)* | `templates` | Ordner, in den die Vorlagendateien kopiert werden sollen. |
| `--target`, `-t` | `all` | Zielformat der Vorlagen (`pdf` oder `all`). |

### Erläuterungen

Beim Export werden die Typst-Vorlagendateien (`template.typ`) sowie die zugehörige Beschriftungsdatei `i18n.yaml` in das Zielverzeichnis kopiert. Liegt ein Theme im Projektordner unter `templates/`, greift markpublish automatisch darauf zu.

Beispiel:

```bash
# Exportiert das Standard-Theme in den lokalen Ordner ./templates
markpublish export-template default ./templates
```

---

## markpublish labels

Zeigt eine detaillierte Aufstellung aller statischen Beschriftungen (wie „Inhaltsverzeichnis“, „Kapitel“, „Seite X von Y“) für die im Projekt gewählte Sprache sowie deren Herkunftsebene in der Kaskade.

```bash
markpublish labels [CONFIG_FILE] [OPTIONEN]
```

### Optionen

| Option | Default | Bedeutung |
| :--- | :--- | :--- |
| `CONFIG_FILE` *(Argument)* | `markpublish.yaml` | Pfad zur Projekt-Konfigurationsdatei. |
| `--target`, `-t` | `pdf` | Zielformat, dessen Beschriftungskaskade angezeigt werden soll. |
| `--templates-dir` | `None` | Benutzerdefiniertes Vorlagen-Verzeichnis. |
| `--overridden` | `False` | Zeigt ausschließlich Beschriftungen an, die durch ein Theme oder Projekt überschrieben wurden. |

### Erläuterungen

Dieser Befehl ist besonders hilfreich bei der Erstellung eigener Themes oder neuer Übersetzungen, um zu prüfen, ob alle benötigten Textbausteine vollständig vorhanden sind.

Die Spalte **i18n-Quelle** nennt die Ebene der Kaskade, aus der ein Text stammt:

| Wert | Datei |
| :--- | :--- |
| `mpub` | Der Programmstandard, `markpublish/i18n.yaml` |
| `theme` | `<theme>/i18n.yaml` |
| `target` | `<theme>/<zielformat>/i18n.yaml` |
| `projekt` | `i18n.yaml` neben Ihrer `markpublish.yaml` |

Grün hervorgehoben sind die Ebenen, die den Programmstandard ersetzt haben — genau diese zeigt `--overridden` allein. Der Sprachblock steht nur dann in Klammern dabei, wenn er von der Dokumentsprache abweicht: `(*)` für einen sprachunabhängigen Eintrag, `(en)` für einen Rückfall auf die Fallback-Sprache. Am Fuß der Ausgabe stehen die vollständigen Pfade zu allen vier Ebenen.

Zusätzlich prüft der Befehl das Theme gegen den Aufruf, den markpublish beim Rendern erzeugt. Ein Theme, dessen `setup-document` einen gesendeten Parameter nicht deklariert, wird hier gemeldet — vor dem Bauen statt währenddessen.

---

## Globale Optionen

Folgende Optionen stehen global für alle Befehle zur Verfügung:

| Option | Bedeutung |
| :--- | :--- |
| `--version`, `-v` | Gibt die installierte Version von markpublish aus und beendet das Programm. |
| `--help` | Zeigt die integrierte Hilfe und Parameterübersicht im Terminal an. |
