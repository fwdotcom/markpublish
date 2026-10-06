#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Frank Winter
# SPDX-License-Identifier: MIT
"""
Führt Befehle im Projektordner aus, z. B. Prüfungen und Tests. Allgemein verwendbar.

Konfiguration [commands]:
  run  Liste von Befehlen, jeder als Liste aus Programm und Argumenten,
       z. B. [["npm", "run", "check"], ["npm", "test"]]

Der Schritt bricht beim ersten Befehl ab, der fehlschlägt.

Aufruf:  python scripts/release/steps/40-commands.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.common import fail, load_step  # noqa: E402


def main() -> None:
    step = load_step(__file__, "Befehle im Projektordner ausführen (Prüfungen, Tests).")
    commands = step.require("run")
    for command in commands:
        executable = shutil.which(command[0])
        if not executable:
            fail(f"{command[0]} wurde nicht gefunden")
        print(f"> {' '.join(command)}", flush=True)
        result = subprocess.run([executable, *command[1:]], cwd=step.root)
        if result.returncode != 0:
            fail(f"{' '.join(command)} ist fehlgeschlagen (Exit-Code {result.returncode})")


if __name__ == "__main__":
    main()
