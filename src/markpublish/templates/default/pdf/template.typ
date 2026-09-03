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
  status: "",
  language: "de",
  show-cover: true,
  summary: "",
  show-toc: true,
  toc-title: "Inhaltsverzeichnis",
  toc-depth: 3,
  show-header: true,
  show-footer: true,
  meta: (:),
  labels: (:),
  body,
) = {
  // Page settings: Cover and Dividers have no header/footer; TOC and content have header/footer
  set page(
    paper: "a4",
    margin: (top: 2.8cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
    header: context {
      let cur-page = here().page()
      let is-cover = show-cover and query(label("cover-page")).any(it => it.location().page() == cur-page)
      let is-divider = query(selector(label("part-divider")).or(selector(label("chapter-divider")))).any(it => it.location().page() == cur-page)
      if show-header and not is-cover and not is-divider {
        let all-h = query(selector(heading.where(level: 1)))
        let chapter-h = all-h.filter(h => not (h.has("label") and (str(h.label) == "part-entry" or str(h.label) == "chapter-divider")))
        let on-p = chapter-h.filter(h => h.location().page() == cur-page)
        let before-p = chapter-h.filter(h => h.location().page() < cur-page)
        let active = if on-p.len() > 0 { on-p.first() } else if before-p.len() > 0 { before-p.last() } else { none }
        let ch-title = if active != none and active.location().page() <= cur-page { active.body } else { "" }
        grid(
          columns: (1fr, 1fr),
          align: (left + top, right + top),
          [
            #text(size: 8.5pt, fill: rgb("#334155"))[#title]
            #if subtitle != "" and subtitle != none [
              \ #text(size: 7.5pt, fill: rgb("#64748b"))[#subtitle]
            ]
          ],
          [
            #text(size: 8.5pt, fill: rgb("#64748b"))[#ch-title]
          ],
        )
        v(-2pt)
        line(length: 100%, stroke: 0.5pt + rgb("#cbd5e1"))
      }
    },
    footer: context {
      let cur-page = here().page()
      let is-cover = show-cover and query(label("cover-page")).any(it => it.location().page() == cur-page)
      let is-divider = query(selector(label("part-divider")).or(selector(label("chapter-divider")))).any(it => it.location().page() == cur-page)
      if show-footer and not is-cover and not is-divider {
        let doc-ends = query(label("doc-end"))
        let total-pages = if doc-ends.len() > 0 { doc-ends.last().location().page() } else { 1 }
        line(length: 100%, stroke: 0.5pt + rgb("#cbd5e1"))
        v(-2pt)
        grid(
          columns: (1fr, 1fr),
          align: (left + top, right + top),
          [
            #if copyright != "" and copyright != none [
              #text(size: 8pt, fill: rgb("#64748b"))[#copyright]
            ]
          ],
          [
            #text(size: 8pt, fill: rgb("#64748b"))[
              #if version != "" and version != none [#version]
              #if version != "" and version != none and date != "" and date != none [ | ]
              #if date != "" and date != none [#date]
            ]
            \ #text(size: 8pt, fill: rgb("#64748b"))[#labels.at("page", default: "Seite") #counter(page).display() #labels.at("page_of", default: "von") #total-pages]
          ],
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
    if it.has("label") and str(it.label) == "part-entry" {
      text(size: 22pt, weight: "bold", fill: rgb("0f172a"))[#it.body]
    } else if it.has("label") and str(it.label) == "chapter-divider" {
      none
    } else {
      v(if it.level == 1 { 1.6em } else if it.level == 2 { 1.2em } else { 0.9em })
      let num = if it.numbering != none { counter(heading).display(it.numbering) } else { none }
      let h-text = if num != none and str(num).trim() != "" [ #num #it.body ] else [ #it.body ]
      text(
        fill: rgb("0f172a"),
        weight: "bold",
        size: if it.level == 1 { 18pt } else if it.level == 2 { 14pt } else if it.level == 3 { 11.5pt } else { 10.5pt },
      )[#h-text]
      v(0.6em)
    }
  }

  // Links styling: Web URLs blue and underlined, internal links natural
  show link: it => {
    if type(it.dest) == str {
      text(fill: rgb("#2563eb"), underline(stroke: 0.5pt + rgb("#93c5fd"), offset: 2pt)[#it])
    } else {
      it
    }
  }

  // Outline / TOC styling: Part entries stand out bold without dots; Level-1 chapters bold with blank line for 2..n
  show outline.entry: it => {
    let elem = it.element
    if elem.has("label") and str(elem.label) == "part-entry" {
      v(1.4em)
      text(weight: "bold", size: 11pt, fill: rgb("#0f172a"))[#link(elem.location())[#elem.body]]
      v(0.4em)
    } else if it.level == 1 {
      let all-h1 = query(selector(heading.where(level: 1)))
      let ch-h1 = all-h1.filter(h => not (h.has("label") and (str(h.label) == "part-entry" or str(h.label) == "chapter-divider")))
      let is-first = ch-h1.len() > 0 and ch-h1.first() == elem
      if not is-first {
        v(0.9em)
      }
      text(weight: "bold", fill: rgb("#0f172a"))[#it]
    } else {
      text(weight: "regular", fill: rgb("#334155"))[#it]
    }
  }

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
  show raw.where(block: false): it => highlight(
    fill: rgb("#f1f5f9"),
    radius: 2pt,
    extent: 1.5pt,
    top-edge: "ascender",
    bottom-edge: "descender",
  )[#text(fill: rgb("#0f172a"), font: ("Consolas", "Courier New", "monospace"), size: 8.5pt)[#it]]

  // Render Cover Page if enabled
  if show-cover {
    [#metadata("cover") <cover-page>]
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
    let meta-items = if meta.len() > 0 {
      meta.values().filter(it => not (it.key in ("title", "subtitle", "summary")) and it.value != "" and it.value != none and it.value != ())
    } else {
      (
        if version != "" { (key: "version", label: labels.at("version", default: "Version"), value: version) },
        if date != "" { (key: "date", label: labels.at("date", default: "Datum"), value: date) },
        if authors != () and authors != "" { (key: "author", label: labels.at("author", default: "Autor"), value: authors) },
        if copyright != "" { (key: "copyright", label: labels.at("copyright", default: "Copyright"), value: copyright) },
        if status != "" and status != none { (key: "status", label: labels.at("status", default: "Status"), value: status) },
      ).filter(it => it != none)
    }

    grid(
      columns: (auto, 1fr),
      row-gutter: 10pt,
      column-gutter: 20pt,
      ..meta-items.map(it => (
        text(weight: "bold", fill: rgb("#64748b"))[#if it.label != none and it.label != "" { it.label } else { it.key }],
        text(fill: rgb("#0f172a"))[#if type(it.value) == array { it.value.join(", ") } else { str(it.value) }],
      )).flatten()
    )
    v(1cm)
    pagebreak()
  }

  // Render Table of Contents
  if show-toc {
    v(1cm)
    text(size: 16pt, weight: "bold", fill: rgb("#0f172a"))[#toc-title]
    v(1cm)
    outline(
      title: none,
      depth: toc-depth,
      indent: 1.2em,
    )
    v(1cm)
    pagebreak()
  }

  body
  [#metadata("end") <doc-end>]
}

// Part Divider Page
#let render-part-divider(
  title: "",
  subtitle: none,
  summary: none,
  tag: "ABSCHNITT",
  in-toc: true,
  toc-title: "Inhalt dieses Abschnitts",
  toc-items: (),
) = {
  [#metadata("part-divider") <part-divider>]
  v(3cm)
  text(size: 10pt, weight: "bold", fill: rgb("2563eb"), tracking: 0.1em)[#upper(tag)]
  v(0.3em)
  if in-toc [
    #heading(level: 1, outlined: true, numbering: none)[#title] <part-entry>
  ] else [
    #text(size: 22pt, weight: "bold", fill: rgb("0f172a"))[#title]
  ]
  v(0.5em)
  line(length: 100%, stroke: 2pt + rgb("2563eb"))
  v(1.5em)

  if subtitle != none and subtitle != "" {
    text(size: 12pt, fill: rgb("64748b"))[#subtitle]
    v(1em)
  }

  if summary != none and summary != "" {
    block(
      fill: rgb("f8fafc"),
      stroke: (left: 3pt + rgb("2563eb")),
      inset: (x: 12pt, y: 10pt),
      radius: (right: 4pt),
    )[
      #text(size: 10pt, fill: rgb("334155"))[#summary]
    ]
    v(2em)
  }

  if toc-items.len() > 0 [
    #block(
      width: 100%,
      fill: rgb("f8fafc"),
      inset: (x: 14pt, y: 14pt),
      radius: 4pt,
      stroke: 0.5pt + rgb("e2e8f0"),
    )[
      #text(size: 8.5pt, weight: "bold", fill: rgb("475569"), tracking: 0.08em)[#upper(toc-title)]
      #v(10pt)
      #{
        let ch_count = 0
        for item in toc-items {
          if item.at("is_header", default: false) [
            #v(6pt)
            #text(weight: "bold", size: 9.5pt, fill: rgb("0f172a"))[#item.title]
            #v(2pt)
          ] else {
            let lvl = item.at("level", default: 1)
            let is_lvl1 = (lvl == 1)
            if is_lvl1 {
              ch_count += 1
              if ch_count > 1 {
                v(8pt)
              }
            }
            
            let item_font_weight = if is_lvl1 { "bold" } else { "regular" }
            let item_font_size = if is_lvl1 { 9.5pt } else { 9pt }
            let item_text_color = if is_lvl1 { rgb("#0f172a") } else { rgb("#334155") }
            let item_indent = if is_lvl1 { 0pt } else { item.at("indent", default: 12pt) }

            grid(
              columns: (1fr, auto),
              align: (left + horizon, right + horizon),
              [
                #h(item_indent)
                #if item.at("slug", default: "") != "" [
                  #link(label(item.slug))[#text(size: item_font_size, weight: item_font_weight, fill: item_text_color)[#item.title]]
                ] else [
                  #text(size: item_font_size, weight: item_font_weight, fill: item_text_color)[#item.title]
                ]
              ],
              [
                #if item.at("slug", default: "") != "" [
                  #context {
                    let locs = query(label(item.slug))
                    if locs.len() > 0 [
                      #text(size: item_font_size, weight: item_font_weight, fill: rgb("#64748b"))[#counter(page).at(locs.first().location()).first()]
                    ]
                  }
                ]
              ],
            )
            v(if is_lvl1 { 3pt } else { 2.5pt })
          }
        }
      }
    ]
  ]
  pagebreak()
}

// Chapter Divider Page
#let render-chapter-divider(
  title: "",
  subtitle: none,
  summary: none,
  tag: "KAPITEL",
  toc-title: "Inhalt dieses Kapitels",
  toc-items: (),
) = {
  [#heading(level: 1, outlined: false, numbering: none)[#title] <chapter-divider>]
  v(3cm)
  text(size: 9pt, weight: "bold", fill: rgb("64748b"), tracking: 0.1em)[#upper(tag)]
  v(0.3em)
  text(size: 20pt, weight: "bold", fill: rgb("0f172a"))[#title]
  v(0.5em)
  line(length: 100%, stroke: 1pt + rgb("cbd5e1"))
  v(1.5em)

  if subtitle != none and subtitle != "" {
    text(size: 11.5pt, fill: rgb("64748b"))[#subtitle]
    v(1em)
  }

  if summary != none and summary != "" {
    block(
      fill: rgb("f8fafc"),
      stroke: (left: 3pt + rgb("64748b")),
      inset: (x: 12pt, y: 10pt),
      radius: (right: 4pt),
    )[
      #text(size: 9.5pt, fill: rgb("334155"))[#summary]
    ]
    v(2em)
  }

  if toc-items.len() > 0 [
    #block(
      width: 100%,
      fill: rgb("f8fafc"),
      inset: (x: 14pt, y: 12pt),
      radius: 4pt,
      stroke: 0.5pt + rgb("e2e8f0"),
    )[
      #text(size: 8.5pt, weight: "bold", fill: rgb("475569"), tracking: 0.08em)[#upper(toc-title)]
      #v(8pt)
      #for item in toc-items [
        #grid(
          columns: (1fr, auto),
          align: (left + horizon, right + horizon),
          [
            #h(item.at("indent", default: 0pt))
            #if item.at("slug", default: "") != "" [
              #link(label(item.slug))[#text(size: 9pt, fill: rgb("334155"))[#item.title]]
            ] else [
              #text(size: 9pt, fill: rgb("334155"))[#item.title]
            ]
          ],
          [
            #if item.at("slug", default: "") != "" [
              #context {
                let locs = query(label(item.slug))
                if locs.len() > 0 [
                  #text(size: 9pt, fill: rgb("64748b"))[#counter(page).at(locs.first().location()).first()]
                ]
              }
            ]
          ],
        )
        #v(3pt)
      ]
    ]
  ]
  pagebreak()
}
