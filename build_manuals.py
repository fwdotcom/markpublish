"""
Baut das offizielle markpublish Benutzerhandbuch in Deutsch und Englisch
und legt die fertigen Dokumente im Verzeichnis 'manual/' ab.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from markpublish.cli import _render_bundled_doc

app = typer.Typer(
    name="build-manuals",
    help="Baut das offizielle markpublish Handbuch in Deutsch und Englisch.",
    add_completion=False,
)
console = Console()


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
):
    """
    Rendert das Benutzerhandbuch in allen gepflegten Sprachen (DE und EN)
    in das angegebene Zielverzeichnis.
    """
    out_dir = output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    languages = ["de", "en"]
    console.print(f"[bold blue]Baue offizielle Handbücher ({', '.join(languages).upper()}) nach [cyan]{out_dir}[/cyan]...[/bold blue]\n")

    for lang in languages:
        console.print(f"[bold green]▶[/bold green] Rendere Handbuch: Sprache [cyan]{lang.upper()}[/cyan] | Format [yellow]{target.upper()}[/yellow]")
        _render_bundled_doc(
            name="manual",
            lang=lang,
            target=target,
            output=out_dir,
            theme=None,
            templates_dir=None,
        )

    console.print(f"\n[bold green][ERFOLG][/bold green] Alle Handbücher erfolgreich unter [cyan]{out_dir}[/cyan] aktualisiert.")


if __name__ == "__main__":
    app()
