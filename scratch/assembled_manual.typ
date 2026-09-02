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
    page: "Seite",
    page_of: "von",
    chapter: "Kapitel",
    part: "Teil",
  ),
  doc,
)

#pagebreak()

#render-chapter-divider(title: "Einführung & Architektur", subtitle: "", summary: "Überblick über Zielsetzung, Kernkonzepte und die modulare Verarbeitungs-Pipeline.", tag: "Kapitel 1", toc-title: "Inhalt dieses Kapitels", toc-items: ())

= 1 Einführung & Architektur <einfuehrung-architektur>

Willkommen beim #strong[markpublish Benutzerhandbuch]. `markpublish` ist ein modernes, quelloffenes Publishing-Werkzeug, das aus einfachen Markdown-Dateien professionell gesetzte #strong[PDF-Publikationen] und #strong[HTML-Vorschauen] erzeugt.

== 1.1 Motivation & Zielsetzung <motivation-zielsetzung>

Viele Dokumentationswerkzeuge erfordern entweder komplexe LaTeX-Setups oder beschränken sich auf reine HTML-Webseiten. `markpublish` verbindet die Einfachheit von Markdown mit der typografischen Präzision von #strong[CSS Paged Media] über die #link("https://weasyprint.org/")[WeasyPrint]-Engine.

=== 1.1.1 Kernvorteile auf einen Blick: <kernvorteile-auf-einen-blick>

- #strong[Modulare Kapitel]: Jedes Kapitel wird als separate Markdown-Datei gepflegt.
- #strong[Zweistufige Gliederung]: Übergeordnete Abschnitte (#emph[Parts]) über den Kapiteln; die Tiefe innerhalb eines Kapitels kommt aus dessen Überschriften.
- #strong[Deklarative Steuerung]: Ein zentrales Manifest (`markpublish.yaml`) steuert Inhalt, Metadaten und Layout.
- #strong[W3C CSS Paged Media]: Exakte Kontrolle über `@page`-Ränder, mehrzeilige Kopf- und Fußzeilen, Seitenzahlen und Trennseiten.
- #strong[Erweiterbare Pipeline]: Saubere Trennung zwischen Parser, Renderer und Template-Ebenen.

== 1.2 Die Verarbeitungs-Pipeline <die-verarbeitungs-pipeline>

Die Architektur von `markpublish` folgt einem mehrstufigen Prozess:

+ #strong[Konfigurations-Lader (`config.loader`)]: Liest die YAML-Struktur ein, validiert Datentypen und löst dynamische Variablen (z. B. `date: auto`) auf.
+ #strong[Template-Resolver (`templates.resolver`)]: Sucht nach der 3-stufigen Priorität (#emph[User] \> #emph[Common/Workspace] \> #emph[Package]) nach dem passenden Theme für das Zielformat.
+ #strong[Markdown- & TOC-Engine (`markdown.engine`)]: Parst Markdown mit erweiterten Erweiterungen (Callouts, Tabellen, Pygments-Syntax-Highlighting), vergibt konsistente Überschriftennummern (`1.1`, `1.2`) und baut Inhaltsverzeichnisse auf.
+ #strong[Renderer (`renderers.pdf` & `renderers.html`)]: Übergibt die gerenderten HTML- und CSS-Fragmente an WeasyPrint für den PDF-Export oder speichert eigenständiges, responsives HTML.


#pagebreak()

#render-chapter-divider(title: "Installation & Schnellstart", subtitle: "", summary: "Schritt-für-Schritt-Anleitung zur Installation und Erstellung des ersten Dokuments.", tag: "Kapitel 2", toc-title: "Inhalt dieses Kapitels", toc-items: ((title: "2.1 Voraussetzungen", slug: "voraussetzungen", indent: 0pt), (title: "2.2 Installation via pip", slug: "installation-via-pip", indent: 0pt), (title: "2.3 Erstes Projekt initialisieren", slug: "erstes-projekt-initialisieren", indent: 0pt), (title: "2.4 Nachschlagen", slug: "nachschlagen", indent: 0pt), (title: "2.5 Dokument erstellen", slug: "dokument-erstellen", indent: 0pt)))

= 2 Installation & Schnellstart <installation-schnellstart>

In diesem Kapitel erfahren Sie, wie Sie `markpublish` installieren und in weniger als zwei Minuten Ihr erstes Dokument kompilieren.

== 2.1 Voraussetzungen <voraussetzungen>

`markpublish` benötigt #strong[Python 3.10 oder neuer]. Es läuft nativ unter:

- #strong[Windows] (10, 11, Server)
- #strong[macOS] (Intel und Apple Silicon)
- #strong[Linux] (Debian, Ubuntu, Fedora, Arch, etc.)

== 2.2 Installation via pip <installation-via-pip>

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

== 2.3 Erstes Projekt initialisieren <erstes-projekt-initialisieren>

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

== 2.4 Nachschlagen <nachschlagen>

```bash
# zweiseitige Kurzreferenz
markpublish cheatsheet [--lang CODE] [--target pdf|html|all] [--output PFAD] [--theme NAME]

# dieses Handbuch
markpublish manual [--lang CODE] [--target pdf|html|all] [--output PFAD] [--theme NAME]
```

Beide werden aus Quellen gerendert, die im Paket mitgeliefert werden — sie passen also immer zur installierten Version. Ein erfolgreicher Lauf ist zugleich der Nachweis, dass die Rendering-Kette funktioniert; unter Windows also, dass WeasyPrint seine GTK-Laufzeit findet.

Ohne `--lang` entscheidet die Sprache Ihres Systems; gibt es dafür keine Übersetzung, erscheint die englische. Der Parameter wählt die #strong[Quelle] des Handbuchs, nicht bloß die Beschriftungen der Oberfläche.

== 2.5 Dokument erstellen <dokument-erstellen>

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


#pagebreak()

#render-chapter-divider(title: "Die CLI-Befehle", subtitle: "", summary: "Alle Befehle im Detail: build, init, cheatsheet, manual, templates, export-template und labels.", tag: "Kapitel 3", toc-title: "Inhalt dieses Kapitels", toc-items: ((title: "3.1 Befehlsübersicht", slug: "befehlsuebersicht", indent: 0pt), (title: "3.2 markpublish init", slug: "markpublish-init", indent: 0pt), (title: "3.3 markpublish cheatsheet", slug: "markpublish-cheatsheet", indent: 0pt), (title: "3.4 markpublish manual", slug: "markpublish-manual", indent: 0pt), (title: "3.5 markpublish build", slug: "markpublish-build", indent: 0pt), (title: "3.6 markpublish templates", slug: "markpublish-templates", indent: 0pt), (title: "3.7 markpublish export-template", slug: "markpublish-export-template", indent: 0pt), (title: "3.8 markpublish labels", slug: "markpublish-labels", indent: 0pt)))

= 3 Die CLI-Befehle <die-cli-befehle>

`markpublish` bietet eine schlanke, intuitive Befehlszeilenschnittstelle (CLI), die über `markpublish` oder die Kurzform `mpub` aufgerufen werden kann.

== 3.1 Befehlsübersicht <befehlsuebersicht>

#table(
  columns: (1fr, 2fr),
  align: (left, left),
  table.header([* Befehl *], [* Kurzbeschreibung *]),
  [`markpublish init`], [Erzeugt einen minimalen Projektstumpf (zwei Dateien)],
  [`markpublish cheatsheet`], [Rendert die zweiseitige Kurzreferenz],
  [`markpublish manual`], [Rendert dieses Handbuch],
  [`markpublish build`], [Kompiliert das Dokument zu PDF und/oder HTML],
  [`markpublish templates`], [Listet alle gefundenen Templates und deren Quellen auf],
  [`markpublish export-template`], [Exportiert ein Template zur individuellen Anpassung],
  [`markpublish labels`], [Zeigt die aufgelösten statischen Texte und ihre Herkunft],
)

== 3.2 `markpublish init` <markpublish-init>

Legt einen minimalen Projektstumpf an: eine `markpublish.yaml` und ein Kapitel `next-steps.md`, beide direkt im Zielordner. Kein `chapters/`-Verzeichnis, keine Beispielkapitel.

```bash
markpublish init [ZIELORDNER] [--title "Titel"]
```

Der Stumpf ist absichtlich klein, weil er dazu da ist, gelöscht zu werden — spätestens beim ersten echten Kapitel. Die Referenz liegt deshalb nicht im Stumpf, sondern in `markpublish cheatsheet`; sowohl die YAML als auch das Kapitel verweisen darauf. Cover und Inhaltsverzeichnis sind abgeschaltet, weil ein einseitiger Entwurf beides nicht braucht.

== 3.3 `markpublish cheatsheet` <markpublish-cheatsheet>

Rendert die mitgelieferte Kurzreferenz: Seite 1 die Schlüssel der `markpublish.yaml`, Seite 2 die Grundlagen zu Themes und Templates.

```bash
markpublish cheatsheet [--lang CODE] [--target pdf|html|all] [--output PFAD] [--theme NAME]
```

== 3.4 `markpublish manual` <markpublish-manual>

Rendert dieses Handbuch.

```bash
markpublish manual [--lang CODE] [--target pdf|html|all] [--output PFAD] [--theme NAME]
```

=== 3.4.1 Gemeinsames Verhalten der beiden Dokumentbefehle <gemeinsames-verhalten-der-beiden-dokumentbefehle>

Beide Quellen liegen im Paket und werden bei jedem Aufruf neu gerendert. Damit passt das Ergebnis immer zur installierten Version, und ein erfolgreicher Lauf ist zugleich der Nachweis, dass die Rendering-Kette funktioniert — unter Windows also, dass WeasyPrint seine GTK-Laufzeit findet. Geschrieben wird nur das fertige Dokument, und zwar ins aktuelle Verzeichnis; Quelldateien landen nie im Projekt des Nutzers.

#table(
  columns: (1.2fr, 1.2fr, 2fr),
  align: (left, left, left),
  table.header([* Option *], [* Standard *], [* Bedeutung *]),
  [`--lang`, `-l`], [Systemsprache], [Welche Übersetzung gerendert wird. `markpublish manual --lang de`],
  [`--target`, `-t`], [`pdf`], [`pdf`, `html` oder `all`],
  [`--output`, `-o`], [aktuelles Verzeichnis], [Datei oder Verzeichnis],
  [`--theme`], [mitgeliefert], [Rendert in einem eigenen Theme],
)

`--lang` wählt die #strong[Quelle], nicht bloß die Beschriftungen — jede Übersetzung bringt ihre eigene `language:` mit und zieht damit die passenden statischen Texte von selbst nach.

Ohne Angabe entscheidet die Sprache Ihres Systems. Diese beiden Dokumente richten sich an die Person vor dem Rechner und nicht an ein Publikum; deren Sprache ist damit die beste verfügbare Vermutung. Gibt es dafür keine Übersetzung, erscheint kommentarlos die englische — verlangt wurde ja nichts. Ein ausdrückliches `--lang fr` dagegen wird gemeldet, statt still einen englischen Rahmen um eine französische Erwartung zu setzen.

Ohne `--theme` oder `--templates-dir` ignorieren beide Befehle bewusst User- und Projekt-Themes und rendern im mitgelieferten. Sonst zöge ein `templates/` im Arbeitsverzeichnis — mit `export-template` angelegt und noch mitten in der Anpassung — die Referenz mit sich: ein fehlendes Label ließe den Build abbrechen, ausgerechnet in dem Moment, in dem jemand nachschlagen will, wie Labels funktionieren.

Fällt der PDF-Weg mangels GTK aus, liefert `--target html` dieselben Dokumente ohne WeasyPrint.

== 3.5 `markpublish build` <markpublish-build>

Kompiliert eine `markpublish.yaml`-Konfiguration.

```bash
markpublish build [CONFIG_FILE] [OPTIONEN]
```

=== 3.5.1 Argumente & Optionen: <argumente-optionen>

- `CONFIG_FILE` #emph[(optional, Standard: `markpublish.yaml`)]: Pfad zur YAML-Datei.
- `--target / -t` #emph[(Standard: `pdf`)]: Zielformat (`pdf`, `html` oder `all`).
- `--output / -o`: Benutzerdefinierter Ausgabepfad (Datei oder Verzeichnis).
- `--templates-dir`: Spezifischer Pfad zu einem gemeinsamen Template-Verzeichnis.

=== 3.5.2 Beispiele: <beispiele>

```bash
# Standard-Build aus aktuellem Verzeichnis
markpublish build

# HTML-Version in ein bestimmtes Zielverzeichnis ausgeben
markpublish build markpublish.yaml -t html -o dist/

# Benutzerdefiniertes Template-Verzeichnis nutzen
markpublish build --templates-dir /shared/company-templates
```

#callout(type: "note", title: [Hinweis])[
`build` hat bewusst kein `--lang`. Die Sprache eines Dokuments gehört in seine eigene `markpublish.yaml`, neben `title` und `author`: sie beschreibt, in welcher Sprache das Dokument #emph[geschrieben ist]. Ein Override von der Kommandozeile würde lediglich die siebzehn statischen Beschriftungen um unveränderten Fließtext herum austauschen.
]

== 3.6 `markpublish templates` <markpublish-templates>

Zeigt eine tabellarische Übersicht aller Templates auf dem System und deren Prioritätsstatus:

```bash
markpublish templates
markpublish templates --target pdf
```

== 3.7 `markpublish export-template` <markpublish-export-template>

Kopiert das eingebaute Standard-Template in Ihr lokales Arbeitsverzeichnis:

```bash
markpublish export-template default templates
```

== 3.8 `markpublish labels` <markpublish-labels>

Zeigt, welcher statische Text am Ende gilt und aus welcher Ebene der Label-Kaskade er stammt. Nützlich, sobald ein Theme oder ein Dokument eigene Texte mitbringt und nicht mehr offensichtlich ist, welche Ebene gewinnt.

```bash
markpublish labels                          # alle Schlüssel, Zielformat PDF
markpublish labels --target html            # Kaskade für die HTML-Ausgabe
markpublish labels --overridden             # nur überschriebene Texte
markpublish labels pfad/zu/markpublish.yaml
```

=== 3.8.1 Argumente & Optionen <argumente-optionen-1>

#table(
  columns: (1.2fr, 0.9fr, 1fr, 2fr),
  align: (left, left, left, left),
  table.header([* Parameter *], [* Typ *], [* Standard *], [* Beschreibung *]),
  [`config_file`], [Pfad], [`markpublish.yaml`], [Pfad zur Konfigurationsdatei],
  [`--target`, `-t`], [String], [`pdf`], [Zielformat, dessen Kaskade gezeigt wird (`pdf` oder `html`)],
  [`--templates-dir`], [Pfad], [–], [Alternativer Template-Ordner],
  [`--overridden`], [Flag], [aus], [Nur Texte anzeigen, die das Theme ändert],
)

Die Spalte #emph[Source] nennt die Ebene: `i18n.yaml (de)` für den Programmstandard oder den Pfad einer Theme- bzw. Zielformat-`i18n.yaml`. Unter der Tabelle steht, in welchen Dateien nach Overrides gesucht wurde und welche existieren.

#callout(type: "tip", title: [Tipp])[
`--overridden` beantwortet die häufigste Frage direkt: #emph[Was weicht in diesem Projekt überhaupt vom Standard ab?]
]


#pagebreak()

#render-chapter-divider(title: "Konfigurations-Leitfaden", subtitle: "", summary: "Deklarative Definition von Dokumentenmetadaten, Kapiteln und Hierarchien.", tag: "Kapitel 4", toc-title: "Inhalt dieses Kapitels", toc-items: ((title: "4.1 Das document-Objekt", slug: "das-document-objekt", indent: 0pt), (title: "4.2 Kapitel definieren", slug: "kapitel-definieren", indent: 0pt), (title: "4.3 Dokumentaufbau in 2 Stufen: Parts und Kapitel", slug: "dokumentaufbau-in-2-stufen-parts-und-kapitel", indent: 0pt)))

= 4 Konfigurations-Leitfaden <konfigurations-leitfaden>

Die Datei `markpublish.yaml` ist das zentrale Steuerungsdokument jeder Publikation.

== 4.1 Das `document`-Objekt <das-document-objekt>

Unter `document:` werden alle globalen Metadaten und Schalter hinterlegt:

```yaml
document:
  title: "markpublish Benutzerhandbuch"
  subtitle: "Moderne PDF- und HTML-Dokumentenerstellung"
  summary: "Kurze Zusammenfassung für Deckblatt und Metadaten."
  author: "Frank Winter"
  organisation: "WASDCAT Games"
  date: "auto"                 # "auto" (Tagesdatum) oder festes Datum "2026-08-31"
  version: "1.0.0"             # optional - ohne Angabe entfällt das Feld
  language: "de"               # Beschriftungen und Datumsformat; ohne Angabe die Systemsprache

  # Globale Schalter
  cover: true                  # Deckblatt an/aus
  document_toc: 2              # Großes Verzeichnis, zwei Ebenen tief
  autonum_style: "decimal"     # "decimal", "roman", "legal", "none"
  chapter_toc: 2               # Vorgabe für die Kapitel-Trennseiten
  header: true                 # Laufende Kopfzeile
  footer: true                 # Laufende Fußzeile
```

=== 4.1.1 Automatische Datumsauflösung <automatische-datumsaufloesung>

Wird `date: "auto"` oder `date: "today"` angegeben, setzt `markpublish` das aktuelle Datum im passenden Sprachformat ein:

- `language: "de"` → `31.08.2026`
- `language: "en"` → `2026-08-31`

=== 4.1.2 Zusätzliche Metadatenfelder <zusaetzliche-metadatenfelder>

Beliebige zusätzliche Schlüssel (z. B. `status: "Entwurf"`, `department: "IT-Architektur"`) können frei definiert werden und stehen in allen Jinja2-Templates über `document.<feldname>` zur Verfügung.

== 4.2 Kapitel definieren <kapitel-definieren>

Ein einfaches Kapitel wird mit `file:`, optionalem `title:` und `summary:` angegeben:

```yaml
parts:
  - title: "Hauptteil"
    break_before: "none"
    chapters:
      - file: "chapters/01_intro.md"
        title: "Einleitung"
        summary: "Zielsetzung des Leitfadens."
        break_before: "divider"    # Eigene Trennseite vor dem Kapitel
        chapter_toc: "none"        # Kein kapitelweises Mini-TOC
```

Ein Kapitel steht immer unter einem Part — `chapters:` auf oberster Ebene weist `markpublish` mit einem Hinweis auf den richtigen Aufbau zurück. Der nächste Abschnitt erklärt, warum.

Alle Pfade sind relativ zur `markpublish.yaml`, nicht zum Arbeitsverzeichnis der Shell.

== 4.3 Dokumentaufbau in 2 Stufen: Parts und Kapitel <dokumentaufbau-in-2-stufen-parts-und-kapitel>

`markpublish` organisiert Dokumente in einer klaren 2-stufigen Struktur:

+ #strong[Stufe 1 — Parts (`parts:`):] Gliedert das Dokument in logische Hauptabschnitte (z. B. Hauptteil, Anhänge, Bände). Jeder Part besitzt einen Namen (`title:` oder `part:`).
+ #strong[Stufe 2 — Kapitel (`chapters:`):] Die eigentlichen Inhaltsdateien (\*.md) unter dem jeweiligen Part.
+ #strong[Binnenstruktur (`##`, `###`):] Wird direkt im Markdown formatiert.

```yaml
parts:
  - title: "Hauptteil"         # Hauptabschnitt
    break_before: "none"       # Keine Part-Trennseite für den Hauptteil
    document_toc: "none"       # 'Hauptteil' erscheint nicht im TOC; Kapitel direkt gelistet
    chapters:
      - file: "chapters/01_intro.md"
        title: "Einführung"
      - file: "chapters/02_usage.md"
        title: "Nutzung"

  - title: "Anhänge"           # Gliedernder Abschnitt mit Trennseite & TOC-Rubrik
    summary: "Ergänzende Tabellen und Referenzen."
    break_before: "divider"
    autonum_from_level: 2
    document_toc: 2
    chapters:
      - file: "chapters/appendix_a.md"
        title: "Anhang A: Referenz"
        autonum_prefix: "A."
      - file: "chapters/appendix_b.md"
        title: "Anhang B: Glossar"
        autonum_prefix: "B."
```

Ein benannter Part gruppiert seine Kapitel, erhält auf Wunsch eine Trennseite und steht als gliedernde Rubrik im Inhaltsverzeichnis (wenn nicht mit `document_toc: "none"` ausgeblendet). Alle Kapitel stehen typografisch bündig auf derselben primären Fluchtlinie.


#pagebreak()

#render-chapter-divider(title: "Das Template- und Design-System", subtitle: "", summary: "3-stufige Auflösungshierarchie, CSS Paged Media und 2-zeilige Kopf-/Fußzeilen.", tag: "Kapitel 5", toc-title: "Inhalt dieses Kapitels", toc-items: ((title: "5.1 Theme-basierte Verzeichnisstruktur", slug: "theme-basierte-verzeichnisstruktur", indent: 0pt), (title: "5.2 Die 3-stufige Auflösungs-Hierarchie", slug: "die-3-stufige-aufloesungs-hierarchie", indent: 0pt), (title: "5.3 Statische Texte und Sprache", slug: "statische-texte-und-sprache", indent: 0pt), (title: "5.4 Kopf- und Fußzeilen", slug: "kopf-und-fusszeilen", indent: 0pt)))

= 5 Das Template- und Design-System <das-template-und-design-system>

Das Template-System von `markpublish` ermöglicht vollständige visuelle Anpassbarkeit bei gleichzeitiger Wartbarkeit.

== 5.1 Theme-basierte Verzeichnisstruktur <theme-basierte-verzeichnisstruktur>

Templates sind nach Theme gruppiert, darunter liegt das Ausgabeformat. So gehören alle Dateien eines Designs zusammen und ein Theme lässt sich als Ganzes kopieren, weitergeben oder versionieren:

```
templates/
└── default/                       # Theme-Name
    ├── pdf/
    │   ├── layout.html            # HTML-Grundgerüst
    │   ├── styles.css             # CSS Paged Media & Kopf-/Fußzeilen
    │   ├── fonts/                 # Mitgelieferte Schrift (Open Sans, variabel) + OFL.txt
    │   ├── cover.html             # Deckblatt-Template
    │   ├── part_divider.html      # Trennseite für übergeordnete Parts
    │   ├── chapter_divider.html   # Trennseite für Kapitel mit Mini-TOC
    │   └── toc.html               # Globales Inhaltsverzeichnis
    └── html/
        ├── layout.html            # Standalone Web-Layout
        ├── styles.css             # Screen/Responsive Stylesheet
        └── ...
```

== 5.2 Die 3-stufige Auflösungs-Hierarchie <die-3-stufige-aufloesungs-hierarchie>

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

=== 5.2.1 Konfiguration des gemeinsamen Template-Ordners <konfiguration-des-gemeinsamen-template-ordners>

Sie können den gemeinsamen Template-Pfad auf 4 Wegen festlegen:

+ #strong[CLI-Parameter]: `markpublish build --templates-dir /pfad/zu/templates`
+ #strong[In `markpublish.yaml`]: `templates_dir: "./custom-templates"`
+ #strong[Umgebungsvariable]: `MARKPUBLISH_TEMPLATES_DIR=/pfad/zu/templates`
+ #strong[Automatischer Fallback]: `./templates` im Projektordner.

== 5.3 Statische Texte und Sprache <statische-texte-und-sprache>

Die festen Beschriftungen — Überschrift des Inhaltsverzeichnisses, Kapitel-Marken, Cover-Labels, Seitenzahl-Fußzeile, Callout-Titel — stehen nicht im Template, sondern in `i18n.yaml`-Dateien. Welche Sprache gilt, bestimmt `document.language`:

```yaml
document:
  title: "User Guide"
  language: "en"      # steuert Beschriftungen, Callout-Titel und Datumsformat
```

Mitgeliefert sind `de` und `en`. Regionale Formen werden zugeordnet (`de-AT` → `de`), eine unbekannte Sprache fällt auf Englisch zurück. Fehlt `language:` ganz, gilt die Systemsprache — `markpublish init` schreibt sie gleich hin, damit ein Dokument auf jedem Rechner gleich gebaut wird.

#callout(type: "note", title: [Hinweis])[
#strong[i18n] bezeichnet die Quellen — die Dateien und den YAML-Eintrag, jeweils über alle Sprachen. #strong[labels] ist das daraus aufgelöste Ergebnis für #emph[ein] Dokument in #emph[einer] Sprache: das, was im Template unter `{{ labels.chapter }}` ankommt.
]

=== 5.3.1 Die 3-stufige i18n-Kaskade <die-3-stufige-i18n-kaskade>

Alle drei Ebenen sind #strong[identisch aufgebaut]: Sprachcode auf oberster Ebene, darunter die Texte. Jede tiefere Ebene überschreibt die höher liegende — und zwar #strong[nur die Schlüssel, die sie tatsächlich setzt]. Alles andere bleibt, wie es weiter oben steht:

```
1. Programm      markpublish/i18n.yaml
   │             vollständig, de + en
   ▼
2. Theme         <templates>/<theme>/i18n.yaml
   │             gilt für alle Zielformate des Themes
   ▼
3. Zielformat    <templates>/<theme>/<target>/i18n.yaml
                 nur für PDF bzw. nur für HTML
```

Ebene 1 ist die einzige, die vollständig sein muss. Sie legt zusätzlich Englisch unter die Dokumentsprache, damit jeder Programmtext garantiert auflöst. Die Ebenen 2 und 3 sind reine Overrides.

Statische Texte werden #strong[ausschließlich im Theme] definiert. Eine Dokumentebene gibt es nicht: `document.i18n` in der `markpublish.yaml` wird abgelehnt, mit Hinweis auf die Theme-Datei. Wer die Texte eines Dokuments ändern will, gibt ihm sein eigenes Theme — `markpublish export-template` legt es an.

#callout(type: "important", title: [Wichtig])[
Die Ebenen 2 und 3 stammen immer aus #strong[genau einem] Theme: welches gilt, entscheidet vorher die Template-Auflösung (User \> Projekt \> Paket). Ein Projekt-Theme erbt #strong[nicht] die Texte des gleichnamigen Paket-Themes — gemischt wird nur das eine gefundene Theme mit dem Programmstandard.
]

#callout(type: "important", title: [Wichtig])[
Die Ebenen 2 und 3 greifen #strong[nur für die gewählte Sprache]. Ein Theme, das einen `en:`-Block definiert, verändert eine deutsche Ausgabe nicht — sonst würden englische Theme-Texte in fremdsprachige Dokumente durchschlagen.
]

=== 5.3.2 Das gemeinsame Format <das-gemeinsame-format>

```yaml
# templates/mytheme/i18n.yaml
de:
  part: "Abschnitt"
  chapter_toc_title: "Auf dieser Seite"
en:
  part: "Section"
  chapter_toc_title: "On this page"
```

Der Sonderschlüssel `"*"` gilt für #strong[jede] Sprache und wird vor dem sprachspezifischen Block angewendet — für Begriffe, die unabhängig von der Dokumentsprache gleich heißen:

```yaml
"*":
  version: "Rev."       # in jeder Sprache "Rev."
de:
  part: "Abschnitt"
```

Wer nur eine Sprache pflegt, darf die Sprachebene auch weglassen; die flache Form ist gleichbedeutend mit `"*"`:

```yaml
part: "Abschnitt"       # entspricht:  "*":\n  part: "Abschnitt"
```

Regionale Blöcke schlagen den Basis-Block: bei `language: "de-AT"` gewinnt `de-at:` über `de:`. Fehlt eine `i18n.yaml`, ist das kein Fehler — ein Theme ohne eigene Texte ist der Normalfall. Ist sie vorhanden, aber fehlerhaft, bricht der Build mit Angabe der Datei ab, statt still die Standardtexte zu verwenden.

=== 5.3.3 Beispiel: PDF und HTML unterschiedlich beschriften <beispiel-pdf-und-html-unterschiedlich-beschriften>

```
templates/mytheme/
├── i18n.yaml            de: chapter: "Kapitel"
├── pdf/
│   └── i18n.yaml        de: chapter: "Kap."      ← nur im PDF
└── html/
    └── i18n.yaml        (leer → erbt "Kapitel")
```

Das mitgelieferte Theme `default` bringt alle drei Dateien als #strong[auskommentiertes Muster] mit: `templates/default/i18n.yaml`, `default/pdf/i18n.yaml` und `default/html/i18n.yaml`. Sie sind bewusst wirkungslos — das Standard-Theme soll exakt wie der Programmstandard aussprechen. Kommentieren Sie aus, was Sie ändern möchten. `markpublish export-template` kopiert diese Dateien mit — auch die `i18n.yaml` der Theme-Ebene, die neben den Zielformat-Ordnern liegt.

=== 5.3.4 Freie Labels: eigene Texte des Templates <freie-labels-eigene-texte-des-templates>

Ein Theme darf #strong[eigene Schlüssel] definieren, die das Programm nicht kennt — für die statischen Texte des Templates selbst. Der Aufbau ist derselbe, der Zugriff ebenso:

```yaml
# templates/mytheme/i18n.yaml
de:
  imprint_title: "Impressum"
  disclaimer: "Alle Angaben ohne Gewähr."
en:
  imprint_title: "Imprint"
  disclaimer: "All information without guarantee."
```

```html
<!-- templates/mytheme/html/layout.html -->
<footer>{{ labels.imprint_title }}</footer>
```

#callout(type: "warning", title: [Warnung])[
Für freie Labels gibt es #strong[keinen Programmstandard], der einspringen könnte. Deshalb gilt hier eine strikte Regel: Ein Label, das ein Template notiert, #strong[muss] in der Kaskade auflösen. Tut es das nicht, bricht der Build ab und nennt Schlüssel, Fundstelle mit Zeilennummer, Dokumentsprache und die durchsuchten Dateien:

```
Label 'imprint_title' ist im Template notiert, aber in keiner i18n-Ebene definiert.
Dokumentsprache: de
Fundstelle:
templates/mytheme/html/layout.html:108
Gesucht in:
templates/mytheme/html/i18n.yaml  (vorhanden)
templates/mytheme/i18n.yaml       (vorhanden)
markpublish/i18n.yaml             (vorhanden)
```

Pflegen Sie also jede Sprache, die Sie ausliefern, oder legen Sie den Schlüssel unter `"*"` ab. Ein leerer Text im fertigen PDF fällt niemandem auf — ein Abbruch schon.
]

Geprüft werden die Template-Quellen, nicht der Renderlauf: auch ein Label in einem Zweig, den genau dieses Dokument nicht durchläuft, wird gemeldet. `styles.css` zählt mit, da es durch dieselbe Jinja-Umgebung läuft.

=== 5.3.5 Die aufgelöste Tabelle ansehen <die-aufgeloeste-tabelle-ansehen>

Bei drei Ebenen ist nicht immer offensichtlich, woher ein Text kommt. `markpublish labels` zeigt das Ergebnis samt Herkunft:

```bash
markpublish labels                       # alle Schlüssel, Ziel PDF
markpublish labels --target html         # Kaskade für die HTML-Ausgabe
markpublish labels --overridden          # nur das, was vom Theme kommt
```

=== 5.3.6 Verfügbare Schlüssel <verfuegbare-schluessel>

#table(
  columns: (1.2fr, 1.2fr, 2fr),
  align: (left, left, left),
  table.header([* Schlüssel *], [* `de` *], [* `en` *]),
  [`toc_title`], [Inhaltsverzeichnis], [Table of Contents],
  [`toc_sidebar`], [Inhalt], [Contents],
  [`chapter_toc_title`], [Inhalt dieses Kapitels], [In this chapter],
  [`chapter`], [Kapitel], [Chapter],
  [`part`], [Teil], [Part],
  [`author`], [Autor], [Author],
  [`status`], [Status], [Status],
  [`version`], [Version], [Version],
  [`date`], [Datum], [Date],
  [`copyright`], [Copyright], [Copyright],
  [`page`], [Seite], [Page],
  [`page_of`], [von], [of],
  [`alert_note`], [Hinweis], [Note],
  [`alert_tip`], [Tipp], [Tip],
  [`alert_important`], [Wichtig], [Important],
  [`alert_warning`], [Warnung], [Warning],
  [`alert_caution`], [Achtung], [Caution],
)

Die `alert_*`-Titel entstehen bereits beim Markdown-Parsen, nicht erst im Template — die Kaskade wird dorthin durchgereicht, ein `alert_note` im Theme wirkt also auch im Callout.

Eine neue Sprache legen Sie an, indem Sie in `markpublish/i18n.yaml` einen vollständigen Block ergänzen — oder, ohne das Paket anzufassen, auf Ebene 2 oder 3 alle Schlüssel unter dem gewünschten Sprachcode setzen.

#callout(type: "tip", title: [Tipp])[
In eigenen Templates greifen Sie mit `{{ labels.chapter }}` auf das Ergebnis zu — auch in `styles.css`, das durch dieselbe Jinja-Umgebung läuft. So ist die Fußzeile `"{{ labels.page }} " counter(page) " {{ labels.page_of }} " counter(pages)` gebaut.
]

== 5.4 Kopf- und Fußzeilen <kopf-und-fusszeilen>

Kopf- und Fußzeile sind #strong[Running Elements]: ein Block im `layout.html` bekommt `position: running(name)` und wird damit aus dem Textfluss genommen; die `@page`-Regel setzt ihn über `content: element(name)` in die Margin-Box ein.

Der Unterschied zu einer `content:`-Zeichenkette ist wesentlich: In der Margin-Box steht dadurch #strong[echtes Markup]. Damit sind beliebig viele Zeilen möglich, jede mit eigener Auszeichnung — eine Zeichenkette kennt nur eine Formatierung für alles.

```html
<!-- layout.html -->
<div class="page-header-runner">
  <div class="hf-left">
    <div class="hf-doc-title">{{ document.title }}</div>
    <div class="hf-doc-subtitle">{{ document.subtitle }}</div>
  </div>
  <div class="hf-right"><span class="hf-section"></span></div>
</div>
```

```css
/* styles.css */
.page-header-runner {
  position: running(pageheader);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;    /* rechte Spalte bleibt oben */
}
.hf-doc-title { font-weight: 700; }
.hf-section::before { content: string(current-section); }

@page {
  @top-left {
    content: element(pageheader);
    width: 100%;
    vertical-align: top;
    margin-top: 12mm;          /* Abstand zur Papierkante */
    padding-bottom: 0;
    border-bottom: 0.5pt solid #cbd5e1;
    margin-bottom: 12mm;       /* Abstand zum Inhalt */
  }
}
```

=== 5.4.1 Geometrie <geometrie>

Von der Papierkante nach innen:

```
Kante ── margin ── Zeilen (top-aligned) ── Linie ── margin ── Inhalt
         12 mm                                       12 mm
```

Beide Abstände sind bewusst gleich groß: eine Kopfzeile, die dicht über dem Text sitzt, liest sich als Teil des Satzspiegels statt als Seitenfurnitur.

Beide Spalten sitzen in einem Flex-Container mit `align-items: flex-start`. Die rechte Spalte beginnt deshalb auf der Höhe der #strong[ersten] linken Zeile, auch wenn links drei Zeilen stehen und rechts nur eine.

#callout(type: "important", title: [Wichtig])[
Der Abstand zum Inhalt kommt aus `margin-bottom`, nicht aus `padding-bottom`. In CSS liegt der Rahmen #strong[außerhalb] des Paddings — ein `padding-bottom` würde die Trennlinie vom Text wegschieben und an den Inhalt drücken. Gewollt ist das Gegenteil: Linie direkt am Text, Abstand danach.
]

#callout(type: "warning", title: [Warnung])[
Eine Margin-Box #strong[schiebt den Inhalt nicht]. Ihre Höhe ist durch den Seitenrand gedeckelt; zusätzliche Zeilen laufen aus der Seite heraus, statt den Satzspiegel zu verkleinern. Der Seitenrand wird deshalb in `styles.css` aus der Zeilenzahl gerechnet:

```
margin-top = Rand zur Kante + Zeilen × Zeilenhöhe + Linienstärke + Abstand zum Inhalt
```

Wer in `layout.html` eine Zeile ergänzt, zieht `hf_header_lines` bzw. `hf_footer_lines` in `styles.css` mit.
]

=== 5.4.2 Standardbelegung des Themes <standardbelegung-des-themes>

```
Kopfzeile     Dokumenttitel (fett)                        Kapiteltitel
              Untertitel

Fußzeile      Copyright                     Version 1.0.0 | 01.09.2026
                                                        Seite X von Y
```

Untertitel und Version sind optional. Fehlt der Untertitel, hat die Kopfzeile nur eine Zeile und der Satzspiegel rückt entsprechend nach oben. Fehlt die Version, entfällt sie samt Trenner — in der Fußzeile steht dann nur das Datum, und auf dem Deckblatt fehlt das Feld ganz.

Der Kapiteltitel kommt aus `string(current-section)`, das die Kapitel-`<article>` per `string-set` setzen; `counter(page)` funktioniert innerhalb des Running Elements ebenso wie in einer Margin-Box. Die Schalter `document.header` und `document.footer` blenden den jeweiligen Block ab; auf Deck- und Trennseiten ist er ohnehin abgeschaltet.


#pagebreak()

#render-chapter-divider(title: "Markdown-Features & Syntax", subtitle: "", summary: "Tabellen, Admonitions/Callouts, Pygments Syntax-Highlighting und Tasklisten.", tag: "Kapitel 6", toc-title: "Inhalt dieses Kapitels", toc-items: ((title: "6.1 Code-Blöcke & Syntax Highlighting", slug: "code-bloecke-syntax-highlighting", indent: 0pt), (title: "6.2 Tabellen", slug: "tabellen", indent: 0pt), (title: "6.3 GitHub-Style Callout-Boxen (Alerts)", slug: "github-style-callout-boxen-alerts", indent: 0pt), (title: "6.4 Tasklisten", slug: "tasklisten", indent: 0pt)))

= 6 Markdown-Features & Syntax <markdown-features-syntax>

`markpublish` beinhaltet eine leistungsfähige Markdown-Engine mit voller Unterstützung moderner Dokumentations-Elemente.

== 6.1 Code-Blöcke & Syntax Highlighting <code-bloecke-syntax-highlighting>

Quellcode wird durch Pygments hervorgehoben:

```python
from markpublish.config.loader import load_config
from markpublish.markdown.engine import MarkdownPipeline

# Manifest laden
config = load_config("markpublish.yaml")
print(f"Building: {config.document.title}")
```

== 6.2 Tabellen <tabellen>

Tabellen werden mit sauberem CSS-Zebramuster und Seitenumbruchschutz gerendert:

#table(
  columns: (1.2fr, 0.9fr, 1fr, 2fr),
  align: (left, left, left, left),
  table.header([* Parameter *], [* Typ *], [* Standard *], [* Beschreibung *]),
  [`title`], [String], [#emph[Pflicht]], [Haupttitel des Dokuments],
  [`author`], [String], [`None`], [Name des Autors],
  [`status`], [String], [`None`], [Dokumentstatus (z.B. "Freigegeben", "Draft")],
  [`copyright`], [String], [`None`], [Copyright-Vermerk (z.B. "© 2026 Frank Winter")],
  [`version`], [String], [`null`], [Versionskennung. Ohne Angabe entfällt das Feld auf dem Deckblatt; ist sie gesetzt, steht sie in der Fußzeile links neben dem Datum],
)

== 6.3 GitHub-Style Callout-Boxen (Alerts) <github-style-callout-boxen-alerts>

`markpublish` unterstützt die gängige #strong[GitHub-Alert-Syntax] mit fünf semantischen Typen. Die Icons stammen dabei direkt aus dem Template:

#callout(type: "note", title: [Hinweis])[
Dies ist eine informative Notiz mit blauem Akzent und passendem Info-Icon.
]

#callout(type: "tip", title: [Tipp])[
Nutzen Sie `markpublish build --target all`, um PDF und HTML parallel in einem Durchgang zu erstellen.
]

#callout(type: "important", title: [Wichtig])[
GitHub-Callouts werden automatisch anhand der Dokumentensprache lokalisiert (z. B. #emph[Hinweis], #emph[Tipp], #emph[Wichtig], #emph[Warnung], #emph[Achtung]).
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

== 6.4 Tasklisten <tasklisten>

- #task-item(checked: true)[Projekt initialisieren]
- #task-item(checked: true)[Kapitel schreiben]
- #task-item(checked: false)[Dokument veröffentlichen]


#pagebreak()

#render-part-divider(title: "Anhänge", subtitle: "", summary: "Vollständige Spezifikations-Tabellen, Troubleshooting und Best Practices.", tag: "Teil", in-toc: true, toc-title: "Inhalt dieses Abschnitts", toc-items: ((title: "Anhang A: YAML-Schema-Referenz", slug: "anhang-a-yaml-schema-referenz", level: 1, indent: 0pt), (title: "A.1 Dokumenten-Eigenschaften (document)", slug: "dokumenten-eigenschaften-document", level: 2, indent: 12pt), (title: "A.2 Part-Eigenschaften (parts)", slug: "part-eigenschaften-parts", level: 2, indent: 12pt), (title: "A.3 Kapitel-Eigenschaften (chapters)", slug: "kapitel-eigenschaften-chapters", level: 2, indent: 12pt), (title: "A.4 Nummerierung", slug: "nummerierung", level: 2, indent: 12pt), (title: "Anhang B: Fehlerbehebung & FAQ", slug: "anhang-b-fehlerbehebung-faq", level: 1, indent: 0pt)))

= Anhang A: YAML-Schema-Referenz <anhang-a-yaml-schema-referenz>

Vollständige Übersicht aller Konfigurationsoptionen in `markpublish.yaml`.

== A.1 Dokumenten-Eigenschaften (`document`) <dokumenten-eigenschaften-document>

#table(
  columns: (1.2fr, 0.9fr, 1fr, 2fr),
  align: (left, left, left, left),
  table.header([* Schlüssel *], [* Typ *], [* Standard *], [* Beschreibung *]),
  [`title`], [String], [#emph[Pflicht]], [Titel der Publikation],
  [`subtitle`], [String], [`null`], [Untertitel],
  [`summary`], [String], [`null`], [Zusammenfassung für Deckblatt],
  [`author`], [String], [`null`], [Name des Autors],
  [`status`], [String], [`null`], [Dokumentstatus (z. B. "Entwurf", "Freigegeben")],
  [`copyright`], [String], [`null`], [Copyright-Angabe (z. B. "© 2026 Frank Winter")],
  [`date`], [String], [`"auto"`], [Datum oder `"auto"` für Tagesdatum],
  [`version`], [String], [`null`], [Versionskennung],
  [`language`], [String], [Systemsprache], [ISO-Sprachcode (`de`, `en`, ...)],
  [`cover`], [Bool], [`true`], [Deckblatt aktivieren/deaktivieren],
  [`document_toc`], [String/Int], [`full`], [Vorgabe für das Hauptverzeichnis],
  [`part_toc`], [String/Int], [`full`], [Vorgabe für Part-Trennseiten-TOCs],
  [`chapter_toc`], [String/Int], [`full`], [Vorgabe für Kapitel-Trennseiten-TOCs],
  [`autonum_style`], [String], [`"decimal"`], [Vorgabe für Nummerierungsstil (`decimal`, `roman`, `legal`, `none`)],
  [`autonum_from_level`], [Int], [`1`], [Vorgabe für Start-Überschriftenebene],
  [`autonum_prefix`], [String], [`null`], [Vorgabe für Ziffernpräfix],
  [`autonum_reset`], [Bool], [`false`], [Vorgabe für Zähler-Reset],
  [`pagenum_reset`], [Bool], [`false`], [Vorgabe für Seitennummern-Reset],
  [`header`], [Bool], [`true`], [Laufende Kopfzeile aktivieren],
  [`footer`], [Bool], [`true`], [Laufende Fußzeile aktivieren],
)

== A.2 Part-Eigenschaften (`parts`) <part-eigenschaften-parts>

#table(
  columns: (1.2fr, 0.9fr, 1fr, 2fr),
  align: (left, left, left, left),
  table.header([* Schlüssel *], [* Typ *], [* Standard *], [* Beschreibung *]),
  [`title` / `part`], [String], [#emph[Pflicht]], [Titel des Parts (z. B. `"Anhänge"`, `"Hauptteil"`)],
  [`subtitle`], [String], [`null`], [Untertitel für die Part-Trennseite],
  [`summary`], [String], [`null`], [Zusammenfassung für die Part-Trennseite],
  [`break_before`], [String], [`"divider"`], [`"divider"`, `"page"` oder `"none"`],
  [`document_toc`], [String/Int], [`full`], [Beitrag des Parts zum Inhaltsverzeichnis],
  [`part_toc`], [String/Int], [`full`], [Lokales Inhaltsverzeichnis auf der Part-Trennseite],
  [`chapter_toc`], [String/Int], [`full`], [Vorgabe für Kapitel-TOCs in diesem Part],
  [`autonum_style`], [String], [`"decimal"`], [Nummerierungsstil für den Part],
  [`autonum_from_level`], [Int], [`1`], [Start-Ebene für Zählung],
  [`autonum_prefix`], [String], [`null`], [Präfix für Ziffern (z. B. `"A."`)],
  [`autonum_reset`], [Bool], [`false`], [Zähler-Reset bei Part-/Kapitelwechsel],
  [`pagenum_reset`], [Bool], [`false`], [Seitennummerierung ab Part-Beginn auf 1 zurücksetzen],
  [`chapters`], [Liste], [`[]`], [Flache Liste der Kapitel dieses Parts],
)

== A.3 Kapitel-Eigenschaften (`chapters`) <kapitel-eigenschaften-chapters>

#table(
  columns: (1.2fr, 0.9fr, 1fr, 2fr),
  align: (left, left, left, left),
  table.header([* Schlüssel *], [* Typ *], [* Standard *], [* Beschreibung *]),
  [`file`], [String], [`null`], [Pfad zur Markdown-Datei],
  [`title`], [String], [`null`], [Überschreibt den Titel der Datei],
  [`subtitle`], [String], [`null`], [Untertitel für die Kapitel-Trennseite],
  [`summary`], [String], [`null`], [Zusammenfassung für Trennseite],
  [`break_before`], [String], [`page`], [Wie das Kapitel abgesetzt wird: `page`, `divider` oder `none`],
  [`document_toc`], [String/Int], [`full`], [Beitrag zum Haupt-Inhaltsverzeichnis],
  [`chapter_toc`], [String/Int], [`full`], [Lokales Inhaltsverzeichnis auf der Kapitel-Trennseite],
  [`autonum_style`], [String], [`"decimal"`], [Nummerierungsstil für dieses Kapitel],
  [`autonum_from_level`], [Int], [`1`], [Ab welcher Überschriften-Ebene nummeriert wird],
  [`autonum_prefix`], [String], [`null`], [Optionales Präfix für Ziffern (z. B. `"A."` ➔ `A.1`, `A.2`)],
  [`autonum_reset`], [Bool], [`false`], [Zähler zu Kapitelbeginn auf 0 zurücksetzen],
  [`pagenum_reset`], [Bool], [`false`], [Seitennummerierung ab Kapitelbeginn auf 1 zurücksetzen],
)

=== A.3.1 `break_before` — wie ein Kapitel abgesetzt wird <break-before-wie-ein-kapitel-abgesetzt-wird>

Ein Schlüssel mit drei Werten, keine zwei unabhängigen Schalter:

#table(
  columns: (1fr, 2fr),
  align: (left, left),
  table.header([* Wert *], [* Wirkung *]),
  [`page`], [Standard. Das Kapitel beginnt oben auf einer neuen Seite],
  [`divider`], [Dem Kapitel geht eine eigene Trennseite voraus],
  [`none`], [Das Kapitel läuft im Fließtext weiter],
)

Dass es #emph[ein] Schlüssel ist, hat einen Grund: die drei Werte sind eine Achse, nicht drei Fragen. Als zwei Booleans ließe sich „Trennseite, aber kein Seitenumbruch" hinschreiben — ein Zustand, den es nicht gibt, weil eine Trennseite immer umbricht. Eine Angabe, die man notieren kann und die nichts bewirkt, ist eine Fehlerquelle ohne Gegenwert.

`page` ist die Erwartung an ein gesetztes Dokument. Wer kurze Abschnitte durchlaufen lassen will — Merkblätter, Referenzkarten, eng gesetzte Anhänge — setzt am einzelnen Kapitel `break_before: "none"`.

Bei `divider` fallen der Umbruch des Kapitels und der der Trennseite auf dieselbe Stelle und verschmelzen zu einem — es entsteht kein Leerblatt. Vor dem ersten Kapitel greift die Regel nicht.

Ein unbekannter Wert bricht den Build ab, statt still auf `page` zurückzufallen: aus einem vertippten `divder` würde sonst klaglos ein normaler Seitenumbruch, und die fehlende Trennseite fände man erst beim Durchblättern des fertigen PDFs.

=== A.3.2 `chapter_toc` und `document_toc` — zwei Verzeichnisse, ein Vokabular <chapter-toc-und-document-toc-zwei-verzeichnisse-ein-vokabular>

Ein Dokument hat zwei Inhaltsverzeichnisse, und für jedes gibt es ein Paar aus Vorgabe und Einzelfall:

#table(
  columns: (1.2fr, 1.2fr, 2fr),
  align: (left, left, left),
  table.header([* Verzeichnis *], [* Vorgabe unter `document:` *], [* Am Kapitel *]),
  [Das #strong[große] vorn im Dokument], [`document_toc`], [`document_toc`],
  [Das #strong[kleine] auf der Kapitel-Trennseite], [`chapter_toc`], [`chapter_toc`],
)

Alle vier Schlüssel nehmen dieselben drei Schreibweisen:

#table(
  columns: (1fr, 2fr),
  align: (left, left),
  table.header([* Wert *], [* Bedeutung *]),
  [`none`], [Kommt in diesem Verzeichnis gar nicht vor],
  [`full`], [Jede Ebene],
  [#emph[Zahl]], [Bis zu dieser Tiefe, gezählt ab der Kapitelüberschrift],
)

Die Tiefe zählt #strong[innerhalb des Kapitels]: 1 ist die Kapitelüberschrift selbst, 2 die Ebene darunter. `document_toc: 1` nimmt das Kapitel also ins große Verzeichnis auf, seine Zwischenüberschriften aber nicht. `chapter_toc: 2` listet auf der Trennseite genau die Ebene unterhalb der Kapitelüberschrift.

Für den häufigsten Fall genügen damit zwei Zeilen im `document`-Block:

```yaml
document:
  document_toc: 2       # großes Verzeichnis, zwei Ebenen tief
  chapter_toc: 2        # kleine Verzeichnisse ebenso
```

`document_toc: "none"` lässt das große Verzeichnis ganz weg; die Angaben an den Kapiteln sind dann gegenstandslos.

=== A.3.3 Vererbung <vererbung>

`document_toc` wird nach unten vererbt: an einem Part gesetzt, gilt er für alle Kapitel darunter, und ein Kapitel gibt ihn an seine Unterkapitel weiter. Für den häufigsten Fall — ein Anhang, dessen innere Gliederung das Verzeichnis nur aufbläht — genügt damit eine Zeile:

```yaml
  - part: "Anhänge"
    document_toc: 1
    chapters:
      - file: "chapters/07_appendix_yaml_spec.md"
        title: "Anhang A: YAML-Schema-Referenz"
      - file: "chapters/08_appendix_troubleshooting.md"
        title: "Anhang B: Troubleshooting"
```

Ein einzelnes Kapitel schlägt das Geerbte — auch zurück auf `full`. Genau dafür gibt es das Schlüsselwort: ohne es müsste man eine willkürlich große Zahl hinschreiben, um „doch wieder alles" zu sagen.

`chapter_toc` wird #strong[nicht] von Kapitel zu Unterkapitel gereicht. Es beschreibt die Trennseite genau dieses Kapitels, und die hat jedes Kapitel für sich; ohne eigene Angabe gilt schlicht `document.chapter_toc`.

=== A.3.4 Was gekürzt wird — und was nicht <was-gekuerzt-wird-und-was-nicht>

Der Fließtext bleibt unberührt: die Zwischenüberschriften stehen weiterhin im Kapitel, samt Nummerierung und Sprungzielen. Gekürzt wird ausschließlich das Verzeichnis. Ein Unterkapitel behält dabei seinen eigenen Eintrag — vererbt wird die Tiefe relativ zu jedem Kapitel, nicht über die zusammengelegte Liste.

Ein unbekannter Wert bricht den Build ab. Auch Wahrheitswerte werden abgewiesen: einem `true` sähe man die Tiefe nicht an — genau dafür gibt es `full`.

== A.4 Nummerierung <nummerierung>

`document.autonum_style` legt den Stil für das ganze Dokument fest; `autonum_style` an einem Kapitel oder Part weicht davon ab und #strong[gibt den Wert nach unten weiter]. Ohne diese Vererbung bliebe die Angabe am Part wirkungslos: die Überschriften stehen in den Kapiteldateien, nicht im Part.

`autonum_style: "none"` heißt: in diesem Zweig trägt #strong[nichts] eine Nummer — weder die Kapitelüberschrift noch die Ebenen darunter. Es gibt also auch keinen Neustart bei 1, denn innerhalb des Zweigs läuft keine Zählung, die neu beginnen könnte.

Der Dokumentzähler bleibt dabei unangetastet. Eine unnummerierte Strecke verbraucht keine Nummer:

```yaml
parts:
  - chapters:
      - file: "chapters/01.md"          # 1
  - part: "Anhänge"
    autonum_style: "none"           # Anhänge: keine Nummern
    chapters:
      - file: "chapters/a.md"
      - file: "chapters/b.md"
  - chapters:
      - file: "chapters/02.md"          # 2, nicht 4
```

=== A.4.1 Nummerierung ab Unterebenen (`autonum_from_level` & `autonum_prefix`) <nummerierung-ab-unterebenen-autonum-from-level-autonum-prefix>

Für lange Anhänge oder spezialisierte Abschnitte, deren Haupttitel keine Ziffer tragen soll (z. B. #emph[„Anhang A: Referenz“]), deren Unterabschnitte aber durchnummeriert werden sollen:

- `autonum_from_level: 2` lässt die `h1`-Überschrift unnummeriert und beginnt die Zählung erst ab `h2` (`1`, `2`, ...) bzw. `h3` (`1.1`, `1.2`).
- Bei `autonum_from_level > 1` wird der Zähler für jedes Kapitel automatisch isoliert zurückgesetzt.
- `autonum_prefix: "A."` stellt den generierten Nummern ein Präfix voran (`A.1`, `A.2`, `A.2.1`).

```yaml
parts:
  - part: "Anhänge"
    autonum_from_level: 2           # erbt autonum_style aus document
    chapters:
      - file: "chapters/appendix_a.md"
        title: "Anhang A: Referenz"
        autonum_prefix: "A."        # A.1, A.2, A.2.1

      - file: "chapters/appendix_b.md"
        title: "Anhang B: FAQ"
        autonum_prefix: "B."        # B.1, B.2, B.2.1
```


#pagebreak()

= Anhang B: Fehlerbehebung & FAQ <anhang-b-fehlerbehebung-faq>

Häufige Fragen, Fehlermeldungen und Lösungen bei der Dokumentenerstellung.

#table(
  columns: (1.2fr, 1.2fr, 2fr),
  align: (left, left, left),
  table.header([* Problem / Fehlermeldung *], [* Mögliche Ursache *], [* Lösung *]),
  [`cannot load library 'libgobject-2.0-0'`], [WeasyPrint benötigt auf Windows die C-Bibliotheken von Pango und GTK.], [GTK3-Runtime installieren (#link("https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer")[GTK-Installer]) oder MSYS2: `pacman -S mingw-w64-x86_64-pango`. Schnelle Alternative: `--target html` rendert ohne WeasyPrint.],
  [Leere Bildrahmen / fehlende Grafiken im PDF], [Bildpfad ist falsch oder absolut statt relativ notiert.], [Pfade immer relativ zur jeweiligen Markdown-Datei angeben (z. B. `images/diag.png`). markpublish bettet Grafiken bis 12 MB als Data-URI ein.],
  [Inhaltsverzeichnis: Falsche Seitenzahlen], [Manuell vergebene Heading-IDs kollidieren im Zweipass-Rendering.], [Automatische Eindeutigkeit von markpublish nutzen oder manuell vergebene Anker (`{#id}`) prüfen.],
  [`Label 'x' is used in template but defined in no i18n level`], [Ein Theme verwendet einen statischen Textschlüssel, der in keiner `i18n.yaml` deklariert ist.], [Schlüssel in `<theme>/i18n.yaml` für alle Sprachen oder unter `*` eintragen. Gültige Texte mit `markpublish labels` prüfen.],
  [`cheatsheet` oder `manual` ignoriert Arbeitsordner-Theme], [Eingebaute Referenzen nutzen standardmäßig das robuste Built-in-Theme.], [Mit `--theme <name>` explizit das Rendern im eigenen Theme anfordern.],
)

