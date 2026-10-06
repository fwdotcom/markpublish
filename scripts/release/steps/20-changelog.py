#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Frank Winter
# SPDX-License-Identifier: MIT
"""
Schließt im Changelog den Abschnitt der unveröffentlichten Änderungen ab. Allgemein verwendbar.

Gesucht wird eine Überschrift wie "## [Unveröffentlicht]" oder "## Unreleased" (mit oder ohne Klammern, beliebige
Ebene, Groß-/Kleinschreibung egal). Sie wird zu "## [<VERSION>] – <Datum>". Besteht der Abschnitt der Version
schon, bleibt die Datei unverändert.

Konfiguration [changelog] (alles optional):
  file         Pfad des Changelogs (Standard: CHANGELOG.md)
  unreleased   Namen der Überschrift (Standard: ["Unveröffentlicht", "Unreleased"])
  heading      Neue Überschrift; Platzhalter {hashes}, {version}, {date}, {name}
               (Standard: "{hashes} [{version}] – {date}")
  date_format  strftime-Format für {date} (Standard: "%Y-%m-%d")
  keep_unreleased  true legt über dem neuen Abschnitt wieder eine leere Überschrift an (Standard: false)
  tag          Tag-Name für Vergleichslinks, Platzhalter {version} (Standard: "v{version}")
  allow_downgrade  true erlaubt eine ältere Version als die höchste im Changelog (Standard: false)

Vergleichslinks wie bei Keep a Changelog werden nachgezogen, wenn es sie gibt:
  [Unreleased]: https://…/compare/v1.1.0...HEAD
wird zu
  [Unreleased]: https://…/compare/v1.2.0...HEAD
  [1.2.0]: https://…/compare/v1.1.0...v1.2.0

Aufruf:  python scripts/release/steps/20-changelog.py 1.2.0
"""

from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.common import fail, info, load_step, read, version_key, write  # noqa: E402


def main() -> None:
    step = load_step(__file__, "Abschnitt der unveröffentlichten Änderungen im Changelog abschließen.")
    version = step.require_version()
    path = step.path(step.get("file", "CHANGELOG.md"))
    if not path.is_file():
        fail(f"{step.rel(path)} nicht gefunden")
    names = step.get("unreleased", ["Unveröffentlicht", "Unreleased"])
    heading = step.get("heading", "{hashes} [{version}] – {date}")
    date = datetime.date.today().strftime(step.get("date_format", "%Y-%m-%d"))
    tag = step.get("tag", "v{version}")

    text = read(path)
    if re.search(rf"^#+\s*\[?{re.escape(version)}\]?(?:\s|$)", text, re.MULTILINE):
        info(f"{step.rel(path)}: Abschnitt {version} besteht bereits")
        return

    # Nicht älter als die höchste Version, die das Changelog schon enthält (nur bei SemVer)
    released = [v for v in re.findall(r"^#+\s*\[?v?([0-9][^\]\s]*)\]?", text, re.MULTILINE) if version_key(v)]
    if released and not step.get("allow_downgrade", False) and version_key(version):
        latest = max(released, key=version_key)
        if version_key(version) < version_key(latest):
            fail(f"{version} ist älter als {latest} im Changelog")

    alternatives = "|".join(re.escape(n) for n in names)
    head_re = re.compile(rf"^(#+)[ \t]*\[?({alternatives})\]?[ \t]*(\r?\n)", re.MULTILINE | re.IGNORECASE)
    match = head_re.search(text)
    if not match:
        fail(f"{step.rel(path)} hat keine Überschrift {' / '.join(names)} mit den Änderungen dieser Version")
    hashes, name, newline = match.groups()
    new_heading = heading.format(hashes=hashes, version=version, date=date, name=name)
    replacement = new_heading + newline
    if step.get("keep_unreleased", False):
        replacement = f"{hashes} [{name}]{newline}{newline}{replacement}"
    text = text[: match.start()] + replacement + text[match.end() :]
    info(f"{step.rel(path)}: {name} → {new_heading.lstrip('# ')}")

    # Vergleichslink der unveröffentlichten Änderungen
    link_re = re.compile(rf"^\[({alternatives})\]:[ \t]*(\S*?)([^/\s]+)\.\.\.(\S+)[ \t]*$", re.MULTILINE | re.IGNORECASE)
    link = link_re.search(text)
    if link:
        label, base, previous, _head = link.groups()
        new_tag = tag.format(version=version)
        eol = "\r\n" if "\r\n" in text else "\n"
        lines = f"[{label}]: {base}{new_tag}...{_head}{eol}[{version}]: {base}{previous}...{new_tag}"
        text = text[: link.start()] + lines + text[link.end() :]
        info(f"{step.rel(path)}: Vergleichslinks für {new_tag} nachgezogen")

    write(path, text)


if __name__ == "__main__":
    main()
