# markpublish.yaml

Oberste Ebene der Konfigurationsdatei: `document`, `theme`, `parts`, optional `templates_dir`. Sämtliche Pfade gelten relativ zum Verzeichnis dieser Datei. Bauen mit: `markpublish build [CONFIG_FILE] [OPTIONEN]`.

## document

Metadaten und globale Layout-Schalter. Pflichtangabe ist allein `title`.

| Schlüssel | Standard | Bedeutung |
| :--- | :--- | :--- |
| `title` | *Pflichtangabe* | Titel des Dokuments (Deckblatt, Kopfzeile, Dateiname) |
| `subtitle` | – | Untertitel auf dem Deckblatt |
| `summary` | – | Zusammenfassung / Abstract auf dem Deckblatt |
| `author` | – | Name des Autors (Deckblatt) |
| `date` | `auto` | Datum auf dem Deckblatt (`auto` oder `today` für das Baudatum) |
| `version` | – | Versionsnummer auf dem Deckblatt und in der Fußzeile |
| `status` | – | Dokumentstatus auf dem Deckblatt (z. B. `Entwurf`, `Freigegeben`) |
| `copyright` | – | Copyright-Hinweis auf dem Deckblatt |
| `language` | Systemsprache | ISO-Sprachcode für statische Beschriftungen (`de`, `en`) |
| `cover` | `false` | Deckblatt erzeugen (`true` oder `false`) |
| `header` | `true` | Lebende Kopfzeilen aktivieren (`true` oder `false`) |
| `footer` | `true` | Fußzeilen aktivieren (`true` oder `false`) |
| `document_toc` | `full` | Haupt-Inhaltsverzeichnis: `none`, `full` oder Tiefe als Zahl |
| `part_toc` | `full` | Vorgabe für Part-Trennseiten: `none`, `full` oder Tiefe |
| `chapter_toc` | `full` | Vorgabe für Kapitel-Trennseiten: `none`, `full` oder Tiefe |
| `autonum_style` | `decimal` | Zählstil für Überschriften: `decimal`, `roman`, `legal`, `none` |
| `autonum_from_level` | `1` | Ab welcher Ebene nummeriert wird (1 = H1, 2 = H2, ...) |
| `autonum_prefix` | – | Präfix vor Überschriftennummern (z. B. `A.` für A.1) |
| `autonum_reset` | `false` | Zähler für Überschriften bei jedem Kapitel neu beginnen |
| `pagenum_reset` | `false` | Seitennummerierung für jeden Part oder Kapitel neu beginnen |

Eigene Zusatzfelder unter `document:` (z. B. `abteilung: "F&E"`, `projekt: "Alpha"`)
werden über das Wörterbuch `meta` an das Theme weitergereicht (`meta.at("feld").value`)
und gedruckt, sofern das Theme sie vorsieht. Statische Beschriftungen gehören in die
`i18n.yaml`, nicht in `document:`.

## parts und chapters

Genau zwei Stufen: `parts:` gliedert, `chapters:` trägt den Inhalt. Seitentitel
stammen aus der H1 der Markdown-Datei; Verzeichnis- und Trennseitentitel lassen sich
individuell steuern.

| Schlüssel | Ebene | Standard | Bedeutung |
| :--- | :--- | :--- | :--- |
| `part` | Part | *Pflichtangabe* | Name des Abschnitts |
| `chapters` | Part / Kapitel | *Pflichtangabe* | Liste der Kapitel bzw. Unterkapitel (mindestens eines) |
| `file` | Kapitel | *Pflichtangabe* | Pfad zur Markdown-Datei (relativ zur Konfiguration) |
| `show_title` | Kapitel | `true` | Datei-H1 auf der Inhaltsseite anzeigen (`false` blendet sie aus) |
| `toc_title` | Part / Kapitel | Datei-H1 / `part` | Titel für Haupt-Inhaltsverzeichnis und Kopfzeilen |
| `divider_title` | Part / Kapitel | `part` / Datei-H1 | Titel auf der Trennseite |
| `subtitle` | Part / Kapitel | – | Untertitel auf der Trennseite |
| `summary` | Part / Kapitel | – | Kurzbeschreibung auf der Trennseite |
| `break_before` | Part / Kapitel | `none` / `page` | Seitenumbruch: `divider` (Trennseite), `page` oder `none` |
| `document_toc` | Part / Kapitel | geerbt | Beitrag zum Haupt-Inhaltsverzeichnis (`none`, `full`, Tiefe) |
| `part_toc` | Part | geerbt | Lokales Verzeichnis auf der Part-Trennseite |
| `chapter_toc` | Part / Kapitel | geerbt | Lokales Verzeichnis auf der Kapitel-Trennseite |
| `autonum_style` | Part / Kapitel | geerbt | Lokaler Zählstil (`decimal`, `roman`, `legal`, `none`) |
| `autonum_from_level` | Part / Kapitel | geerbt | Ebene, ab der nummeriert wird |
| `autonum_prefix` | Part / Kapitel | geerbt | Präfix für Nummern in diesem Abschnitt |
| `autonum_reset` | Part / Kapitel | `false` | Zähler am Beginn des Abschnitts/Kapitels zurücksetzen |
| `pagenum_reset` | Part / Kapitel | `false` | Seitennummerierung am Beginn zurücksetzen |

`document_toc: 1` listet ein Kapitel ohne seine Unterüberschriften; am Part
gesetzt, flacht es alle enthaltenen Kapitel auf einmal ab. Optionen mit dem
Vermerk *geerbt* übernehmen ihren Standardwert von `document` über den Part
zum Kapitel – die tiefere Angabe gewinnt.
