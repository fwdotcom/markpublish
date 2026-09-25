# Tabellen & Beschriftungen

Tabellen erhalten ihre Beschriftung oben, wie im Buchsatz üblich. Nummerierung und Verweise funktionieren genauso wie bei Abbildungen.

| Element | Markdown | Ergebnis im PDF |
| :--- | :--- | :--- |
| Abbildung | `/// figure-caption` | nummeriert, im Abbildungsverzeichnis |
| Tabelle | `/// table-caption` | nummeriert, Beschriftung oben |
| Verweis | `[](#id)` | „Abbildung 1“, anklickbar |
| Verzeichnis | `list_of: figures` | eigene Seite im Dokument |

/// table-caption
    attrs: {id: tab-elemente}
Beschriftete Elemente und ihre Schreibweise
///

[](#tab-elemente) fasst die Schreibweisen zusammen. Die Wörter „Abbildung“ und „Tabelle“ stammen aus der i18n-Kaskade und folgen damit der Dokumentsprache.
