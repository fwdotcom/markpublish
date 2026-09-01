"""
Baut das offizielle markpublish Benutzerhandbuch in Deutsch und Englisch
und legt die fertigen Dokumente im Verzeichnis 'manual/' ab.

Die Ergebnisse sind zugleich die Schaustuecke im README: vier Dateien, zwei
Sprachen mal zwei Zielformate. Deshalb baut der Aufruf ohne Argumente beides -
haette er weiter nur PDF erzeugt, waere die HTML-Fassung im Repository still
veraltet, waehrend die PDF-Fassung daneben aktuell bleibt.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from markpublish.cli import _parse_targets, _render_bundled_doc

app = typer.Typer(
    name="build-manuals",
    help="Baut das offizielle markpublish Handbuch in Deutsch und Englisch.",
    add_completion=False,
)
console = Console()

#: Sprachen, in denen das Handbuch gepflegt wird.
LANGUAGES = ("de", "en")


@app.command()
def main(
    target: Annotated[
        str,
        typer.Option(
            "--target",
            "-t",
            help="Ausgabeformat: 'pdf', 'html' oder 'all'.",
        ),
    ] = "all",
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            help="Zielverzeichnis für die Handbücher.",
        ),
    ] = Path("manual"),
):
    """
    Rendert das Benutzerhandbuch in allen gepflegten Sprachen (DE und EN)
    in das angegebene Zielverzeichnis.
    """
    out_dir = output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Frueh pruefen, statt nach dem ersten gerenderten Dokument abzubrechen:
    # ein Tippfehler im Zielformat soll keine halbe Ausgabe hinterlassen.
    targets = _parse_targets(target)

    console.print(
        f"[bold blue]Baue offizielle Handbücher "
        f"({', '.join(lang.upper() for lang in LANGUAGES)}) "
        f"als {', '.join(t.upper() for t in targets)} "
        f"nach [cyan]{out_dir}[/cyan]...[/bold blue]\n"
    )

    for lang in LANGUAGES:
        for tgt in targets:
            console.print(
                f"[bold green]▶[/bold green] Rendere Handbuch: "
                f"Sprache [cyan]{lang.upper()}[/cyan] | "
                f"Format [yellow]{tgt.upper()}[/yellow]"
            )
            _render_bundled_doc(
                name="manual",
                lang=lang,
                target=tgt,
                output=out_dir,
                theme=None,
                templates_dir=None,
            )

    _print_summary(out_dir, targets)


def _print_summary(out_dir: Path, targets: list[str]) -> None:
    """
    Listet, was am Ende wirklich im Zielverzeichnis liegt.

    Gelesen wird das Verzeichnis, nicht die Liste der Auftraege: eine Datei,
    die nicht geschrieben wurde, faellt so auf, statt in einer Erfolgsmeldung
    unterzugehen.
    """
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Datei", style="cyan")
    table.add_column("Format", style="yellow")
    table.add_column("Größe", justify="right")

    found = sorted(
        path
        for tgt in targets
        for path in out_dir.glob(f"*.{tgt}")
    )
    for path in found:
        table.add_row(
            path.name,
            path.suffix.lstrip(".").upper(),
            f"{path.stat().st_size / 1024:,.0f} kB",
        )

    console.print()
    console.print(table)

    expected = len(LANGUAGES) * len(targets)
    if len(found) == expected:
        console.print(
            f"\n[bold green][ERFOLG][/bold green] {expected} Dokumente unter "
            f"[cyan]{out_dir}[/cyan] aktualisiert."
        )
    else:
        console.print(
            f"\n[bold yellow][WARNUNG][/bold yellow] {len(found)} von {expected} "
            f"Dokumenten gefunden - bitte die Ausgabe oben prüfen."
        )


if __name__ == "__main__":
    app()
