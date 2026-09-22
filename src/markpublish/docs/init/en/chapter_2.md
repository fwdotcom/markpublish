# Features and Typography

This second chapter demonstrates standard typography and layout elements supported by markpublish.

## Callout Boxes

Highlight important notices or warnings using GitHub-style alerts:

> [!NOTE]
> markpublish has zero external binary dependencies. No Pandoc, Node.js, or LaTeX setup required.

> [!TIP]
> Colors, margins, and typography are defined centrally within the selected theme.

Classic block quotes feature a subtle grey accent bar:

> Good typography is like glass: it allows the content to shine through without drawing attention to itself.

## Code Blocks and Tables

Source code is formatted with syntax highlighting and monospace typography:

```python
from markpublish import build_document

def publish():
    print("Publishing with Typst precision!")
```

Tables are styled with booktabs-style rules:

| Element | Markdown Syntax | Purpose |
| :--- | :--- | :--- |
| Callout | `> [!NOTE]` | Styled admonition box |
| Block quote | `> Quote text` | Grey accent bar |
| Code block | ` ```python ` | Syntax-highlighted code |
| Formulas | `$E = m c^2$` | Mathematical typesetting |

## Mathematical Formulas

Formulas can be set inline like $a^2 + b^2 = c^2$ or as display blocks:

$$E = m c^2 \quad\text{or}\quad \sum_{i=1}^{n} x_i = X$$
