"""
Einsprung der Kommandozeile.

Er existiert wegen einer einzigen Eigenschaft von Typer: `help=` wird beim
Import ausgewertet. Wuerde `markpublish.cli` geladen, bevor die Sprache
feststeht, waeren saemtliche Hilfetexte bereits in der falschen Sprache
gebacken -- und `--ui-lang de --help` zeigte englische Hilfe.

Deshalb liest dieser Einsprung `--ui-lang` selbst aus der Kommandozeile,
setzt die Sprache und importiert die CLI erst danach. Die Flagge wird dabei
aus argv entfernt; Typer soll sie nicht noch einmal sehen.

Angemeldet ist dieser Einsprung als `markpublish` und `mpub`
(siehe [project.scripts]). `markpublish.cli:app` bleibt daneben benutzbar --
etwa im Test -- und nimmt dann die Sprache aus Umgebung und System.
"""

from __future__ import annotations

import sys
from typing import List, Optional, Sequence, Tuple

#: Die Flagge, die dieser Einsprung selbst verarbeitet.
UI_LANG_FLAG = "--ui-lang"


def split_ui_lang(argv: Sequence[str]) -> Tuple[List[str], Optional[str]]:
    """
    Trennt `--ui-lang <code>` bzw. `--ui-lang=<code>` von den uebrigen Argumenten.

    Genommen wird die letzte Angabe, nicht die erste: wer eine Flagge zweimal
    schreibt, meint ueblicherweise die spaetere. Steht `--ui-lang` ganz am Ende
    ohne Wert, bleibt der Wert None -- die Sprache faellt dann auf Umgebung und
    System zurueck, statt dass der Aufruf an einer Nebensaechlichkeit scheitert.
    """
    rest: List[str] = []
    language: Optional[str] = None

    args = iter(range(len(argv)))
    skip_next = False
    for index in args:
        if skip_next:
            skip_next = False
            continue
        arg = argv[index]
        if arg == UI_LANG_FLAG:
            if index + 1 < len(argv):
                language = argv[index + 1]
                skip_next = True
        elif arg.startswith(UI_LANG_FLAG + "="):
            language = arg.split("=", 1)[1]
        else:
            rest.append(arg)

    return rest, language


def main() -> None:
    """Bestimmt die Sprache der Oberflaeche und uebergibt an die CLI."""
    from markpublish.ui import set_ui_language

    argv, explicit = split_ui_lang(sys.argv[1:])
    set_ui_language(explicit)

    # Erst jetzt: mit diesem Import entstehen die Hilfetexte.
    from markpublish.cli import app

    app(args=argv, prog_name="markpublish")
