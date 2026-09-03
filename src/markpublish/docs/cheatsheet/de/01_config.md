# markpublish.yaml

Oberste Ebene: `document`, `theme`, `parts`, optional `templates_dir`. Pfade
relativ zu dieser Datei. Bauen: `markpublish build [datei] -t pdf`.

## document

Metadaten und globale Layout-Schalter. Pflicht ist allein `title`.

| Schlüssel | Standard | Bedeutung |
| :--- | :--- | :--- |
| `title` / `subtitle` | *title nötig* | Deckblatt, Kopfzeile, Dateiname |
| `author` | – | Deckblatt |
| `date` / `version` | `auto` / – | `auto` oder `today` für das Baudatum |
| `language` | Systemsprache | Wählt die Beschriftungen, sonst `en` |
| `cover` / `header` / `footer` | `true` | Deckblatt, Kopf- und Fußzeile |
| `document_toc` | `full` | Großes Verzeichnis: `none`, `full` oder Tiefe |
| `part_toc` / `chapter_toc` | `full` | Trennseiten-Verzeichnisse, gleiche Formen |
| `autonum_style` | `decimal` | `decimal`, `roman`, `legal`, `none` |
| `autonum_from_level` | `1` | Ab welcher Überschriftenebene gezählt wird |
| `autonum_reset` / `pagenum_reset` | `false` | Zähler bzw. Seitenzahl neu beginnen |

Außerdem `summary` (Deckblatt), `status`, `copyright` (Fußzeile). Eigene
Zusatzfelder gehen über das Wörterbuch `meta` (`meta.at("mein_schluessel").value`) ans Theme.

## parts und chapters

Genau zwei Stufen: `parts:` gliedert, `chapters:` trägt den Inhalt. Seitentitel
stammen aus der Datei-H1, Verzeichnis- und Trennseitentitel lassen sich steuern.

| Schlüssel | Gilt für | Bedeutung |
| :--- | :--- | :--- |
| `part` | Part | Name des Parts, Pflicht |
| `chapters` | Part | Liste der Kapitel, mindestens eines |
| `file` | Kapitel | Pfad zur Markdown-Datei |
| `toc_title` | beide | Titel für Inhaltsverzeichnis und Kopfzeilen |
| `divider_title` | beide | Titel auf der Trennseite |
| `subtitle` / `summary` | beide | Untertitel und Kurzbeschreibung auf Trennseiten |
| `break_before` | beide | `page`, `divider` (Trennseite) oder `none` |
| `document_toc` | beide | Anteil am Verzeichnis vorn |
| `part_toc` / `chapter_toc` | Part / Kapitel | Verzeichnis auf der Trennseite |
| `autonum_*`, `pagenum_reset` | beide | Wie unter `document`, hier lokal |

`document_toc: 1` listet ein Kapitel ohne seine Unterüberschriften; am Part
gesetzt, flacht es alle Anhänge auf einmal ab. `autonum_*` und `document_toc`
vererben von `document` über den Part zum Kapitel — der tiefere Wert gewinnt.
