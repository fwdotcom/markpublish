#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Frank Winter
# SPDX-License-Identifier: MIT
"""
Bereitet ein Release vor, indem es die Schritte in steps/ nacheinander ausführt – wie run-parts unter Linux:

  - Ein Schritt ist eine Datei steps/NN-name.py (NN = Zahl, name aus Kleinbuchstaben, Ziffern, Bindestrichen).
  - Die Reihenfolge ergibt sich aus der Zahl. Andere Dateien werden übergangen; zum Abschalten einen Schritt
    umbenennen (z. B. in 50-handbuch-screenshots.py.off) oder löschen.
  - Jeder Schritt läuft als eigener Prozess im Projektordner, mit der Version als Argument und in
    RELEASE_VERSION, dazu RELEASE_ROOT und RELEASE_CONFIG. Endet einer mit Fehler, bricht das Release ab.
  - Seine Parameter liest jeder Schritt aus release.toml (Abschnitt = Dateiname ohne Nummer).

Committet, getaggt und veröffentlicht wird nicht; das bleibt Handarbeit.

Aufruf:  python scripts/release/release.py 1.2.0
         python scripts/release/release.py 1.2.0 --skip "*screenshots"
         python scripts/release/release.py --only screenshots
         python scripts/release/release.py --list
Voraussetzung:  pip install -r scripts/release/requirements.txt && python -m playwright install chromium
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

from lib.common import DEFAULT_CONFIG, fail, normalize_version, setup_console

STEPS_DIR = Path(__file__).resolve().parent / "steps"
STEP_RE = re.compile(r"^(\d+)-([a-z0-9][a-z0-9-]*)\.py$")


def discover() -> list[tuple[str, Path]]:
    found = []
    for path in STEPS_DIR.iterdir():
        match = STEP_RE.match(path.name)
        if path.is_file() and match:
            found.append((int(match.group(1)), match.group(2), path))
    return [(name, path) for _, name, path in sorted(found)]


def main() -> None:
    setup_console()
    parser = argparse.ArgumentParser(description="Release vorbereiten: Schritte aus steps/ der Reihe nach ausführen.")
    parser.add_argument("version", nargs="?", help="neue Version, z. B. 1.2.0")
    parser.add_argument("--skip", action="append", default=[], metavar="MUSTER", help="Schritte überspringen (Name oder Muster wie *screenshots, mehrfach möglich)")
    parser.add_argument("--only", action="append", default=[], metavar="MUSTER", help="nur diese Schritte ausführen (mehrfach möglich)")
    parser.add_argument("--list", action="store_true", help="Schritte nur auflisten")
    args = parser.parse_args()

    steps = discover()
    if not steps:
        fail(f"keine Schritte in {STEPS_DIR}")
    selected = [
        (name, path)
        for name, path in steps
        if (not args.only or any(fnmatch.fnmatch(name, p) for p in args.only))
        and not any(fnmatch.fnmatch(name, p) for p in args.skip)
    ]

    if args.list:
        for name, path in steps:
            print(f"  {'✓' if (name, path) in selected else '–'} {path.name}")
        return

    version = normalize_version(args.version) if args.version else None
    config_file = Path(os.environ.get("RELEASE_CONFIG") or DEFAULT_CONFIG).resolve()
    with config_file.open("rb") as f:
        project = tomllib.load(f)
    root = Path(os.environ.get("RELEASE_ROOT") or (config_file.parent / project.get("root", "."))).resolve()

    env = {**os.environ, "RELEASE_ROOT": str(root), "RELEASE_CONFIG": str(config_file), "PYTHONUTF8": "1"}
    if version:
        env["RELEASE_VERSION"] = version

    for number, (name, path) in enumerate(selected, start=1):
        print(f"\n== {number}/{len(selected)} {name}", flush=True)
        result = subprocess.run([sys.executable, str(path), *([version] if version else [])], cwd=root, env=env)
        if result.returncode != 0:
            fail(f"Schritt {path.name} ist fehlgeschlagen (Exit-Code {result.returncode})")

    skipped = [path.name for name, path in steps if (name, path) not in selected]
    if skipped:
        print(f"\nÜbersprungen: {', '.join(skipped)}")
    if version:
        tag = project.get("release", {}).get("tag", "v{version}").format(version=version)
        print(f"\nVersion {version} ist vorbereitet. Noch zu tun:")
        print("  - Änderungen prüfen (git status, git diff)")
        print(f'  - committen, z. B. git commit -am "prepare for release {version}"')
        print(f"  - Release {tag} veröffentlichen")


if __name__ == "__main__":
    main()
