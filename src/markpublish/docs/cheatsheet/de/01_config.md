<style>
/* Eine Referenzkarte ist absichtlich dichter gesetzt als Fliesstext: nur so
   bleiben beide Seiten vollstaendig. Der Block gilt nur fuer dieses Dokument -
   auf eigene Builds hat er keine Wirkung. Farben, Schrift und Rahmen kommen
   weiterhin aus dem Theme, hier wird ausschliesslich die Dichte geregelt.

   Beide Uebersetzungen tragen denselben Block, bemessen an der laengeren:
   deutscher Satz braucht fuer dieselbe Aussage rund ein Sechstel mehr Platz.
   Wer hier lockerer setzt, verliert die zweite Seite - in einer Sprache. */
.chapter-body table { margin: 0.4em 0; font-size: 8.5pt; }
.chapter-body th, .chapter-body td { padding: 0.9mm 2.2mm; }
.chapter-body h1 { margin-top: 0; margin-bottom: 0.3em; }
.chapter-body h2 { margin-top: 0.75em; margin-bottom: 0.15em; }
.chapter-body p { margin: 0.35em 0; }
.chapter-body pre { margin: 0.4em 0; }
</style>

# markpublish.yaml

Drei Schlüssel auf oberster Ebene: `document`, `theme`, `chapters`. Alle Pfade
sind relativ zu dieser Datei. Bauen: `markpublish build [datei] -t pdf|html|all`.

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
| `chapter_toc` | `none` | Kleine Trennseiten-Verzeichnisse, gleiche Formen |
| `autonum_style` | `decimal` | `decimal`, `roman`, `legal`, `none` |

Außerdem: `summary` (Abstract auf dem Deckblatt), `status`, `copyright`
(Fußzeile). Unbekannte Schlüssel gehen als `{{ document.mein_schluessel }}` ans
Theme.

## chapters

Kapitel, Unterkapitel und Parts; rekursiv verschachtelbar.

| Schlüssel | Standard | Bedeutung |
| :--- | :--- | :--- |
| `file` | – | Pfad zu einer Markdown-Datei |
| `title` | – | Ersetzt die Überschrift in TOC und Kopfzeile |
| `part` | – | Macht den Eintrag zum Part statt zum Kapitel |
| `break_before` | `page` | `page`, `divider` (eigene Trennseite) oder `none` |
| `chapter_toc` | `none` | Kleines Verzeichnis auf der Trennseite |
| `document_toc` | `full` | Anteil dieses Kapitels am Verzeichnis vorn |
| `chapters` | `[]` | Verschachtelte Unterkapitel |

Beide TOC-Schlüssel nehmen `none`, `full` oder eine Tiefe, gezählt ab der
eigenen Überschrift. `document_toc: 1` listet das Kapitel ohne seine
Unterüberschriften; am Part gesetzt, flacht es alle Anhänge auf einmal ab.
`document_toc`, `autonum` und `autonum_from_level` (z. B. `2` für Zählung ab `##` mit optionalem `autonum_prefix`) vererben nach unten, `chapter_toc` fällt auf `document.chapter_toc` zurück.
