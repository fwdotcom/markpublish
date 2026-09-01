# Code- und Dokumentations-Review markpublish — 01.09.2026

**Bezug auf Vorreviews:**
- [docs/reviews/2026-09-01_code-review.md](2026-09-01_code-review.md)
- [docs/reviews/2026-08-31_code-review.md](2026-08-31_code-review.md)

**Stand:** Workspace-Stand am 01.09.2026 (Abschlussprüfung)  
**Umfang:** `src/markpublish/**`, `tests/**`, `README.md`, `examples/**`, Dokumentationen (`src/markpublish/docs/manual/{de,en}` & `src/markpublish/docs/cheatsheet/{de,en}`)  
**Prüfmethodik:** Statische Code- und Doku-Analyse, Verifikation der CLI-Befehle, Testsuite & Code Coverage (`pytest --cov`), Linter (`ruff check`).  
**Verifikationsergebnis:** `pytest` 197 passed (100%), Testabdeckung **88%**, `ruff` clean (0 Linter-Meldungen).

---

## 1. Bearbeitungsstand & Nachverfolgung

Alle identifizierten Punkte wurden umgesetzt und getestet:

| ID | Thema / Bereich | Status | Details |
| :--- | :--- | :--- | :--- |
| **M1** | Handbuch YAML-Spec: Syntax `toc: "none"` | **Behoben** | In `manual/de` und `manual/en` ([`07_appendix_yaml_spec.md`](../src/markpublish/docs/manual/de/chapters/07_appendix_yaml_spec.md)) auf `document_toc: "none"` korrigiert (bewusst *ohne* Alias im Code). |
| **M2** | Part-Trennseite / „Cover“ für Anhang A | **Behoben** | `break_before: "divider"` am Part `Anhänge` / `Appendices` in `markpublish.yaml` entfernt. Anhang A startet direkt auf neuer Seite ohne Part-Trennseite. |
| **M3** | CLI-Befehlstabelle in `README.md` unvollständig | **Behoben** | [`README.md`](../../README.md) um `cheatsheet`, `manual` und `labels` ergänzt. |
| **N1** | `export-template` Target-Validierung | **Behoben** | In [`cli.py`](../../src/markpublish/cli.py) auf `_parse_targets(target)` umgestellt; mit neuem Test in `tests/test_cli.py` abgesichert. |
| **N2** | Troubleshooting: Präzisierung Bild-URIs | **Behoben** | In [`08_appendix_troubleshooting.md`](../src/markpublish/docs/manual/de/chapters/08_appendix_troubleshooting.md) (DE & EN) präzisiert, dass standardmäßig Data-URIs genutzt werden. |

---

## 2. Gesamteinschätzung der Codebasis & Dokumentation

Das Projekt befindet sich in einem exzellenten, stabilen Zustand:

1. **Mehrsprachigkeit (i18n) & Systemintegration:**
   - Die 3-stufige Label-Kaskade ([`i18n.py`](../../src/markpublish/i18n.py)) mit strikter Vorab-Validierung freier Template-Texte (`validate_label_references`) fängt fehlende Übersetzungen vor dem Rendern ab.
   - Plattformübergreifende Erkennung der Nutzersprache (`detect_system_language()`) via POSIX-Umgebungsvariablen (`LANGUAGE`, `LC_ALL`, `LANG`) und Windows API (`GetUserDefaultUILanguage()`).
   - Neues CLI-Kommando `markpublish labels` macht die Kaskade transparent nachvollziehbar (`--overridden`).
2. **Autonome Dokumentenbereitstellung:**
   - Sowohl das Benutzerhandbuch (`manual`) als auch die 2-seitige Referenzkarte (`cheatsheet`) sind zweisprachig (Deutsch und Englisch) direkt im Paket gebündelt (`src/markpublish/docs`) und werden on-demand gebaut.
   - `test_cli_cheatsheet_stays_two_pages` sichert via `pypdfium2` für beide Sprachen ab, dass die Kurzreferenz exakt auf zwei Seiten bleibt.
3. **Qualitätssicherung:**
   - 197 Tests, 88% Gesamtabdeckung, alle Rendering-Pfade (PDF & HTML) und Regressionsszenarien sind automatisiert abgesichert.

