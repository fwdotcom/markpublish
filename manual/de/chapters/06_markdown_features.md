# Markdown-Features & Syntax

`markpublish` beinhaltet eine leistungsfähige Markdown-Engine mit voller Unterstützung moderner Dokumentations-Elemente.

## Code-Blöcke & Syntax Highlighting

Quellcode wird durch Pygments hervorgehoben:

```python
from markpublish.config.loader import load_config
from markpublish.markdown.engine import MarkdownPipeline

# Manifest laden
config = load_config("markpublish.yaml")
print(f"Building: {config.document.title}")
```

## Tabellen

Tabellen werden mit sauberem CSS-Zebramuster und Seitenumbruchschutz gerendert:

| Parameter | Typ | Standard | Beschreibung |
| :--- | :--- | :--- | :--- |
| `title` | String | *Pflicht* | Haupttitel des Dokuments |
| `author` | String | `None` | Name des Autors |
| `status` | String | `None` | Dokumentstatus (z.B. "Freigegeben", "Draft") |
| `copyright` | String | `None` | Copyright-Vermerk (z.B. "© 2026 Frank Winter") |
| `version` | String | `"1.0.0"` | Versionskennung |

## GitHub-Style Callout-Boxen (Alerts)

`markpublish` unterstützt die gängige **GitHub-Alert-Syntax** mit fünf semantischen Typen. Die Icons stammen dabei direkt aus dem Template:

> [!NOTE]
> Dies ist eine informative Notiz mit blauem Akzent und passendem Info-Icon.

> [!TIP]
> Nutzen Sie `markpublish build --target all`, um PDF und HTML parallel in einem Durchgang zu erstellen.

> [!IMPORTANT]
> GitHub-Callouts werden automatisch anhand der Dokumentensprache lokalisiert (z. B. *Hinweis*, *Tipp*, *Wichtig*, *Warnung*, *Achtung*).

> [!WARNING]
> Achten Sie bei relativen Bildpfaden darauf, dass diese relativ zur jeweiligen Markdown-Datei liegen.

> [!CAUTION]
> Fehlerhafte YAML-Einrückungen führen zu Abbruchfehlern beim Parsen des Manifests.

> [!TIP] Eigener Titel
> Sie können nach dem Alert-Typ auch einen individuellen Titel angeben, der die Standardbeschriftung überschreibt.

Alternativ wird auch weiterhin die klassische `!!! note`-Syntax unterstützt.

## Tasklisten

- [x] Projekt initialisieren
- [x] Kapitel schreiben
- [ ] Dokument veröffentlichen

