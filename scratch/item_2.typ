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

#render-chapter-divider(title: "Die CLI-Befehle", subtitle: "", summary: "Alle Befehle im Detail: build, init, cheatsheet, manual, templates, export-template und labels.", tag: "Kapitel 3")

= Die CLI-Befehle <die-cli-befehle>

`markpublish` bietet eine schlanke, intuitive Befehlszeilenschnittstelle (CLI), die über `markpublish` oder die Kurzform `mpub` aufgerufen werden kann.

== Befehlsübersicht <befehlsuebersicht>

#table(
  columns: 2,
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

== `markpublish init` <markpublish-init>

Legt einen minimalen Projektstumpf an: eine `markpublish.yaml` und ein Kapitel `next-steps.md`, beide direkt im Zielordner. Kein `chapters/`-Verzeichnis, keine Beispielkapitel.

```bash
markpublish init [ZIELORDNER] [--title "Titel"]
```

Der Stumpf ist absichtlich klein, weil er dazu da ist, gelöscht zu werden — spätestens beim ersten echten Kapitel. Die Referenz liegt deshalb nicht im Stumpf, sondern in `markpublish cheatsheet`; sowohl die YAML als auch das Kapitel verweisen darauf. Cover und Inhaltsverzeichnis sind abgeschaltet, weil ein einseitiger Entwurf beides nicht braucht.

== `markpublish cheatsheet` <markpublish-cheatsheet>

Rendert die mitgelieferte Kurzreferenz: Seite 1 die Schlüssel der `markpublish.yaml`, Seite 2 die Grundlagen zu Themes und Templates.

```bash
markpublish cheatsheet [--lang CODE] [--target pdf|html|all] [--output PFAD] [--theme NAME]
```

== `markpublish manual` <markpublish-manual>

Rendert dieses Handbuch.

```bash
markpublish manual [--lang CODE] [--target pdf|html|all] [--output PFAD] [--theme NAME]
```

=== Gemeinsames Verhalten der beiden Dokumentbefehle <gemeinsames-verhalten-der-beiden-dokumentbefehle>

Beide Quellen liegen im Paket und werden bei jedem Aufruf neu gerendert. Damit passt das Ergebnis immer zur installierten Version, und ein erfolgreicher Lauf ist zugleich der Nachweis, dass die Rendering-Kette funktioniert — unter Windows also, dass WeasyPrint seine GTK-Laufzeit findet. Geschrieben wird nur das fertige Dokument, und zwar ins aktuelle Verzeichnis; Quelldateien landen nie im Projekt des Nutzers.

#table(
  columns: 3,
  align: (left, left, left),
  table.header([* Option *], [* Standard *], [* Bedeutung *]),
  [`--lang`, `-l`], [Systemsprache], [Welche Übersetzung gerendert wird. `markpublish manual --lang de`],
  [`--target`, `-t`], [`pdf`], [`pdf`, `html` oder `all`],
  [`--output`, `-o`], [aktuelles Verzeichnis], [Datei oder Verzeichnis],
  [`--theme`], [mitgeliefert], [Rendert in einem eigenen Theme],
)

`--lang` wählt die *Quelle*, nicht bloß die Beschriftungen — jede Übersetzung bringt ihre eigene `language:` mit und zieht damit die passenden statischen Texte von selbst nach.

Ohne Angabe entscheidet die Sprache Ihres Systems. Diese beiden Dokumente richten sich an die Person vor dem Rechner und nicht an ein Publikum; deren Sprache ist damit die beste verfügbare Vermutung. Gibt es dafür keine Übersetzung, erscheint kommentarlos die englische — verlangt wurde ja nichts. Ein ausdrückliches `--lang fr` dagegen wird gemeldet, statt still einen englischen Rahmen um eine französische Erwartung zu setzen.

Ohne `--theme` oder `--templates-dir` ignorieren beide Befehle bewusst User- und Projekt-Themes und rendern im mitgelieferten. Sonst zöge ein `templates/` im Arbeitsverzeichnis — mit `export-template` angelegt und noch mitten in der Anpassung — die Referenz mit sich: ein fehlendes Label ließe den Build abbrechen, ausgerechnet in dem Moment, in dem jemand nachschlagen will, wie Labels funktionieren.

Fällt der PDF-Weg mangels GTK aus, liefert `--target html` dieselben Dokumente ohne WeasyPrint.

== `markpublish build` <markpublish-build>

Kompiliert eine `markpublish.yaml`-Konfiguration.

```bash
markpublish build [CONFIG_FILE] [OPTIONEN]
```

=== Argumente & Optionen: <argumente-optionen>

- `CONFIG_FILE` _(optional, Standard: `markpublish.yaml`)_: Pfad zur YAML-Datei.
- `--target / -t` _(Standard: `pdf`)_: Zielformat (`pdf`, `html` oder `all`).
- `--output / -o`: Benutzerdefinierter Ausgabepfad (Datei oder Verzeichnis).
- `--templates-dir`: Spezifischer Pfad zu einem gemeinsamen Template-Verzeichnis.

=== Beispiele: <beispiele>

```bash
# Standard-Build aus aktuellem Verzeichnis
markpublish build

# HTML-Version in ein bestimmtes Zielverzeichnis ausgeben
markpublish build markpublish.yaml -t html -o dist/

# Benutzerdefiniertes Template-Verzeichnis nutzen
markpublish build --templates-dir /shared/company-templates
```

#callout(type: "note", title: [Hinweis])[
`build` hat bewusst kein `--lang`. Die Sprache eines Dokuments gehört in seine eigene `markpublish.yaml`, neben `title` und `author`: sie beschreibt, in welcher Sprache das Dokument _geschrieben ist_. Ein Override von der Kommandozeile würde lediglich die siebzehn statischen Beschriftungen um unveränderten Fließtext herum austauschen.
]

== `markpublish templates` <markpublish-templates>

Zeigt eine tabellarische Übersicht aller Templates auf dem System und deren Prioritätsstatus:

```bash
markpublish templates
markpublish templates --target pdf
```

== `markpublish export-template` <markpublish-export-template>

Kopiert das eingebaute Standard-Template in Ihr lokales Arbeitsverzeichnis:

```bash
markpublish export-template default templates
```

== `markpublish labels` <markpublish-labels>

Zeigt, welcher statische Text am Ende gilt und aus welcher Ebene der Label-Kaskade er stammt. Nützlich, sobald ein Theme oder ein Dokument eigene Texte mitbringt und nicht mehr offensichtlich ist, welche Ebene gewinnt.

```bash
markpublish labels                          # alle Schlüssel, Zielformat PDF
markpublish labels --target html            # Kaskade für die HTML-Ausgabe
markpublish labels --overridden             # nur überschriebene Texte
markpublish labels pfad/zu/markpublish.yaml
```

=== Argumente & Optionen <argumente-optionen>

#table(
  columns: 4,
  align: (left, left, left, left),
  table.header([* Parameter *], [* Typ *], [* Standard *], [* Beschreibung *]),
  [`config_file`], [Pfad], [`markpublish.yaml`], [Pfad zur Konfigurationsdatei],
  [`--target`, `-t`], [String], [`pdf`], [Zielformat, dessen Kaskade gezeigt wird (`pdf` oder `html`)],
  [`--templates-dir`], [Pfad], [–], [Alternativer Template-Ordner],
  [`--overridden`], [Flag], [aus], [Nur Texte anzeigen, die das Theme ändert],
)

Die Spalte _Source_ nennt die Ebene: `i18n.yaml (de)` für den Programmstandard oder den Pfad einer Theme- bzw. Zielformat-`i18n.yaml`. Unter der Tabelle steht, in welchen Dateien nach Overrides gesucht wurde und welche existieren.

#callout(type: "tip", title: [Tipp])[
`--overridden` beantwortet die häufigste Frage direkt: _Was weicht in diesem Projekt überhaupt vom Standard ab?_
]

