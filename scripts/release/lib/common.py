# SPDX-FileCopyrightText: 2026 Frank Winter
# SPDX-License-Identifier: MIT
"""
Gemeinsame Grundlage der Release-Schritte.

Jeder Schritt unter steps/ ist ein eigenständiges Skript. Er ruft zu Beginn load_step() auf und bekommt
damit Projektordner, seinen Abschnitt aus release.toml und – falls übergeben – die neue Version.

Woher die Werte kommen (jeweils das erste, das gesetzt ist):
  Konfiguration  RELEASE_CONFIG, sonst release.toml neben diesem Ordner
  Projektordner  RELEASE_ROOT, sonst "root" aus release.toml (relativ zur Datei), sonst deren Ordner
  Version        erstes Argument des Aufrufs, sonst RELEASE_VERSION; ein führendes "v" fällt weg.
                 Das Format prüft der Schritt version.
  Abschnitt      Dateiname des Schritts ohne Nummer, Bindestriche als Unterstriche
                 (steps/30-security-txt.py → [security_txt])
  Einzelwerte    RELEASE_<ABSCHNITT>_<SCHLÜSSEL> überschreibt einen Wert des Abschnitts als Text,
                 z. B. RELEASE_SCREENSHOTS_HANDBUCH_OUT_DIR=/tmp/bilder
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

RELEASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = RELEASE_DIR / "release.toml"

# SemVer: X.Y.Z, optional mit Vorabversion oder Build-Angabe (1.2.0-rc.1, 1.2.0+build.5)
SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$")


def fail(message: str) -> None:
    print(f"Fehler: {message}", file=sys.stderr)
    sys.exit(1)


def info(message: str) -> None:
    print(f"  {message}", flush=True)


# Umlaute und Pfeile auch in der Windows-Konsole und bei umgeleiteter Ausgabe
def setup_console() -> None:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.stderr.reconfigure(encoding="utf-8")


# Zeilenenden der Dateien (LF oder CRLF) bleiben erhalten
def read(path: Path) -> str:
    with path.open(encoding="utf-8", newline="") as f:
        return f.read()


def write(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write(text)


def normalize_version(value: str) -> str:
    version = value.strip().removeprefix("v")
    if not version:
        fail("Version ist leer")
    return version


# Sortierschlüssel nach SemVer (Vorabversionen vor der zugehörigen Version); None, wenn keine SemVer-Version
def version_key(version: str) -> tuple | None:
    match = SEMVER_RE.match(version)
    if not match:
        return None
    major, minor, patch, pre = match.groups()
    if pre is None:
        return (int(major), int(minor), int(patch), 1, ())
    parts = tuple((0, int(p), "") if p.isdigit() else (1, 0, p) for p in pre.split("."))
    return (int(major), int(minor), int(patch), 0, parts)


def step_section(script: str | Path) -> str:
    stem = Path(script).stem
    return re.sub(r"^\d+-", "", stem).replace("-", "_")


@dataclass
class Step:
    name: str
    root: Path
    config_file: Path
    config: dict[str, Any]
    project: dict[str, Any] = field(repr=False)
    version: str | None

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def require(self, key: str) -> Any:
        if key not in self.config:
            fail(f"[{self.name}] {key} fehlt in {self.config_file.name}")
        return self.config[key]

    def path(self, value: str | Path) -> Path:
        return (self.root / value).resolve()

    def rel(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return str(path)

    def require_version(self) -> str:
        if not self.version:
            fail(f"{self.name}: Version fehlt (als Argument oder RELEASE_VERSION)")
        return self.version


def load_step(script: str | Path, description: str) -> Step:
    """Liest Aufruf, Konfiguration und Umgebung für den Schritt, dessen Datei script ist."""
    setup_console()
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("version", nargs="?", help="neue Version, z. B. 1.2.0 (nur für Schritte, die sie brauchen)")
    args = parser.parse_args()

    config_file = Path(os.environ.get("RELEASE_CONFIG") or DEFAULT_CONFIG).resolve()
    if not config_file.is_file():
        fail(f"Konfiguration nicht gefunden: {config_file}")
    with config_file.open("rb") as f:
        project = tomllib.load(f)

    root_env = os.environ.get("RELEASE_ROOT")
    root = Path(root_env).resolve() if root_env else (config_file.parent / project.get("root", ".")).resolve()

    name = step_section(script)
    config = dict(project.get(name, {}))
    prefix = f"RELEASE_{name.upper()}_"
    for key, value in os.environ.items():
        if key.startswith(prefix) and value:
            config[key[len(prefix):].lower()] = value

    version_arg = args.version or os.environ.get("RELEASE_VERSION")
    version = normalize_version(version_arg) if version_arg else None
    return Step(name=name, root=root, config_file=config_file, config=config, project=project, version=version)


# ---------- Version im Projekt ----------

def version_location(step: Step, entry: dict[str, str]) -> tuple[Path, re.Match]:
    """Datei und Fundstelle eines Eintrags {file, pattern}; die erste Klammergruppe ist die Version."""
    path = step.path(entry["file"])
    if not path.is_file():
        fail(f"{step.rel(path)} nicht gefunden")
    match = re.search(entry["pattern"], read(path), re.MULTILINE)
    if not match or match.lastindex is None:
        fail(f"Versionseintrag ({entry['pattern']}) nicht gefunden in {step.rel(path)}")
    return path, match


def current_version(step: Step) -> str:
    """Aktuelle Version des Projekts: die Fundstelle des ersten Eintrags in [version].files."""
    files = step.project.get("version", {}).get("files")
    if not files:
        fail(f"[version] files fehlt in {step.config_file.name}")
    return version_location(step, files[0])[1].group(1)
