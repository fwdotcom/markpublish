# Code-Review markpublish — 31.08.2026

**Stand:** Commit `5a4e59a` + lokale Änderungen am Checkbox-Styling
**Umfang:** `src/markpublish/**` (ca. 1.500 LOC), beide mitgelieferten Themes (`pdf/default`, `html/default`), `tests/**`, `manual/de`, `examples/quickstart`
**Testlauf:** `pytest` → 17 passed
**Methodik:** Statische Durchsicht plus empirische Verifikation. Jeder als *bestätigt* markierte Befund wurde reproduziert — durch Rendern des Handbuchs, Rasterisieren der PDF-Seiten (pypdfium2), Textextraktion aus dem PDF oder isolierte WeasyPrint-Testfälle.

---

---

## Bearbeitungsstand (31.08.2026, nachgetragen)

**Alle 23 Befunde sind behoben.** Umgesetzt in der unten empfohlenen Reihenfolge.
`pytest`: 48 passed (17 vorher, 31 neu). `ruff check src tests`: sauber.

Zwei Dinge kamen beim Beheben dazu:

- **Zusatzbefund (kritisch, behoben):** Die Templates setzten `string-set: current-section`,
  das Stylesheet las `string(current_section)` — Bindestrich gegen Unterstrich. CSS-Bezeichner
  sind an dieser Stelle nicht austauschbar, die **zweite Kopfzeile war deshalb immer leer**.
  Zusammen mit C2 war der Header damit doppelt defekt. Beides ist korrigiert; der laufende
  Kolumnentitel zeigt jetzt den Kapitelnamen.
- **Verhaltensänderung durch H1:** Lokale Bilder werden nicht mehr zu `file://`-URIs, sondern
  als Data-URI eingebettet (SVG prozentkodiert, Rastergrafik base64, Grenze 12 MB). Die
  HTML-Ausgabe ist damit tatsächlich portabel — das ist der Zweck von H1, verändert aber die
  erzeugten Dateien sichtbar.

Bewusst *nicht* geändert:

- **Dateinamen bleiben mit Unterstrich.** H6 nutzt jetzt `slugify()`, aber mit
  `separator="_"` — sonst wäre aus `markpublish_benutzerhandbuch.pdf` ein
  `markpublish-benutzerhandbuch.pdf` geworden, eine Umbenennung ohne Not.
- **`ruff`-Regelsatz ohne `UP*`.** Die Modernisierungsregeln hätten den Typing-Stil des
  gesamten Codebases umgeschrieben (86 Treffer) — das hat mit Fehlersuche nichts zu tun.
  Aktiv sind `E`, `F`, `W`, `I`, `B`; `F821` hätte C4 sofort gemeldet.
- **CI-Anbindung.** `ruff` und `pypdfium2` stehen als Dev-Dependencies in `pyproject.toml`,
  die Regeln sind konfiguriert. Die Verdrahtung in eine Pipeline hängt an Ihrer
  CI-Plattform und ist deshalb offen geblieben.

### Was die Tests jetzt absichern

`tests/test_regressions.py` (31 Tests) prüft **Inhalt statt Existenz** — die Lücke, durch die
C1 bis C4 überhaupt ausliefern konnten. Elf Fixes wurden gegengeprüft, indem sie einzeln
zurückgebaut und der zugehörige Test beobachtet wurde: **11/11 schlagen bei zurückgebautem
Fix fehl.** Ein Test, der die Mutation überlebt, sichert nichts ab.

### Verifikation am ausgelieferten Handbuch

| Prüfung | Vorher | Nachher |
| :--- | :--- | :--- |
| Rumpf des Unterkapitels 4.2 | fehlt | vorhanden |
| Tote TOC-Anker | 3 | 0 |
| Doppelte `id`-Attribute | 8 | 0 |
| Kopfzeile | `v1.0.0଱.08.2026` | `v1.0.0` / `31.08.2026` |
| Laufender Kolumnentitel | leer | Kapitelname |
| TOC-Seitenzahlen | keine | vorhanden |
| Seitenzahl gesamt | 23 | 24 |

---

## Gesamteinschätzung

Die Architektur ist sauber: Config (Pydantic) → Markdown-Pipeline → Renderer → Templates sind klar getrennt, die 3-stufige Template-Auflösung (User > Projekt > Package) ist ein gutes Design, und die Trennung von `MarkdownEngine` (Konvertierung) und `MarkdownPipeline` (Orchestrierung) trägt. Der Code ist durchgehend typannotiert und lesbar.

Die Schwachstellen liegen fast alle an **einer** Stelle: in der letzten Meile zwischen Pipeline und Template. Die Pipeline baut korrekte Datenstrukturen auf, die Templates werten sie nur teilweise aus. Drei der vier kritischen Befunde sind Template-/CSS-Fehler, die im ausgelieferten Handbuch sichtbar sind — aber von keinem Test erfasst werden, weil die Tests nur Dateigrößen und Titel prüfen, nie den gerenderten Inhalt.

**Priorität:** Zuerst C1–C3 (sichtbar in jedem erzeugten Dokument), dann H1–H6.

| Kategorie | Anzahl |
| :--- | ---: |
| Kritisch (Datenverlust / falsche Ausgabe) | 4 |
| Hoch (funktionale Fehler) | 6 |
| Mittel (Robustheit, Wartbarkeit) | 8 |
| Niedrig (Hygiene, Kosmetik) | 5 |

---

## Kritisch

### C1 — Verschachtelte Unterkapitel verschwinden spurlos aus der Ausgabe

**Dateien:** [pdf/default/layout.html:53](src/markpublish/templates/pdf/default/layout.html#L53), [html/default/layout.html:75](src/markpublish/templates/html/default/layout.html#L75), [engine.py:286-290](src/markpublish/markdown/engine.py#L286-L290)
**Status: bestätigt am ausgelieferten Handbuch**

`MarkdownPipeline._process_chapter()` verarbeitet rekursiv `chapter_cfg.chapters` und füllt `item.children`. Beide `layout.html` iterieren `item.children` aber **nur im `is_part`-Zweig**. Für ein normales Kapitel mit Unterkapiteln wird ausschließlich `item.html_content` gerendert — die Kinder werden nie ausgegeben. Auch im Part-Zweig endet die Rekursion nach einer Ebene (`child.children` wird ignoriert).

Die TOC-Knoten der Unterkapitel werden dagegen sehr wohl eingesammelt (`toc_nodes.extend(sub_tocs)`). Ergebnis: **Das Inhaltsverzeichnis verweist auf Inhalte, die im Dokument nicht existieren.**

Reproduktion am mitgelieferten Handbuch — `04_1_chapters_and_hierarchy.md` ist in `manual/de/markpublish.yaml` als Unterkapitel von Kapitel 4 konfiguriert:

```
$ grep -c "Um ein Unterkapitel zu definieren" manual/de/markpublish_benutzerhandbuch.html
0                                    # Fließtext des Unterkapitels: fehlt komplett

$ grep -c 'id="kapitel-unterkapitel-und-parts"' manual/de/markpublish_benutzerhandbuch.html
0                                    # Sprungziel existiert nicht

# ... obwohl das TOC drei Einträge dorthin verlinkt:
4.2   Kapitel, Unterkapitel und Parts     -> toter Link
4.2.1 Kapitel-Definition                  -> toter Link
4.2.2 Hierarchische Unterkapitel          -> toter Link
```

Dasselbe im Beispielprojekt (`examples/quickstart`, `02_1_details.md`) und im `init`-Scaffold, das die CLI selbst erzeugt. Das Feature ist im Handbuch dokumentiert (Kapitel 4.2) und funktioniert nicht.

**Empfehlung:** Rekursives Rendering in beiden Layouts. Sauberste Variante ist ein Jinja-Makro mit Selbstaufruf, das gleichzeitig C1 und die einstufige Part-Verschachtelung löst:

```jinja
{% macro render_item(item) %}
  <article class="chapter-article">
    {% if item.divider_page %}{% with chapter = item %}{% include "chapter_divider.html" %}{% endwith %}{% endif %}
    <div class="chapter-body">{{ item.html_content | safe }}</div>
  </article>
  {% for child in item.children %}{{ render_item(child) }}{% endfor %}
{% endmacro %}
```

Ergänzend ein Test, der ein Dokument mit Unterkapitel rendert und den Fließtext des Kindes in der Ausgabe erwartet.

---

### C2 — Kopfzeile jedes PDFs enthält ein Fremdzeichen statt des Zeilenumbruchs

**Datei:** [pdf/default/styles.css:25](src/markpublish/templates/pdf/default/styles.css#L25)
**Status: bestätigt via Textextraktion aus dem PDF**

```css
@top-right {
  content: "v{{ document.version }}\A{{ document.date }}";
}
```

`\A` ist in CSS keine feste Escape-Sequenz für „Zeilenumbruch", sondern der Beginn eines **Hex-Escapes von bis zu sechs Ziffern**. Der Parser liest gierig weiter. Bei der Datumsangabe `31.08.2026` entsteht dadurch `\A31` → **U+0A31 (ORIYA LETTER RRA)**, gefolgt von `.08.2026`.

Extrahiert aus `manual/de/markpublish_benutzerhandbuch.pdf`, Seite 19:

```python
'v1.0.0\u0a31.08.2026'
#        ^^^^^^ statt '\n' + '31'
```

Sichtbar auf **jeder Seite jedes erzeugten PDFs** als Tofu-Kästchen: `v1.0.0□08.2026`. Zusätzlich geht der beabsichtigte Zeilenumbruch verloren, wodurch das zweizeilige Header-Layout (das explizite Feature) nicht greift.

Betroffen sind alle Datumsformate, die mit einer Hex-Ziffer beginnen — also `%d.%m.%Y` **und** `%Y-%m-%d`, d. h. beide von `format_current_date()` erzeugten Varianten. Immer.

Zeile 12 (`...\A" string(...)`) ist zufällig korrekt, weil das Anführungszeichen das Escape terminiert. Zeile 41 funktioniert nur, solange `copyright` mit `©` beginnt — bei einem Copyright-String, der mit einer Ziffer anfängt (`2026 Firma GmbH`), bricht auch die Fußzeile.

**Fix:** Escape mit einem Leerzeichen terminieren (das Leerzeichen wird dabei konsumiert, nicht ausgegeben) — oder die volle 6-stellige Form verwenden:

```css
content: "v{{ document.version }}\A {{ document.date }}";   /* \A + Space */
content: "v{{ document.version }}\00000A{{ document.date }}"; /* alternativ */
```

Alle drei `\A`-Vorkommen in der Datei angleichen, nicht nur Zeile 25.

---

### C3 — Das Inhaltsverzeichnis enthält keine Seitenzahlen

**Datei:** [pdf/default/styles.css:382-384](src/markpublish/templates/pdf/default/styles.css#L382-L384)
**Status: bestätigt via isoliertem WeasyPrint-Testfall**

```css
.toc-page-number::after {
  content: target-counter(attr(href), page);
}
```

`attr(href)` liest das Attribut **des Elements, auf dem die Eigenschaft steht**. `.toc-page-number` ist ein leeres `<span>` *innerhalb* des `<a class="toc-link">`; das `href` liegt beim Vorfahren. `attr(href)` ist damit leer, `target-counter()` schlägt fehl und erzeugt nichts.

Sichtbare Folge: Das Inhaltsverzeichnis zeigt Titel und Führungspunkte, die ins Leere laufen — ohne eine einzige Seitenzahl. Für ein Druckdokument ist das TOC damit unbrauchbar. Gleiches gilt für die Kapitel-Mini-TOCs auf den Trennseiten.

Isolierter Nachweis (WeasyPrint 69.0, identische Struktur, Textextraktion aus dem Ergebnis):

```
Regel auf dem <span>  (aktuell) -> 'Kapitel A\nKapitel B'
Regel auf dem <a>     (Fix)     -> 'Kapitel A\n2\nKapitel B\n3'
```

**Fix:** Die Regel auf das Element verschieben, das das `href` trägt:

```css
.toc-link::after {
  content: target-counter(attr(href), page);
  font-variant-numeric: tabular-nums;
  font-weight: 500;
}
```

Das leere `<span class="toc-page-number">` in `toc.html` und `chapter_divider.html` entfällt dann. Alternativ `attr(href)` auf dem `<a>` in eine CSS-Variable schreiben — die `::after`-Variante ist aber einfacher und robuster.

---

### C4 — `Union` wird in `resolver.py` verwendet, aber nicht importiert

**Datei:** [templates/resolver.py:30,64,121](src/markpublish/templates/resolver.py#L30) (Import in Zeile 10)
**Status: bestätigt**

```python
from typing import Dict, List, Optional, Tuple      # Union fehlt
...
def get_common_templates_dir(custom_dir: Optional[Union[str, Path]] = None, ...)
```

Nur `from __future__ import annotations` verhindert den sofortigen Absturz — Annotationen bleiben Strings und werden nie ausgewertet. Sobald jemand sie auflöst, knallt es:

```python
>>> typing.get_type_hints(resolver.resolve_template_path)
NameError: name 'Union' is not defined
```

Das trifft Pydantic-`validate_call`, FastAPI-Wrapper, `inspect.signature(..., eval_str=True)`, viele Doku-Generatoren und Typer selbst, falls diese Funktionen jemals als Kommando gebunden werden. Latent, aber trivial zu beheben.

**Fix:** `Union` in den Import aufnehmen. Da `requires-python = ">=3.10"` gilt, wäre `str | Path | None` die modernere Schreibweise. Ein `mypy`- oder `ruff`-Lauf in CI fängt diese Klasse von Fehlern generell ab.

---

## Hoch

### H1 — HTML-Ausgabe enthält absolute `file:///`-Pfade für Bilder

**Dateien:** [markdown/assets.py:28](src/markpublish/markdown/assets.py#L28), [renderers/base.py:80](src/markpublish/renderers/base.py#L80), [engine.py:248](src/markpublish/markdown/engine.py#L248)
**Status: bestätigt**

`rewrite_html_asset_paths()` wird in `_process_chapter()` unabhängig vom Zielformat aufgerufen und ersetzt jedes relative `<img src>` durch `asset_file.as_uri()`. Für WeasyPrint ist das sinnvoll; für die HTML-Ausgabe zerstört es die Portabilität:

```html
<img alt="Bild" src="file:///C:/Users/Frank/.../chapters/pic.svg">
```

Diese HTML-Datei lässt sich nicht verschicken, nicht ausliefern und nicht auf einem anderen Rechner öffnen — die Bilder fehlen überall außer auf der Build-Maschine. Betrifft auch Nicht-SVG-Assets in `asset_url()` (Logos auf dem Cover).

Im Handbuch fällt es nur deshalb nicht auf, weil es keine Bilder enthält (`grep -c 'file:///' → 0`).

**Empfehlung:** `DocumentContext.target` bis in die Pipeline durchreichen und fallunterscheiden — für PDF absolute URIs, für HTML relative Pfade zur Ausgabedatei (oder Data-URIs für ein wirklich standalone-Dokument). Da `HTMLRenderer` bewusst eine einzelne Datei erzeugt, wären Data-URIs die konsistentere Wahl.

---

### H2 — `toc: {enabled: false}` wird ignoriert

**Dateien:** [config/models.py:80-91](src/markpublish/config/models.py#L80-L91), [engine.py:264](src/markpublish/markdown/engine.py#L264)
**Status: bestätigt**

Der Validator wandelt `{"enabled": False, ...}` in ein `ChapterTOCConfig(enabled=False)` um. Der Konsument prüft aber nur die Wahrheit des Objekts:

```python
if toc_config:          # ChapterTOCConfig ist als BaseModel IMMER truthy
```

```python
>>> ci = ChapterItem(file="a.md", toc={"enabled": False, "max_depth": 3})
>>> ci.toc, bool(ci.toc)
(ChapterTOCConfig(enabled=False, max_depth=3), True)
```

Das dokumentierte Feld `enabled` hat also keinerlei Wirkung — nur die Kurzform `toc: false` (die der Validator zu `False` auflöst) schaltet ab. Dieselbe Prüfung steht auch in `chapter_divider.html:12`.

Randfall gleicher Ursache: `toc: 0` erzeugt `ChapterTOCConfig(enabled=True, max_depth=0)` → truthy → leeres TOC-Kästchen mit Überschrift, aber ohne Einträge.

**Fix:** Entweder `__bool__` auf `ChapterTOCConfig` definieren (`return self.enabled and self.max_depth > 0`) oder alle Prüfstellen auf `toc_config and toc_config.enabled` umstellen. Ersteres ist weniger fehleranfällig, weil es auch die Templates automatisch korrigiert.

---

### H3 — Alert-Syntax in Code-Blöcken wird zerstört

**Datei:** [markdown/alerts.py:104](src/markpublish/markdown/alerts.py#L104)
**Status: bestätigt**

`GitHubAlertsPreprocessor` ist mit Priorität **27** registriert. `fenced_code` / `pymdownx.superfences` laufen bei **25**, also *später*. Der Alerts-Preprocessor sieht den Quelltext ungefiltert und ersetzt auch Zeilen innerhalb von Code-Fences.

```python
>>> eng.convert('```markdown\n> [!NOTE]\n> Hinweistext\n```')
'<div class="highlight"><pre><code>!!! note "Hinweis"\n    Hinweistext\n</code></pre></div>'
```

Erwartet wäre der wörtliche Text `> [!NOTE]`. Jede Dokumentation, die die eigene Alert-Syntax in einem Code-Block zeigt, wird still verfälscht — genau der Fall, den `manual/de/chapters/06_markdown_features.md` beschreibt (dort aktuell nur nicht als Code-Block gesetzt, deshalb noch unauffällig).

**Fix:** Priorität unter 25 setzen (z. B. 24) — dann sind Fences bereits als Platzhalter extrahiert. Alternativ im Preprocessor selbst einen Fence-Zustand mitführen. Die Prioritätsänderung ist die kleinere und robustere Änderung; ein Regressionstest mit Alert-in-Fence gehört dazu.

---

### H4 — `sane_lists` fehlt: Nummerierte Listen verlieren ihre Nummerierung

**Datei:** [markdown/engine.py:69-84](src/markpublish/markdown/engine.py#L69-L84)
**Status: bestätigt**

Ohne die `sane_lists`-Extension verschmilzt Python-Markdown eine `ol`, die direkt auf eine `ul` folgt, in die vorhergehende Liste:

```python
>>> eng.convert("- eins\n- zwei\n\n1. a\n2. b\n")
'<ul><li>eins</li><li><p>zwei</p></li><li><p>a</p></li><li>b</li></ul>'
```

Aus `1.` / `2.` werden Aufzählungspunkte in der Vorgängerliste — die Nummerierung ist weg, die Semantik ebenso. Für ein Publishing-Tool, dessen Kernaufgabe die getreue Wiedergabe von Markdown ist, ist das eine substanzielle Abweichung von der Erwartung. Der Effekt ist in PDF und HTML identisch reproduzierbar.

**Fix:** `"sane_lists"` in beide Extension-Listen aufnehmen (siehe auch M6 zur Duplizierung). Nebeneffekt: `sane_lists` verlangt für verschachtelte Listen konsistente Einrückung — das sollte im Changelog stehen.

---

### H5 — Doppelte `id`-Attribute in jedem Kapitel

**Dateien:** [html/default/layout.html:48,55,68](src/markpublish/templates/html/default/layout.html#L48), [engine.py:259](src/markpublish/markdown/engine.py#L259)
**Status: bestätigt**

`ContentItem.slug` wird aus der ersten Überschrift des Kapitels abgeleitet (`toc_nodes[0].slug`). Dieselbe Überschrift trägt bereits ihr eigenes `id`. Das Layout setzt den Slug ein zweites Mal auf das umschließende `<article>`:

```
$ grep -o 'id="[^"]*"' manual/de/markpublish_benutzerhandbuch.html | sort | uniq -c | awk '$1>1'
  2 id="einfuhrung-architektur"
  2 id="installation-schnellstart"
  ... (8 Kapitel, jeweils doppelt)
```

Ungültiges HTML. Praktisch fällt es kaum auf, weil beide Elemente unmittelbar benachbart sind, aber `document.getElementById`, Anker-Navigation und Screenreader treffen jeweils nur das erste. Auch `NumberingContext.unique_slug()` — das für Eindeutigkeit gebaut wurde — wird hier umgangen.

**Fix:** Dem Container einen eigenen Namensraum geben (`id="chapter-{{ item.slug }}"`) oder das `id` am `<article>` weglassen und im TOC direkt auf die Überschrift verlinken (das TOC tut das ohnehin bereits).

---

### H6 — Ausgabedateiname wird ungeprüft aus dem Dokumenttitel gebildet

**Datei:** [cli.py:155](src/markpublish/cli.py#L155)
**Status: bestätigt**

```python
doc_slug = config.document.title.lower().replace(" ", "_")
```

Nur Leerzeichen werden behandelt. Titel mit `/`, `\`, `:`, `?`, `*` oder `<`/`>` — bei Berichten völlig üblich — erzeugen ungültige oder verirrte Pfade:

```python
"Report: Q3/2026 <final>"  ->  'report:_q3/2026_<final>'
```

Unter Windows scheitert das mit `OSError`, unter POSIX schreibt `/` die Datei in ein Unterverzeichnis (bzw. schlägt fehl, wenn es nicht existiert). Ein führendes `../` im Titel wäre ein Pfad-Traversal beim Schreiben.

Bemerkenswert: Das Projekt besitzt bereits eine passende Funktion — `toc.slugify()` in [toc.py:21](src/markpublish/markdown/toc.py#L21) — sie wird hier nur nicht verwendet.

**Fix:** `slugify(config.document.title)` verwenden und auf einen Fallback (`"document"`) zurückfallen, wenn das Ergebnis leer ist. `slugify` liefert das bereits (`return text or "section"`).

---

## Mittel

### M1 — Kapitel-Mini-TOC listet das Kapitel selbst auf

[engine.py:270](src/markpublish/markdown/engine.py#L270) — `local_toc_items` filtert nur nach `max_depth`, schließt aber die H1 des Kapitels nicht aus. Auf der Trennseite steht der Kapiteltitel dadurch zweimal: einmal als große Überschrift, direkt darunter als erster Eintrag von „Inhalt dieses Kapitels" (verifiziert auf Seite 6 des Handbuchs: *2 Installation & Schnellstart* als erster TOC-Eintrag unter der Überschrift *Installation & Schnellstart*). Filter auf `n.level > eigenes_level` ergänzen.

### M2 — `max_depth` ist absolut, nicht kapitelrelativ

[engine.py:270](src/markpublish/markdown/engine.py#L270) — `n.level` enthält bereits den `base_level_offset`. Für ein Unterkapitel (`base_level=2`) verschiebt sich damit die Bedeutung von `toc: 2`: Die H2 des Kindes liegt auf Level 3 und fällt aus dem Filter. `max_depth` sollte gegen `n.level - base_level_offset` geprüft werden. (Derzeit maskiert von C1 — Unterkapitel werden ohnehin nicht gerendert.)

### M3 — HTML-Theme hat gar kein Kapitel-TOC

[html/default/chapter_divider.html](src/markpublish/templates/html/default/chapter_divider.html) — die `local-toc`-Sektion existiert nur im PDF-Theme. Die Konfiguration `toc: 2` bleibt in der HTML-Ausgabe wirkungslos, ohne Hinweis. Entweder nachziehen oder in der Dokumentation als PDF-only kennzeichnen.

### M4 — `list_templates()` liefert Duplikate

[resolver.py:133-134](src/markpublish/templates/resolver.py#L133-L134) — beide `sources`-Einträge zeigen auf denselben Pfad, sobald `~/.markpublish/templates` existiert (dann gibt `get_user_templates_dir()` genau diesen zurück). Die Schleife hängt pro Fund unbedingt eine Zeile an; `seen` steuert nur `is_active`. Ergebnis: jedes User-Template erscheint zweimal in `markpublish templates`, das zweite Mal als „nicht aktiv". Vor der Schleife über `dict.fromkeys()` deduplizieren.

### M5 — `load_config()` mutiert das übergebene Dictionary

[loader.py:54-59](src/markpublish/config/loader.py#L54-L59) — `raw_data.get("document")` liefert bei Dict-Eingabe eine Referenz; `doc["date"] = ...` schreibt in das Objekt des Aufrufers zurück:

```python
>>> d = {"document": {"title": "T", "date": "auto"}}
>>> load_config(d); d
{'document': {'title': 'T', 'date': '31.08.2026'}}   # 'auto' überschrieben
```

Für eine Funktion mit reiner Lade-/Validierungssemantik überraschend. `copy.deepcopy(raw_data)` vor der Bearbeitung.

### M6 — Extension-Listen doppelt gepflegt

[engine.py:22-51](src/markpublish/markdown/engine.py#L22-L51) vs. [engine.py:67-84](src/markpublish/markdown/engine.py#L67-L84) — `DEFAULT_MARKDOWN_EXTENSIONS` ist toter Code (nirgends referenziert) und dupliziert `_build_default_extensions()` Eintrag für Eintrag. Zwei Quellen der Wahrheit, die zwangsläufig auseinanderlaufen — H4 ist an genau **einer** von beiden zu beheben, was leicht übersehen wird. Konstante entfernen oder die Methode daraus ableiten.

Kleiner Nebenpunkt derselben Stelle: `self.extensions = extensions or self._build_default_extensions(...)` — ein bewusst leeres `extensions=[]` fällt still auf die Defaults zurück. `if extensions is None` wäre korrekt.

### M7 — GTK-Initialisierung mit globalem Seiteneffekt beim Import

[renderers/pdf.py:14-41](src/markpublish/renderers/pdf.py#L14-L41) — `_init_windows_gtk()` läuft beim Import des Moduls und schreibt in `os.environ["PATH"]`. Für eine importierbare Bibliothek ist das eine unerwartete globale Mutation. Die Prüfung `if str(p) not in os.environ.get("PATH", "")` ist zudem ein Substring-Test: Ein PATH-Eintrag, der den Kandidaten als Präfix enthält, unterdrückt das Hinzufügen fälschlich. Besser lazy in `PDFRenderer.render()` und Vergleich über `os.pathsep`-getrennte, normalisierte Pfade.

*(Anmerkung: Der Mechanismus funktioniert — der Fallback auf `C:\Program Files\darktable\bin` hat auf diesem System die Handbuch-Builds ermöglicht.)*

### M8 — `pygments_style` ist wirkungslos, Token-Abdeckung lückenhaft

[engine.py:43-44](src/markpublish/markdown/engine.py#L43-L44) — mit `noclasses: False` erzeugt Pygments CSS-Klassen; `pygments_style: "github-dark"` hat dann **keine** Wirkung. Die tatsächlichen Farben stehen handgeschrieben in [styles.css:418-425](src/markpublish/templates/pdf/default/styles.css#L418-L425) — und zwar in der GitHub-**Light**-Palette. Die Konfiguration behauptet also das Gegenteil dessen, was passiert.

Zusätzlich decken die acht handgepflegten Regeln nur einen Teil der Token-Klassen ab; `.o` (Operator), `.p` (Punktuation), `.l`, `.err`, `.gd`/`.gi` (Diff) fehlen und rendern in der Standard-Textfarbe. Empfehlung: `pygmentize -S github-light -f html -a .highlight` erzeugen und einbinden, den irreführenden Konfigurationswert entfernen.

---

## Niedrig

### N1 — `HEADING_REGEX` verträgt kein `>` in Attributwerten
[toc.py:14-17](src/markpublish/markdown/toc.py#L14-L17) — `<h([1-6])([^>]*)>` bricht bei `<h2 title="a > b">`. Über `attr_list` erreichbar. Selten, aber die Folge wäre stille Fehlverarbeitung.

### N2 — Überflüssiges Leerzeichen im Heading-Tag
[toc.py:172](src/markpublish/markdown/toc.py#L172) — `f'<h{orig_level} {attrs}>'` erzeugt bei leeren `attrs` ein `<h2 >`. Kosmetisch.

### N3 — Kollisionsrisiko zwischen expliziten und generierten Slugs
[toc.py:148-155](src/markpublish/markdown/toc.py#L148-L155) — ein vorhandenes `id` wird erst *nachträglich* in `used_slugs` aufgenommen. Ein per `attr_list` gesetztes `{#einleitung}`, das nach einer bereits generierten `einleitung` kommt, erzeugt ein Duplikat. Ein Vorlauf über alle expliziten IDs würde das ausschließen.

### N4 — `slugify()` transliteriert Umlaute nicht sprachgerecht
[toc.py:21-27](src/markpublish/markdown/toc.py#L21-L27) — NFKD + ASCII-Encode macht aus `Anhänge` → `anhange` statt `anhaenge`. Für ein primär deutschsprachiges Werkzeug (Default-Sprache `de`, deutsches Handbuch) sind die Anker damit systematisch unschön. Eine kleine Ersetzungstabelle vor der Normalisierung genügt.

### N5 — `.gitignore`: erledigt, mit Restposten
[.gitignore:33-36](.gitignore#L33-L36) — Ursprünglicher Befund: `*.pdf` und `*.html` waren global ausgeschlossen, wodurch `manual/de/markpublish_benutzerhandbuch.pdf` und `examples/quickstart/*.html` **nicht** eingecheckt waren — wer das Repo klonte, fand Handbuch und Showcase nicht vor.

**Während dieses Reviews behoben** (beide Muster entfernt, `git check-ignore` meldet die Dateien nicht mehr). Übrig bleibt die verwaiste Ausnahme `!src/markpublish/templates/**/*.html` in Zeile 36 — sie negiert nichts mehr und kann entfallen.

---

## Testabdeckung

17 Tests, alle grün — aber keiner der vier kritischen Befunde wird erfasst. Die Ursache ist ein durchgehendes Muster: **Die Tests prüfen, dass etwas erzeugt wurde, nie was darin steht.**

```python
assert pdf_out.stat().st_size > 1000    # test_renderers.py:85
assert "Einleitung" in html_text        # steht auch im TOC — sagt nichts über den Rumpf
```

Besonders aufschlussreich: `test_cli_init_and_build` baut das `init`-Scaffold, das ein verschachteltes Unterkapitel enthält (`02_1_details.md`), und prüft ausschließlich `.is_file()`. Der Test durchläuft C1 bei jedem Lauf, ohne ihn sehen zu können.

Vorschläge, nach Nutzen sortiert:

1. **Rumpf-Assertions statt Existenz-Assertions.** Eindeutige Textmarker pro Kapitel im Fixture setzen und deren Vorkommen in der Ausgabe prüfen — fängt C1 sofort.
2. **PDF-Textextraktion im Test.** `pypdfium2` (Dev-Dependency, wenige MB) macht C2 und C3 direkt prüfbar: `assert "\u0a31" not in text`, `assert re.search(r"Inhaltsverzeichnis[\s\S]*?\b\d+\b", text)`.
3. **Anker-Integrität.** Jedes `href="#…"` in der HTML-Ausgabe muss ein passendes `id` haben; `id`-Werte müssen eindeutig sein. Deckt C1 und H5 in einem Test ab.
4. **Markdown-Golden-Tests** für Tasklisten, Alerts-in-Fences (H3), `ol` nach `ul` (H4).
5. **`mypy` oder `ruff` in CI** — fängt C4 und dessen Verwandte statisch.

---

## Umgesetzte Änderung: Checkbox-Darstellung

Im Rahmen dieses Reviews bereits behoben (siehe `git diff`):

**Vorher:** Tasklisten rendern im PDF als schwarzes Quadrat oder Leerkästchen, jeweils auf einer **eigenen Zeile**, der Aufgabentext darunter eingerückt.

**Ursache:** `pymdownx.tasklist` läuft mit `custom_checkbox: True` und liefert `<label class="task-list-control"><input type="checkbox" [checked]><span class="task-list-indicator"></span></label>`. Dieses Markup ist ausdrücklich dafür gedacht, per CSS gestaltet zu werden — beide Themes hatten dafür jedoch **keine Regeln** (das HTML-Theme enthielt überhaupt keine Tasklisten-Styles). Damit rendert WeasyPrint das native Widget aus seinem UA-Stylesheet, und dort steht `input { display: block }` ([html5_ua.css:176](.venv/Lib/site-packages/weasyprint/css/html5_ua.css#L176)) — daher der Zeilenumbruch, und `input[checked]::before { background: black }` — daher das schwarze Quadrat.

**Änderungen:**

| Datei | Änderung |
| :--- | :--- |
| `templates/pdf/default/assets/icons/checkbox-check.svg` | neu — weißes Häkchen im Octicon-Stil der bestehenden Icons |
| `templates/html/default/assets/icons/checkbox-check.svg` | neu — identisch |
| `templates/pdf/default/styles.css` | Tasklisten-Block ersetzt |
| `templates/html/default/styles.css` | Tasklisten-Block ergänzt (vorher nicht vorhanden) |

Das native `<input>` wird ausgeblendet, `.task-list-indicator` als 3,1 mm großes, abgerundetes Kästchen gestaltet. Der Zustand kommt über den Attributselektor `input[type="checkbox"][checked] + .task-list-indicator` — statisch und ohne Abhängigkeit von `:checked`-Unterstützung im PDF-Renderer; das HTML-Theme führt `:checked` zusätzlich für interaktive Fälle. Farben aus der bestehenden Palette (`#2563eb` Akzent, `#94a3b8` Rahmen), das Häkchen als Data-URI über den vorhandenen `asset_url()`-Mechanismus — konsistent mit den Admonition-Icons.

Layout: `li.task-list-item` mit `position: relative` und 6 mm Textgutter, die Box absolut positioniert. Dadurch stimmt der hängende Einzug — Folgezeilen umbrechender Aufgaben richten sich am Text aus, nicht an der Box. Verschachtelte Tasklisten erben den Gutter des Eltern-`<li>` (`padding-left: 0`), sodass eine Kind-Checkbox exakt unter dem Text des Elternteils sitzt; es entsteht ein sauberes 6-mm-Raster über alle Ebenen.

**Verifiziert** an einem Stresstest-Dokument (einfach, mehrzeilig umbrechend, drei Verschachtelungsebenen, gemischt mit normalen Listen, mit Inline-Formatierung) in **beiden** Ausgabeformaten — PDF über Rasterisierung, HTML über Headless-Chrome-Screenshot. Handbuch und Beispielprojekt wurden neu gebaut, `pytest` bleibt grün (17 passed).

---

## Empfohlene Reihenfolge

1. **C2, C3** — reine CSS-Korrekturen, wenige Zeilen, sofort in jedem Dokument sichtbar.
2. **C1** — Rekursion in beiden Layouts; behebt Datenverlust und tote TOC-Links.
3. **C4, H6** — Einzeiler.
4. **H2, H4, H3** — Konfiguration bzw. Extension-Priorität, jeweils lokal begrenzt.
5. **H1, H5** — brauchen eine kleine Designentscheidung (Zielformat-Weitergabe, ID-Schema).
6. **Testabdeckung** (Punkte 1–3 oben) — verhindert Rückfälle bei allen genannten Befunden.
7. Mittel/Niedrig nach Gelegenheit.
