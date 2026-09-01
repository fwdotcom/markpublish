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
| `language` | String | `"de"` | ISO-Sprachcode (`de`, `en`, ...). Steuert Template-Beschriftungen, Callout-Titel und Datumsformat |
| `cover` | Bool | `true` | Deckblatt aktivieren/deaktivieren |
| `toc` | Bool | `true` | Globales Inhaltsverzeichnis aktivieren |
| `autonum_type` | String | `"decimal"` | `"decimal"`, `"roman"`, `"legal"`, `"none"` |
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
| `toc` | Bool/Int | `false` | Lokales Kapitel-TOC (z. B. `2` für max. Tiefe). Steht auf der Trennseite, also ebenfalls nur PDF |
| `toc_depth` | Int | `null` | Begrenzt, wie tief dieser Zweig ins globale Inhaltsverzeichnis einzieht |
| `autonum` | String | `null` | Lokaler Override des Nummerierungsstils |
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

### `toc_depth` — Anhänge im Inhaltsverzeichnis flach halten

Gezählt wird innerhalb des Kapitels, genau wie bei `toc`: Tiefe 1 ist die
Kapitelüberschrift selbst, Tiefe 2 die Ebene darunter. `toc_depth: 1` nimmt das
Kapitel also ins globale Inhaltsverzeichnis auf, seine Zwischenüberschriften
aber nicht mehr.

Der Wert wird nach unten vererbt: an einem Part gesetzt, gilt er für alle
Kapitel darunter, und ein Kapitel gibt ihn an seine Unterkapitel weiter. Für den
häufigsten Fall — ein Anhang, dessen innere Gliederung das Verzeichnis nur
aufbläht — genügt damit eine Zeile:

```yaml
  - part: "Anhänge"
    toc_depth: 1
    chapters:
      - file: "chapters/07_appendix_yaml_spec.md"
        title: "Anhang A: YAML-Schema-Referenz"
      - file: "chapters/08_appendix_troubleshooting.md"
        title: "Anhang B: Troubleshooting"
```

Der Fließtext bleibt unberührt: die Zwischenüberschriften stehen weiterhin im
Kapitel, samt Nummerierung und Sprungzielen. Gekürzt wird ausschließlich das
Verzeichnis. Ein Unterkapitel behält dabei seinen eigenen Eintrag — vererbt wird
die Tiefe relativ zu jedem Kapitel, nicht über die zusammengelegte Liste.

