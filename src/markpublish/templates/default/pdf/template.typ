// ==============================================================================
// markpublish Official Default Typst Template
// ==============================================================================

// -----------------------------------------------------------------------------
// Design Tokens & Theming Constants
// -----------------------------------------------------------------------------

// --- Color Palette ---
#let c-primary        = rgb("#2563eb")  // Brand / accent color (Blue 600)
#let c-primary-light  = rgb("#dbeafe")  // Soft accent background (Blue 100)
#let c-text-dark      = rgb("#0f172a")  // Headings & primary text (Slate 900)
#let c-text-body      = rgb("#1e293b")  // Body & callout text (Slate 800)
#let c-text-secondary = rgb("#334155")  // Secondary text / TOC / subtitles (Slate 700)
#let c-text-muted     = rgb("#64748b")  // Metadata, tags, captions & running headers (Slate 500)
#let c-text-subtle    = rgb("#94a3b8")  // Subtle leader dots & numbers (Slate 400)
#let c-border         = rgb("#e2e8f0")  // Table lines & dividers (Slate 200)
#let c-border-strong  = rgb("#cbd5e1")  // Code block border / divider line (Slate 300)
#let c-bg-subtle      = rgb("#f8fafc")  // Callouts, boxes, cards (Slate 50)
#let c-bg-muted       = rgb("#f1f5f9")  // Badges & code blocks (Slate 100)
#let c-white          = rgb("#ffffff")

// --- Typography Tokens ---
#let font-family-sans = ("Open Sans", "Liberation Sans", "Arial", "Helvetica")
#let font-family-mono = ("Noto Sans Mono", "Consolas", "Courier New", "monospace")

// --- Radii Tokens ---
#let radius-sm        = 2pt   // Badges, checkboxes, inline code
#let radius-md        = 4pt   // Callouts, code blocks, summary boxes, TOC boxes

// --- Stroke Widths ---
#let stroke-hairline       = 0.35pt // Running header/footer lines
#let stroke-border         = 0.5pt  // Box borders, TOC borders, code blocks
#let stroke-table-divider  = 0.4pt  // Table body row dividers (A7)
#let stroke-table-top      = 1.2pt  // Table top & bottom border (Booktabs A6)
#let stroke-table-mid      = 0.6pt  // Table header bottom line
#let stroke-accent         = 2.0pt  // Major accent lines (cover, part divider)
#let stroke-bar            = 3.0pt  // Summary callout accent bar
#let stroke-callout        = 3.5pt  // Markdown callout accent bar

// --- Document Layout & Body Typography (B1, B2, B3) ---
#let page-paper       = "a4"
#let page-margin      = (top: 2.8cm, bottom: 2.5cm, left: 3.0cm, right: 3.0cm)
#let body-size        = 10pt
#let par-leading      = 0.85em
#let par-spacing      = 1.5em
#let list-spacing     = 1.2em
#let size-code-block    = 8.5pt
#let size-code-inline   = 1.0em
#let weight-code-inline = "medium"

// --- Title & Divider Font Sizes (C1) ---
#let size-cover-title      = 26pt
#let size-cover-subtitle   = 13pt
#let size-cover-summary    = 10.5pt
#let size-part-title       = 22pt
#let size-part-subtitle    = 12pt
#let size-chapter-title    = 20pt
#let size-chapter-subtitle = 11.5pt
#let size-toc-title        = 16pt

// --- Callout Admonition Colors ---
#let callout-colors = (
  note:      (border: rgb("#2563eb"), bg: rgb("#eff6ff"), text: rgb("#1e3a8a")),
  tip:       (border: rgb("#16a34a"), bg: rgb("#f0fdf4"), text: rgb("#14532d")),
  important: (border: rgb("#7c3aed"), bg: rgb("#f5f3ff"), text: rgb("#4c1d95")),
  warning:   (border: rgb("#d97706"), bg: rgb("#fffbeb"), text: rgb("#78350f")),
  caution:   (border: rgb("#dc2626"), bg: rgb("#fef2f2"), text: rgb("#7f1d1d")),
)

// --- Heading Scale (Level 1..6) (B6, A8) ---
#let heading-scales = (
  "1": (size: 18pt,   above: 2.2em, below: 0.6em, weight: "bold"),
  "2": (size: 14pt,   above: 1.7em, below: 0.5em, weight: "bold"),
  "3": (size: 11.5pt, above: 1.3em, below: 0.4em, weight: "semibold"),
  "4": (size: 10.5pt, above: 1.1em, below: 0.4em, weight: "semibold"),
  "5": (size: 9.5pt,  above: 1.0em, below: 0.3em, weight: "semibold"),
  "6": (size: 9.0pt,  above: 0.9em, below: 0.3em, weight: "regular"),
)

// -----------------------------------------------------------------------------
// Component Helpers
// -----------------------------------------------------------------------------

// NOTE: Interne Hilfsfunktionen MÜSSEN mit einem führenden Unterstrich `_`
// beginnen (z. B. `_render-local-toc`). Dies stellt sicher, dass der statische
// Theme-Contract-Parser (`markpublish.templates.contract._LET_RE`) sie als
// interne Helfer erkennt und nicht fälschlich als Pflicht-Theme-Schnittstelle
// einstuft.

// Summary / Description Callout Box (A7)
#let _render-summary-box(
  summary,
  accent-color: c-primary,
  accent-bar: stroke-bar,
  font-size: 10pt,
  text-color: c-text-secondary,
  inset: (x: 12pt, y: 10pt),
  style: "normal",
) = {
  block(
    fill: c-bg-subtle,
    stroke: (left: accent-bar + accent-color),
    inset: inset,
    radius: (right: radius-md),
  )[
    #text(size: font-size, fill: text-color, style: style)[#summary]
  ]
}

// Local Table of Contents for Part and Chapter Dividers (C2)
#let _render-local-toc(toc-title, toc-items, is-chapter: false) = {
  if toc-items == none or toc-items.len() == 0 { return }
  block(
    width: 100%,
    fill: c-bg-subtle,
    inset: (x: 14pt, y: if is-chapter { 12pt } else { 14pt }),
    radius: radius-md,
    stroke: stroke-border + c-border,
  )[
    #text(size: 8.5pt, weight: "bold", fill: rgb("#475569"), tracking: 0.08em)[#upper(toc-title)]
    #v(if is-chapter { 8pt } else { 10pt })
    #{
      let ch-count = 0
      for item in toc-items {
        if item.at("is_header", default: false) [
          #v(6pt)
          #text(weight: "bold", size: 9.5pt, fill: c-text-dark)[#item.title]
          #v(2pt)
        ] else {
          let lvl = item.at("level", default: if is-chapter { 2 } else { 1 })
          let is-lvl1 = not is-chapter and (lvl == 1)
          if is-lvl1 {
            ch-count += 1
            if ch-count > 1 {
              v(8pt)
            }
          }

          let item-weight = if is-lvl1 { "bold" } else { "regular" }
          let item-size = if is-lvl1 { 9.5pt } else { 9pt }
          let item-color = if is-lvl1 { c-text-dark } else { c-text-secondary }
          let item-indent = if is-lvl1 { 0pt } else { item.at("indent", default: if is-chapter { 0pt } else { 12pt }) }

          grid(
            columns: (1fr, auto),
            align: (left + horizon, right + horizon),
            [
              #h(item-indent)
              #if item.at("slug", default: "") != "" [
                #link(label(item.slug))[#text(size: item-size, weight: item-weight, fill: item-color)[#item.title]]
              ] else [
                #text(size: item-size, weight: item-weight, fill: item-color)[#item.title]
              ]
            ],
            [
              #if item.at("slug", default: "") != "" [
                #context {
                  let locs = query(label(item.slug))
                  if locs.len() > 0 [
                    #text(size: item-size, weight: item-weight, fill: c-text-muted)[#counter(page).at(locs.first().location()).first()]
                  ]
                }
              ]
            ],
          )
          v(if is-lvl1 { 3pt } else { 2.5pt })
        }
      }
    }
  ]
}

// Helper to determine if the current page suppresses headers/footers (C2)
#let _is-special-page(cur-page) = {
  let is-cover = query(label("cover-page")).any(it => it.location().page() == cur-page)
  let is-divider = query(selector(label("part-divider")).or(selector(label("chapter-divider")))).any(it => it.location().page() == cur-page)
  is-cover or is-divider
}

// -----------------------------------------------------------------------------
// Markdown Element Customizations
// -----------------------------------------------------------------------------

// Callout / Admonition Box (B4, C2)
#let callout(type: "note", title: none, body) = {
  let safe-type = if type in callout-colors { type } else { "note" }
  let c = callout-colors.at(safe-type)
  let icon-file = "assets/icons/" + safe-type + ".svg"

  v(0.6em)
  block(
    width: 100%,
    fill: c.bg,
    stroke: (left: stroke-callout + c.border),
    inset: (top: 10pt, bottom: 10pt, left: 14pt, right: 14pt),
    radius: (right: radius-md),
  )[
    #if title != none [
      #grid(
        columns: (auto, 1fr),
        gutter: 8pt,
        align: (center + horizon, left + horizon),
        image(icon-file, width: 11pt, height: 11pt),
        text(weight: "bold", fill: c.text, size: 10pt)[#title]
      )
    ]
    #block(above: if title != none { 7pt } else { 0pt })[
      #text(size: 9.5pt, fill: c-text-body)[#body]
    ]
  ]
  v(0.6em)
}

// Task Item Checkbox (C3, B3)
#let task-item(checked: false, body) = {
  block(spacing: list-spacing)[
    #grid(
      columns: (14pt, 1fr),
      align: (left + top, left + top),
      box(
        width: 9.5pt,
        height: 9.5pt,
        stroke: 0.8pt + c-text-muted,
        radius: radius-sm,
        fill: if checked { c-primary } else { none },
        baseline: 0pt,
        inset: (top: 1pt),
      )[
        #if checked [
          #align(center + horizon)[#image("assets/icons/checkbox-check.svg", width: 7.5pt, height: 7.5pt)]
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

// Wie ein Metadatenwert im Titelblatt erscheint (C2: rekursiv für Arrays)
//
// Der Typ kommt aus der markpublish.yaml unveraendert an -- ein `reviewed: true`
// ist hier ein Bool, keine Zeichenkette "True". Die Wortwahl entscheidet damit
// das Theme ueber die i18n-Kaskade, nicht der Renderer ueber str().
#let meta-value(value, labels) = {
  if type(value) == bool {
    if value { labels.at("bool_true", default: "Ja") } else { labels.at("bool_false", default: "Nein") }
  } else if type(value) == array {
    value.map(v => meta-value(v, labels)).join(", ")
  } else {
    str(value)
  }
}

// -----------------------------------------------------------------------------
// Global Document Setup
// -----------------------------------------------------------------------------

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

  // B10: PDF-Dokumentmetadaten im Reader setzen
  set document(
    title: if title != none and title != "" { title } else { none },
    author: if meta.at("author", default: none) != none and meta.at("author").value != none and meta.at("author").value != "" {
      let a = meta.at("author").value
      if type(a) == array { a.map(str) } else { (str(a),) }
    } else { () },
  )

  // Page settings: Cover and Dividers have no header/footer; TOC and content have header/footer
  set page(
    paper: page-paper,
    margin: page-margin,
    header: context {
      let cur-page = here().page()
      if show-header and not _is-special-page(cur-page) {
        let all-h = query(selector(heading.where(level: 1)))
        let chapter-h = all-h.filter(h => not (h.has("label") and (str(h.label) == "part-entry" or str(h.label) == "chapter-divider")))
        let on-p = chapter-h.filter(h => h.location().page() == cur-page)
        let before-p = chapter-h.filter(h => h.location().page() < cur-page)
        let active = if on-p.len() > 0 { on-p.first() } else if before-p.len() > 0 { before-p.last() } else { none }
        let num-str = if active != none and active.numbering != none {
          let n = counter(heading).at(active.location())
          numbering(active.numbering, ..n)
        } else { none }
        let ch-title = if active != none and active.location().page() <= cur-page {
          if num-str != none and str(num-str).trim() != "" [ #num-str #h(0.3em) #active.body ] else [ #active.body ]
        } else { "" }
        set text(hyphenate: false)
        grid(
          columns: (1fr, 1fr),
          column-gutter: 12pt,
          align: (left + top, right + top),
          [
            #text(size: 8.5pt, fill: c-text-secondary)[#title]
            #if subtitle != "" and subtitle != none [
              \ #text(size: 7.5pt, fill: c-text-muted)[#subtitle]
            ]
          ],
          [
            #text(size: 8.5pt, fill: c-text-muted)[#ch-title]
          ],
        )
        v(-2pt)
        line(length: 100%, stroke: stroke-hairline + c-border)
      }
    },
    footer: context {
      let cur-page = here().page()
      if show-footer and not _is-special-page(cur-page) {
        let doc-ends = query(label("doc-end"))
        let total-pages = if doc-ends.len() > 0 { doc-ends.last().location().page() } else { 1 }
        line(length: 100%, stroke: stroke-hairline + c-border)
        v(-2pt)
        grid(
          columns: (1fr, 1fr),
          align: (left + top, right + top),
          [
            #if copyright != "" and copyright != none [
              #text(size: 8pt, fill: c-text-muted)[#copyright]
            ]
          ],
          [
            #text(size: 8pt, fill: c-text-muted)[
              #if version != "" and version != none [#version]
              #if version != "" and version != none and date != "" and date != none [ | ]
              #if date != "" and date != none [#date]
            ]
            \ #text(size: 8pt, fill: c-text-muted)[#labels.at("page", default: "Seite") #counter(page).display() #labels.at("page_of", default: "von") #total-pages]
          ],
        )
      }
    }
  )

  // Typography settings
  set text(
    font: font-family-sans,
    size: body-size,
    lang: language,
    hyphenate: true,
    fill: c-text-dark,
  )
  set par(
    justify: true,
    leading: par-leading,
    spacing: par-spacing,
  )
  set list(
    spacing: list-spacing,
  )
  set enum(
    spacing: list-spacing,
  )
  set terms(
    spacing: list-spacing,
    tight: false,
  )

  // Heading Styling (A1: kein Blocksatz, keine Silbentrennung; B6, A8: Skalierung)
  show heading: it => {
    set par(justify: false)
    set text(hyphenate: false)
    if it.has("label") and str(it.label) == "part-entry" {
      text(size: size-part-title, weight: "bold", fill: c-text-dark)[#it.body]
    } else if it.has("label") and str(it.label) == "chapter-divider" {
      none
    } else {
      let cfg = heading-scales.at(str(it.level), default: heading-scales.at("4"))
      v(cfg.above)
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
        fill: c-text-dark,
        weight: cfg.weight,
        size: cfg.size,
      )[
        #context block(width: 100%, above: par.spacing, below: par.spacing, sticky: true)[#h-text]
      ]
      v(cfg.below)
    }
  }

  // Links styling: Web URLs blue and underlined, internal links natural
  show link: it => {
    if type(it.dest) == str {
      text(fill: c-primary, underline(stroke: 0.5pt + rgb("#93c5fd"), offset: 2pt)[#it])
    } else {
      it
    }
  }

  // Outline / TOC styling (B8: Führungspunkte mager belassen)
  show outline.entry: it => {
    let elem = it.element
    let all-outlined = query(selector(heading.where(outlined: true)))
    let is-first-toc = all-outlined.len() > 0 and elem.location() == all-outlined.first().location()
    let elem-idx = all-outlined.position(h => h.location() == elem.location())
    let follows-part = if elem-idx != none and elem-idx > 0 {
      let prev = all-outlined.at(elem-idx - 1)
      prev.has("label") and str(prev.label) == "part-entry"
    } else {
      false
    }

    if elem.has("label") and str(elem.label) == "part-entry" {
      let num = if elem.numbering != none {
        numbering(elem.numbering, ..counter(heading).at(elem.location()))
      } else { none }
      let pg = counter(page).at(elem.location()).first()
      if not is-first-toc {
        v(1.8em)
      }
      link(elem.location())[
        #text(weight: "bold", size: 11pt, fill: c-text-dark)[#if num != none [#num #h(0.35em)]#elem.body]
        #box(width: 1fr)
        #text(weight: "bold", size: 11pt, fill: c-text-dark)[#pg]
      ]
      v(0.85em)
    } else if it.level == 1 {
      if not is-first-toc and not follows-part {
        v(0.9em)
      }
      let num = if elem.numbering != none {
        numbering(elem.numbering, ..counter(heading).at(elem.location()))
      } else { none }
      let pg = counter(page).at(elem.location()).first()
      link(elem.location())[
        #text(weight: "bold", fill: c-text-dark)[#if num != none and str(num).trim() != "" [#num #h(0.35em)]#elem.body]
        #box(width: 1fr, text(fill: c-text-subtle)[#it.fill])
        #text(weight: "bold", fill: c-text-dark)[#pg]
      ]
    } else {
      text(weight: "regular", fill: c-text-secondary)[#it]
    }
  }

  // Table styling (Booktabs-Stil A6 & B9)
  set table(
    stroke: (x, y) => if y == 0 {
      (top: stroke-table-top + c-text-dark, bottom: stroke-table-mid + c-text-dark)
    } else {
      (bottom: stroke-table-divider + c-border)
    },
    fill: none,
    inset: (x, y) => if x == 0 {
      (top: 7pt, bottom: 7pt, left: 0pt, right: 10pt)
    } else {
      (top: 7pt, bottom: 7pt, left: 10pt, right: 10pt)
    },
  )
  show table: set par(justify: false)
  show table: set text(number-width: "tabular")
  show table: it => block(stroke: (bottom: stroke-table-top + c-text-dark))[#it]

  // Code Block styling
  show raw.where(block: true): it => block(
    fill: c-bg-muted,
    stroke: stroke-border + c-border-strong,
    inset: 10pt,
    radius: radius-md,
    width: 100%,
    text(font: font-family-mono, size: size-code-block)[#it]
  )
  // Relative Schriftgröße für Inline-Code (Optischer Grauwert angepasst über weight-code-inline)
  show raw.where(block: false): it => highlight(
    fill: c-bg-muted,
    radius: radius-sm,
    extent: 1.5pt,
    top-edge: "ascender",
    bottom-edge: "descender",
  )[#text(fill: c-text-dark, font: font-family-mono, size: size-code-inline, weight: weight-code-inline)[#it]]

  // Render Cover Page if enabled (A1: kein Blocksatz, keine Silbentrennung auf Titeln)
  if show-cover {
    [#metadata("cover") <cover-page>]
    set par(justify: false)
    set text(hyphenate: false)
    v(2cm)
    text(size: size-cover-title, weight: "bold", fill: c-text-dark)[#title]
    v(0.5em)
    if subtitle != none and subtitle != "" {
      text(size: size-cover-subtitle, fill: c-text-muted)[#subtitle]
      v(1.5em)
    }
    line(length: 100%, stroke: stroke-accent + c-primary)
    v(1.5em)

    if summary != none and summary != "" {
      _render-summary-box(
        summary,
        accent-color: c-primary,
        accent-bar: 4pt,
        font-size: size-cover-summary,
        text-color: c-text-secondary,
        inset: (x: 14pt, y: 12pt),
        style: "italic",
      )
      v(2em)
    }

    // Metadata Grid
    v(1fr)
    let meta-items = cover-fields(meta).filter(
      it => it != none and it.value != "" and it.value != none and it.value != ()
    )

    grid(
      columns: (auto, 1fr),
      row-gutter: 10pt,
      column-gutter: 20pt,
      ..meta-items.map(it => (
        text(weight: "bold", fill: c-text-muted)[#if it.label != none and it.label != "" { it.label } else { it.key }],
        text(fill: c-text-dark)[#meta-value(it.value, labels)],
      )).flatten()
    )
    v(1cm)
    pagebreak()
  }

  // Render Table of Contents
  if show-toc {
    v(1cm)
    text(size: size-toc-title, weight: "bold", fill: c-text-dark)[#toc-title]
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

// -----------------------------------------------------------------------------
// Divider Pages (Part & Chapter)
// -----------------------------------------------------------------------------

// Part Divider Page (A1: kein Blocksatz/Silbentrennung, A4: breakable: false)
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
  block(width: 100%, breakable: false)[
    #set par(justify: false)
    #set text(hyphenate: false)
    #v(3cm)
    #let has-number = number != none and number != ""
    #let tag-word = upper(str(tag)).trim()
    #let tag-line = if has-number and tag-word != "" {
      tag-word + " " + number
    } else if has-number {
      number
    } else {
      tag-word
    }
    #if tag-line != "" [
      #text(size: 10pt, weight: "bold", fill: c-primary, tracking: 0.1em)[#tag-line]
      #v(0.3em)
    ]
    #let num-fn = if has-number { (..nums) => number } else { none }
    #if in-toc [
      #heading(level: 1, outlined: true, numbering: num-fn)[#title] <part-entry>
    ] else [
      #text(size: size-part-title, weight: "bold", fill: c-text-dark)[#title]
    ]
    #v(0.5em)
    #line(length: 100%, stroke: stroke-accent + c-primary)
    #v(1.5em)

    #if subtitle != none and subtitle != "" [
      #text(size: size-part-subtitle, fill: c-text-muted)[#subtitle]
      #v(1em)
    ]

    #if summary != none and summary != "" [
      #_render-summary-box(
        summary,
        accent-color: c-primary,
        font-size: 10pt,
        text-color: c-text-secondary,
        inset: (x: 12pt, y: 10pt),
        style: "normal",
      )
      #v(2em)
    ]

    #if toc-items.len() > 0 [
      #_render-local-toc(toc-title, toc-items, is-chapter: false)
    ]
  ]
  pagebreak()
}

// Chapter Divider Page (A1: kein Blocksatz/Silbentrennung, A4: breakable: false)
#let render-chapter-divider(
  title: "",
  subtitle: none,
  summary: none,
  tag: "KAPITEL",
  toc-title: "Inhalt dieses Kapitels",
  toc-items: (),
) = {
  [#heading(level: 1, outlined: false, numbering: none)[#title] <chapter-divider>]
  block(width: 100%, breakable: false)[
    #set par(justify: false)
    #set text(hyphenate: false)
    #v(3cm)
    #let tag-line = upper(str(tag)).trim()
    #if tag-line != "" [
      #text(size: 9pt, weight: "bold", fill: c-text-muted, tracking: 0.1em)[#tag-line]
      #v(0.3em)
    ]
    #text(size: size-chapter-title, weight: "bold", fill: c-text-dark)[#title]
    #v(0.5em)
    #line(length: 100%, stroke: 1pt + c-border-strong)
    #v(1.5em)

    #if subtitle != none and subtitle != "" [
      #text(size: size-chapter-subtitle, fill: c-text-muted)[#subtitle]
      #v(1em)
    ]

    #if summary != none and summary != "" [
      #_render-summary-box(
        summary,
        accent-color: c-text-muted,
        font-size: 9.5pt,
        text-color: c-text-secondary,
        inset: (x: 12pt, y: 10pt),
        style: "normal",
      )
      #v(2em)
    ]

    #if toc-items.len() > 0 [
      #_render-local-toc(toc-title, toc-items, is-chapter: true)
    ]
  ]
  pagebreak()
}
