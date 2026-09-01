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
| `autonum_type` | String | `"decimal"` | `"decimal"`, `"roman"`, `"legal"`, `"none"`. Wurzel für `chapters.autonum` |
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
| `autonum` | String | `null` | Nummerierungsstil für diesen Zweig. Wird nach unten vererbt |
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

`document.autonum_type` legt den Stil für das ganze Dokument fest; `autonum` an
einem Kapitel oder Part weicht davon ab und **gibt den Wert nach unten weiter**.
Ohne diese Vererbung bliebe die Angabe am Part wirkungslos: die Überschriften
stehen in den Kapiteldateien, nicht im Part.

`autonum: "none"` heißt: in diesem Zweig trägt **nichts** eine Nummer — weder die
Kapitelüberschrift noch die Ebenen darunter. Es gibt also auch keinen Neustart
bei 1, denn innerhalb des Zweigs läuft keine Zählung, die neu beginnen könnte.

Der Dokumentzähler bleibt dabei unangetastet. Eine unnummerierte Strecke
verbraucht keine Nummer:

```yaml
chapters:
  - file: "chapters/01.md"          # 1
  - part: "Anhänge"
    autonum: "none"                 # Anhänge: keine Nummern
    chapters:
      - file: "chapters/a.md"
      - file: "chapters/b.md"
  - file: "chapters/02.md"          # 2, nicht 4
```
