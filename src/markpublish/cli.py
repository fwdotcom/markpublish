"""
markpublish CLI Interface.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from markpublish import __version__
from markpublish.config.loader import load_config
from markpublish.i18n import (
    BUILTIN_I18N_PATH,
    I18N_FILENAME,
    LabelFileError,
    UndefinedLabelError,
    describe_labels,
)
from markpublish.markdown.engine import MarkdownPipeline
from markpublish.markdown.toc import slugify
from markpublish.renderers.base import DocumentContext
from markpublish.renderers.html import HTMLRenderer
from markpublish.renderers.pdf import PDFRenderer
from markpublish.templates.resolver import (
    get_package_templates_dir,
    list_templates,
    resolve_template_path,
)

app = typer.Typer(
    name="markpublish",
    help="Modern, modular Markdown to PDF/HTML publishing tool powered by WeasyPrint.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    if value:
        console.print(f"[bold blue]markpublish[/bold blue] version [green]{__version__}[/green]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", help="Show the application's version and exit.", callback=version_callback, is_eager=True
    )
):
    """markpublish CLI"""
    pass


@app.command(name="build")
def build_cmd(
    config_file: Path = typer.Argument(
        Path("markpublish.yaml"),
        help="Path to markpublish.yaml configuration file.",
        exists=False,
    ),
    target: str = typer.Option(
        "pdf",
        "--target",
        "-t",
        help="Output target: 'pdf', 'html', or 'all'.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Custom output file or directory path.",
    ),
    templates_dir: Optional[Path] = typer.Option(
        None,
        "--templates-dir",
        help="Custom templates directory path.",
    ),
):
    """
    Builds document to PDF and/or HTML based on markpublish.yaml.
    """
    if not config_file.exists():
        console.print(f"[bold red]Error:[/bold red] Configuration file '{config_file}' not found.")
        raise typer.Exit(code=1)

    base_dir = config_file.parent.resolve()

    with console.status("[bold green]Loading configuration...[/bold green]"):
        try:
            config = load_config(config_file)
        except Exception as e:
            console.print(f"[bold red]Configuration error:[/bold red] {e}")
            raise typer.Exit(code=1) from e

    console.print(
        Panel(
            f"[bold]{config.document.title}[/bold]\n"
            f"Author: {config.document.author or 'N/A'} | Version: {config.document.version or 'N/A'} | Date: {config.document.date}\n"
            f"Theme: [cyan]{config.theme}[/cyan] | Targets: [yellow]{target.upper()}[/yellow]",
            title="[bold blue]markpublish build[/bold blue]",
            border_style="blue",
        )
    )

    # Determine targets to build
    targets_to_build: List[str] = []
    target_clean = target.lower().strip()
    if target_clean in ("all", "both"):
        targets_to_build = ["pdf", "html"]
    elif target_clean in ("pdf", "html"):
        targets_to_build = [target_clean]
    else:
        console.print(f"[bold red]Error:[/bold red] Unknown target '{target}'. Choose 'pdf', 'html', or 'all'.")
        raise typer.Exit(code=1)

    effective_templates_dir = templates_dir or (Path(config.templates_dir) if config.templates_dir else None)

    for tgt in targets_to_build:
        with console.status(f"[bold green]Processing Markdown and rendering {tgt.upper()}...[/bold green]"):
            try:
                tmpl_path = resolve_template_path(
                    target=tgt,
                    theme=config.theme,
                    custom_templates_dir=effective_templates_dir,
                    config_base_dir=base_dir,
                )
            except Exception as e:
                console.print(f"[bold red]Template error for {tgt}:[/bold red] {e}")
                raise typer.Exit(code=1) from e

            context = DocumentContext(
                config=config,
                content_items=[],
                toc_tree=[],
                template_path=tmpl_path,
                base_dir=base_dir,
                target=tgt,
            )

            # Die Kaskade endet beim Zielformat (Ebene 3), und die Alert-Titel
            # entstehen schon beim Markdown-Parsen. Die Pipeline laeuft deshalb
            # pro Zielformat mit dessen Labels -- sonst haette ein
            # <theme>/pdf/i18n.yaml auf "Hinweis" keine Wirkung.
            try:
                labels = context.labels
            except LabelFileError as e:
                console.print(f"[bold red]Label file error ({tgt}):[/bold red] {e}")
                raise typer.Exit(code=1) from e

            pipeline = MarkdownPipeline(config, base_dir=base_dir, labels=labels)
            context.content_items, context.toc_tree = pipeline.process_document()

            # Determine output file path
            doc_slug = slugify(config.document.title, separator="_")
            if output:
                if output.is_dir() or str(output).endswith(("/", "\\")):
                    out_file = output / f"{doc_slug}.{tgt}"
                elif len(targets_to_build) > 1 and output.suffix != f".{tgt}":
                    out_file = output.parent / f"{output.stem}.{tgt}"
                else:
                    out_file = output
            else:
                out_file = base_dir / f"{doc_slug}.{tgt}"

            try:
                if tgt == "pdf":
                    renderer = PDFRenderer()
                else:
                    renderer = HTMLRenderer()

                out_result = renderer.render(context, out_file)
                console.print(f"[bold green][OK][/bold green] {tgt.upper()} successfully generated: [cyan]{out_result}[/cyan]")
            except UndefinedLabelError as e:
                # Eigener Zweig, weil die Meldung mehrzeilig ist und Fundstelle
                # samt durchsuchten Dateien nennt - die gehoert nicht hinter ein
                # "Rendering error:" auf dieselbe Zeile gequetscht.
                console.print(f"[bold red]Undefined label ({tgt}):[/bold red]")
                console.print(str(e))
                raise typer.Exit(code=1) from e
            except Exception as e:
                console.print(f"[bold red]Rendering error ({tgt}):[/bold red] {e}")
                raise typer.Exit(code=1) from e


@app.command(name="init")
def init_cmd(
    target_dir: Path = typer.Argument(
        Path("."),
        help="Directory to initialize.",
    ),
    title: str = typer.Option(
        "Neues Dokument",
        "--title",
        "-t",
        help="Document title.",
    ),
):
    """
    Initializes a new markpublish project with sample structure and chapters.
    """
    target_dir = target_dir.resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    chapters_dir = target_dir / "chapters"
    chapters_dir.mkdir(exist_ok=True)

    # 1. Sample YAML
    yaml_content = f"""# markpublish.yaml
document:
  title: "{title}"
  subtitle: "Erstellt mit markpublish"
  summary: "Kurze Zusammenfassung des Dokuments."
  author: "Autor Name"
  date: "auto"
  version: "1.0.0"
  language: "de"

  cover: true
  toc: true
  autonum_type: "decimal"
  header: true
  footer: true

theme: "default"

chapters:
  - file: "chapters/01_introduction.md"
    title: "Einleitung"
    summary: "Einführung in das Thema."
    divider_page: true
    toc: false

  - file: "chapters/02_architecture.md"
    title: "Hauptteil"
    summary: "Detaillierte Erläuterungen und Architektur."
    divider_page: true
    toc: 2
    chapters:
      - file: "chapters/02_1_details.md"
        title: "Detailaspekte"

  - part: "Anhänge"
    summary: "Glossar und Zusatzinformationen."
    divider_page: true
    autonum: "none"
    chapters:
      - file: "chapters/03_appendix.md"
        title: "Anhang A: Glossar"
"""
    yaml_file = target_dir / "markpublish.yaml"
    if not yaml_file.exists():
        yaml_file.write_text(yaml_content, encoding="utf-8")

    # 2. Sample Chapters
    c1 = chapters_dir / "01_introduction.md"
    if not c1.exists():
        c1.write_text("""# Einleitung

Willkommen zu Ihrem neuen Dokument. Dieses Projekt wurde mit **markpublish** erstellt.

## Zielsetzung
Hier beschreiben Sie die Ziele und Anforderungen.

!!! note "Hinweis"
    Admonitions und Callouts werden voll unterstützt.
""", encoding="utf-8")

    c2 = chapters_dir / "02_architecture.md"
    if not c2.exists():
        c2.write_text("""# Hauptteil

In diesem Kapitel beschreiben Sie die Kerninhalte.

## Übersicht
Die Systemlandschaft gliedert sich in modulare Komponenten.

```python
def publish(doc):
    print(f"Publishing {doc}...")
```
""", encoding="utf-8")

    c2_1 = chapters_dir / "02_1_details.md"
    if not c2_1.exists():
        c2_1.write_text("""# Detailaspekte

Dies ist ein hierarchisches Unterkapitel.

### Spezifische Konfiguration
Hier folgen weitere Details.
""", encoding="utf-8")

    c3 = chapters_dir / "03_appendix.md"
    if not c3.exists():
        c3.write_text("""# Anhang A: Glossar

| Begriff | Erklärung |
| :--- | :--- |
| **markpublish** | Modulares Markdown Publishing Tool |
| **WeasyPrint** | CSS Paged Media PDF Engine |
""", encoding="utf-8")

    console.print(f"[bold green][OK][/bold green] Initialized markpublish project in [cyan]{target_dir}[/cyan]")
    console.print("Run [bold cyan]markpublish build[/bold cyan] to generate your first PDF!")


@app.command(name="templates")
def templates_list_cmd(
    target: Optional[str] = typer.Option(
        None,
        "--target",
        "-t",
        help="Filter by target format ('pdf' or 'html').",
    ),
    templates_dir: Optional[Path] = typer.Option(
        None,
        "--templates-dir",
        help="Custom templates directory path.",
    ),
):
    """
    Lists all available templates across User, Common, and Package sources.
    """
    all_tmpls = list_templates(custom_templates_dir=templates_dir)

    table = Table(title="Available Templates", show_header=True, header_style="bold blue")
    table.add_column("Target", style="yellow")
    table.add_column("Theme", style="bold")
    table.add_column("Source", style="cyan")
    table.add_column("Layout", style="magenta")
    table.add_column("Active", justify="center")
    table.add_column("Path", style="dim")

    has_legacy = False
    for t in all_tmpls:
        if target and t["target"] != target.lower().strip():
            continue
        active_str = "[bold green]Yes[/bold green]" if t["is_active"] else "[dim]No[/dim]"
        legacy = t.get("layout") == "legacy"
        has_legacy = has_legacy or legacy
        layout_str = "[yellow]<target>/<theme>[/yellow]" if legacy else "[dim]<theme>/<target>[/dim]"
        table.add_row(t["target"], t["theme"], t["source"], layout_str, active_str, t["path"])

    console.print(table)

    if has_legacy:
        console.print(
            "\n[yellow]Hinweis:[/yellow] Die gelb markierten Templates liegen im alten Layout "
            "[bold]<target>/<theme>[/bold]. Bitte nach [bold]<theme>/<target>[/bold] verschieben "
            "(z. B. [cyan]templates/pdf/mytheme[/cyan] -> [cyan]templates/mytheme/pdf[/cyan]); "
            "die alte Aufloesung entfaellt in einer kuenftigen Version."
        )


@app.command(name="export-template")
def export_template_cmd(
    theme: str = typer.Argument("default", help="Theme name to export."),
    destination: Path = typer.Argument(Path("templates"), help="Destination directory."),
    target: str = typer.Option("all", "--target", "-t", help="Target to export ('pdf', 'html', or 'all')."),
):
    """
    Exports a built-in template to project directory for customization.
    """
    pkg_base = get_package_templates_dir()
    targets = ["pdf", "html"] if target.lower() in ("all", "both") else [target.lower()]

    exported_any = False
    for tgt in targets:
        src = pkg_base / theme / tgt
        if not src.exists():
            console.print(f"[yellow]Warning:[/yellow] Built-in template '{theme}' for target '{tgt}' not found at {src}")
            continue

        dest = destination / theme / tgt
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dest, dirs_exist_ok=True)
        exported_any = True
        console.print(f"[bold green][OK][/bold green] Exported template [cyan]{tgt}/{theme}[/cyan] to [yellow]{dest}[/yellow]")

    # Die i18n.yaml auf Theme-Ebene liegt neben den Zielformat-Ordnern, nicht
    # darin - ohne diesen Schritt exportiert man das Theme und ausgerechnet die
    # Datei, in der die statischen Texte definiert werden, bliebe zurueck.
    theme_i18n = pkg_base / theme / I18N_FILENAME
    if exported_any and theme_i18n.is_file():
        dest_i18n = destination / theme / I18N_FILENAME
        if dest_i18n.exists():
            console.print(f"[dim]Kept existing[/dim] [yellow]{dest_i18n}[/yellow]")
        else:
            shutil.copy2(theme_i18n, dest_i18n)
            console.print(f"[bold green][OK][/bold green] Exported [cyan]{theme}/{I18N_FILENAME}[/cyan] to [yellow]{dest_i18n}[/yellow]")


@app.command(name="labels")
def labels_cmd(
    config_file: Path = typer.Argument(
        Path("markpublish.yaml"),
        help="Path to markpublish.yaml configuration file.",
    ),
    target: str = typer.Option(
        "pdf",
        "--target",
        "-t",
        help="Target format whose label cascade to show ('pdf' or 'html').",
    ),
    templates_dir: Optional[Path] = typer.Option(
        None,
        "--templates-dir",
        help="Custom templates directory path.",
    ),
    only_overridden: bool = typer.Option(
        False,
        "--overridden",
        help="Show only labels that a template or the document changed.",
    ),
):
    """
    Shows the resolved static texts and which layer supplied each one.

    Cascade, later wins: markpublish/i18n.yaml -> <theme>/i18n.yaml ->
    <theme>/<target>/i18n.yaml. The theme is the one the template
    resolution picked; a document cannot override texts.
    """
    if not config_file.exists():
        console.print(f"[bold red]Error:[/bold red] Configuration file '{config_file}' not found.")
        raise typer.Exit(code=1)

    base_dir = config_file.parent.resolve()

    try:
        config = load_config(config_file)
    except Exception as e:
        console.print(f"[bold red]Configuration error:[/bold red] {e}")
        raise typer.Exit(code=1) from e

    tgt = target.lower().strip()
    if tgt not in ("pdf", "html"):
        console.print(f"[bold red]Error:[/bold red] Unknown target '{target}'. Choose 'pdf' or 'html'.")
        raise typer.Exit(code=1)

    effective_templates_dir = templates_dir or (
        Path(config.templates_dir) if config.templates_dir else None
    )

    try:
        tmpl_path = resolve_template_path(
            target=tgt,
            theme=config.theme,
            custom_templates_dir=effective_templates_dir,
            config_base_dir=base_dir,
        )
    except Exception as e:
        console.print(f"[bold red]Template error for {tgt}:[/bold red] {e}")
        raise typer.Exit(code=1) from e

    context = DocumentContext(
        config=config,
        content_items=[],
        toc_tree=[],
        template_path=tmpl_path,
        base_dir=base_dir,
        target=tgt,
    )

    try:
        resolved = describe_labels(
            config.document.language,
            template_dirs=context.label_source_dirs,
        )
    except LabelFileError as e:
        console.print(f"[bold red]Label file error:[/bold red] {e}")
        raise typer.Exit(code=1) from e

    console.print(
        Panel(
            f"Language: [cyan]{config.document.language}[/cyan] | "
            f"Theme: [cyan]{config.theme}[/cyan] | Target: [yellow]{tgt.upper()}[/yellow]",
            title="[bold blue]markpublish labels[/bold blue]",
            border_style="blue",
        )
    )

    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Key", style="bold")
    table.add_column("Value")
    table.add_column("Source", style="dim")

    for key in sorted(resolved):
        entry = resolved[key]
        from_program = entry["path"] == str(BUILTIN_I18N_PATH)
        if only_overridden and from_program:
            continue
        source_style = "dim" if from_program else "green"
        table.add_row(key, entry["value"], f"[{source_style}]{entry['source']}[/{source_style}]")

    console.print(table)

    searched = [str(d / I18N_FILENAME) for d in context.label_source_dirs]
    console.print("\n[dim]Gesucht nach Overrides in:[/dim]")
    for path_str in searched:
        marker = "[green]gefunden[/green]" if Path(path_str).is_file() else "[dim]nicht vorhanden[/dim]"
        console.print(f"  {path_str}  {marker}")
