# Anhang A: YAML-Schema-Referenz

Vollständige Übersicht aller Konfigurationsoptionen in `markpublish.yaml`.

## Dokumenten-Eigenschaften (`document`)

| Schlüssel | Typ | Standard | Beschreibung |
| :--- | :--- | :--- | :--- |
| `title` | String | *Pflicht* | Titel der Publikation |
| `subtitle` | String | `null` | Untertitel |
| `summary` | String | `null` | Zusammenfassung für Deckblatt |
| `author` | String | `null` | Name des Autors |
| `status` | String | `null` | Dokumentstatus (z. B. "Entwurf", "Freigegeben") |
| `copyright` | String | `null` | Copyright-Angabe (z. B. "© 2026 Frank Winter") |
| `date` | String | `"auto"` | Datum oder `"auto"` für Tagesdatum |
| `version` | String | `null` | Versionskennung. Ohne Angabe entfällt das Feld auf dem Deckblatt; ist sie gesetzt, steht sie in der Fußzeile links neben dem Datum |
| `language` | String | Systemsprache | ISO-Sprachcode (`de`, `en`, ...). Steuert Template-Beschriftungen, Callout-Titel und Datumsformat |
| `cover` | Bool | `true` | Deckblatt aktivieren/deaktivieren |
| `document_toc` | String/Int | `full` | Das große Verzeichnis: `none`, `full` oder eine Tiefe. Vorgabe für die Kapitel |
| `autonum_style` | String | `"decimal"` | `"decimal"`, `"roman"`, `"legal"`, `"none"`. Wurzel für `chapters.autonum_style` |
| `chapter_toc` | String/Int | `none` | Die kleinen Verzeichnisse: `none`, `full` oder eine Tiefe. Vorgabe für die Kapitel |
| `header` | Bool | `true` | Laufende Kopfzeile aktivieren (Aufbau im Theme) |
| `footer` | Bool | `true` | Laufende Fußzeile aktivieren (Aufbau im Theme) |

## Kapitel- und Part-Eigenschaften (`chapters`)

| Schlüssel | Typ | Standard | Beschreibung |
| :--- | :--- | :--- | :--- |
| `file` | String | `null` | Pfad zur Markdown-Datei |
| `title` | String | `null` | Überschreibt den Titel der Datei |
| `summary` | String | `null` | Zusammenfassung für Trennseite |
| `part` | String | `null` | Deklariert einen übergeordneten Part |
| `break_before` | String | `page` | Wie das Kapitel abgesetzt wird: `page`, `divider` oder `none`. Nur PDF — das mitgelieferte HTML-Theme kennt weder Seiten noch Trennseiten |
| `chapter_toc` | String/Int | `none` | Das kleine Verzeichnis auf der Trennseite des Kapitels. Also ebenfalls nur PDF |
| `document_toc` | String/Int | `full` | Der Beitrag zum großen Verzeichnis vorn im Dokument. Wird nach unten vererbt |
| `autonum_style` | String | `null` | Nummerierungsstil für diesen Zweig (`decimal`, `roman`, `legal`, `none`). Wird nach unten vererbt |
| `autonum_from_level` | Int | `1` | Ab welcher Überschriften-Ebene nummeriert wird (`1` = `h1`, `2` = `h2`, ...). Wird nach unten vererbt |
| `autonum_prefix` | String | `null` | Optionales Präfix für Ziffern (z. B. `"A."` ➔ `A.1`, `A.2`). Wird nach unten vererbt |
| `autonum_reset` | Bool | `false` | Zähler zu Kapitelbeginn auf 0 zurücksetzen (Standard `true` bei `autonum_from_level > 1`) |
| `chapters` | Liste | `[]` | Verschachtelte Unterkapitel |

### `break_before` — wie ein Kapitel abgesetzt wird

Ein Schlüssel mit drei Werten, keine zwei unabhängigen Schalter:

| Wert | Wirkung |
| :--- | :--- |
| `page` | Standard. Das Kapitel beginnt oben auf einer neuen Seite |
| `divider` | Dem Kapitel geht eine eigene Trennseite voraus |
| `none` | Das Kapitel läuft im Fließtext weiter |

Dass es *ein* Schlüssel ist, hat einen Grund: die drei Werte sind eine Achse,
nicht drei Fragen. Als zwei Booleans ließe sich „Trennseite, aber kein
Seitenumbruch" hinschreiben — ein Zustand, den es nicht gibt, weil eine
Trennseite immer umbricht. Eine Angabe, die man notieren kann und die nichts
bewirkt, ist eine Fehlerquelle ohne Gegenwert.

`page` ist die Erwartung an ein gesetztes Dokument. Wer kurze Abschnitte
durchlaufen lassen will — Merkblätter, Referenzkarten, eng gesetzte Anhänge —
setzt am einzelnen Kapitel `break_before: "none"`; die Vorgabe lässt sich auch
im Frontmatter der Markdown-Datei überschreiben.

Bei `divider` fallen der Umbruch des Kapitels und der der Trennseite auf
dieselbe Stelle und verschmelzen zu einem — es entsteht kein Leerblatt. Vor dem
ersten Kapitel greift die Regel nicht.

Ein unbekannter Wert bricht den Build ab, statt still auf `page` zurückzufallen:
aus einem vertippten `divder` würde sonst klaglos ein normaler Seitenumbruch,
und die fehlende Trennseite fände man erst beim Durchblättern des fertigen PDFs.

### `chapter_toc` und `document_toc` — zwei Verzeichnisse, ein Vokabular

Ein Dokument hat zwei Inhaltsverzeichnisse, und für jedes gibt es ein Paar aus
Vorgabe und Einzelfall:

| Verzeichnis | Vorgabe unter `document:` | Am Kapitel |
| :--- | :--- | :--- |
| Das **große** vorn im Dokument | `document_toc` | `document_toc` |
| Das **kleine** auf der Kapitel-Trennseite | `chapter_toc` | `chapter_toc` |

Alle vier Schlüssel nehmen dieselben drei Schreibweisen:

| Wert | Bedeutung |
| :--- | :--- |
| `none` | Kommt in diesem Verzeichnis gar nicht vor |
| `full` | Jede Ebene |
| *Zahl* | Bis zu dieser Tiefe, gezählt ab der Kapitelüberschrift |

Die Tiefe zählt **innerhalb des Kapitels**: 1 ist die Kapitelüberschrift selbst,
2 die Ebene darunter. `document_toc: 1` nimmt das Kapitel also ins große
Verzeichnis auf, seine Zwischenüberschriften aber nicht. `chapter_toc: 2`
listet auf der Trennseite genau die Ebene unterhalb der Kapitelüberschrift.

Für den häufigsten Fall genügen damit zwei Zeilen im `document`-Block:

```yaml
document:
  document_toc: 2       # großes Verzeichnis, zwei Ebenen tief
  chapter_toc: 2        # kleine Verzeichnisse ebenso
```

`document_toc: "none"` lässt das große Verzeichnis ganz weg; die Angaben an den Kapiteln
sind dann gegenstandslos.

### Vererbung

`document_toc` wird nach unten vererbt: an einem Part gesetzt, gilt er für alle
Kapitel darunter, und ein Kapitel gibt ihn an seine Unterkapitel weiter. Für den
häufigsten Fall — ein Anhang, dessen innere Gliederung das Verzeichnis nur
aufbläht — genügt damit eine Zeile:

```yaml
  - part: "Anhänge"
    document_toc: 1
    chapters:
      - file: "chapters/07_appendix_yaml_spec.md"
        title: "Anhang A: YAML-Schema-Referenz"
      - file: "chapters/08_appendix_troubleshooting.md"
        title: "Anhang B: Troubleshooting"
```

Ein einzelnes Kapitel schlägt das Geerbte — auch zurück auf `full`. Genau dafür
gibt es das Schlüsselwort: ohne es müsste man eine willkürlich große Zahl
hinschreiben, um „doch wieder alles" zu sagen.

`chapter_toc` wird **nicht** von Kapitel zu Unterkapitel gereicht. Es beschreibt
die Trennseite genau dieses Kapitels, und die hat jedes Kapitel für sich; ohne
eigene Angabe gilt schlicht `document.chapter_toc`.

### Was gekürzt wird — und was nicht

Der Fließtext bleibt unberührt: die Zwischenüberschriften stehen weiterhin im
Kapitel, samt Nummerierung und Sprungzielen. Gekürzt wird ausschließlich das
Verzeichnis. Ein Unterkapitel behält dabei seinen eigenen Eintrag — vererbt wird
die Tiefe relativ zu jedem Kapitel, nicht über die zusammengelegte Liste.

Ein unbekannter Wert bricht den Build ab. Auch Wahrheitswerte werden abgewiesen:
einem `true` sähe man die Tiefe nicht an — genau dafür gibt es `full`.

## Nummerierung

`document.autonum_style` legt den Stil für das ganze Dokument fest; `autonum_style` an
einem Kapitel oder Part weicht davon ab und **gibt den Wert nach unten weiter**.
Ohne diese Vererbung bliebe die Angabe am Part wirkungslos: die Überschriften
stehen in den Kapiteldateien, nicht im Part.

`autonum_style: "none"` heißt: in diesem Zweig trägt **nichts** eine Nummer — weder die
Kapitelüberschrift noch die Ebenen darunter. Es gibt also auch keinen Neustart
bei 1, denn innerhalb des Zweigs läuft keine Zählung, die neu beginnen könnte.

Der Dokumentzähler bleibt dabei unangetastet. Eine unnummerierte Strecke
verbraucht keine Nummer:

```yaml
chapters:
  - file: "chapters/01.md"          # 1
  - part: "Anhänge"
    autonum_style: "none"           # Anhänge: keine Nummern
    chapters:
      - file: "chapters/a.md"
      - file: "chapters/b.md"
  - file: "chapters/02.md"          # 2, nicht 4
```

### Nummerierung ab Unterebenen (`autonum_from_level` & `autonum_prefix`)

Für lange Anhänge oder spezialisierte Abschnitte, deren Haupttitel keine Ziffer tragen soll (z. B. *„Anhang A: Referenz“*), deren Unterabschnitte aber durchnummeriert werden sollen:

- `autonum_from_level: 2` lässt die `h1`-Überschrift unnummeriert und beginnt die Zählung erst ab `h2` (`1`, `2`, ...) bzw. `h3` (`1.1`, `1.2`).
- Bei `autonum_from_level > 1` wird der Zähler für jedes Kapitel automatisch isoliert zurückgesetzt.
- `autonum_prefix: "A."` stellt den generierten Nummern ein Präfix voran (`A.1`, `A.2`, `A.2.1`).

```yaml
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
