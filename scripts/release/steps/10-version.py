#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Frank Winter
# SPDX-License-Identifier: MIT
"""
Prüft die übergebene Version und trägt sie an allen Stellen des Projekts ein. Allgemein verwendbar.

Quelle ist allein die übergebene Version. Sie muss dem Format entsprechen und darf nicht älter sein als die
Versionen, die bisher im Projekt stehen.

Konfiguration [version]:
  files   Liste von {file, pattern}: alle Stellen, an denen die Version steht. pattern ist ein regulärer
          Ausdruck (mehrzeilig, ^/$ je Zeile), seine erste Klammergruppe ist die Version und wird ersetzt.
          Der erste Eintrag gilt für andere Schritte als aktuelle Version des Projekts. Ohne Einträge prüft
          der Schritt nur das Format (z. B. wenn die Version nur im Changelog steht).
  format  regulärer Ausdruck für die Version (Standard: SemVer, z. B. 1.2.0 oder 1.2.0-rc.1)
  allow_downgrade  true erlaubt eine ältere Version (Standard: false; geprüft wird nur bei SemVer)

JSON-Dateien werden nach dem Eintragen auf Gültigkeit geprüft. Geschrieben wird erst, wenn alle Stellen
gefunden sind.

Aufruf:  python scripts/release/steps/10-version.py 1.2.0
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.common import (  # noqa: E402
    SEMVER_RE,
    fail,
    info,
    load_step,
    read,
    version_key,
    version_location,
    write,
)


def main() -> None:
    step = load_step(__file__, "Version prüfen und an allen Stellen des Projekts eintragen.")
    version = step.require_version()
    fmt = step.get("format")
    if not (re.fullmatch(fmt, version) if fmt else SEMVER_RE.match(version)):
        fail(f"„{version}“ entspricht nicht dem Versionsformat {fmt or 'X.Y.Z (SemVer)'}")

    files = step.get("files", [])
    if not files:
        info(f"Version {version}: Format geprüft, keine Stellen zum Eintragen")
        return

    # Erst alle Stellen finden und prüfen, dann schreiben
    changes = []
    for entry in files:
        path, match = version_location(step, entry)
        old = match.group(1)
        if not step.get("allow_downgrade", False):
            new_key, old_key = version_key(version), version_key(old)
            if new_key is not None and old_key is not None and new_key < old_key:
                fail(f"{version} ist älter als {old} in {step.rel(path)}")
        start, end = match.span(1)
        changes.append((path, old, start, end))

    # Mehrere Einträge können dieselbe Datei betreffen: je Datei von hinten nach vorn ersetzen
    texts: dict[Path, str] = {}
    for path, _old, start, end in sorted(changes, key=lambda c: (str(c[0]), -c[2])):
        text = texts.get(path, read(path))
        texts[path] = text[:start] + version + text[end:]
    for path, text in texts.items():
        if path.suffix == ".json":
            try:
                json.loads(text)
            except json.JSONDecodeError as err:
                fail(f"{step.rel(path)} wäre danach kein gültiges JSON: {err}")
    for path, text in texts.items():
        write(path, text)
    for path, old, _, _ in changes:
        info(f"{step.rel(path)}: {old} → {version}")


if __name__ == "__main__":
    main()
