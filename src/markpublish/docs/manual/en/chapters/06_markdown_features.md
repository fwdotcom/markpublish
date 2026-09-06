# Advanced Markdown Features

markpublish supports the full range of modern CommonMark and GitHub Flavored Markdown standards. Fundamental elements such as headings, paragraphs, text formatting (*italic*, **bold**), tables, bullet lists, code blocks, and hyperlinks work exactly as expected.

This chapter focuses exclusively on features and typographic enhancements beyond the standard supported by markpublish. Each section demonstrates first the Markdown syntax and immediately below the rendered result as typeset in this manual.

---

## Callout Boxes (Admonitions)

To emphasize important passages, markpublish supports GitHub-compatible callout blocks. They are written as blockquotes whose first line specifies the box type in square brackets:

```markdown
> [!NOTE]
> General information with helpful background details.

> [!TIP]
> A practical tip to streamline your workflow.

> [!IMPORTANT]
> Important information essential for understanding.

> [!WARNING]
> Warning against potential misconfigurations or unexpected behavior.

> [!CAUTION]
> Critical safety note to prevent potential data loss.
```

In the PDF, these are rendered as styled boxes with colored borders and icons:

> [!NOTE]
> General information with helpful background details.

> [!TIP]
> A practical tip to streamline your workflow.

> [!IMPORTANT]
> Important information essential for understanding.

> [!WARNING]
> Warning against potential misconfigurations or unexpected behavior.

> [!CAUTION]
> Critical safety note to prevent potential data loss.

If a custom title is desired, it can be added directly after the type on the first line:

```markdown
> [!NOTE] Custom Title
> Dedicated content with a customized header.
```

> [!NOTE] Custom Title
> Dedicated content with a customized header.

### Automatic Localization via i18n Labels

Without a custom title, the header of the callout box ("Note", "Tip", "Important", "Warning", "Caution") is automatically populated via the `i18n.yaml` file for the active document language:

| Box Type | i18n Key Used | English Label |
| :--- | :--- | :--- |
| `[!NOTE]` | `alert_note` | Note |
| `[!TIP]` | `alert_tip` | Tip |
| `[!IMPORTANT]` | `alert_important` | Important |
| `[!WARNING]` | `alert_warning` | Warning |
| `[!CAUTION]` | `alert_caution` | Caution |

### Alternative Syntax with `!!!`

Alongside the GitHub notation, markpublish also supports the admonition syntax popularized by MkDocs. The type follows three exclamation marks, an optional title is written in quotes, and content is indented by four spaces:

```markdown
!!! warning "Custom Title"
    Indented content can span multiple paragraphs.
```

!!! warning "Custom Title"
    Indented content can span multiple paragraphs.

Both notations generate identical styled boxes. One minor difference remains: without a custom title, `!!!` uses the extension's English default ("Note", "Tip", "Warning") rather than looking up the label from the i18n cascade. To use the localized title header, either write `> [!NOTE]` or supply an explicitly empty title string:

```markdown
!!! note ""
    The title bar is then retrieved from the i18n cascade.
```

!!! note ""
    The title bar is then retrieved from the i18n cascade.

An unrecognized box type (such as `!!! info`) is rendered as a Note box, retaining its name as the title.

---

## Definition Lists

For glossaries, parameter listings, or terminology overviews, definition lists provide clean typographical structure. The term stands on its own line, followed by the explanation indented with a colon:

```markdown
Markdown
: Simple, readable markup language for structured documents in plain text.

markpublish.yaml
: Central project configuration file controlling document hierarchy, metadata, and numbering.

Theme
: Design template composed of Typst layouts and text labels that define visual styling.

Typst
: Modern, high-performance typesetting engine used by markpublish to generate print-ready PDFs.
```

This renders as a distinct block featuring highlighted terms with indented definitions:

Markdown
: Simple, readable markup language for structured documents in plain text.

markpublish.yaml
: Central project configuration file controlling document hierarchy, metadata, and numbering.

Theme
: Design template composed of Typst layouts and text labels that define visual styling.

Typst
: Modern, high-performance typesetting engine used by markpublish to generate print-ready PDFs.

---

## Task Lists

For checklists, actionable steps, or release milestones, task lists are supported. They are written as bullet items starting with brackets:

```markdown
- [x] Install Python 3.10 or newer
- [x] Install markpublish
- [ ] Publish your first document
```

markpublish typesets task lists cleanly without bullet points, aligning multi-line descriptions directly beneath the first line:

- [x] Install Python 3.10 or newer

- [x] Install markpublish

- [ ] Publish your first document

---

## Footnotes

markpublish supports classic Markdown footnote syntax. This allows referencing sources or providing supplementary commentary without disrupting the flow of the main text.

Footnotes use a two-part notation: insert a numeric reference like `[^1]` or an identifier like `[^note]` within the text. The corresponding definition can be placed anywhere in the Markdown document – typically at the end of the chapter:

```markdown
This sentence contains a numbered footnote[^1] and a reference with a text key[^note].

[^1]: This is the body of the first footnote.
[^note]: Text keys are automatically converted into sequential numbers during typesetting.
```

In the rendered document, this produces the following references; their text appears at the bottom of the page, with bi-directional clickable links between the reference marker and the footnote text:

This sentence contains a numbered footnote[^1] and a reference with a text key[^note].

[^1]: This is the body of the first footnote.
[^note]: Text keys are automatically converted into sequential numbers during typesetting.

---

## Mathematical Formulas

markpublish allows inserting mathematical formulas directly inline or as display blocks. Formulas are rendered with typographic precision by Typst.

Common mathematical expressions such as fractions (`\frac{a}{b}`), square roots (`\sqrt{x}`), summations (`\sum`), integrals (`\int`), Greek characters (`\alpha`, `\pi`, `\sigma`), and native Typst math expressions are supported. Inline formulas are enclosed by single dollar signs, display blocks by double dollar signs:

```markdown
The famous mass-energy equivalence is $E = m c^2$.

Circular area calculation and quadratic formula:

$$ A = \pi \cdot r^2 \quad \text{and} \quad x = \frac{-b \pm \sqrt{b^2 - 4 a c}}{2 a} $$
```

In the PDF, this is typeset as:

The famous mass-energy equivalence is $E = m c^2$.

Circular area calculation and quadratic formula:

$$ A = \pi \cdot r^2 \quad \text{and} \quad x = \frac{-b \pm \sqrt{b^2 - 4 a c}}{2 a} $$

*Typographical note on variables:*  
In Typst Math, multi-letter words denote function names or identifiers (such as `sin`, `cos`, `sqrt`). Multiplication of individual variables is therefore written with space separation (e.g., `m c^2` or `4 a c`).

---

## Typographical Text Formats and Punctuation

Beyond standard Markdown, markpublish supports fine typographical formatting and authentic punctuation glyphs:

| Formatting | Input | Output | Typical Use Case |
| :--- | :--- | :--- | :--- |
| **Superscript** | `10^3^` or `m^2^` | 10^3^ or m^2^ | Powers, square/cubic meters |
| **Subscript** | `H~2~O` or `CO~2~` | H~2~O or CO~2~ | Chemical formulas, indices |
| **Strikethrough** | `~~outdated~~` | ~~outdated~~ | Corrections, deprecated items |
| **En-Dash** | `10--20 hours` | 10--20 hours | Date, time, and page ranges |
| **Em-Dash** | `Thought --- or not` | Thought --- or not | Parenthetical thoughts, narrative pauses |
| **Ellipsis** | `Loading...` | Loading... | Omissions, trailing off |

> [!TIP] Prose vs. Mathematical Typesetting
> The syntax `^superscript^` and `~subscript~` is designed for standard units ($m^2$) and chemical formulas ($H_2O$) within text. For mathematical formulas and equation systems, use the dedicated math environment with `$...$` or `$$...$$` (see section *Mathematical Formulas*).

---

## Automatic Symbols and Arrows

Frequent symbols and operators typed in plain text are automatically converted into proper typographical glyphs:

| Symbol | Input | Output | Typical Use Case |
| :--- | :--- | :--- | :--- |
| **Arrows** | `-->`, `<--`, `<-->` | -->, <--, <--> | Flow steps, back-references, equivalence |
| **Fractions** | `1/2`, `1/4`, `3/4` | 1/2, 1/4, 3/4 | Measurements, fractional values |
| **Arithmetic Glyphs** | `+/-`, `=/=` | +/-, =/= | Tolerances (±), inequality (≠) |
| **Copyright & Trademarks** | `(c)`, `(tm)`, `(r)` | (c), (tm), (r) | Copyright, Trademark, Registered |

---

## Automatic Linking and Cross-References

Web URLs and email addresses are automatically recognized and turned into clickable links. In addition, internal cross-references allow linking directly to any heading:

| Feature | Input | Output | Description |
| :--- | :--- | :--- | :--- |
| **Web Address (Magic Link)** | `https://example.com` | https://example.com | URLs are linked without explicit Markdown brackets |
| **Email Address (Magic Link)** | `contact@example.com` | contact@example.com | Email addresses become clickable `mailto:` links |
| **Document Cross-Reference** | `[Chapter top](#advanced-markdown-features)` | [Chapter top](#advanced-markdown-features) | Clickable internal link pointing to a heading anchor |

---

## Escape-Free Special Characters

Many documentation systems require cumbersome escaping for common characters. markpublish processes standard symbols in plain text safely without collision:

| Category | Example | Behavior in Document |
| :--- | :--- | :--- |
| **Currency Amounts** | `$5.00` or `10.50 $` | Not misparsed as mathematical formulas. |
| **Programming Languages** | `C#` | Does not trigger internal Typst commands. |
| **Usernames & Mentions** | `@author` or `user@domain.com` | Printed safely as text or autolinked. |
| **Technical Identifiers** | `<target_directory>` | Angle brackets remain intact as literal text. |

