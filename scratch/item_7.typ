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

= Anhang A: YAML-Schema-Referenz <anhang-a-yaml-schema-referenz>

Vollständige Übersicht aller Konfigurationsoptionen in `markpublish.yaml`.

== Dokumenten-Eigenschaften (`document`) <dokumenten-eigenschaften-document>

#table(
  columns: 4,
  align: (left, left, left, left),
  table.header([* Schlüssel *], [* Typ *], [* Standard *], [* Beschreibung *]),
  [`title`], [String], [_Pflicht_], [Titel der Publikation],
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

== Part-Eigenschaften (`parts`) <part-eigenschaften-parts>

#table(
  columns: 4,
  align: (left, left, left, left),
  table.header([* Schlüssel *], [* Typ *], [* Standard *], [* Beschreibung *]),
  [`title` / `part`], [String], [_Pflicht_], [Titel des Parts (z. B. `"Anhänge"`, `"Hauptteil"`)],
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

== Kapitel-Eigenschaften (`chapters`) <kapitel-eigenschaften-chapters>

#table(
  columns: 4,
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

=== `break_before` — wie ein Kapitel abgesetzt wird <breakbefore-wie-ein-kapitel-abgesetzt-wird>

Ein Schlüssel mit drei Werten, keine zwei unabhängigen Schalter:

#table(
  columns: 2,
  align: (left, left),
  table.header([* Wert *], [* Wirkung *]),
  [`page`], [Standard. Das Kapitel beginnt oben auf einer neuen Seite],
  [`divider`], [Dem Kapitel geht eine eigene Trennseite voraus],
  [`none`], [Das Kapitel läuft im Fließtext weiter],
)

Dass es _ein_ Schlüssel ist, hat einen Grund: die drei Werte sind eine Achse, nicht drei Fragen. Als zwei Booleans ließe sich „Trennseite, aber kein Seitenumbruch" hinschreiben — ein Zustand, den es nicht gibt, weil eine Trennseite immer umbricht. Eine Angabe, die man notieren kann und die nichts bewirkt, ist eine Fehlerquelle ohne Gegenwert.

`page` ist die Erwartung an ein gesetztes Dokument. Wer kurze Abschnitte durchlaufen lassen will — Merkblätter, Referenzkarten, eng gesetzte Anhänge — setzt am einzelnen Kapitel `break_before: "none"`.

Bei `divider` fallen der Umbruch des Kapitels und der der Trennseite auf dieselbe Stelle und verschmelzen zu einem — es entsteht kein Leerblatt. Vor dem ersten Kapitel greift die Regel nicht.

Ein unbekannter Wert bricht den Build ab, statt still auf `page` zurückzufallen: aus einem vertippten `divder` würde sonst klaglos ein normaler Seitenumbruch, und die fehlende Trennseite fände man erst beim Durchblättern des fertigen PDFs.

=== `chapter_toc` und `document_toc` — zwei Verzeichnisse, ein Vokabular <chaptertoc-und-documenttoc-zwei-verzeichnisse-ein-vokabular>

Ein Dokument hat zwei Inhaltsverzeichnisse, und für jedes gibt es ein Paar aus Vorgabe und Einzelfall:

#table(
  columns: 3,
  align: (left, left, left),
  table.header([* Verzeichnis *], [* Vorgabe unter `document:` *], [* Am Kapitel *]),
  [Das *große* vorn im Dokument], [`document_toc`], [`document_toc`],
  [Das *kleine* auf der Kapitel-Trennseite], [`chapter_toc`], [`chapter_toc`],
)

Alle vier Schlüssel nehmen dieselben drei Schreibweisen:

#table(
  columns: 2,
  align: (left, left),
  table.header([* Wert *], [* Bedeutung *]),
  [`none`], [Kommt in diesem Verzeichnis gar nicht vor],
  [`full`], [Jede Ebene],
  [_Zahl_], [Bis zu dieser Tiefe, gezählt ab der Kapitelüberschrift],
)

Die Tiefe zählt *innerhalb des Kapitels*: 1 ist die Kapitelüberschrift selbst, 2 die Ebene darunter. `document_toc: 1` nimmt das Kapitel also ins große Verzeichnis auf, seine Zwischenüberschriften aber nicht. `chapter_toc: 2` listet auf der Trennseite genau die Ebene unterhalb der Kapitelüberschrift.

Für den häufigsten Fall genügen damit zwei Zeilen im `document`-Block:

```yaml
document:
  document_toc: 2       # großes Verzeichnis, zwei Ebenen tief
  chapter_toc: 2        # kleine Verzeichnisse ebenso
```

`document_toc: "none"` lässt das große Verzeichnis ganz weg; die Angaben an den Kapiteln sind dann gegenstandslos.

=== Vererbung <vererbung>

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

`chapter_toc` wird *nicht* von Kapitel zu Unterkapitel gereicht. Es beschreibt die Trennseite genau dieses Kapitels, und die hat jedes Kapitel für sich; ohne eigene Angabe gilt schlicht `document.chapter_toc`.

=== Was gekürzt wird — und was nicht <was-gekuerzt-wird-und-was-nicht>

Der Fließtext bleibt unberührt: die Zwischenüberschriften stehen weiterhin im Kapitel, samt Nummerierung und Sprungzielen. Gekürzt wird ausschließlich das Verzeichnis. Ein Unterkapitel behält dabei seinen eigenen Eintrag — vererbt wird die Tiefe relativ zu jedem Kapitel, nicht über die zusammengelegte Liste.

Ein unbekannter Wert bricht den Build ab. Auch Wahrheitswerte werden abgewiesen: einem `true` sähe man die Tiefe nicht an — genau dafür gibt es `full`.

== Nummerierung <nummerierung>

`document.autonum_style` legt den Stil für das ganze Dokument fest; `autonum_style` an einem Kapitel oder Part weicht davon ab und *gibt den Wert nach unten weiter*. Ohne diese Vererbung bliebe die Angabe am Part wirkungslos: die Überschriften stehen in den Kapiteldateien, nicht im Part.

`autonum_style: "none"` heißt: in diesem Zweig trägt *nichts* eine Nummer — weder die Kapitelüberschrift noch die Ebenen darunter. Es gibt also auch keinen Neustart bei 1, denn innerhalb des Zweigs läuft keine Zählung, die neu beginnen könnte.

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

=== Nummerierung ab Unterebenen (`autonum_from_level` & `autonum_prefix`) <nummerierung-ab-unterebenen-autonumfromlevel-autonumprefix>

Für lange Anhänge oder spezialisierte Abschnitte, deren Haupttitel keine Ziffer tragen soll (z. B. _„Anhang A: Referenz“_), deren Unterabschnitte aber durchnummeriert werden sollen:

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

