# Code- und Dokumentations-Review markpublish - 01.09.2026

**Bezug auf Vorreview:** [docs/reviews/2026-08-31_code-review.md](docs/reviews/2026-08-31_code-review.md)
**Stand:** Workspace-Stand am 01.09.2026 (HEAD `ea5b15c`)
**Umfang:** `src/markpublish/**`, `README.md`, `src/markpublish/manual/**`, `tests/**`
**Methodik:** statische Durchsicht, gezielte Reproduktion per `CliRunner`/Python-Snippet, Projektchecks
**Verifikation:** `pytest` (178 passed), `ruff check src tests` (clean)

---

## Findings (priorisiert)

### M1 - `--output` behandelt nicht existierende Verzeichnisse als Datei

**Datei:** [src/markpublish/cli.py](src/markpublish/cli.py#L231)
**Schweregrad:** Mittel

**Befund**

Die Ausgabe-Pfadauflosung entscheidet nur uber `output.is_dir()` oder ein String-Suffix (`/` bzw. `\\`). Bei `Path` geht das Suffix verloren (`Path("dist/") -> "dist"`). Ein nicht existentes Zielverzeichnis wird dadurch als Dateiname interpretiert.

**Reproduktion**

`build ... --output <tmp>/dist` erzeugt eine Datei `dist` statt ein Verzeichnis mit `out_dir_test.pdf`:

- Exit: `0`
- `dist exists True`
- `is_file True`
- `is_dir False`

**Risiko**

Das Verhalten widerspricht der CLI-Hilfe („Custom output file or directory path."). Nutzer erhalten je nach Existenzzustand des Pfads unterschiedliche Semantik.

**Empfehlung**

Die Semantik eindeutig machen, z. B.:

1. explizite Option `--output-dir` einfuhren (robusteste Variante), oder
2. bei fehlender Endung plus Einzel-Target konsistent als Verzeichnis behandeln und bei Mehrdeutigkeit mit klarer Fehlermeldung abbrechen.

Mindestens ein Regressionstest in [tests/test_cli.py](tests/test_cli.py) sollte den Fall „nicht existentes Output-Verzeichnis“ absichern.

---

### M2 - README widerspricht sich zur Template-Verzeichnisstruktur

**Datei:** [README.md](README.md#L170)
**Schweregrad:** Mittel (Dokumentation)

**Befund**

Im README stehen zwei widerspruchliche Aussagen:

- korrekt: `templates/<theme>/pdf` und `templates/<theme>/html` ([README.md](README.md#L17))
- widerspruchlich im Baum: `templates/pdf/default` bzw. `templates/html/default` ([README.md](README.md#L170))

Code und Tests bestatigen eindeutig `theme/target`:

- [src/markpublish/templates/resolver.py](src/markpublish/templates/resolver.py#L108)
- [tests/test_templates.py](tests/test_templates.py#L27)

**Risiko**

Nutzer legen Custom-Themes an der falschen Stelle ab und erhalten `Template ... not found` trotz „scheinbar richtiger“ Struktur.

**Empfehlung**

README-Baum auf `templates/<theme>/<target>` korrigieren und kurz einen Hinweis auf die auflosungsrelevante Struktur (`<base>/<theme>/<target>`) direkt am Baum lassen.

---

### N1 - Versionierte Build-Artefakte lokal als geloscht markiert

**Dateien:** `manual/markpublish_benutzerhandbuch.html`, `manual/markpublish_benutzerhandbuch.pdf`
**Schweregrad:** Niedrig (Repository-Hygiene)

**Befund**

Im Arbeitsbaum sind beide getrackten Artefakte als geloscht markiert (`git status --short`), historisch zuletzt in Commit `711c0ee`.

**Risiko**

Je nach Teamprozess kann das beabsichtigt (aktualisieren/entfernen) oder versehentlich sein. Ohne klare Konvention entsteht vermeidbares Diff-Rauschen bei inhaltlichen Anderungen.

**Empfehlung**

Kurz festlegen, ob diese Artefakte weiterhin versioniert werden sollen. Falls ja: bei Doku-Anderungen konsistent mitbauen; falls nein: einmalig aus Historie/Buildprozess bereinigen und im Beitragendenleitfaden dokumentieren.

---

## Delta zum Review vom 31.08.2026

Die im Vorreview priorisierten Kernprobleme sind im aktuellen Stand nachvollziehbar adressiert:

1. Rekursives Kapitel-Rendering vorhanden ([src/markpublish/templates/default/pdf/layout.html](src/markpublish/templates/default/pdf/layout.html#L71)).
2. TOC-Seitenzahlen kommen uber den Link-Kontext (`.toc-link::after`) ([src/markpublish/templates/default/pdf/styles.css](src/markpublish/templates/default/pdf/styles.css#L494)).
3. Fehlender `Union`-Import ist behoben ([src/markpublish/templates/resolver.py](src/markpublish/templates/resolver.py#L10)).
4. Dateinamensbildung nutzt `slugify(..., separator="_")` ([src/markpublish/cli.py](src/markpublish/cli.py#L229)).

Gesamtbild: keine neuen kritischen Befunde, Test- und Lint-Basis deutlich starker als im Stand vom 31.08.

---

## Offene Fragen / Annahmen

1. Soll die CLI weiterhin eine einzelne `--output`-Option fur Datei **und** Verzeichnis tragen, oder ist eine Trennung in `--output-file` / `--output-dir` gewunscht?
2. Sind die Handbuch-Artefakte unter `manual/` bewusst Bestandteil des Repos?

---

## Kurzfazit

Seit dem Review vom 31.08. ist die Qualitat deutlich angezogen (insbesondere Absicherung uber Tests). Aktuell sind vor allem zwei mittelgrose Nacharbeiten sinnvoll: eindeutige `--output`-Semantik in der CLI und Konsistenzkorrektur in der README-Template-Struktur.