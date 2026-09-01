<style>
/* Eine Referenzkarte ist absichtlich dichter gesetzt als Fliesstext: nur so
   bleiben beide Seiten vollstaendig. Der Block gilt nur fuer dieses Dokument -
   auf eigene Builds hat er keine Wirkung. Farben, Schrift und Rahmen kommen
   weiterhin aus dem Theme, hier wird ausschliesslich die Dichte geregelt.

   Beide Uebersetzungen tragen denselben Block, bemessen an der laengeren:
   deutscher Satz braucht fuer dieselbe Aussage rund ein Sechstel mehr Platz.
   Wer hier lockerer setzt, verliert die zweite Seite - in einer Sprache.

   8pt in den Tabellen ist die Untergrenze. Waechst das Schema weiter, ist
   nicht die Schrift das Stellrad, sondern der Inhalt: die vollstaendige
   Referenz steht in Anhang A des Handbuchs, hier nur, was man staendig
   nachschlaegt. */
.chapter-body table { margin: 0.4em 0; font-size: 8pt; }
.chapter-body th, .chapter-body td { padding: 0.7mm 2.0mm; }
.chapter-body h1 { margin-top: 0; margin-bottom: 0.3em; }
.chapter-body h2 { margin-top: 0.75em; margin-bottom: 0.15em; }
.chapter-body p { margin: 0.35em 0; }
.chapter-body pre { margin: 0.4em 0; }
</style>

# markpublish.yaml

Oberste Ebene: `document`, `theme`, `parts`, optional `templates_dir`. Pfade
relativ zu dieser Datei. Bauen: `markpublish build [datei] -t pdf|html|all`.

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

Außerdem `summary` (Deckblatt), `status`, `copyright` (Fußzeile). Unbekannte
Schlüssel gehen als `{{ document.mein_schluessel }}` ans Theme.

## parts und chapters

Genau zwei Stufen: `parts:` gliedert, `chapters:` trägt den Inhalt. Kapitel
schachteln **nicht** weiter — Tiefe entsteht aus den Überschriften der Datei.

| Schlüssel | Gilt für | Bedeutung |
| :--- | :--- | :--- |
| `title` / `part` | Part | Name des Parts, Pflicht |
| `chapters` | Part | Flache Liste der Kapitel, mindestens eines |
| `file` | Kapitel | Pfad zur Markdown-Datei |
| `title` / `subtitle` / `summary` | beide | Überschreiben, was in der Datei steht |
| `break_before` | beide | `page`, `divider` (Trennseite) oder `none` |
| `document_toc` | beide | Anteil am Verzeichnis vorn |
| `part_toc` / `chapter_toc` | Part / Kapitel | Verzeichnis auf der Trennseite |
| `autonum_*`, `pagenum_reset` | beide | Wie unter `document`, hier lokal |

`document_toc: 1` listet ein Kapitel ohne seine Unterüberschriften; am Part
gesetzt, flacht es alle Anhänge auf einmal ab. `autonum_*` und `document_toc`
vererben von `document` über den Part zum Kapitel — der tiefere Wert gewinnt.
