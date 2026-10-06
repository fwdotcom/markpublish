# Release-Schritte

Bereitet ein Release vor: Version eintragen, Changelog abschließen, Handbücher und Showcase-Assets bauen, Linter
und Tests ausführen. Committet, getaggt und veröffentlicht wird nicht; das bleibt Handarbeit.

`release.py`, `lib/` und die Schritte stammen aus dem Grundschutz++ Explorer und sollen dort und hier gleich
bleiben. Projektspezifisch ist nur `release.toml`.

```
release.py     Runner: führt die Schritte aus steps/ der Reihe nach aus
release.toml   Projektkonfiguration, ein Abschnitt je Schritt
steps/         die Schritte, je eine Datei NN-name.py
lib/           gemeinsame Bausteine
```

Voraussetzung ist Python ab 3.11 und `pip install -e ".[dev]"`.

## Aufruf

```sh
python scripts/release/release.py 2.4.0                    # alle Schritte
python scripts/release/release.py 2.4.0 --skip commands    # ohne Bauen und Tests
python scripts/release/release.py --only commands          # nur Bauen und Tests
python scripts/release/release.py --list                   # Schritte anzeigen
```

Danach die Änderungen prüfen (`git status`, `git diff`), committen und das Release `v<VERSION>` auf GitHub
veröffentlichen.

## Die Schritte

| Schritt       | Zweck                                                                     |
| ------------- | ------------------------------------------------------------------------- |
| `10-version`  | Version prüfen und in `pyproject.toml`, `__init__.py` und allen `markpublish.yaml` eintragen |
| `20-changelog` | Überschrift `## [Unreleased]` zu `## [<VERSION>] - <Datum>` machen       |
| `40-commands` | `build_manuals.py`, `build_showcase_assets.py`, `ruff`, `pytest`          |

Die neuen Einträge im Changelog stehen unter `## [Unreleased]`; ohne diese Überschrift bricht der Schritt ab.
Einzelheiten stehen jeweils am Anfang der Datei.

## Wie die Schritte laufen

- Ein Schritt ist eine Datei `steps/NN-name.py`; die Reihenfolge ergibt sich aus der Zahl. Abschalten durch
  Umbenennen (z. B. `40-commands.py.off`), hinzufügen durch eine neue Datei.
- Jeder Schritt läuft als eigener Prozess im Projektordner. Endet einer mit einem Fehler, bricht das Release ab.
- Seine Parameter liest jeder Schritt aus dem Abschnitt von `release.toml`, der seinem Dateinamen ohne Nummer
  entspricht. Einzelne Werte lassen sich per Umgebung überschreiben: `RELEASE_<ABSCHNITT>_<SCHLÜSSEL>`.
- Jeder Schritt lässt sich auch direkt aufrufen, z. B. `python scripts/release/steps/10-version.py 2.4.0`.
