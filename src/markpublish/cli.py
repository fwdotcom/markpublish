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
    default_document_language,
    describe_labels,
    detect_system_language,
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
    help="Modern, modular Markdown to PDF publishing tool powered by Typst.",
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


#: Sprache, in der die mitgelieferten Dokumente erscheinen, wenn weder --lang
#: noch die Systemsprache zu einer Uebersetzung fuehrt. Englisch, weil CLI-Hilfe
#: und README es ebenfalls sind.
DEFAULT_DOC_LANGUAGE = "en"

#: Wurzel der mitgelieferten Dokumente. Handbuch und Kurzreferenz liegen darin
#: nebeneinander, je Sprache ein Unterordner - dieselbe Form fuer beide, damit
#: eine dritte Uebersetzung nur ein Verzeichnis kostet.
BUNDLED_DOCS_DIRNAME = "docs"


def get_bundled_doc_dir(name: str) -> Path:
    """Returns the directory of a document shipped with the package."""
    return Path(__file__).resolve().parent / BUNDLED_DOCS_DIRNAME / name


def _available_doc_languages(name: str) -> List[str]:
    """Language codes the packaged document `name` is available in."""
    base = get_bundled_doc_dir(name)
    if not base.is_dir():
        return []
    return sorted(d.name for d in base.iterdir() if (d / "markpublish.yaml").is_file())


def _match_doc_language(available: List[str], requested: Optional[str]) -> Optional[str]:
    """
    Picks the shipped translation that fits `requested`, or None.

    Erst der volle Code, dann die Basissprache: eine Systemsprache meldet sich
    als "de-DE" oder "pt-BR", mitgeliefert wird "de". Ohne diesen zweiten
    Versuch fiele jeder Rechner mit regionaler Einstellung auf Englisch zurueck.
    """
    if not requested:
        return None
    code = requested.strip().lower().replace("_", "-")
    for candidate in (code, code.split("-", 1)[0]):
        if candidate in available:
            return candidate
    return None


def _resolve_bundled_doc(name: str, lang: Optional[str]) -> Path:
    """
    Resolves the requested translation of a packaged document to its manifest.

    Ohne --lang entscheidet die Systemsprache: die mitgelieferten Dokumente
    richten sich an die Person vor dem Rechner, nicht an ein Publikum, und
    deren Sprache ist die beste verfuegbare Vermutung.

    Der Unterschied zwischen den beiden Wegen liegt im Hinweis. Eine
    ausdruecklich verlangte Sprache, die es nicht gibt, wird gemeldet -- still
    auf Englisch auszuweichen waere hier besonders unangenehm: wer `--lang fr`
    tippt, bekaeme ein Dokument, das aussieht als waere es uebersetzt worden,
    und merkte es womoeglich nicht. Greift dagegen nur die Erkennung daneben,
    bleibt es still: verlangt wurde nichts, und ein Hinweis bei jedem Aufruf
    waere Laerm.
    """
    available = _available_doc_languages(name)
    if not available:
        console.print(
            f"[bold red]Error:[/bold red] The packaged '{name}' is missing from "
            f"'{get_bundled_doc_dir(name)}'. This points to an incomplete "
            "installation - reinstall markpublish."
        )
        raise typer.Exit(code=1)

    detected = detect_system_language()
    chosen = _match_doc_language(available, lang or detected)

    if chosen is None:
        chosen = DEFAULT_DOC_LANGUAGE if DEFAULT_DOC_LANGUAGE in available else available[0]
        if lang:
            console.print(
                f"[yellow]Note:[/yellow] '{name}' is not available in "
                f"[cyan]{lang.strip().lower()}[/cyan]. Rendering [cyan]{chosen}[/cyan] "
                f"instead (available: {', '.join(available)})."
            )

    return get_bundled_doc_dir(name) / chosen / "markpublish.yaml"


def _render_bundled_doc(
    name: str,
    lang: Optional[str],
    target: str,
    output: Optional[Path],
    theme: Optional[str],
    templates_dir: Optional[Path],
) -> None:
    """Renders one of the documents that ship with markpublish."""
    config_file = _resolve_bundled_doc(name, lang)
    targets_to_build = _parse_targets(target)

    try:
        config = load_config(config_file)
    except Exception as e:
        console.print(f"[bold red]Configuration error:[/bold red] {e}")
        raise typer.Exit(code=1) from e

    if theme:
        config.theme = theme

    # Die Quelle liegt im Paket, das Ergebnis gehoert ins Arbeitsverzeichnis:
    # site-packages ist haeufig schreibgeschuetzt, und selbst wo es das nicht
    # ist, wuerde dort niemand nach seinem PDF suchen.
    #
    # Ohne ausdruecklichen Wunsch rendert das Dokument im mitgelieferten Theme.
    # Sonst zoege ein 'templates/' im Arbeitsverzeichnis - angelegt mit
    # export-template und noch mitten in der Anpassung - die Referenz mit sich:
    # ein fehlendes Label liesse sie abbrechen, ausgerechnet in dem Moment, in
    # dem jemand nachschlagen will, wie Labels funktionieren.
    _render_document(
        config=config,
        base_dir=config_file.parent,
        targets_to_build=targets_to_build,
        output=output,
        effective_templates_dir=templates_dir,
        output_base_dir=Path.cwd(),
        package_templates_only=not (theme or templates_dir),
    )


def _parse_targets(target: str) -> List[str]:
    """Maps the --target option to the list of formats to render."""
    cleaned = target.lower().strip()
    if cleaned in ("all", "both"):
        return ["pdf", "html"]
    if cleaned in ("pdf", "html"):
        return [cleaned]
    console.print(f"[bold red]Error:[/bold red] Unknown target '{target}'. Choose 'pdf', 'html', or 'all'.")
    raise typer.Exit(code=1)


def _is_output_directory(output: Path) -> bool:
    """
    Entscheidet, ob --output als Verzeichnis zu behandeln ist.

    Ein nicht existentes Ziel ohne Dateiendung gilt als Verzeichnis. Sonst
    waere `--output dist` vom Existenzzustand abhaengig und wuerde leicht als
    Dateiname statt Zielordner interpretiert.
    """
    if output.exists():
        return output.is_dir()
    if str(output).endswith(("/", "\\")):
        return True
    return output.suffix == ""


def _render_document(
    config,
    base_dir: Path,
    targets_to_build: List[str],
    output: Optional[Path],
    effective_templates_dir: Optional[Path],
    output_base_dir: Optional[Path] = None,
    package_templates_only: bool = False,
) -> None:
    """
    Renders one loaded configuration into every requested target format.

    `base_dir` is where chapter files and a project theme are looked up.
    `output_base_dir` is where a result lands when no --output was given; it
    defaults to `base_dir`. The two differ for the packaged cheat sheet, whose
    sources sit in site-packages -- writing the PDF next to them would fail on
    a read-only installation and hide the file from the user either way.
    """
    out_root = output_base_dir or base_dir

    for tgt in targets_to_build:
        with console.status(f"[bold green]Processing Markdown and rendering {tgt.upper()}...[/bold green]"):
            try:
                tmpl_path = resolve_template_path(
                    target=tgt,
                    theme=config.theme,
                    custom_templates_dir=effective_templates_dir,
                    config_base_dir=base_dir,
                    package_only=package_templates_only,
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
                if _is_output_directory(output):
                    out_file = output / f"{doc_slug}.{tgt}"
                elif len(targets_to_build) > 1 and output.suffix != f".{tgt}":
                    out_file = output.parent / f"{output.stem}.{tgt}"
                else:
                    out_file = output
            else:
                out_file = out_root / f"{doc_slug}.{tgt}"

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
        help="Custom output file or directory path (a non-existing path without extension is treated as directory).",
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
            # Die Sprache steht mit in der Kopfzeile, weil sie ohne Angabe in
            # der YAML vom System kommt - was gilt, soll man sehen, ohne es
            # ausrechnen zu muessen.
            f"Theme: [cyan]{config.theme}[/cyan] | Language: [cyan]{config.document.language}[/cyan]"
            f" | Targets: [yellow]{target.upper()}[/yellow]",
            title="[bold blue]markpublish build[/bold blue]",
            border_style="blue",
        )
    )

    targets_to_build = _parse_targets(target)
    effective_templates_dir = templates_dir or (Path(config.templates_dir) if config.templates_dir else None)

    _render_document(
        config=config,
        base_dir=base_dir,
        targets_to_build=targets_to_build,
        output=output,
        effective_templates_dir=effective_templates_dir,
    )


@app.command(name="init")
def init_cmd(
    target_dir: Path = typer.Argument(
        Path("."),
        help="Directory to initialize.",
    ),
    title: str = typer.Option(
        "New Document",
        "--title",
        "-t",
        help="Document title.",
    ),
):
    """
    Creates a minimal markpublish project: one config file and one chapter.

    Deliberately small. The scaffold is meant to be deleted as soon as real
    content arrives, so it demonstrates nothing it does not have to -- the
    reference lives in 'markpublish cheatsheet', which stays available after
    the last scaffold file is gone.
    """
    target_dir = target_dir.resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    # Die erkannte Sprache wird hingeschrieben, nicht erst beim Bauen
    # ermittelt: sonst saehe dasselbe Projekt auf einem englischen Rechner
    # anders aus als auf dem, auf dem es entstanden ist.
    yaml_content = f"""# markpublish.yaml
#
# Minimal starting point. For the full reference -- every key of this file, and
# how themes work -- run:
#
#     markpublish cheatsheet
#
document:
  title: "{title}"
  author: "Your Name"
  date: "auto"
  language: "{default_document_language()}"

  # A one-page draft needs neither of these. Switch them on once the document
  # has grown enough to need a way in.
  cover: false
  document_toc: "none"

theme: "default"

# Chapters always live under a part -- that is the two-level structure of a
# markpublish document. One part is enough here; break_before: "none" keeps it
# from claiming a divider page of its own.
parts:
  - title: "Main"
    break_before: "none"
    document_toc: "none"
    chapters:
      - file: "next-steps.md"
        title: "Next steps"
"""
    yaml_file = target_dir / "markpublish.yaml"
    if not yaml_file.exists():
        yaml_file.write_text(yaml_content, encoding="utf-8")

    chapter = target_dir / "next-steps.md"
    if not chapter.exists():
        chapter.write_text("""# Next steps

This project is two files: `markpublish.yaml` and this chapter. Replace both
with your own content -- nothing here is needed once you start writing.

## Build it

```bash
markpublish build                 # PDF
markpublish build --target html   # standalone HTML
markpublish build --target all    # both
```

## Look things up

```bash
markpublish cheatsheet
```

Renders a two-page reference: every key of `markpublish.yaml` on page one,
themes and templates on page two. It is generated by the version you have
installed, so it cannot drift out of date.

## Add a chapter

Write a Markdown file, then list it under a part's `chapters:` in
`markpublish.yaml`. Paths are relative to the config file:

```yaml
parts:
  - title: "Main"
    break_before: "none"
    chapters:
      - file: "next-steps.md"
        title: "Next steps"
      - file: "chapters/01_introduction.md"
        title: "Introduction"
```

A document is always two levels: parts divide it, chapters carry the content.

## Change the look

```bash
markpublish export-template default ./templates
```

Copies the built-in theme into your project, where markpublish picks it up
automatically on the next build.
""", encoding="utf-8")

    console.print(f"[bold green][OK][/bold green] Initialized markpublish project in [cyan]{target_dir}[/cyan]")
    console.print("Run [bold cyan]markpublish build[/bold cyan] to generate your first PDF.")
    console.print("Run [bold cyan]markpublish cheatsheet[/bold cyan] for the two-page reference.")


@app.command(name="cheatsheet")
def cheatsheet_cmd(
    lang: Optional[str] = typer.Option(
        None,
        "--lang",
        "-l",
        help="Language of the bundled source to render (default: your system language, else en).",
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
        help="Custom output file or directory path. Defaults to the current directory.",
    ),
    theme: Optional[str] = typer.Option(
        None,
        "--theme",
        help="Render with a theme of your own instead of the built-in one.",
    ),
    templates_dir: Optional[Path] = typer.Option(
        None,
        "--templates-dir",
        help="Custom templates directory path.",
    ),
):
    """
    Renders the two-page reference for markpublish.yaml and themes.

    The source ships inside the package and is rendered on demand, so the
    result always matches the installed version -- and a successful run doubles
    as proof that the rendering toolchain works. Only the finished document is
    written; no sources land in your project.
    """
    _render_bundled_doc("cheatsheet", lang, target, output, theme, templates_dir)


@app.command(name="manual")
def manual_cmd(
    lang: Optional[str] = typer.Option(
        None,
        "--lang",
        "-l",
        help="Language of the bundled source to render (default: your system language, else en).",
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
        help="Custom output file or directory path. Defaults to the current directory.",
    ),
    theme: Optional[str] = typer.Option(
        None,
        "--theme",
        help="Render with a theme of your own instead of the built-in one.",
    ),
    templates_dir: Optional[Path] = typer.Option(
        None,
        "--templates-dir",
        help="Custom templates directory path.",
    ),
):
    """
    Renders the full user guide.

    Same deal as 'cheatsheet': the source ships with the package, so the guide
    describes the version you actually have rather than whatever was current
    when someone last rebuilt a PDF. Use --lang to pick a translation.
    """
    _render_bundled_doc("manual", lang, target, output, theme, templates_dir)


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
    table.add_column("Active", justify="center")
    table.add_column("Path", style="dim")

    for t in all_tmpls:
        if target and t["target"] != target.lower().strip():
            continue
        active_str = "[bold green]Yes[/bold green]" if t["is_active"] else "[dim]No[/dim]"
        table.add_row(t["target"], t["theme"], t["source"], active_str, t["path"])

    console.print(table)


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
    targets = _parse_targets(target)

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
