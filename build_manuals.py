"""
Baut das offizielle markpublish Benutzerhandbuch in Deutsch und Englisch
als PDF und legt die fertigen Dokumente im Verzeichnis 'manual/' ab.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from markpublish.cli import (
    _available_doc_languages,
    _parse_targets,
    _render_bundled_doc,
)
from markpublish.ui import t, tn

app = typer.Typer(
    name="build-manuals",
    help=t("manuals.app.help"),
    add_completion=False,
)
console = Console()

#: Sprachen, die ohne --lang gebaut werden.
#:
#: Nur Deutsch: das Handbuch wird auf Deutsch geschrieben, die englische
#: Fassung entsteht daraus, wenn die deutsche steht. Sie bei jedem Lauf
#: mitzubauen erzeugte nur ein PDF aus veralteter Quelle.
DEFAULT_LANGUAGES = ("de",)


SCRIPT_DIR = Path(__file__).resolve().parent


@app.command()
def main(
    target: Annotated[
        str,
        typer.Option(
            "--target",
            "-t",
            help=t("manuals.opt.target"),
        ),
    ] = "pdf",
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            help=t("manuals.opt.output_dir"),
        ),
    ] = Path("manual"),
    lang: Annotated[
        str,
        typer.Option(
            "--lang",
            "-l",
            help=t("manuals.opt.lang"),
        ),
    ] = ",".join(DEFAULT_LANGUAGES),
):
    """
    Rendert das Benutzerhandbuch in das angegebene Zielverzeichnis.

    Ohne --lang nur Deutsch. Eine Fassung, die gerade nicht gepflegt wird,
    baut sonst bei jedem Lauf mit und sieht danach aktueller aus, als sie ist.
    """
    out_dir = (output_dir if output_dir.is_absolute() else (SCRIPT_DIR / output_dir)).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Frueh pruefen, statt nach dem ersten gerenderten Dokument abzubrechen:
    # ein Tippfehler im Zielformat soll keine halbe Ausgabe hinterlassen.
    targets = _parse_targets(target)
    languages = _parse_languages(lang)

    console.print(
        "[bold blue]"
        + t(
            "manuals.building",
            language=", ".join(code.upper() for code in languages),
            target=", ".join(tgt.upper() for tgt in targets),
            path=f"[cyan]{out_dir}[/cyan]",
        )
        + "[/bold blue]\n"
    )

    started_at = time.time()

    for code in languages:
        for tgt in targets:
            console.print(
                "[bold green]▶[/bold green] "
                + t(
                    "manuals.rendering",
                    language=f"[cyan]{code.upper()}[/cyan]",
                    target=f"[yellow]{tgt.upper()}[/yellow]",
                )
            )
            _render_bundled_doc(
                name="manual",
                lang=code,
                target=tgt,
                output=out_dir,
                theme=None,
                templates_dir=None,
            )

    _print_summary(out_dir, targets, languages, started_at)


def _parse_languages(value: str) -> list[str]:
    """
    Bringt --lang auf die Liste der zu bauenden Sprachen.

    Geprueft wird gegen die Sprachordner im Paket, nicht gegen eine Liste im
    Code: was mitgeliefert wird, entscheidet der Inhalt von docs/manual/.
    """
    available = _available_doc_languages("manual")
    if not available:
        console.print(
            f"[bold red]{t('label.error')}[/bold red] " + t("manuals.err.no_source")
        )
        raise typer.Exit(code=1)

    cleaned = value.strip().lower()
    if cleaned in ("all", "alle"):
        return available

    wanted = [code.strip() for code in cleaned.split(",") if code.strip()]
    unknown = [code for code in wanted if code not in available]
    if unknown:
        console.print(
            f"[bold red]{t('label.error')}[/bold red] "
            + t(
                "manuals.err.unknown_lang",
                language=", ".join(unknown),
                available=", ".join(available),
            )
        )
        raise typer.Exit(code=1)
    if not wanted:
        console.print(
            f"[bold red]{t('label.error')}[/bold red] " + t("manuals.err.lang_empty")
        )
        raise typer.Exit(code=1)
    return wanted


def _print_summary(
    out_dir: Path,
    targets: list[str],
    languages: list[str],
    started_at: float,
) -> None:
    """
    Listet, was am Ende wirklich im Zielverzeichnis liegt.

    Gelesen wird das Verzeichnis, nicht die Liste der Auftraege: eine Datei,
    die nicht geschrieben wurde, faellt so auf, statt in einer Erfolgsmeldung
    unterzugehen.

    Die Spalte "Stand" trennt dabei die Dokumente dieses Laufs von denen, die
    schon dalagen -- seit nicht mehr jede Sprache bei jedem Lauf mitgebaut
    wird, liegt beides nebeneinander, und eine alte Datei soll nicht wie ein
    frisches Ergebnis aussehen.
    """
    table = Table(show_header=True, header_style="bold blue")
    table.add_column(t("manuals.table.file"), style="cyan")
    table.add_column(t("manuals.table.format"), style="yellow")
    table.add_column(t("manuals.table.size"), justify="right")
    table.add_column(t("manuals.table.state"))

    found = sorted(path for tgt in targets for path in out_dir.glob(f"*.{tgt}"))
    fresh = 0
    for path in found:
        is_fresh = path.stat().st_mtime >= started_at
        fresh += 1 if is_fresh else 0
        table.add_row(
            path.name,
            path.suffix.lstrip(".").upper(),
            f"{path.stat().st_size / 1024:,.0f} kB",
            (
                f"[green]{t('manuals.state.rebuilt')}[/green]"
                if is_fresh
                else f"[dim]{t('manuals.state.unchanged')}[/dim]"
            ),
        )

    console.print()
    console.print(table)

    expected = len(languages) * len(targets)
    if fresh == expected:
        console.print(
            f"\n[bold green][{t('manuals.label.success')}][/bold green] "
            + tn("manuals.success", expected, path=f"[cyan]{out_dir}[/cyan]")
        )
    else:
        console.print(
            f"\n[bold yellow][{t('label.warning').rstrip(':').upper()}][/bold yellow] "
            + tn("manuals.partial", expected, done=fresh, expected=expected)
        )


if __name__ == "__main__":
    # Falls ein lokales .venv existiert und nicht aktiv ist (z. B. beim Doppelklick im Explorer),
    # fuehre das Skript transparent mit dem venv-Python aus:
    import sys
    venv_python = SCRIPT_DIR / ".venv" / "Scripts" / "python.exe"
    if venv_python.is_file() and Path(sys.executable).resolve() != venv_python.resolve():
        import subprocess
        res = subprocess.run([str(venv_python), str(__file__)] + sys.argv[1:])
        sys.exit(res.returncode)

    app()
