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
  block(spacing: 0.65em)[
    #grid(
      columns: (14pt, 1fr),
      align: (left + top, left + top),
      box(
        width: 9.5pt,
        height: 9.5pt,
        stroke: 0.8pt + rgb("#64748b"),
        radius: 2pt,
        fill: if checked { rgb("#2563eb") } else { none },
        baseline: 0pt,
        inset: (top: 1pt),
      )[
        #if checked [
          #align(center + horizon)[#text(size: 6.5pt, fill: white, weight: "bold")[✓]]
        ]
      ],
      body,
    )
  ]
}

// Welche Angaben das Metadatenraster des Titelblatts zeigt -- und in welcher
// Reihenfolge.
//
// Die Liste ist abschliessend, nicht nur eine Sortierung: markpublish reicht
// saemtliche Angaben aus `document:` als Woerterbuch herein, gedruckt wird
// davon nur, was hier steht. Ein frei ergaenztes Feld erreicht das Theme also,
// erscheint aber erst, wenn es hier aufgenommen wird -- sonst fuellte jeder
// Tippfehler in der markpublish.yaml das Titelblatt: `abteilnug: "F&E"`
// stuende als zusaetzliche Zeile darauf, und niemand haette sie angeordnet.
//
// Jeder Eintrag steht als eigener Zugriff da statt als Schluesselname in einer
// Schleife. Damit liest `markpublish labels` diesem Theme ab, welche Angaben
// es tatsaechlich druckt, und kann ein Feld melden, das die markpublish.yaml
// setzt und dieses Theme nicht kennt.
#let cover-fields(meta) = (
  meta.at("version", default: none),
  meta.at("date", default: none),
  meta.at("author", default: none),
  meta.at("copyright", default: none),
  meta.at("status", default: none),
)

// Wie ein Metadatenwert im Titelblatt erscheint.
//
// Der Typ kommt aus der markpublish.yaml unveraendert an -- ein `reviewed: true`
// ist hier ein Bool, keine Zeichenkette "True". Die Wortwahl entscheidet damit
// das Theme ueber die i18n-Kaskade, nicht der Renderer ueber str().
#let meta-value(value, labels) = {
  if type(value) == bool {
    if value { labels.at("bool_true", default: "Ja") } else { labels.at("bool_false", default: "Nein") }
  } else if type(value) == array {
    value.map(v => str(v)).join(", ")
  } else {
    str(value)
  }
}

// Global Document Setup
//
// Saemtliche Dokumentangaben kommen in `meta` -- Titel und Version genauso wie
// ein frei ergaenztes `abteilung:`. Eigene Parameter dafuer gibt es nicht mehr:
// zwei Wege zur selben Angabe koennen auseinanderlaufen, und ein neues Feld
// haette sonst jedes Mal auch einen neuen Parameter gebraucht.
#let setup-document(
  language: "de",
  show-cover: true,
  show-toc: true,
  toc-title: "Inhaltsverzeichnis",
  toc-depth: 3,
  show-header: true,
  show-footer: true,
  meta: (:),
  labels: (:),
  body,
) = {
  // Namentlich gelesen, nicht ueber einen Helfer mit variablem Schluessel:
  // `markpublish labels` liest diese Zeilen und kann nur benennen, was hier
  // auch benannt steht. Ein Kernfeld liegt immer in `meta`, auch ungesetzt --
  // ein `default:` braucht es deshalb nur fuer freie Felder.
  let title = meta.at("title").value
  let subtitle = meta.at("subtitle").value
  let summary = meta.at("summary").value
  let version = meta.at("version").value
  let date = meta.at("date").value
  let copyright = meta.at("copyright").value
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
            #text(size: 8.5pt, fill: rgb("#94a3b8"))[#ch-title]
          ],
        )
        v(-2pt)
        line(length: 100%, stroke: 0.35pt + rgb("#e2e8f0"))
      }
    },
    footer: context {
      let cur-page = here().page()
      let is-cover = show-cover and query(label("cover-page")).any(it => it.location().page() == cur-page)
      let is-divider = query(selector(label("part-divider")).or(selector(label("chapter-divider")))).any(it => it.location().page() == cur-page)
      if show-footer and not is-cover and not is-divider {
        let doc-ends = query(label("doc-end"))
        let total-pages = if doc-ends.len() > 0 { doc-ends.last().location().page() } else { 1 }
        line(length: 100%, stroke: 0.35pt + rgb("#e2e8f0"))
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
    hyphenate: true,
    fill: rgb("#0f172a"),
  )
  set par(
    justify: true,
    leading: 0.7em,
    spacing: 1.5em,
  )
  set list(
    spacing: 1.2em,
  )
  set enum(
    spacing: 1.2em,
  )

  // Heading Styling
  show heading: it => {
    if it.has("label") and str(it.label) == "part-entry" {
      text(size: 22pt, weight: "bold", fill: rgb("0f172a"))[#it.body]
    } else if it.has("label") and str(it.label) == "chapter-divider" {
      none
    } else {
      v(if it.level == 1 { 2.2em } else if it.level == 2 { 1.7em } else if it.level == 3 { 1.3em } else { 1.1em })
      let num = if it.numbering != none { counter(heading).display(it.numbering) } else { none }
      let h-text = if num != none and str(num).trim() != "" [ #num #it.body ] else [ #it.body ]
      // `sticky: true` haelt die Ueberschrift bei ihrem Text: stuende sie sonst
      // als letzte Zeile am Seitenfuss, wandert sie mit auf die naechste Seite.
      // Typsts eingebaute Ueberschrift bringt das mit -- diese Regel ersetzt sie
      // und muesste es sonst mit ihr verlieren.
      //
      // Der Block steht *innerhalb* von `text`, und `above`/`below` kommen aus
      // `par.spacing`: beides zusammen haelt die Abstaende auf den Werten von
      // vorher. Ohne den Block war der Ueberschriftentext ein Absatz im Fluss
      // und brachte seinen Absatzabstand mit, aufgeloest an der Schriftgroesse
      // der Ueberschrift -- 1.5em sind bei 18pt eben 27pt, nicht 15pt. Ein
      // Block ausserhalb von `text` loeste dieselben 1.5em an der Grundschrift
      // auf und verschoebe damit das ganze Dokument.
      text(
        fill: rgb("0f172a"),
        weight: "bold",
        size: if it.level == 1 { 18pt } else if it.level == 2 { 14pt } else if it.level == 3 { 11.5pt } else { 10.5pt },
      )[
        #context block(width: 100%, above: par.spacing, below: par.spacing, sticky: true)[#h-text]
      ]
      v(if it.level == 1 { 0.6em } else if it.level == 2 { 0.5em } else { 0.4em })
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
      let num = if elem.numbering != none {
        numbering(elem.numbering, ..counter(heading).at(elem.location()))
      } else { none }
      v(1.4em)
      text(weight: "bold", size: 11pt, fill: rgb("#0f172a"))[#link(elem.location())[#if num != none [#num #h(0.35em)]#elem.body]]
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

  // Table styling (Booktabs-Stil: klare Linien, dezente Haarlinien, kein unruhiges Zebra)
  set table(
    stroke: (x, y) => if y == 0 { (top: 1.2pt + rgb("#0f172a"), bottom: 0.6pt + rgb("#0f172a")) } else { (bottom: 0.4pt + rgb("#e2e8f0")) },
    fill: none,
    inset: (top: 7pt, bottom: 7pt, left: 10pt, right: 10pt),
  )

  // Code Block styling
  show raw.where(block: true): it => block(
    fill: rgb("#f1f5f9"),
    stroke: 0.5pt + rgb("#cbd5e1"),
    inset: 10pt,
    radius: 4pt,
    width: 100%,
    text(font: ("Consolas", "Courier New", "monospace"), size: 8.5pt)[#it]
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
    if subtitle != none and subtitle != "" {
      text(size: 13pt, fill: rgb("#64748b"))[#subtitle]
      v(1.5em)
    }
    line(length: 100%, stroke: 2pt + rgb("#2563eb"))
    v(1.5em)

    if summary != none and summary != "" {
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
    // Gezeigt wird, was `cover-fields` nennt -- in genau dieser Reihenfolge.
    // Beides ist Gestaltung und steht deshalb dort, nicht im Programm.
    //
    // Ein Schluessel, den dieses Dokument nicht setzt, faellt still weg; das
    // Raster hat dann eine Zeile weniger.
    let meta-items = cover-fields(meta).filter(
      it => it != none and it.value != "" and it.value != none and it.value != ()
    )

    grid(
      columns: (auto, 1fr),
      row-gutter: 10pt,
      column-gutter: 20pt,
      ..meta-items.map(it => (
        text(weight: "bold", fill: rgb("#64748b"))[#if it.label != none and it.label != "" { it.label } else { it.key }],
        text(fill: rgb("#0f172a"))[#meta-value(it.value, labels)],
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
  number: none,
  in-toc: true,
  toc-title: "Inhalt dieses Abschnitts",
  toc-items: (),
) = {
  [#metadata("part-divider") <part-divider>]
  v(3cm)
  let has-number = number != none and number != ""
  let tag-word = upper(str(tag)).trim()
  let tag-line = if has-number and tag-word != "" {
    tag-word + " " + number
  } else if has-number {
    number
  } else {
    tag-word
  }
  if tag-line != "" [
    #text(size: 10pt, weight: "bold", fill: rgb("2563eb"), tracking: 0.1em)[#tag-line]
    #v(0.3em)
  ]
  // Die Nummer steht fertig aus markpublish hier an; die konstante
  // numbering-Funktion traegt sie ins Inhaltsverzeichnis, ohne dass Typst
  // einen eigenen Zaehler dafuer fuehren muesste.
  let num-fn = if has-number { (..nums) => number } else { none }
  if in-toc [
    #heading(level: 1, outlined: true, numbering: num-fn)[#title] <part-entry>
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
  let tag-line = upper(str(tag)).trim()
  if tag-line != "" [
    #text(size: 9pt, weight: "bold", fill: rgb("64748b"), tracking: 0.1em)[#tag-line]
    #v(0.3em)
  ]
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
