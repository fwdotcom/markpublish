# Schema-Referenz markpublish.yaml

Dieser Anhang enthält die vollständige Spezifikation aller Konfigurationsoptionen der `markpublish.yaml`.

---

## Dokument-Ebene (document)

Die Sektion `document:` legt globale Metadaten, Layoutschalter, Verzeichnisvorgaben und Nummerierungsstile für das Gesamtdokument fest.

| Schlüssel | Typ | Default | Beschreibung |
| :--- | :--- | :--- | :--- |
| `title` | String | *(Pflichtfeld)* | Titel des Dokuments (erscheint auf Deckblatt, Kopfzeilen und Metadaten). |
| `subtitle` | String | `None` | Untertitel des Dokuments. |
| `summary` | String | `None` | Zusammenfassung oder Abstract (erscheint auf dem Deckblatt). |
| `author` | String | `None` | Name des Autors oder der Organisation. |
| `status` | String | `None` | Status des Dokuments (z. B. „Entwurf“, „Freigegeben“, „Vertraulich“). |
| `copyright` | String | `None` | Copyright-Hinweis (z. B. „© 2026 Frank Winter“). |
| `date` | String | `"auto"` | Datum des Dokuments. Bei `"auto"` oder `"today"` wird das aktuelle Tagesdatum eingesetzt. |
| `version` | String | `None` | Versionskennung (z. B. `"2.0.0"`). Wird nur gedruckt, wenn explizit gesetzt. |
| `language` | String | *(Systemsprache)* | ISO-Sprachcode (z. B. `"de"` oder `"en"`). Steuert Silbentrennung und UI-Texte. |
| `cover` | Boolean | `false` | Steuert, ob eine gestaltete Deckblattseite erzeugt wird. Ohne Angabe beginnt das Dokument mit dem ersten Inhalt. |
| `header` | Boolean | `true` | Aktiviert oder deaktiviert die laufende Kopfzeile im Dokument. |
| `footer` | Boolean | `true` | Aktiviert oder deaktiviert die laufende Fußzeile (inkl. Seitennummerierung). |
| `document_toc` | Scope | `"full"` | Tiefe des Haupt-Inhaltsverzeichnisses (`"none"`, `"full"` oder Zahl $\ge 1$). |
| `part_toc` | Scope | `"full"` | Standardtiefe für lokale Inhaltsverzeichnisse auf Abschnitts-Trennseiten. |
| `chapter_toc` | Scope | `"full"` | Standardtiefe für lokale Inhaltsverzeichnisse auf Kapitel-Trennseiten. |
| `autonum_pattern` | String | *s. unten* | Aufbau der Nummern; Slot 1 ist der Part, Slot 2 das Kapitel. `none` schaltet die Nummerierung ab. |
| `autonum_reset` | Boolean | `false` | Lässt die Ebenen darunter beim Betreten wieder bei 1 anfangen. |
| `part_label` | String | aus i18n | Wort, das einen Abschnitt benennt (z. B. `"Teil"`). Leer notiert (`""`) entfällt es. |
| `chapter_label` | String | aus i18n | Wort, das ein Kapitel benennt (z. B. `"Kapitel"`). Leer notiert (`""`) entfällt es. |
| `pagenum_reset` | Boolean | `false` | Startet die Seitennummerierung bei jedem Abschnitt oder Kapitel neu bei Seite 1. |

> [!NOTE] Freie Metadatenfelder unter `document:`
> Über die aufgeführten Standardfelder hinaus sind unter `document:` beliebige eigene Metadatenfelder erlaubt (z. B. `abteilung: "F&E"`, `freigegeben: true`). Sie werden typisiert an das Theme (`meta: (:)`) übergeben.
>
> Statische Textbeschriftungen (`document.i18n` oder `document.labels`) sind hier jedoch unzulässig und führen zum Abbruch – Textübersetzungen gehören ausschließlich in die `i18n.yaml`-Dateien der Kaskade.


---

## Globale Projekt-Einstellungen

Direkt auf oberster Ebene der `markpublish.yaml` (neben `document:` und `parts:`) können folgende Schalter gesetzt werden:

| Schlüssel | Typ | Default | Beschreibung |
| :--- | :--- | :--- | :--- |
| `theme` | String | `"default"` | Name des zu verwendenden Themes. |
| `templates_dir` | String | `None` | Optionaler benutzerdefinierter Pfad zu einem Verzeichnis mit Themes. |

> [!NOTE] Strikte Schlüsselprüfung auf oberster Ebene
> Auf oberster Ebene der `markpublish.yaml` sind ausschließlich die deklarierten Schlüssel (`document`, `theme`, `templates_dir`, `parts`) zulässig. Unbekannte Schlüssel (wie Tippfehler bei `theam:`) werden mit einem Namensvorschlag strikt abgewiesen.

### Nummerierungs-Pattern

`autonum_pattern` beschreibt den Aufbau der Nummern als Kette von Slots, getrennt durch `|`. Slot 1 gehört zur ersten Ebene *unter* der Stelle, an der das Pattern steht: unter `document:` ist das der Part, an einem Part das Kapitel, an einem Kapitel die H2. Ein Pattern beschreibt also nie die Ebene, an der es notiert ist.

| Symbol | Ergebnis |
| :--- | :--- |
| `1` | 1, 2, 3 … |
| `01`, `001` | 01, 02 … bzw. 001, 002 … (feste Stellenzahl) |
| `a` / `A` | a, b, c … / A, B, C … |
| `i` / `I` | i, ii, iii … / I, II, III … |
| `_` | Ebene bleibt unnummeriert |
| `+` | wiederholt den Slot davor für alle tieferen Ebenen |

Alles andere im Slot ist Literal und braucht keine Anführungszeichen; nur wer ein reserviertes Zeichen wörtlich meint, setzt es in Hochkommas (`'Artikel '1`). Ein fehlerhaftes Pattern bricht den Build ab.

```text
  "_|1|.1|+"      Part ohne Nummer, Kapitel 1, Abschnitt 1.1   (Vorgabe)
  "I|1|.1|+"      Abschnitt I, II … Kapitel zählen durch
  "'Anhang 'A|.1" Anhang A, Anhang A.1
```

Notiert man ein `label`, tritt das Wort vor die Nummer der Überschrift und ihres Verzeichniseintrags: aus `A` wird `Anhang A: `. Die Unterüberschriften bleiben davon unberührt und zählen weiter `A.1`, `A.2` — deshalb gehört das Wort in diesen Schlüssel und nicht ins Pattern. Das Trennzeichen kommt aus der i18n-Kaskade (`label_separator`).

Die Part-Nummer geht nicht in die Kapitelnummern ein: sie steht auf der Trennseite und im Inhaltsverzeichnis, nicht vor jedem Kapitel. Ein Abschnitt mit `document_toc: "none"` bekommt keine Nummer und verbraucht auch keine.

---

## Abschnitts-Ebene (parts)

Die Liste `parts:` unterteilt das Dokument in übergeordnete Abschnitte. Ein Abschnitt fasst Kapitel zusammen und vererbt seine Einstellungen nach unten.

| Schlüssel | Typ | Default | Beschreibung |
| :--- | :--- | :--- | :--- |
| `part` | String | *(Pflichtfeld)* | Name des Abschnitts (z. B. „Hauptteil“, „Anhänge“). |
| `toc_title` | String | `None` | Optionaler abweichender Titel für das Inhaltsverzeichnis und Kopfzeilen (Standard: `part`). |
| `divider_title` | String | `None` | Optionaler abweichender Titel auf der Abschnitts-Trennseite (Standard: `part`). |
| `subtitle` | String | `None` | Untertitel des Abschnitts (erscheint auf der Trennseite). |
| `summary` | String | `None` | Kurzbeschreibung des Abschnitts (erscheint auf der Trennseite). |
| `break_before` | String | `"none"` | Umbruchverhalten vor dem Abschnitt: `"divider"` (Trennseite), `"page"` (Überschrift auf neuer Seite) oder `"none"` – der Abschnitt gliedert dann nur die Konfiguration und belegt keine eigene Seite. |
| `document_toc` | Scope | `None` | Überschreibt den Beitrag dieses Abschnitts zum Haupt-Inhaltsverzeichnis. |
| `part_toc` | Scope | `None` | Steuert das lokale Inhaltsverzeichnis auf der Abschnitts-Trennseite. |
| `chapter_toc` | Scope | `None` | Vererbt die Vorgabe für Kapitelverzeichnisse an alle Kapitel des Abschnitts. |
| `autonum_pattern` | String | `None` | Nummern für diesen Abschnitt; Slot 1 ist hier das Kapitel. |
| `autonum_reset` | Boolean | `None` | Lässt die Kapitel dieses Abschnitts wieder bei 1 anfangen. |
| `label` | String | aus i18n | Wort, das diesen Abschnitt benennt. Leer notiert (`""`) entfällt es. |
| `chapter_label` | String | geerbt | Wort für jedes Kapitel dieses Abschnitts (z. B. `"Anhang"`). Leer notiert (`""`) entfällt es. |
| `pagenum_reset` | Boolean | `None` | Setzt den Seitenzähler zu Beginn des Abschnitts auf 1 zurück. |
| `chapters` | Liste | *(Pflichtfeld)* | Liste der Inhaltskapitel innerhalb dieses Abschnitts (mindestens 1 Eintrag). |

---

## Kapitel-Ebene (chapters)

Die Liste `chapters:` definiert die Inhaltsdateien. Kapitel stehen immer unmittelbar unter einem Eintrag aus `parts:`.

Die Überschrift auf der Inhaltsseite wird standardmäßig durch die führende `#`-Überschrift der Markdown-Datei bestimmt (kann über `show_title: false` unterdrückt werden). Für Verzeichnisse und Trennseiten stehen zwei explizite, optionale Schlüssel bereit:

| Schlüssel | Typ | Default | Beschreibung |
| :--- | :--- | :--- | :--- |
| `file` | String | `None` | Relativer Pfad zur Markdown-Datei (z. B. `"chapters/01_intro.md"`). |
| `show_title` | Boolean | `true` | Steuert, ob die `#`-Überschrift der Datei auf der Inhaltsseite gedruckt wird. |
| `toc_title` | String | `None` | Titel für das Inhaltsverzeichnis (Haupt- und Part-TOC) sowie Kopfzeilen. Standard: Datei-H1. |
| `divider_title` | String | `None` | Titel auf der Kapitel-Trennseite (`break_before: "divider"`). Standard: Datei-H1. |
| `subtitle` | String | `None` | Untertitel des Kapitels (erscheint auf Trennseiten). |
| `summary` | String | `None` | Kurzbeschreibung (wird auf Trennseiten genutzt). |
| `break_before` | String | `"page"` | Umbruch vor dem Kapitel: `"page"` (neue Seite), `"divider"` (Trennseite) oder `"none"`. |
| `document_toc` | Scope | `None` | Beitrag dieses Kapitels zum Hauptverzeichnis (`"none"`, `"full"`, Zahl). |
| `chapter_toc` | Scope | `None` | Lokales Verzeichnis auf der Trennseite dieses Kapitels. |
| `autonum_pattern` | String | `None` | Nummern innerhalb dieses Kapitels; Slot 1 ist hier die H2. Die Kapitelnummer selbst kommt vom Abschnitt. |
| `autonum_reset` | Boolean | `None` | Lässt die Überschriften dieses Kapitels wieder bei 1 anfangen. |
| `label` | String | geerbt | Wort, das dieses Kapitel benennt (z. B. `"Exkurs"`). Leer notiert (`""`) entfällt es. |
| `pagenum_reset` | Boolean | `None` | Setzt die Seitennummerierung zu Beginn dieses Kapitels auf 1 zurück. |

> [!IMPORTANT]
> Auf `parts:` und `chapters:` sind **nur** die hier aufgeführten Schlüssel erlaubt. Ein unbekannter Schlüssel bricht den Build ab und nennt, falls vorhanden, den ähnlich geschriebenen – `break_befor` also, bevor das Kapitel still mit dem falschen Umbruch gesetzt wird. Freie Felder gibt es ausschließlich unter `document:`; dort erreichen sie das Theme, hier blieben sie wirkungslos.

---

## Verzeichnis-Steuerung (Scope-Werte)

Die Verzeichnisschalter `document_toc`, `part_toc` und `chapter_toc` akzeptieren folgende Werte:

| Wert | Bedeutung |
| :--- | :--- |
| `"none"` | Schaltet das jeweilige Verzeichnis komplett ab bzw. nimmt das Element nicht auf. |
| `"full"` | Nimmt alle vorhandenen Überschriftenebenen ohne Tiefenbegrenzung auf. |
| Ganze Zahl (z. B. `1`, `2`, `3`) | Begrenzt die Verzeichnistiefe exakt auf die angegebene Zahl von Ebenen. |

> [!WARNING] Keine Booleans zulässig
> Wahrheitswerte (`true` oder `false`) sind für Verzeichnisschalter unzulässig und führen zu einem `ConfigurationError`. Um ein Verzeichnis zu unterdrücken, notieren Sie stets `"none"`.

