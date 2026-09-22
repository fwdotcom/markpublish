# Syntax, Code & Mathematics

Technical reports and scientific documentation require specialized typographical presentation. This chapter illustrates the integration of source code listings, mathematical expressions, and structured data tables.

## Mathematical Typesetting

Mathematical expressions are compiled natively via the embedded Typst math engine, avoiding rasterized image artifacts or slow JavaScript rendering layers.

### Inline Mathematics

Formulas integrate seamlessly into running text. For example, the well-known mass-energy equivalence $E = m c^2$ can be referenced directly within a sentence. Statistical parameters, such as the arithmetic mean $\mu = 1/N sum_(i=1)^N x_i$, preserve line height and baseline alignment.

### Display Equation Blocks

Complex equations are set centered as dedicated blocks:

$$ frac(d, d x) integral_a^x f(t) d t = f(x) $$

Matrix operations, asymptotic bounds, and infinite limits blend harmoniously into the document layout:

$$ lim_(n -> oo) (1 + 1/n)^n = e approx 2.71828 $$

## Source Code Listings and Syntax Highlighting

Source code blocks feature monospaced typography with syntax highlighting optimized for contrast in both monochrome print and color screen viewing.

### Python Example

The following snippet demonstrates document compilation programmatically via the internal Python API:

```python
# renderer.py
from pathlib import Path
from typing import Optional
from markpublish.config import load_config
from markpublish.renderers.pdf import PDFRenderer

def compile_document(manifest_path: Path, output_dir: Optional[Path] = None) -> Path:
    """Loads document configuration and compiles PDF via Typst backend."""
    config = load_config(manifest_path)
    renderer = PDFRenderer(theme=config.theme)
    target_path = (output_dir or manifest_path.parent) / f"{config.slug}.pdf"
    
    with open(target_path, "wb") as fh:
        fh.write(renderer.render(config))
    return target_path
```

### Configuration Manifest (YAML)

The parameter schema in `markpublish.yaml` provides human-readable keywords for structural control:

```yaml
document:
  title: "Specification Version 2"
  language: "en"
  autonum_pattern: "_|1|.1|+"
  header: true
  footer: true
```

## Data Tables and Smart Typography

Tables organize comparative data metrics with precise column alignments:

| Component | Version | Latency (ms) | Throughput (docs/s) | Status |
| :--- | :---: | :---: | :---: | :--- |
| Markdown Parser | 3.5.2 | 1.4 | 710 | Active |
| Typst Engine | 0.15.0 | 4.8 | 208 | Active |
| Font Resolver | 1.0.0 | 0.2 | 5,000 | Cached |
| PDF Postprocessor | 2.1.0 | ~~12.5~~ 3.1 | 320 | Optimized |

Typographic symbols like copyright (c), registered trademarks (tm), ellipses... or em-dashes --- such as this one --- are automatically normalized to their correct glyphs.

