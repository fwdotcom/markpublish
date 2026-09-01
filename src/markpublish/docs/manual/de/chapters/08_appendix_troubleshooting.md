# Anhang B: Fehlerbehebung & FAQ

Häufige Fragen, Fehlermeldungen und Lösungen bei der Dokumentenerstellung.

| Problem / Fehlermeldung | Mögliche Ursache | Lösung |
| :--- | :--- | :--- |
| `cannot load library 'libgobject-2.0-0'` | WeasyPrint benötigt auf Windows die C-Bibliotheken von Pango und GTK. | GTK3-Runtime installieren ([GTK-Installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer)) oder MSYS2: `pacman -S mingw-w64-x86_64-pango`. Schnelle Alternative: `--target html` rendert ohne WeasyPrint. |
| Leere Bildrahmen / fehlende Grafiken im PDF | Bildpfad ist falsch oder absolut statt relativ notiert. | Pfade immer relativ zur jeweiligen Markdown-Datei angeben (z. B. `images/diag.png`). markpublish bettet Grafiken bis 12 MB als Data-URI ein. |
| Inhaltsverzeichnis: Falsche Seitenzahlen | Manuell vergebene Heading-IDs kollidieren im Zweipass-Rendering. | Automatische Eindeutigkeit von markpublish nutzen oder manuell vergebene Anker (`{#id}`) prüfen. |
| `Label 'x' is used in template but defined in no i18n level` | Ein Theme verwendet einen statischen Textschlüssel, der in keiner `i18n.yaml` deklariert ist. | Schlüssel in `<theme>/i18n.yaml` für alle Sprachen oder unter `*` eintragen. Gültige Texte mit `markpublish labels` prüfen. |
| `cheatsheet` oder `manual` ignoriert Arbeitsordner-Theme | Eingebaute Referenzen nutzen standardmäßig das robuste Built-in-Theme. | Mit `--theme <name>` explizit das Rendern im eigenen Theme anfordern. |

