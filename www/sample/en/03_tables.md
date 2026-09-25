# Tables & Captions

Tables carry their caption on top, as is customary in book typesetting. Numbering and references work just like they do for figures.

| Element | Markdown | Result in the PDF |
| :--- | :--- | :--- |
| Figure | `/// figure-caption` | numbered, in the list of figures |
| Table | `/// table-caption` | numbered, caption on top |
| Reference | `[](#id)` | "Figure 1", clickable |
| List | `list_of: figures` | a page of its own in the document |

/// table-caption
    attrs: {id: tbl-elements}
Captioned elements and how to write them
///

[](#tbl-elements) sums up the notation. The words "Figure" and "Table" come from the i18n cascade and thus follow the document language.
