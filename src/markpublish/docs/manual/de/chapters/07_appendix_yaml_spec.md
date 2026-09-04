# Anhang A: Schema-Referenz markpublish.yaml

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
| `cover` | Boolean | `true` | Steuert, ob eine gestaltete Deckblattseite erzeugt wird. |
| `header` | Boolean | `true` | Aktiviert oder deaktiviert die laufende Kopfzeile im Dokument. |
| `footer` | Boolean | `true` | Aktiviert oder deaktiviert die laufende Fußzeile (inkl. Seitennummerierung). |
| `document_toc` | Scope | `"full"` | Tiefe des Haupt-Inhaltsverzeichnisses (`"none"`, `"full"` oder Zahl $\ge 1$). |
| `part_toc` | Scope | `"full"` | Standardtiefe für lokale Inhaltsverzeichnisse auf Abschnitts-Trennseiten. |
| `chapter_toc` | Scope | `"full"` | Standardtiefe für lokale Inhaltsverzeichnisse auf Kapitel-Trennseiten. |
| `autonum_style` | String | `"decimal"` | Nummerierungsstil: `"decimal"` (1.2.3), `"legal"`, `"roman"` oder `"none"`. |
| `autonum_from_level`| Integer | `1` | Überschriftenebene, ab der nummeriert wird (`1` = ab H1, `2` = erst ab H2). |
| `autonum_prefix` | String | `None` | Zeichenkette vor den Nummern (z. B. `"A."` für Anhänge). |
| `autonum_reset` | Boolean | `false` | Setzt den Überschriftenzähler bei jedem neuen Kapitel auf 1 zurück. |
| `pagenum_reset` | Boolean | `false` | Startet die Seitennummerierung bei jedem Abschnitt oder Kapitel neu bei Seite 1. |

---

## Globale Projekt-Einstellungen

Direkt auf oberster Ebene der `markpublish.yaml` (neben `document:` und `parts:`) können folgende Schalter gesetzt werden:

| Schlüssel | Typ | Default | Beschreibung |
| :--- | :--- | :--- | :--- |
| `theme` | String | `"default"` | Name des zu verwendenden Themes. |
| `templates_dir` | String | `None` | Optionaler benutzerdefinierter Pfad zu einem Verzeichnis mit Themes. |

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
| `break_before` | String | `"divider"` | Umbruchverhalten vor dem Abschnitt: `"divider"` (Trennseite), `"page"` (Seitenwechsel) oder `"none"`. |
| `document_toc` | Scope | `None` | Überschreibt den Beitrag dieses Abschnitts zum Haupt-Inhaltsverzeichnis. |
| `part_toc` | Scope | `None` | Steuert das lokale Inhaltsverzeichnis auf der Abschnitts-Trennseite. |
| `chapter_toc` | Scope | `None` | Vererbt die Vorgabe für Kapitelverzeichnisse an alle Kapitel des Abschnitts. |
| `autonum_style` | String | `None` | Überschreibt den Nummerierungsstil für alle Kapitel des Abschnitts. |
| `autonum_from_level`| Integer | `None` | Überschreibt die Startebene der Nummerierung für den Abschnitt. |
| `autonum_prefix` | String | `None` | Präfix für Nummern innerhalb des Abschnitts (z. B. `"A."`). |
| `autonum_reset` | Boolean | `None` | Steuert, ob Kapitel im Abschnitt jeweils bei 1 neu nummerieren. |
| `pagenum_reset` | Boolean | `None` | Setzt den Seitenzähler zu Beginn des Abschnitts auf 1 zurück. |
| `chapters` | Liste | *(Pflichtfeld)* | Liste der Inhaltskapitel innerhalb dieses Abschnitts (mindestens 1 Eintrag). |

---

## Kapitel-Ebene (chapters)

Die Liste `chapters:` definiert die Inhaltsdateien. Kapitel können unter `parts:` oder verschachtelt innerhalb anderer Kapitel liegen.

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
| `autonum_style` | String | `None` | Nummerierungsstil für Überschriften dieses Kapitels. |
| `autonum_from_level`| Integer | `None` | Startebene der Nummerierung innerhalb des Kapitels. |
| `autonum_prefix` | String | `None` | Präfix für Überschriftennummern dieses Kapitels. |
| `autonum_reset` | Boolean | `None` | Setzt den Nummerierungszähler zu Beginn dieses Kapitels auf 1 zurück. |
| `pagenum_reset` | Boolean | `None` | Setzt die Seitennummerierung zu Beginn dieses Kapitels auf 1 zurück. |
| `chapters` | Liste | `[]` | Optionale Liste von weiteren Unterkapiteln. |

> [!IMPORTANT]
> Auf `parts:` und `chapters:` sind **nur** die hier aufgeführten Schlüssel erlaubt. Ein unbekannter Schlüssel bricht den Build ab und nennt, falls vorhanden, den ähnlich geschriebenen — `break_befor` also, bevor das Kapitel still mit dem falschen Umbruch gesetzt wird. Freie Felder gibt es ausschließlich unter `document:`; dort erreichen sie das Theme, hier blieben sie wirkungslos.

---

## Verzeichnis-Steuerung (Scope-Werte)

Die Verzeichnisschalter `document_toc`, `part_toc` und `chapter_toc` akzeptieren folgende Werte:

| Wert | Bedeutung |
| :--- | :--- |
| `"none"` | Schaltet das jeweilige Verzeichnis komplett ab bzw. nimmt das Element nicht auf. |
| `"full"` | Nimmt alle vorhandenen Überschriftenebenen ohne Tiefenbegrenzung auf. |
| Ganze Zahl (z. B. `1`, `2`, `3`) | Begrenzt die Verzeichnistiefe exakt auf die angegebene Zahl von Ebenen. |
