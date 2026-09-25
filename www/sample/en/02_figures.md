# Figures & References

A graphic with a caption becomes a numbered figure. markpublish sets the word and number itself, and every figure can be referenced in the text by its ID.

![Processing chain from Markdown to PDF](pipeline.svg){width=100% noframe}

/// figure-caption
    attrs: {id: fig-pipeline}
From Markdown chapter to print-ready PDF
///

As [](#fig-pipeline) shows, markpublish reads the chapter files, numbers headings, figures and tables, and hands the result to Typst. References like this one always stay correctly numbered and are clickable in the PDF.
