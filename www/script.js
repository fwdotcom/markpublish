/**
 * markpublish — Website Script (Bilingual i18n, Interactive Showcase & Legal Modal)
 */

(function () {
  'use strict';

  // --- I18N Translations Dictionary ---
  const translations = {
    de: {
      nav_highlights: "Highlights",
      nav_features: "Funktionen",
      nav_quickstart: "Schnellstart",
      nav_manuals: "Handbücher",
      hero_badge: "Powered by Typst & Python",
      hero_title: "Moderne PDF-Dokumente aus <span class=\"gradient-text\">strukturiertem Markdown</span>",
      hero_subtitle: "markpublish setzt Markdown-Kapitel in druckreife, hochwertige PDFs — Deckblatt, Verzeichnisse und Kopfzeilen entstehen automatisch.",
      hero_btn_manuals: "Handbücher & Quickstart",
      copied: "Kopiert!",
      hi_deps: "Keine externen Compiler-Binaries",
      hi_speed: "Blitzschnelle Kompilierung",
      hi_license: "Freie MIT-Lizenz",

      showcase_tag: "HIGHLIGHTS",
      showcase_title: "Automatische Struktur<br/>und visuelle Akzente",
      showcase_desc: "Ein PDF aus vielen Markdown-Dateien: Nummerierung, Verzeichnisse und Kopfzeilen bleiben über alle Kapitel hinweg synchron.",
      download_sample_pdf: "Beispiel-PDF",
      download_sample_zip: "Projekt (.zip)",
      zoom_btn: "Vergrößern",
      open_pdf_page: "Ganze Seite anzeigen",
      copy_command: "Befehl kopieren",
      close: "Schließen",
      close_esc: "Schließen (Esc)",
      view_full_file: "Ganze Datei öffnen",
      snippet_tag: "SO SCHREIBST DU ES",
      engine_speed: "< 100 ms",

      feat_tag: "FUNKTIONEN",
      feat_title: "Professionelle Dokumente<br/>out-of-the-box",
      feat_desc: "Keine Probleme mit komplizierten Pipelines",
      f1_title: "Ein Manifest für alles",
      f1_desc: "Titel, Deckblatt, Verzeichnisse sowie die Reihenfolge der Kapitel werden zentral in <code>markpublish.yaml</code> definiert.",
      f2_title: "Kapitel & Trennseiten",
      f2_desc: "Abschnitte und Kapitel erhalten auf Wunsch stilvolle Trennseiten mit Untertitel und eigenem lokalem Teil-Inhaltsverzeichnis.",
      f3_title: "Musterbasierte Nummerierung",
      f3_desc: "Muster wie <code>\"1|.1|+\"</code>, <code>\"A|.1|+\"</code> oder <code>\"I|1|.1|+\"</code> steuern die Nummerierung. Frei anpassbare Präfixe („Kapitel“, „Anhang“) sind möglich.",
      f4_title: "Themen in Typst",
      f4_desc: "Mit <code>markpublish export-template</code> kann das default-Theme exportiert und angepasst werden.",
      f5_title: "Markdown, das mehr kann",
      f5_desc: "GitHub-style Alerts (<code>[!NOTE]</code>, <code>[!WARNING]</code>), Fußnoten, Aufgabenlisten, Definitionslisten, Mathe in LaTeX-Schreibweise und erstklassiges Code-Highlighting.",
      f6_title: "Mehrsprachig gedacht",
      f6_desc: "Flexible Mehrsprachigkeit auch für statische Texte in Templates — aktuell Deutsch und Englisch.",
      f7_title: "Keine manuellen Abhängigkeiten",
      f7_desc: "Kein separates Typst-Binary oder Pandoc-Setup nötig. Der Typst-Compiler wird direkt über offizielle Python-Wheels eingebettet.",
      f8_title: "Selbst-dokumentierend",
      f8_desc: "<code>markpublish cheatsheet</code> und <code>markpublish manual</code> generieren die Handbücher direkt aus dem installierten Paket — immer versionsgenau.",

      qs_tag: "SCHNELLSTART",
      qs_title: "In 3 Schritten zum ersten Dokument",
      qs_desc: "Installieren, Projekt anlegen, PDF bauen — fertig.",
      qs_c1: "# 1. markpublish installieren (benötigt Python 3.10+)",
      qs_c2: "# 2. Projekt anlegen — erzeugt markpublish.yaml und welcome.md",
      qs_cmd2: "markpublish init mein-dokument",
      qs_out2: "[OK] markpublish-Projekt eingerichtet in mein-dokument<br/>markpublish build mein-dokument/markpublish.yaml erzeugt Ihr erstes PDF.",
      qs_c3: "# 3. Druckreifes PDF kompilieren (Dateiname aus dem Dokumententitel)",
      qs_cmd3: "markpublish build mein-dokument/markpublish.yaml",
      qs_out3: "[OK] PDF erfolgreich erzeugt: mein-dokument/mein_dokument.pdf",

      man_tag: "DOKUMENTATION & DOWNLOADS",
      man_title: "Handbücher & Kurzreferenzen",
      man_desc: "Alle Handbücher wurden vollständig mit markpublish selbst gesetzt. Direkt als PDF herunterladen oder im Browser ansehen.",
      man_de_user_desc: "Vollständige Anleitung zu Konfiguration, Typst-Integration, Kapiteln, Metadaten und CLI-Befehlen.",
      man_de_ref_desc: "Kompakte Referenz aller Syntaxelemente, Autonumbering-Muster, YAML-Optionen und Tastenkürzel.",
      man_en_user_desc: "Comprehensive guide covering configuration, Typst integration, numbering patterns, and CLI options.",
      man_en_ref_desc: "Compact cheat sheet covering all syntax, YAML manifest parameters, formatting rules and commands.",

      footer_impressum: "Impressum",
      footer_datenschutz: "Datenschutz",

      modal_impressum_title: "Impressum",
      modal_impressum_content: `
        <h4>Angaben gemäß § 5 DDG (Digitale-Dienste-Gesetz)</h4>
        <p><strong>Frank Winter</strong><br>
        Wilhelmstr. 5A<br>
        03046 Cottbus<br>
        E-Mail: <a href="mailto:studio@frankwinter.com">studio@frankwinter.com</a></p>

        <h4>Haftung für Inhalte</h4>
        <p>Als Diensteanbieter bin ich gemäß § 7 Abs. 1 DDG für eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 DDG bin ich als Diensteanbieter jedoch nicht verpflichtet, übermittelte oder gespeicherte fremde Informationen zu überwachen oder nach Umständen zu forschen, die auf eine rechtswidrige Tätigkeit hinweisen.</p>

        <h4>Haftung für Links</h4>
        <p>Mein Angebot enthält Links zu externen Websites Dritter, auf deren Inhalte ich keinen Einfluss habe. Deshalb kann ich für diese fremden Inhalte keine Gewähr übernehmen. Für die Inhalte der verlinkten Seiten ist stets der jeweilige Anbieter oder Betreiber der Seiten verantwortlich.</p>

        <h4>Urheberrecht & Open Source</h4>
        <p>Die von mir erstellten Inhalte und Werke auf diesen Seiten unterliegen dem Urheberrecht. Das Softwareprojekt markpublish ist unter der freien <strong>MIT-Lizenz</strong> lizenziert.</p>
      `,

      modal_datenschutz_title: "Datenschutzerklärung",
      modal_datenschutz_content: `
        <h4>1. Datenschutz auf einen Blick</h4>
        <p>Diese Website dient ausschließlich der Information über das Open-Source-Projekt <strong>markpublish</strong>. Ich erhebe, verarbeite oder speichere auf dieser Website keine personenbezogenen Daten, setze keine Tracking-Cookies und verwende keine externen Analysedienste oder Werbenetzwerke.</p>

        <h4>2. Hosting via GitHub Pages</h4>
        <p>Diese Website wird als statische Seite über <strong>GitHub Pages</strong> gehostet. Anbieter ist die GitHub Inc., 88 Colin P Kelly Jr St, San Francisco, CA 94107, USA.</p>
        <p>Beim Besuch dieser Website erfasst GitHub automatisch technische Server-Logfiles (u.a. Browsertyp, Betriebssystem, Referrer URL, Hostname des zugreifenden Rechners, Uhrzeit der Serveranfrage und IP-Adresse). Dies ist technisch erforderlich, um die Website sicher und stabil bereitzustellen (Rechtsgrundlage: Art. 6 Abs. 1 lit. f DSGVO berechtigtes Interesse an einer verlässlichen Bereitstellung).</p>
        <p>Weitere Informationen finden Sie in der <a href="https://docs.github.com/en/site-policy/privacy-policies/github-privacy-statement" target="_blank" rel="noopener">Datenschutzerklärung von GitHub</a>.</p>

        <h4>3. Ihre Rechte als betroffene Person</h4>
        <p>Sie haben nach der Datenschutz-Grundverordnung (DSGVO) das Recht auf Auskunft (Art. 15 DSGVO), Berichtigung (Art. 16 DSGVO), Löschung (Art. 17 DSGVO) und Einschränkung der Verarbeitung (Art. 18 DSGVO) bezüglich etwaiger personenbezogener Daten. Bei Fragen zum Datenschutz können Sie mich jederzeit unter der im Impressum angegebenen E-Mail-Adresse kontaktieren.</p>
      `
    },

    en: {
      nav_highlights: "Highlights",
      nav_features: "Features",
      nav_quickstart: "Quickstart",
      nav_manuals: "Manuals",
      hero_badge: "Powered by Typst & Python",
      hero_title: "Modern PDF Publishing from <span class=\"gradient-text\">Structured Markdown</span>",
      hero_subtitle: "markpublish typesets Markdown chapters into print-ready, publication-grade PDFs — covers, contents and running headers come automatically.",
      hero_btn_manuals: "Manuals & Quickstart",
      copied: "Copied!",
      hi_deps: "Zero external compiler binaries",
      hi_speed: "Lightning-fast compilation",
      hi_license: "Permissive MIT License",

      showcase_tag: "HIGHLIGHTS",
      showcase_title: "Automatic structure<br/>and visual accents",
      showcase_desc: "One PDF from many Markdown files: numbering, contents and running headers stay in sync across every chapter.",
      download_sample_pdf: "Sample PDF",
      download_sample_zip: "Project (.zip)",
      zoom_btn: "Enlarge",
      open_pdf_page: "Show full page",
      copy_command: "Copy command",
      close: "Close",
      close_esc: "Close (Esc)",
      view_full_file: "Open full file",
      snippet_tag: "HOW YOU WRITE IT",
      engine_speed: "< 100 ms",

      feat_tag: "FEATURES",
      feat_title: "Professional documents<br/>out of the box",
      feat_desc: "No wrestling with complicated pipelines",
      f1_title: "One manifest for everything",
      f1_desc: "Title, cover, contents and chapter order are defined centrally in <code>markpublish.yaml</code>.",
      f2_title: "Chapters & Dividers",
      f2_desc: "Sections and chapters can get styled divider pages with subtitle and their own local table of contents.",
      f3_title: "Pattern-based numbering",
      f3_desc: "Patterns like <code>\"1|.1|+\"</code>, <code>\"A|.1|+\"</code> or <code>\"I|1|.1|+\"</code> drive the numbering. Freely adjustable prefixes (\"Chapter\", \"Appendix\") are possible.",
      f4_title: "Typst Themes",
      f4_desc: "<code>markpublish export-template</code> exports the default theme for customization.",
      f5_title: "Supercharged Markdown",
      f5_desc: "GitHub-style alerts (<code>[!NOTE]</code>, <code>[!WARNING]</code>), footnotes, task lists, definition lists, math in LaTeX notation, and syntax highlighting.",
      f6_title: "Multilingual by design",
      f6_desc: "Flexible multilingual support, including static text in templates — currently German and English.",
      f7_title: "No manual dependencies",
      f7_desc: "No separate Typst executable or Pandoc installation required. The compiler is natively embedded via Python wheels.",
      f8_title: "Self-documenting",
      f8_desc: "<code>markpublish cheatsheet</code> and <code>markpublish manual</code> compile the references directly from the installed package — always version-accurate.",

      qs_tag: "QUICKSTART",
      qs_title: "Publish your first document in 3 steps",
      qs_desc: "Install, initialize project, build PDF — done.",
      qs_c1: "# 1. Install markpublish (requires Python 3.10+)",
      qs_c2: "# 2. Create a project — writes markpublish.yaml and welcome.md",
      qs_cmd2: "markpublish init my-document",
      qs_out2: "[OK] Initialized markpublish project in my-document<br/>Run markpublish build my-document/markpublish.yaml to generate your first PDF.",
      qs_c3: "# 3. Compile the print-ready PDF (filename comes from the document title)",
      qs_cmd3: "markpublish build my-document/markpublish.yaml",
      qs_out3: "[OK] PDF successfully generated: my-document/my_document.pdf",

      man_tag: "DOCUMENTATION & DOWNLOADS",
      man_title: "Manuals & Quick References",
      man_desc: "All manuals were typeset entirely with markpublish itself. Download as PDF or inspect directly in your browser.",
      man_de_user_desc: "Complete guide covering configuration, Typst integration, numbering patterns, and CLI options in German.",
      man_de_ref_desc: "Compact cheat sheet covering syntax elements, YAML options, and keyboard shortcuts in German.",
      man_en_user_desc: "Comprehensive guide covering configuration, Typst integration, numbering patterns, and CLI options.",
      man_en_ref_desc: "Compact cheat sheet covering all syntax, YAML manifest parameters, formatting rules and commands.",

      footer_impressum: "Legal Notice (Impressum)",
      footer_datenschutz: "Privacy Policy",

      modal_impressum_title: "Legal Notice (Impressum)",
      modal_impressum_content: `
        <h4>Information according to § 5 DDG (German Digital Services Act)</h4>
        <p><strong>Frank Winter</strong><br>
        Wilhelmstr. 5A<br>
        03046 Cottbus<br>
        Email: <a href="mailto:studio@frankwinter.com">studio@frankwinter.com</a></p>

        <h4>Liability for Contents</h4>
        <p>As a service provider, I am responsible for my own content on these pages in accordance with general legislation pursuant to Section 7 (1) of the DDG. According to Sections 8 to 10 of the DDG, however, I am not obliged to monitor transmitted or stored third-party information or to investigate circumstances that indicate illegal activity.</p>

        <h4>Liability for Links</h4>
        <p>This website contains links to external websites of third parties, over whose contents I have no control. I therefore cannot assume any liability for these external contents. The respective provider or operator of the pages is always responsible for the content of the linked pages.</p>

        <h4>Copyright & Open Source</h4>
        <p>The contents and works I created on these pages are subject to copyright law. The software project markpublish is licensed under the permissive <strong>MIT License</strong>.</p>
      `,

      modal_datenschutz_title: "Privacy Policy (Datenschutzerklärung)",
      modal_datenschutz_content: `
        <h4>1. Privacy at a Glance</h4>
        <p>This website serves exclusively to provide information regarding the open-source project <strong>markpublish</strong>. I do not collect, process, or store personal data on this website, I set no tracking cookies, and I use no third-party analytics or advertising networks.</p>

        <h4>2. Hosting via GitHub Pages</h4>
        <p>This static website is hosted via <strong>GitHub Pages</strong> provided by GitHub Inc., 88 Colin P Kelly Jr St, San Francisco, CA 94107, USA.</p>
        <p>When you visit this website, GitHub automatically collects server log files (such as browser type, operating system, referrer URL, host name of the accessing device, time of server request, and IP address). This is technically necessary to deliver the website reliably and securely (Legal basis: Art. 6 (1) (f) GDPR legitimate interest).</p>
        <p>For more details, please review the <a href="https://docs.github.com/en/site-policy/privacy-policies/github-privacy-statement" target="_blank" rel="noopener">GitHub Privacy Statement</a>.</p>

        <h4>3. Your Rights</h4>
        <p>Under the GDPR, you have the right to information, rectification, erasure, and restriction of processing regarding any personal data. For privacy inquiries, feel free to reach out via the email address indicated in the Legal Notice.</p>
      `
    }
  };

  // --- Showcase 4-Feature Focus Content ---
  const showcaseFiles = {
    cover: {
      de: {
        page: 1,
        badge: "YAML",
        tabLabel: "Deckblatt",
        filename: "markpublish.yaml",
        rawPath: "sample/de/markpublish.yaml",
        title: "markpublish.yaml",
        pill: "markpublish.yaml",
        desc: "Metadaten, Gliederung und Theme-Vorgaben zentral in einem Manifest definiert",
        bullets: [
          "Reines YAML steuert die gesamte Dokumentenstruktur",
          "Automatische Deck- und Zwischenblätter mit Abschnitts-Verzeichnissen",
          "Frei definierbare Nummerierungsmuster"
        ],
        snippet: `document:
  title: "Systemarchitektur & Design"
  subtitle: "Technische Referenzspezifikation"
  summary: "Musterdokumentation zur Demonstration aller markpublish Kernfunktionen."
  author: "Frank Winter"
  version: "2.1.7"
  date: "auto"
  cover: true
  autonum_pattern: "_|1|.1|+"
  header: true
  footer: true

theme: "default"`,
        clip: { x: 0.115, y: 0.1413, w: 0.77, h: 0.257 },
        svg: "assets/showcase/de_page_1.svg",
        png: "assets/showcase/de_page_1.png"
      },
      en: {
        page: 1,
        badge: "YAML",
        tabLabel: "Cover Page",
        filename: "markpublish.yaml",
        rawPath: "sample/en/markpublish.yaml",
        title: "markpublish.yaml",
        pill: "markpublish.yaml",
        desc: "Metadata, structure and theme settings defined centrally in one manifest",
        bullets: [
          "Plain YAML drives the entire document structure",
          "Automatic cover and divider pages with section-level contents",
          "Freely definable numbering patterns"
        ],
        snippet: `document:
  title: "System Architecture & Design"
  subtitle: "Technical Reference Specification"
  summary: "Sample publication demonstrating core markpublish features."
  author: "Frank Winter"
  version: "2.1.7"
  date: "auto"
  cover: true
  autonum_pattern: "_|1|.1|+"
  header: true
  footer: true

theme: "default"`,
        clip: { x: 0.115, y: 0.1413, w: 0.77, h: 0.257 },
        svg: "assets/showcase/en_page_1.svg",
        png: "assets/showcase/en_page_1.png"
      }
    },

    structure: {
      de: {
        page: 2,
        badge: "Markdown",
        tabLabel: "Struktur & Kopfzeilen",
        filename: "01_architektur.md",
        rawPath: "sample/de/01_architektur.md",
        title: "Dynamische Kopfzeilen und flexible Gliederung",
        pill: "01_architektur.md",
        desc: "Keine manuellen Ziffern — markpublish nummeriert vollautomatisch über alle Dateien hinweg",
        bullets: [
          "Automatische Zählung (`1`, `1.1`)",
          "Dynamische Kopfzeilen: Dokumenttitel links, aktuelles Kapitel rechts (templateabhängig)",
          "Nativer Typst-Buchdrucksatz mit akkurater Paginierung („Seite X von Y“)"
        ],
        snippet: `# Einführung & Systemarchitektur

markpublish transformiert strukturierte Markdown-Dateien in 
publikationsreife Dokumente.

> [!NOTE]
> Die native Satz-Engine Typst übernimmt den präzisen Buchdruck-Satz.

## Modulare Gliederung
Dokumente können in Hauptteile (*Parts*), Kapitel und Trennseiten gegliedert werden...`,
        clip: { x: 0.115, y: 0.0, w: 0.77, h: 0.257, pageTop: true },
        svg: "assets/showcase/de_page_2.svg",
        png: "assets/showcase/de_page_2.png"
      },
      en: {
        page: 2,
        badge: "Markdown",
        tabLabel: "Structure & Headers",
        filename: "01_architecture.md",
        rawPath: "sample/en/01_architecture.md",
        title: "Dynamic Headers and Flexible Structure",
        pill: "01_architecture.md",
        desc: "No manual digits — markpublish numbers everything automatically across all files",
        bullets: [
          "Automatic numbering (`1`, `1.1`)",
          "Dynamic headers: document title left, active chapter right (template-dependent)",
          "Native Typst book typesetting with accurate pagination (“Page X of Y”)"
        ],
        snippet: `# Introduction & System Architecture

markpublish transforms structured Markdown files into publication-grade documents.

> [!NOTE]
> Native Typst engine delivers book-grade printing and hyphenation.

## Modular Structure
Documents can be organized into parts, chapters, and divider pages...`,
        clip: { x: 0.115, y: 0.0, w: 0.77, h: 0.257, pageTop: true },
        svg: "assets/showcase/en_page_2.svg",
        png: "assets/showcase/en_page_2.png"
      }
    },

    math: {
      de: {
        page: 3,
        badge: "Markdown",
        tabLabel: "Formeln & Code",
        filename: "02_algorithmen.md",
        rawPath: "sample/de/02_algorithmen.md",
        title: "Wissenschaftlicher Satz und Syntax Highlighting",
        pill: "02_algorithmen.md",
        desc: "Komplexe mathematische Formeln und Quellcode nativ im Dokument verankert",
        bullets: [
          "Native Typst Math Engine: Vektorsatz ohne Umwege",
          "Syntax-Highlighting für über 100 Sprachen"
        ],
        snippet: `# Wissenschaftliche Berechnungen

Mathematische Formeln werden typografisch präzise gerendert:

$$ E = frac(m c^2, sqrt(1 - v^2 / c^2)) $$

## Pipeline-Implementierung
\`\`\`python
def render_pdf(manifest_file: Path) -> bytes:
    doc = load_manifest(manifest_file)
    return typst.compile(doc.to_typst())
\`\`\``,
        clip: { x: 0.115, y: 0.0998, w: 0.77, h: 0.257 },
        svg: "assets/showcase/de_page_3.svg",
        png: "assets/showcase/de_page_3.png"
      },
      en: {
        page: 3,
        badge: "Markdown",
        tabLabel: "Formulas & Code",
        filename: "02_algorithms.md",
        rawPath: "sample/en/02_algorithms.md",
        title: "Scientific Typesetting and Syntax Highlighting",
        pill: "02_algorithms.md",
        desc: "Complex mathematical formulas and code blocks embedded natively as crisp vectors",
        bullets: [
          "Native Typst math engine: vector typesetting, no detours",
          "Syntax highlighting for more than 100 languages"
        ],
        snippet: `# Scientific Computations

Mathematical formulas are typeset with high typographic precision:

$$ E = frac(m c^2, sqrt(1 - v^2 / c^2)) $$

## Pipeline Implementation
\`\`\`python
def render_pdf(manifest_file: Path) -> bytes:
    doc = load_manifest(manifest_file)
    return typst.compile(doc.to_typst())
\`\`\``,
        clip: { x: 0.115, y: 0.0998, w: 0.77, h: 0.257 },
        svg: "assets/showcase/en_page_3.svg",
        png: "assets/showcase/en_page_3.png"
      }
    },

    callouts: {
      de: {
        page: 4,
        badge: "Markdown",
        tabLabel: "Callouts & Listen",
        filename: "03_hinweise.md",
        rawPath: "sample/de/03_hinweise.md",
        title: "GitHub-Style Callouts & Checklisten",
        pill: "03_hinweise.md",
        desc: "Visuelle Akzente für professionelle Handbücher, Richtlinien und Prüflisten",
        bullets: [
          "Volle Unterstützung für `[!NOTE]`, `[!TIP]`, `[!WARNING]`, `[!IMPORTANT]` und `[!CAUTION]`",
          "Automatisch lokalisierte Boxen mit Vektor-Icons und dezenten Akzentfarben",
          "Druckreife Aufgabenlisten (`- [x]`) mit sauberem vertikalem Zeilenrhythmus"
        ],
        snippet: `# Hinweise & Checkliste

> [!TIP]
> Ein einheitliches Nummerierungsmuster wie \`1|.1|+\` synchronisiert 
> Überschriften und Verzeichnisse automatisch.

> [!WARNING]
> Benutzerdefinierte Themes vor dem Release lokal mit \`markpublish build\` prüfen.

## Veröffentlichungs-Checkliste
- [x] Projektmanifest markpublish.yaml validieren
- [x] Typst Engine kompilieren
- [ ] Druckfreigabe erteilen`,
        clip: { x: 0.115, y: 0.1722, w: 0.77, h: 0.257 },
        svg: "assets/showcase/de_page_4.svg",
        png: "assets/showcase/de_page_4.png"
      },
      en: {
        page: 4,
        badge: "Markdown",
        tabLabel: "Callouts & Lists",
        filename: "03_notes.md",
        rawPath: "sample/en/03_notes.md",
        title: "GitHub-Style Callouts & Checklists",
        pill: "03_notes.md",
        desc: "Visual callouts for polished technical manuals, alerts, and publishing checklists",
        bullets: [
          "Full support for `[!NOTE]`, `[!TIP]`, `[!WARNING]`, `[!IMPORTANT]`, and `[!CAUTION]`",
          "Automatically localized title labels and embedded vector icons",
          "Print-ready task lists (`- [x]`) with balanced vertical typography"
        ],
        snippet: `# Notes & Checklist

> [!TIP]
> A unified numbering pattern like \`1|.1|+\` synchronizes 
> headings and tables of contents automatically.

> [!WARNING]
> Validate custom themes locally with \`markpublish build\` prior to release.

## Publication Checklist
- [x] Validate project manifest markpublish.yaml
- [x] Compile via Typst engine
- [ ] Sign off publication`,
        clip: { x: 0.115, y: 0.1722, w: 0.77, h: 0.257 },
        svg: "assets/showcase/en_page_4.svg",
        png: "assets/showcase/en_page_4.png"
      }
    }
  };

  const tileKeys = ['cover', 'structure', 'math', 'callouts'];

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // Aspect ratio of a page clipping (page is 595.28 x 841.89 pt)
  function clipAspect(clip) {
    return ((clip.w * 595.28) / (clip.h * 841.89)).toFixed(3);
  }

  // Render `inline code` markers in bullet text as <code>
  function renderInlineCode(str) {
    return escapeHtml(str).replace(/`([^`]+)`/g, '<code>$1</code>');
  }

  // Preload showcase image files for instant switching
  function preloadShowcaseImages() {
    Object.values(showcaseFiles).forEach(tabItem => {
      Object.values(tabItem).forEach(item => {
        if (item.svg) { const img = new Image(); img.src = item.svg; }
        if (item.png) { const img = new Image(); img.src = item.png; }
      });
    });
  }

  // --- State ---
  let currentLang = 'de';
  let currentIndex = 0;

  // --- Initialize Language ---
  function initLanguage() {
    preloadShowcaseImages();
    const savedLang = localStorage.getItem('markpublish_lang');
    if (savedLang === 'de' || savedLang === 'en') {
      currentLang = savedLang;
    } else {
      const browserLang = (navigator.language || '').toLowerCase();
      currentLang = browserLang.startsWith('de') ? 'de' : 'en';
    }
    applyLanguage(currentLang);
  }

  function applyLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('markpublish_lang', lang);
    document.documentElement.lang = lang;

    // Update lang button text (desktop & mobile)
    const langLabel = lang === 'de' ? 'DE (Switch to EN)' : 'EN (Auf DE wechseln)';
    const langBtn = document.getElementById('lang-text');
    if (langBtn) {
      langBtn.textContent = langLabel;
    }
    const langBtnMobile = document.getElementById('lang-text-mobile');
    if (langBtnMobile) {
      langBtnMobile.textContent = langLabel;
    }

    // Update all data-i18n elements
    const i18nElements = document.querySelectorAll('[data-i18n]');
    i18nElements.forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (translations[lang] && translations[lang][key]) {
        el.innerHTML = translations[lang][key];
      }
    });

    // Update tooltips marked for translation
    const titleElements = document.querySelectorAll('[data-i18n-title]');
    titleElements.forEach(el => {
      const key = el.getAttribute('data-i18n-title');
      if (translations[lang] && translations[lang][key]) {
        el.setAttribute('title', translations[lang][key]);
      }
    });

    // Update screen-reader labels marked for translation
    const ariaElements = document.querySelectorAll('[data-i18n-aria]');
    ariaElements.forEach(el => {
      const key = el.getAttribute('data-i18n-aria');
      if (translations[lang] && translations[lang][key]) {
        el.setAttribute('aria-label', translations[lang][key]);
      }
    });

    // Render Showcase Tiles for active language
    renderShowcaseTiles();
  }

  // --- Render Showcase Tiles ---
  function renderShowcaseTiles() {
    const grid = document.getElementById('showcase-tiles');
    if (!grid) return;

    const sampleDocName = currentLang === 'de' ? 'markpublish_beispieldokument.pdf' : 'markpublish_sample_document.pdf';
    const sampleZipName = currentLang === 'de' ? 'markpublish_beispielprojekt.zip' : 'markpublish_sample_project.zip';
    const sampleDocUrl = `manuals/${sampleDocName}`;
    const sampleZipUrl = `manuals/${sampleZipName}`;
    const openPageText = translations[currentLang].open_pdf_page;

    grid.innerHTML = tileKeys.map((key, idx) => {
      const item = showcaseFiles[key][currentLang];
      const bulletsHtml = item.bullets.map(b => `
        <li class="showcase-bullet-item">
          <span class="bullet-check">✓</span>
          <span>${renderInlineCode(b)}</span>
        </li>
      `).join('');

      return `
        <article class="showcase-tile" role="button" tabindex="0" data-index="${idx}"
                 title="${openPageText}" aria-label="${escapeHtml(item.title)} — ${openPageText}">
          <h3 class="tile-heading">${escapeHtml(item.title)}</h3>
          <p class="tile-description">${escapeHtml(item.desc)}</p>

          <ul class="showcase-bullets">
            ${bulletsHtml}
          </ul>

          <!-- Clipping: the region of the PDF page carrying this feature.
               The wrapper carries the shadow: a filter on it traces the torn
               silhouette, while a box-shadow would be cut away by the mask. -->
          <div class="tile-clip-shadow" aria-hidden="true">
            <div class="tile-clip${item.clip.pageTop ? ' is-page-top' : ''}"
                 style="aspect-ratio: ${clipAspect(item.clip)}; --clip-x: ${item.clip.x}; --clip-y: ${item.clip.y}; --clip-w: ${item.clip.w};">
              <picture>
                <source srcset="${item.svg}" type="image/svg+xml">
                <img src="${item.png}" alt="" width="595" height="842" loading="lazy" />
              </picture>
            </div>
          </div>

          <div class="tile-footer">
            <span class="tile-cta">
              <svg viewBox="0 0 20 20" width="15" height="15" fill="currentColor" aria-hidden="true">
                <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
                <path d="M8 6a1 1 0 011 1v1h1a1 1 0 110 2H9v1a1 1 0 11-2 0v-1H6a1 1 0 110-2h1V7a1 1 0 011-1z"/>
              </svg>
              <span>${openPageText}</span>
            </span>
          </div>
        </article>
      `;
    }).join('');

    // Clicking (or activating) a tile opens the matching PDF page in the Lightbox
    grid.querySelectorAll('.showcase-tile').forEach(tile => {
      const idx = parseInt(tile.getAttribute('data-index'), 10);
      tile.addEventListener('click', () => openLightbox(idx));
      tile.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          openLightbox(idx);
        }
      });
    });

    // Update download buttons (PDF & ZIP)
    const dlPdfBtn = document.getElementById('showcase-download-pdf');
    if (dlPdfBtn) {
      dlPdfBtn.href = sampleDocUrl;
      dlPdfBtn.setAttribute('download', sampleDocName);
    }
    const dlZipBtn = document.getElementById('showcase-download-zip');
    if (dlZipBtn) {
      dlZipBtn.href = sampleZipUrl;
      dlZipBtn.setAttribute('download', sampleZipName);
    }
  }

  // --- Lightbox Functions ---
  function openLightbox(index) {
    if (typeof index === 'number') currentIndex = (index + tileKeys.length) % tileKeys.length;
    renderLightboxContent();
    const lbModal = document.getElementById('lightbox-modal');
    if (lbModal) {
      lbModal.classList.add('open');
      lbModal.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
    }
  }

  function closeLightbox() {
    const lbModal = document.getElementById('lightbox-modal');
    if (lbModal) {
      lbModal.classList.remove('open');
      lbModal.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    }
  }

  function renderLightboxContent() {
    const key = tileKeys[currentIndex];
    const fileInfo = showcaseFiles[key][currentLang];
    const sampleDocName = currentLang === 'de' ? 'markpublish_beispieldokument.pdf' : 'markpublish_sample_document.pdf';

    const lbContent = document.getElementById('lightbox-content');
    if (lbContent) {
      lbContent.innerHTML = `
        <picture>
          <source srcset="${fileInfo.svg}" type="image/svg+xml">
          <img src="${fileInfo.png}" alt="${sampleDocName} (${fileInfo.page}/4)" width="595" height="842" />
        </picture>
      `;
    }
  }

  function stepLightbox(delta) {
    currentIndex = (currentIndex + delta + tileKeys.length) % tileKeys.length;
    renderLightboxContent();
  }

  // --- Setup Event Listeners ---
  document.addEventListener('DOMContentLoaded', () => {
    initLanguage();

    // Lang toggle buttons (desktop & mobile)
    function toggleLang() {
      const nextLang = currentLang === 'de' ? 'en' : 'de';
      applyLanguage(nextLang);
    }

    const langBtn = document.getElementById('lang-switch-btn');
    if (langBtn) {
      langBtn.addEventListener('click', toggleLang);
    }

    const langBtnMobile = document.getElementById('lang-switch-btn-mobile');
    if (langBtnMobile) {
      langBtnMobile.addEventListener('click', toggleLang);
    }

    // Pip Copy Button
    const copyPipBtn = document.getElementById('copy-pip');
    if (copyPipBtn) {
      copyPipBtn.addEventListener('click', () => {
        navigator.clipboard.writeText('pip install markpublish').then(() => {
          copyPipBtn.classList.add('copied');
          setTimeout(() => {
            copyPipBtn.classList.remove('copied');
          }, 2000);
        }).catch(() => {
          // Fallback
          const code = document.getElementById('pip-command');
          if (code) {
            const range = document.createRange();
            range.selectNode(code);
            window.getSelection().removeAllRanges();
            window.getSelection().addRange(range);
            document.execCommand('copy');
            copyPipBtn.classList.add('copied');
            setTimeout(() => {
              copyPipBtn.classList.remove('copied');
            }, 2000);
          }
        });
      });
    }

    // Modal Handling (Impressum & Datenschutz)
    const modal = document.getElementById('legal-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalContent = document.getElementById('modal-content');
    const modalCloseBtn = document.getElementById('modal-close-btn');

    function openModal(title, contentHtml) {
      if (!modal) return;
      modalTitle.textContent = title;
      modalContent.innerHTML = contentHtml;
      modal.classList.add('open');
      modal.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
    }

    function closeModal() {
      if (!modal) return;
      modal.classList.remove('open');
      modal.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    }

    const openImpressumBtn = document.getElementById('open-impressum');
    if (openImpressumBtn) {
      openImpressumBtn.addEventListener('click', () => {
        const title = translations[currentLang].modal_impressum_title;
        const content = translations[currentLang].modal_impressum_content;
        openModal(title, content);
      });
    }

    const openDatenschutzBtn = document.getElementById('open-datenschutz');
    if (openDatenschutzBtn) {
      openDatenschutzBtn.addEventListener('click', () => {
        const title = translations[currentLang].modal_datenschutz_title;
        const content = translations[currentLang].modal_datenschutz_content;
        openModal(title, content);
      });
    }

    if (modalCloseBtn) {
      modalCloseBtn.addEventListener('click', closeModal);
    }

    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          closeModal();
        }
      });
    }

    // Mobile Burger Menu Handling
    const burgerBtn = document.getElementById('burger-btn');
    const navLinks = document.getElementById('nav-links');

    function closeBurgerMenu() {
      if (burgerBtn && navLinks) {
        burgerBtn.classList.remove('open');
        navLinks.classList.remove('open');
        burgerBtn.setAttribute('aria-expanded', 'false');
      }
    }

    if (burgerBtn && navLinks) {
      burgerBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = navLinks.classList.toggle('open');
        burgerBtn.classList.toggle('open', isOpen);
        burgerBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      });

      const links = navLinks.querySelectorAll('a');
      links.forEach(link => {
        link.addEventListener('click', closeBurgerMenu);
      });

      document.addEventListener('click', (e) => {
        if (navLinks.classList.contains('open') && !navLinks.contains(e.target) && !burgerBtn.contains(e.target)) {
          closeBurgerMenu();
        }
      });
    }

    // Lightbox Controls
    const lbModal = document.getElementById('lightbox-modal');
    const lbCloseBtn = document.getElementById('lightbox-close-btn');

    if (lbCloseBtn) {
      lbCloseBtn.addEventListener('click', closeLightbox);
    }

    if (lbModal) {
      lbModal.addEventListener('click', (e) => {
        if (e.target === lbModal || e.target.closest('#lightbox-close-btn')) {
          closeLightbox();
        }
      });
    }

    // Keyboard Shortcuts (Arrows inside the Lightbox, Escape to close)
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        if (lbModal && lbModal.classList.contains('open')) {
          closeLightbox();
        }
        if (modal && modal.classList.contains('open')) {
          closeModal();
        }
        closeBurgerMenu();
      } else if (lbModal && lbModal.classList.contains('open')) {
        if (e.key === 'ArrowLeft') {
          stepLightbox(-1);
        } else if (e.key === 'ArrowRight') {
          stepLightbox(1);
        }
      }
    });
  });
})();

