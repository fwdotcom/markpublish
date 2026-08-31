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
| `version` | String | `"1.0.0"` | Versionskennung |
| `language` | String | `"de"` | ISO-Sprachcode (`de`, `en`, ...). Steuert Template-Beschriftungen, Callout-Titel und Datumsformat |
| `i18n` | Map | `{}` | Ebene 4 der i18n-Kaskade. Gleicher Aufbau wie die `i18n.yaml`: Sprachcode, darunter die Texte. Siehe Kapitel 5 |
| `cover` | Bool | `true` | Deckblatt aktivieren/deaktivieren |
| `toc` | Bool | `true` | Globales Inhaltsverzeichnis aktivieren |
| `autonum_type` | String | `"decimal"` | `"decimal"`, `"roman"`, `"legal"`, `"none"` |
| `header` | Bool | `true` | 2-zeilige Kopfzeile aktivieren |
| `footer` | Bool | `true` | 2-zeilige Fußzeile aktivieren |

## Kapitel- und Part-Eigenschaften (`chapters`)

| Schlüssel | Typ | Standard | Beschreibung |
| :--- | :--- | :--- | :--- |
| `file` | String | `null` | Pfad zur Markdown-Datei |
| `title` | String | `null` | Überschreibt den Titel der Datei |
| `summary` | String | `null` | Zusammenfassung für Trennseite |
| `part` | String | `null` | Deklariert einen übergeordneten Part |
| `divider_page`| Bool | `false` | Fügt eine separate Trennseite ein |
| `toc` | Bool/Int | `false` | Lokales Kapitel-TOC (z. B. `2` für max. Tiefe) |
| `autonum` | String | `null` | Lokaler Override des Nummerierungsstils |
| `chapters` | Liste | `[]` | Verschachtelte Unterkapitel |

