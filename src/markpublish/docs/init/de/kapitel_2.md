# Funktionen und Gestaltung

Dieses zweite Kapitel demonstriert typische Typografie- und Gestaltungselemente von markpublish.

## Hinweisboxen (Callouts)

Wichtige Informationen und Warnungen heben Sie über GitHub-Alerts hervor:

> [!NOTE]
> markpublish benötigt keine externen Laufzeitumgebungen wie Pandoc, Node.js oder lokale LaTeX-Installationen.

> [!TIP]
> Farbpaletten, Abstände und Schriften werden zentral über das gewählte Theme gesteuert.

Klassische Zitate erhalten einen dezenten grauen Akzentbalken:

> Gute Typografie ist wie Glas: Sie lässt den Inhalt klar hervortreten, ohne sich selbst in den Vordergrund zu drängen.

## Quellcode und Tabellen

Programmcode wird mit Syntax-Highlighting und Monospace-Schrift gesetzt:

```python
from markpublish import build_document

def publish():
    print("Publizieren mit Typst-Präzision!")
```

Tabellen nutzen eine lesefreundliche Booktabs-Formatierung:

| Element | Markdown-Syntax | Beschreibung |
| :--- | :--- | :--- |
| Hinweisbox | `> [!NOTE]` | Farbiger Hinweiskasten |
| Zitat | `> Zitattext` | Grauer Akzentbalken |
| Codeblock | ` ```python ` | Syntax-Highlighting |
| Formelsatz | `$E = m c^2$` | Mathematische Typst-Formeln |

## Mathematischer Formelsatz

Formeln können sowohl inline wie $a^2 + b^2 = c^2$ als auch als abgesetzter Block formatiert werden:

$$E = m c^2 \quad\text{oder}\quad \sum_{i=1}^{n} x_i = X$$
