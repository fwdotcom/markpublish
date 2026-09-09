"""
Baut die mitgelieferten markpublish-Dokumente - Benutzerhandbuch und
Kurzreferenz - in allen Sprachen, die im Paket liegen, als PDF und legt die
fertigen Dokumente im Verzeichnis 'manual/' ab.
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

#: Die mitgelieferten Dokumente. Die Namen sind zugleich die Unterbefehle
#: von markpublish und die Ordner unter docs/.
DOCUMENTS = ("manual", "cheatsheet")


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
    ] = "all",
):
    """
    Rendert die mitgelieferten Dokumente in das angegebene Zielverzeichnis.

    Ohne --lang jede Sprache, die im Paket liegt. Die fertigen PDFs stehen im
    Repository und tragen die Versionsnummer aus ihrer YAML - eine Fassung,
    die beim Versionssprung nicht mitgebaut wird, behauptet danach eine
    Version, die es nicht mehr gibt.
    """
    out_dir = (output_dir if output_dir.is_absolute() else (SCRIPT_DIR / output_dir)).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Frueh pruefen, statt nach dem ersten gerenderten Dokument abzubrechen:
    # ein Tippfehler im Zielformat soll keine halbe Ausgabe hinterlassen.
    targets = _parse_targets(target)
    languages = _parse_languages(lang)
    jobs = _plan(languages, targets)

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

    for name, code, tgt in jobs:
        console.print(
            "[bold green]▶[/bold green] "
            + t(
                "manuals.rendering",
                document=f"[cyan]{name}[/cyan]",
                language=f"[cyan]{code.upper()}[/cyan]",
                target=f"[yellow]{tgt.upper()}[/yellow]",
            )
        )
        _render_bundled_doc(
            name=name,
            lang=code,
            target=tgt,
            output=out_dir,
            theme=None,
            templates_dir=None,
        )

    _print_summary(out_dir, targets, len(jobs), started_at)


def _available_languages() -> list[str]:
    """
    Sprachen, in denen mindestens eines der Dokumente im Paket liegt.

    Die Vereinigung, nicht der Schnitt: eine Sprache, die vorerst nur das
    Handbuch kennt, soll gebaut werden koennen, statt still aus der Liste zu
    fallen. Was ihr fehlt, benennt _plan.
    """
    return sorted({code for name in DOCUMENTS for code in _available_doc_languages(name)})


def _parse_languages(value: str) -> list[str]:
    """
    Bringt --lang auf die Liste der zu bauenden Sprachen.

    Geprueft wird gegen die Sprachordner im Paket, nicht gegen eine Liste im
    Code: was mitgeliefert wird, entscheidet der Inhalt von docs/.
    """
    available = _available_languages()
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


def _plan(languages: list[str], targets: list[str]) -> list[tuple[str, str, str]]:
    """
    Stellt zusammen, was dieser Lauf baut.

    Nicht jedes Dokument liegt in jeder Sprache. Was fehlt, wird hier benannt
    und uebersprungen: daran soll der Lauf nicht scheitern, aber er soll auch
    nicht so aussehen, als haette er die Sprache gebaut.
    """
    jobs: list[tuple[str, str, str]] = []
    for name in DOCUMENTS:
        available = _available_doc_languages(name)
        for code in languages:
            if code not in available:
                console.print(
                    f"[yellow]{t('label.note')}[/yellow] "
                    + t("manuals.skip", document=name, language=code.upper())
                )
                continue
            jobs.extend((name, code, tgt) for tgt in targets)
    return jobs


def _print_summary(
    out_dir: Path,
    targets: list[str],
    expected: int,
    started_at: float,
) -> None:
    """
    Listet, was am Ende wirklich im Zielverzeichnis liegt.

    Gelesen wird das Verzeichnis, nicht die Liste der Auftraege: eine Datei,
    die nicht geschrieben wurde, faellt so auf, statt in einer Erfolgsmeldung
    unterzugehen.

    Die Spalte "Stand" trennt dabei die Dokumente dieses Laufs von denen, die
    schon dalagen: eine eingeschraenkte Auswahl laesst beides nebeneinander
    liegen, und eine alte Datei soll nicht wie ein frisches Ergebnis aussehen.

    Wieviele es haetten werden sollen, weiss der Aufrufer -- gezaehlt wird die
    Auftragsliste, nicht Sprachen mal Formate: ein uebersprungenes Dokument
    machte die Rechnung sonst zur Warnung.
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
