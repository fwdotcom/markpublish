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

app = typer.Typer(
    name="build-manuals",
    help="Baut das offizielle markpublish Handbuch in Deutsch und Englisch.",
    add_completion=False,
)
console = Console()

#: Sprachen, die ohne --lang gebaut werden.
#:
#: Nur Deutsch: das Handbuch wird auf Deutsch geschrieben, die englische
#: Fassung entsteht daraus, wenn die deutsche steht. Sie bei jedem Lauf
#: mitzubauen erzeugte nur ein PDF aus veralteter Quelle.
DEFAULT_LANGUAGES = ("de",)


@app.command()
def main(
    target: Annotated[
        str,
        typer.Option(
            "--target",
            "-t",
            help="Ausgabeformat: 'pdf', 'html' oder 'all'.",
        ),
    ] = "pdf",
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            help="Zielverzeichnis für die Handbücher.",
        ),
    ] = Path("manual"),
    lang: Annotated[
        str,
        typer.Option(
            "--lang",
            "-l",
            help="Sprachen, kommagetrennt, oder 'all' für alle mitgelieferten.",
        ),
    ] = ",".join(DEFAULT_LANGUAGES),
):
    """
    Rendert das Benutzerhandbuch in das angegebene Zielverzeichnis.

    Ohne --lang nur Deutsch. Eine Fassung, die gerade nicht gepflegt wird,
    baut sonst bei jedem Lauf mit und sieht danach aktueller aus, als sie ist.
    """
    out_dir = output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Frueh pruefen, statt nach dem ersten gerenderten Dokument abzubrechen:
    # ein Tippfehler im Zielformat soll keine halbe Ausgabe hinterlassen.
    targets = _parse_targets(target)
    languages = _parse_languages(lang)

    console.print(
        f"[bold blue]Baue Handbuch "
        f"({', '.join(code.upper() for code in languages)}) "
        f"als {', '.join(t.upper() for t in targets)} "
        f"nach [cyan]{out_dir}[/cyan]...[/bold blue]\n"
    )

    started_at = time.time()

    for code in languages:
        for tgt in targets:
            console.print(
                f"[bold green]▶[/bold green] Rendere Handbuch: "
                f"Sprache [cyan]{code.upper()}[/cyan] | "
                f"Format [yellow]{tgt.upper()}[/yellow]"
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
            "[bold red]Fehler:[/bold red] Im Paket liegt kein Handbuch "
            "(docs/manual/<sprache>/markpublish.yaml fehlt)."
        )
        raise typer.Exit(code=1)

    cleaned = value.strip().lower()
    if cleaned in ("all", "alle"):
        return available

    wanted = [code.strip() for code in cleaned.split(",") if code.strip()]
    unknown = [code for code in wanted if code not in available]
    if unknown:
        console.print(
            f"[bold red]Fehler:[/bold red] Keine Handbuchquelle für "
            f"{', '.join(unknown)}. Mitgeliefert: {', '.join(available)}."
        )
        raise typer.Exit(code=1)
    if not wanted:
        console.print("[bold red]Fehler:[/bold red] --lang ist leer.")
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
    table.add_column("Datei", style="cyan")
    table.add_column("Format", style="yellow")
    table.add_column("Größe", justify="right")
    table.add_column("Stand")

    found = sorted(path for tgt in targets for path in out_dir.glob(f"*.{tgt}"))
    fresh = 0
    for path in found:
        is_fresh = path.stat().st_mtime >= started_at
        fresh += 1 if is_fresh else 0
        table.add_row(
            path.name,
            path.suffix.lstrip(".").upper(),
            f"{path.stat().st_size / 1024:,.0f} kB",
            "[green]neu gebaut[/green]" if is_fresh else "[dim]unverändert[/dim]",
        )

    console.print()
    console.print(table)

    expected = len(languages) * len(targets)
    if fresh == expected:
        console.print(
            f"\n[bold green][ERFOLG][/bold green] {expected} Dokumente unter "
            f"[cyan]{out_dir}[/cyan] aktualisiert."
        )
    else:
        console.print(
            f"\n[bold yellow][WARNUNG][/bold yellow] {fresh} von {expected} "
            f"Dokumenten gebaut - bitte die Ausgabe oben prüfen."
        )


if __name__ == "__main__":
    app()
