// ==============================================================================
// markpublish Official Default Typst Template
// ==============================================================================

#let callout-colors = (
  note: (border: rgb("#2563eb"), bg: rgb("#eff6ff"), text: rgb("#1e3a8a")),
  tip: (border: rgb("#16a34a"), bg: rgb("#f0fdf4"), text: rgb("#14532d")),
  important: (border: rgb("#7c3aed"), bg: rgb("#f5f3ff"), text: rgb("#4c1d95")),
  warning: (border: rgb("#d97706"), bg: rgb("#fffbeb"), text: rgb("#78350f")),
  caution: (border: rgb("#dc2626"), bg: rgb("#fef2f2"), text: rgb("#7f1d1d")),
)

// Callout / Admonition Box
#let callout(type: "note", title: none, body) = {
  let c = callout-colors.at(type, default: callout-colors.note)
  let icon-file = "assets/icons/" + type + ".svg"
  
  v(0.6em)
  block(
    width: 100%,
    fill: c.bg,
    stroke: (left: 3.5pt + c.border),
    inset: (top: 10pt, bottom: 10pt, left: 14pt, right: 14pt),
    radius: (right: 4pt),
  )[
    #if title != none [
      #grid(
        columns: (auto, 1fr),
        gutter: 8pt,
        align: (center + horizon, left + horizon),
        if icon-file != none {
          image(icon-file, width: 14pt, height: 14pt)
        },
        text(weight: "bold", fill: c.text, size: 10pt)[#title]
      )
      #v(4pt)
    ]
    #text(size: 9.5pt, fill: rgb("#1e293b"))[#body]
  ]
  v(0.6em)
}

// Task Item Checkbox
#let task-item(checked: false, body) = {
  box(
    width: 10pt,
    height: 10pt,
    stroke: 0.8pt + rgb("#64748b"),
    radius: 2pt,
    fill: if checked { rgb("#2563eb") } else { none },
    baseline: 1pt,
  )[
    #if checked [
      #align(center + horizon)[#text(size: 7pt, fill: white, weight: "bold")[✓]]
    ]
  ]
  h(6pt)
  body
}

// Global Document Setup
#let setup-document(
  title: "",
  subtitle: "",
  authors: (),
  version: "",
  date: "",
  copyright: "",
  language: "de",
  show-cover: true,
  summary: "",
  show-toc: true,
  toc-title: "Inhaltsverzeichnis",
  toc-depth: 3,
  labels: (:),
  body,
) = {
  // Page settings
  set page(
    paper: "a4",
    margin: (top: 2.8cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
    header: context {
      let page-num = counter(page).get().first()
      if page-num > 1 {
        let headings = query(selector(heading.where(level: 1)).before(here()))
        let current-ch = if headings.len() > 0 { headings.last().body } else { "" }
        grid(
          columns: (1fr, 1fr),
          align: (left, right),
          text(size: 8pt, fill: rgb("#64748b"))[#title],
          text(size: 8pt, fill: rgb("#64748b"))[#current-ch],
        )
        v(-4pt)
        line(length: 100%, stroke: 0.5pt + rgb("#cbd5e1"))
      }
    },
    footer: context {
      let page-num = counter(page).get().first()
      if page-num > 1 {
        line(length: 100%, stroke: 0.5pt + rgb("#cbd5e1"))
        v(-2pt)
        grid(
          columns: (1fr, 1fr, 1fr),
          align: (left, center, right),
          text(size: 8pt, fill: rgb("#64748b"))[
            #if version != "" [#version]
            #if version != "" and date != "" [ | ]
            #if date != "" [#date]
          ],
          text(size: 8pt, fill: rgb("#64748b"))[#copyright],
          text(size: 8pt, fill: rgb("#0f172a"), weight: "bold")[#counter(page).display()],
        )
      }
    }
  )

  // Typography settings
  set text(
    font: ("Open Sans", "Liberation Sans", "Arial", "Helvetica"),
    size: 10pt,
    lang: language,
    fill: rgb("#0f172a"),
  )
  set par(
    justify: true,
    leading: 0.75em,
  )

  // Heading Styling
  show heading: it => {
    v(if it.level == 1 { 1.6em } else if it.level == 2 { 1.2em } else { 0.9em })
    text(
      fill: rgb("#0f172a"),
      weight: "bold",
      size: if it.level == 1 { 18pt } else if it.level == 2 { 14pt } else if it.level == 3 { 11.5pt } else { 10.5pt },
    )[#it.body]
    v(0.6em)
  }

  // Links styling
  show link: it => text(fill: rgb("#2563eb"), underline(stroke: 0.5pt + rgb("#93c5fd"), offset: 2pt)[#it])

  // Table styling
  set table(
    stroke: (x, y) => if y == 0 { (bottom: 1.5pt + rgb("#0f172a")) } else { (bottom: 0.5pt + rgb("#e2e8f0")) },
    fill: (col, row) => if row == 0 { rgb("#f8fafc") } else if calc.even(row) { rgb("#f8fafc") } else { none },
    inset: (top: 8pt, bottom: 8pt, left: 10pt, right: 10pt),
  )

  // Code Block styling
  show raw.where(block: true): it => block(
    fill: rgb("#0f172a"),
    inset: 12pt,
    radius: 4pt,
    width: 100%,
    text(fill: rgb("#f8fafc"), font: ("Consolas", "Courier New", "monospace"), size: 8.5pt)[#it]
  )
  show raw.where(block: false): it => box(
    fill: rgb("#f1f5f9"),
    inset: (x: 4pt, y: 2pt),
    radius: 3pt,
    baseline: 0pt,
    text(fill: rgb("#0f172a"), font: ("Consolas", "Courier New", "monospace"), size: 8.5pt)[#it]
  )

  // Render Cover Page if enabled
  if show-cover {
    v(2cm)
    text(size: 26pt, weight: "bold", fill: rgb("#0f172a"))[#title]
    v(0.5em)
    if subtitle != "" {
      text(size: 13pt, fill: rgb("#64748b"))[#subtitle]
      v(1.5em)
    }
    line(length: 100%, stroke: 2pt + rgb("#2563eb"))
    v(1.5em)

    if summary != "" {
      block(
        fill: rgb("#f8fafc"),
        stroke: (left: 4pt + rgb("#2563eb")),
        inset: (x: 14pt, y: 12pt),
        radius: (right: 4pt),
      )[
        #text(size: 10.5pt, fill: rgb("#334155"), style: "italic")[#summary]
      ]
      v(2em)
    }

    // Metadata Grid
    v(1fr)
    grid(
      columns: (auto, 1fr),
      row-gutter: 10pt,
      column-gutter: 20pt,
      if version != "" [
        #text(weight: "bold", fill: rgb("#64748b"))[#labels.at("version", default: "Version")]
      ],
      if version != "" [
        #text(fill: rgb("#0f172a"))[#version]
      ],
      if date != "" [
        #text(weight: "bold", fill: rgb("#64748b"))[#labels.at("date", default: "Datum")]
      ],
      if date != "" [
        #text(fill: rgb("#0f172a"))[#date]
      ],
      if authors != () and authors != "" [
        #text(weight: "bold", fill: rgb("#64748b"))[#labels.at("author", default: "Autor")]
      ],
      if authors != () and authors != "" [
        #text(fill: rgb("#0f172a"))[#if type(authors) == array { authors.join(", ") } else { str(authors) }]
      ],
      if copyright != "" [
        #text(weight: "bold", fill: rgb("#64748b"))[#labels.at("copyright", default: "Copyright")]
      ],
      if copyright != "" [
        #text(fill: rgb("#0f172a"))[#copyright]
      ],
    )
    v(1cm)
    pagebreak()
  }

  // Render Table of Contents
  if show-toc {
    v(1cm)
    outline(
      title: text(size: 16pt, weight: "bold", fill: rgb("#0f172a"))[#toc-title],
      depth: toc-depth,
      indent: 1.2em,
    )
    v(1cm)
    pagebreak()
  }

  body
}

// Part Divider Page
#let render-part-divider(
  title: "",
  subtitle: none,
  summary: none,
  tag: "ABSCHNITT",
  show-toc: false,
  toc-title: "Inhalt dieses Abschnitts",
) = {
  v(3cm)
  text(size: 10pt, weight: "bold", fill: rgb("#2563eb"), tracking: 0.1em)[#upper(tag)]
  v(0.3em)
  text(size: 22pt, weight: "bold", fill: rgb("#0f172a"))[#title]
  v(0.5em)
  line(length: 100%, stroke: 2pt + rgb("#2563eb"))
  v(1.5em)

  if subtitle != none and subtitle != "" {
    text(size: 12pt, fill: rgb("#64748b"))[#subtitle]
    v(1em)
  }

  if summary != none and summary != "" {
    block(
      fill: rgb("#f8fafc"),
      stroke: (left: 3pt + rgb("#2563eb")),
      inset: (x: 12pt, y: 10pt),
      radius: (right: 4pt),
    )[
      #text(size: 10pt, fill: rgb("#334155"))[#summary]
    ]
    v(2em)
  }
  pagebreak()
}

// Chapter Divider Page
#let render-chapter-divider(
  title: "",
  subtitle: none,
  summary: none,
  tag: "KAPITEL",
) = {
  v(3cm)
  text(size: 9pt, weight: "bold", fill: rgb("#64748b"), tracking: 0.1em)[#upper(tag)]
  v(0.3em)
  text(size: 20pt, weight: "bold", fill: rgb("#0f172a"))[#title]
  v(0.5em)
  line(length: 100%, stroke: 1pt + rgb("#cbd5e1"))
  v(1.5em)

  if subtitle != none and subtitle != "" {
    text(size: 11.5pt, fill: rgb("#64748b"))[#subtitle]
    v(1em)
  }

  if summary != none and summary != "" {
    block(
      fill: rgb("#f8fafc"),
      stroke: (left: 3pt + rgb("#64748b")),
      inset: (x: 12pt, y: 10pt),
      radius: (right: 4pt),
    )[
      #text(size: 9.5pt, fill: rgb("#334155"))[#summary]
    ]
    v(2em)
  }
  pagebreak()
}
