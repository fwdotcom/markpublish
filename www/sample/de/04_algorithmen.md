# Wissenschaftliche Berechnungen

Mathematische Formeln werden über die integrierte Typst-Math-Engine typografisch präzise und nativ im Dokument gerendert:

$$ E = frac(m c^2, sqrt(1 - v^2 / c^2)) $$

## Pipeline-Implementierung
Quellcode-Blöcke erhalten automatisches Syntax-Highlighting mit den integrierten Schriftarten:

```python
# pipeline.py
from pathlib import Path
import typst

def render_pdf(manifest_file: Path) -> bytes:
    """Kompiliert das Dokument über den Typst AST."""
    doc = load_manifest(manifest_file)
    return typst.compile(doc.to_typst())
```

