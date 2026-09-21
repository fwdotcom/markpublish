# Scientific Computations

Mathematical formulas are typeset with high typographic precision using the native Typst math engine:

$$ E = frac(m c^2, sqrt(1 - v^2 / c^2)) $$

## Pipeline Implementation
Source code blocks benefit from syntax highlighting with bundled fonts:

```python
# pipeline.py
from pathlib import Path
import typst

def render_pdf(manifest_file: Path) -> bytes:
    """Compiles the document via Typst AST."""
    doc = load_manifest(manifest_file)
    return typst.compile(doc.to_typst())
```

