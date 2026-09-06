"""
markpublish CLI Interface.
"""

from __future__ import annotations

import shutil
import sys
import warnings
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
from markpublish.config.models import ConfigurationError
from markpublish.i18n import (
    BUILTIN_I18N_PATH,
    I18N_FILENAME,
    LEVEL_BUILTIN,
    LabelFileError,
    UndefinedLabelError,
    UndefinedMetadataError,
    describe_labels,
    detect_system_language,
    normalize_language,
)
from markpublish.markdown.engine import MarkdownPipeline
from markpublish.markdown.toc import slugify
from markpublish.renderers.base import DocumentContext
from markpublish.renderers.pdf import PDFRenderer
from markpublish.templates.contract import (
    DiagnosisStatus,
    Severity,
    ThemeContractWarning,
    ThemeUsage,
    check_theme_contract,
    diagnose_labels_and_metadata,
    parse_sent_arguments,
    parse_theme_contract,
)
from markpublish.templates.resolver import (
    get_package_templates_dir,
    list_templates,
    resolve_template_path,
)
from markpublish.ui import set_ui_language, t, tn

app = typer.Typer(
    name="markpublish",
    help=t("app.help"),
)
console = Console()


def version_callback(value: bool):
    if value:
        console.print(
            f"[bold blue]markpublish[/bold blue] "
            f"{t('app.version_word')} [green]{__version__}[/green]"
        )
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help=t("opt.version.help"),
        callback=version_callback,
        is_eager=True,
    ),
    ui_lang: Optional[str] = typer.Option(
        None,
        "--ui-lang",
        help=t("opt.ui_lang.help"),
    ),
):
    """
    markpublish CLI.

    `--ui-lang` ist hier nur angemeldet, damit die Flagge in der Hilfe
    steht und ein direkter Aufruf von `markpublish.cli:app` sie nicht als
    unbekannt zurueckweist. Ausgewertet hat sie der Einsprung (entry.py)
    schon vor dem Import -- fuer die Hilfetexte muss sie das auch, die
    entstehen beim Import. Erneut gesetzt wird sie nur fuer den Fall, dass
    jemand die App unter Umgehung des Einsprungs aufruft; dann stimmen
    wenigstens die Meldungen zur Laufzeit.
    """
    if ui_lang:
        set_ui_language(ui_lang)


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
            f"[bold red]{t('label.error')}[/bold red] "
            + t("err.bundled.missing", name=name, path=get_bundled_doc_dir(name))
        )
        raise typer.Exit(code=1)

    detected = detect_system_language()
    chosen = _match_doc_language(available, lang or detected)

    if chosen is None:
        chosen = DEFAULT_DOC_LANGUAGE if DEFAULT_DOC_LANGUAGE in available else available[0]
        if lang:
            console.print(
                f"[yellow]{t('label.note')}[/yellow] "
                + t(
                    "note.doc.lang_unavailable",
                    name=name,
                    requested=f"[cyan]{lang.strip().lower()}[/cyan]",
                    chosen=f"[cyan]{chosen}[/cyan]",
                    available=", ".join(available),
                )
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
        console.print(f"[bold red]{t('label.config_error')}[/bold red] {e}")
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
    console.print(
        f"[bold red]{t('label.error')}[/bold red] "
        + t("err.target.unknown", target=target)
    )
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
        if tgt == "html":
            console.print(
                f"[yellow]{t('label.notice')}[/yellow] "
                + t("notice.html.unimplemented")
            )
            continue

        status_text = t("status.rendering", target=tgt.upper())
        with console.status(f"[bold green]{status_text}[/bold green]"):
            try:
                tmpl_path = resolve_template_path(
                    target=tgt,
                    theme=config.theme,
                    custom_templates_dir=effective_templates_dir,
                    config_base_dir=base_dir,
                    package_only=package_templates_only,
                )
            except Exception as e:
                console.print(f"[bold red]{t('label.template_error', target=tgt)}[/bold red] {e}")
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
                console.print(
                    f"[bold red]{t('label.label_file_error_target', target=tgt)}[/bold red] {e}"
                )
                raise typer.Exit(code=1) from e

            try:
                pipeline = MarkdownPipeline(config, base_dir=base_dir, labels=labels)
                context.content_items, context.toc_tree = pipeline.process_document()
            except ConfigurationError as e:
                console.print(f"[bold red]Configuration error:[/bold red] {e}")
                raise typer.Exit(code=1) from e

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
                renderer = PDFRenderer()
                # Theme-Warnungen einsammeln statt sie von Python mit
                # Dateiname und Zeilennummer der Warnstelle drucken zu lassen:
                # interessant ist die Fundstelle im Theme, nicht die im Code.
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always", ThemeContractWarning)
                    out_result = renderer.render(context, out_file)
                for entry in caught:
                    if issubclass(entry.category, ThemeContractWarning):
                        console.print(
                            f"[yellow]{t('label.theme_warning', target=tgt)}[/yellow] "
                            f"{entry.message}"
                        )
                    else:
                        warnings.warn_explicit(
                            entry.message, entry.category, entry.filename, entry.lineno
                        )
                console.print(
                    "[bold green][OK][/bold green] "
                    + t("ok.generated", target=tgt.upper(), path=f"[cyan]{out_result}[/cyan]")
                )
            except UndefinedLabelError as e:
                # Eigener Zweig, weil die Meldung mehrzeilig ist und Fundstelle
                # samt durchsuchten Dateien nennt - die gehoert nicht hinter ein
                # "Rendering error:" auf dieselbe Zeile gequetscht.
                console.print(f"[bold red]{t('label.undefined_label', target=tgt)}[/bold red]")
                console.print(str(e))
                raise typer.Exit(code=1) from e
            except UndefinedMetadataError as e:
                console.print(f"[bold red]{t('label.undefined_metadata', target=tgt)}[/bold red]")
                console.print(str(e))
                raise typer.Exit(code=1) from e
            except Exception as e:
                console.print(f"[bold red]{t('label.rendering_error', target=tgt)}[/bold red] {e}")
                raise typer.Exit(code=1) from e


@app.command(name="build", help=t("cmd.build.help"))
def build_cmd(
    config_file: Path = typer.Argument(
        Path("markpublish.yaml"),
        help=t("opt.config_file.help"),
        exists=False,
    ),
    target: str = typer.Option(
        "pdf",
        "--target",
        "-t",
        help=t("opt.target.help"),
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help=t("opt.output.help"),
    ),
    theme: Optional[str] = typer.Option(
        None,
        "--theme",
        help=t("opt.theme.help"),
    ),
    templates_dir: Optional[Path] = typer.Option(
        None,
        "--templates-dir",
        help=t("opt.templates_dir.help"),
    ),
):
    """
    Builds document to PDF and/or HTML based on markpublish.yaml.
    """
    if not config_file.exists():
        console.print(
            f"[bold red]{t('label.error')}[/bold red] "
            + t("err.config.notfound", path=config_file)
        )
        raise typer.Exit(code=1)

    base_dir = config_file.parent.resolve()

    with console.status(f"[bold green]{t('status.loading_config')}[/bold green]"):
        try:
            config = load_config(config_file)
        except Exception as e:
            console.print(f"[bold red]Configuration error:[/bold red] {e}")
            raise typer.Exit(code=1) from e

    if theme:
        config.theme = theme

    console.print(
        Panel(
            f"[bold]{config.document.title}[/bold]\n"
            + t(
                "panel.build.meta",
                author=config.document.author or t("value.na"),
                version=config.document.version or t("value.na"),
                date=config.document.date,
            )
            + "\n"
            # Die Sprache steht mit in der Kopfzeile, weil sie ohne Angabe in
            # der YAML vom System kommt - was gilt, soll man sehen, ohne es
            # ausrechnen zu muessen.
            + t(
                "panel.build.setup",
                theme=f"[cyan]{config.theme}[/cyan]",
                language=f"[cyan]{config.document.language}[/cyan]",
                targets=f"[yellow]{target.upper()}[/yellow]",
            ),
            title=f"[bold blue]{t('panel.build.title')}[/bold blue]",
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


@app.command(name="init", help=t("cmd.init.help"))
def init_cmd(
    target_dir: Path = typer.Argument(
        Path("."),
        help=t("opt.target_dir.help"),
    ),
    title: str = typer.Option(
        "New Document",
        "--title",
        "-t",
        help=t("opt.title.help"),
    ),
    lang: Optional[str] = typer.Option(
        None,
        "--lang",
        "-l",
        help=t("opt.lang_init.help"),
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

    available = _available_doc_languages("init")
    if not available:
        console.print(
            f"[bold red]{t('label.error')}[/bold red] "
            + t("err.init_template.missing", path=get_bundled_doc_dir("init"))
        )
        raise typer.Exit(code=1)

    detected = detect_system_language()
    chosen = _match_doc_language(available, lang or detected)

    if chosen is None:
        chosen = DEFAULT_DOC_LANGUAGE if DEFAULT_DOC_LANGUAGE in available else available[0]
        if lang:
            console.print(
                f"[yellow]{t('label.note')}[/yellow] "
                + t(
                    "note.init.lang_unavailable",
                    requested=f"[cyan]{lang.strip().lower()}[/cyan]",
                    chosen=f"[cyan]{chosen}[/cyan]",
                    available=", ".join(available),
                )
            )

    src_dir = get_bundled_doc_dir("init") / chosen
    yaml_src = src_dir / "markpublish.yaml"
    yaml_target = target_dir / "markpublish.yaml"

    if not yaml_target.exists() and yaml_src.is_file():
        template_text = yaml_src.read_text(encoding="utf-8")
        filled_text = template_text.replace("{title}", title)
        yaml_target.write_text(filled_text, encoding="utf-8")

    # Copy companion files (e.g. welcome.md, images)
    for f in src_dir.iterdir():
        if f.name == "markpublish.yaml" or not f.is_file() or f.suffix.lower() == ".pdf":
            continue
        dest = target_dir / f.name
        if not dest.exists():
            if f.suffix.lower() in (".md", ".txt", ".yaml", ".yml", ".json"):
                try:
                    text = f.read_text(encoding="utf-8")
                    dest.write_text(text.replace("{title}", title), encoding="utf-8")
                except UnicodeDecodeError:
                    shutil.copy2(f, dest)
            else:
                shutil.copy2(f, dest)

    console.print(
        "[bold green][OK][/bold green] "
        + t("ok.init.done", path=f"[cyan]{target_dir}[/cyan]")
    )
    console.print(t("init.next.build", command="[bold cyan]markpublish build[/bold cyan]"))
    console.print(
        t("init.next.cheatsheet", command="[bold cyan]markpublish cheatsheet[/bold cyan]")
    )


@app.command(name="cheatsheet", help=t("cmd.cheatsheet.help"))
def cheatsheet_cmd(
    lang: Optional[str] = typer.Option(
        None,
        "--lang",
        "-l",
        help=t("opt.lang_bundled.help"),
    ),
    target: str = typer.Option(
        "pdf",
        "--target",
        "-t",
        help=t("opt.target.help"),
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help=t("opt.output_bundled.help"),
    ),
    theme: Optional[str] = typer.Option(
        None,
        "--theme",
        help=t("opt.theme.help"),
    ),
    templates_dir: Optional[Path] = typer.Option(
        None,
        "--templates-dir",
        help=t("opt.templates_dir.help"),
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


@app.command(name="manual", help=t("cmd.manual.help"))
def manual_cmd(
    lang: Optional[str] = typer.Option(
        None,
        "--lang",
        "-l",
        help=t("opt.lang_bundled.help"),
    ),
    target: str = typer.Option(
        "pdf",
        "--target",
        "-t",
        help=t("opt.target.help"),
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help=t("opt.output_bundled.help"),
    ),
    theme: Optional[str] = typer.Option(
        None,
        "--theme",
        help=t("opt.theme.help"),
    ),
    templates_dir: Optional[Path] = typer.Option(
        None,
        "--templates-dir",
        help=t("opt.templates_dir.help"),
    ),
):
    """
    Renders the full user guide.

    Same deal as 'cheatsheet': the source ships with the package, so the guide
    describes the version you actually have rather than whatever was current
    when someone last rebuilt a PDF. Use --lang to pick a translation.
    """
    _render_bundled_doc("manual", lang, target, output, theme, templates_dir)


@app.command(name="templates", help=t("cmd.templates.help"))
def templates_list_cmd(
    target: Optional[str] = typer.Option(
        None,
        "--target",
        "-t",
        help=t("opt.target_filter.help"),
    ),
    templates_dir: Optional[Path] = typer.Option(
        None,
        "--templates-dir",
        help=t("opt.templates_dir.help"),
    ),
):
    """
    Lists all available templates across User, Common, and Package sources.
    """
    all_tmpls = list_templates(custom_templates_dir=templates_dir)

    table = Table(
        title=t("table.templates.title"), show_header=True, header_style="bold blue"
    )
    table.add_column(t("table.templates.target"), style="yellow")
    table.add_column(t("table.templates.theme"), style="bold")
    table.add_column(t("table.templates.source"), style="cyan")
    table.add_column(t("table.templates.active"), justify="center")
    table.add_column(t("table.templates.path"), style="dim")

    for tmpl in all_tmpls:
        if target and tmpl["target"] != target.lower().strip():
            continue
        active_str = (
            f"[bold green]{t('value.yes')}[/bold green]"
            if tmpl["is_active"]
            else f"[dim]{t('value.no')}[/dim]"
        )
        table.add_row(tmpl["target"], tmpl["theme"], tmpl["source"], active_str, tmpl["path"])

    console.print(table)


@app.command(name="export-template", help=t("cmd.export_template.help"))
def export_template_cmd(
    theme: str = typer.Argument("default", help=t("opt.export_theme.help")),
    destination: Path = typer.Argument(Path("templates"), help=t("opt.export_destination.help")),
    target: str = typer.Option("all", "--target", "-t", help=t("opt.export_target.help")),
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
            console.print(
                f"[yellow]{t('label.warning')}[/yellow] "
                + t("warn.export.notfound", theme=theme, target=tgt, path=src)
            )
            continue

        dest = destination / theme / tgt
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dest, dirs_exist_ok=True)
        exported_any = True
        console.print(
            "[bold green][OK][/bold green] "
            + t(
                "ok.export.template",
                name=f"[cyan]{tgt}/{theme}[/cyan]",
                path=f"[yellow]{dest}[/yellow]",
            )
        )

    # Die i18n.yaml auf Theme-Ebene liegt neben den Zielformat-Ordnern, nicht
    # darin - ohne diesen Schritt exportiert man das Theme und ausgerechnet die
    # Datei, in der die statischen Texte definiert werden, bliebe zurueck.
    theme_i18n = pkg_base / theme / I18N_FILENAME
    if exported_any and theme_i18n.is_file():
        dest_i18n = destination / theme / I18N_FILENAME
        if dest_i18n.exists():
            console.print(f"[dim]{t('info.export.kept')}[/dim] [yellow]{dest_i18n}[/yellow]")
        else:
            shutil.copy2(theme_i18n, dest_i18n)
            console.print(
                "[bold green][OK][/bold green] "
                + t(
                    "ok.export.i18n",
                    name=f"[cyan]{theme}/{I18N_FILENAME}[/cyan]",
                    path=f"[yellow]{dest_i18n}[/yellow]",
                )
            )



#: Wie ein Befund in der Tabelle heisst. Der Text steht hier und nicht in
#: contract.py: dort geht es darum, *was* der Fall ist, hier darum, wie es
#: dasteht. Die Bilanz zaehlt ueber `Severity`, nicht ueber diese Zeichenketten.
#: Befund -> (Stil, Schluessel). Getrennt, weil das eine Gestaltung ist und
#: das andere Sprache: eine Uebersetzung soll keine Markup-Klammer schliessen
#: muessen, um die Ausgabe heil zu lassen.
_STATUS_STYLE = {
    DiagnosisStatus.OK: ("green", "labels.status.ok"),
    DiagnosisStatus.UNUSED: ("dim", "labels.status.unused"),
    DiagnosisStatus.LABEL_MISSING: ("yellow", "labels.status.label_missing"),
    DiagnosisStatus.LABEL_FALLBACK: ("yellow", "labels.status.label_fallback"),
    DiagnosisStatus.VALUE_MISSING: ("dim", "labels.status.value_missing"),
    DiagnosisStatus.VALUE_FALLBACK: ("yellow", "labels.status.value_fallback"),
    DiagnosisStatus.LABEL_AND_VALUE_FALLBACK: ("yellow", "labels.status.label_and_value_fallback"),
    DiagnosisStatus.LABEL_FALLBACK_VALUE_MISSING: ("yellow", "labels.status.label_fallback_value_missing"),
    DiagnosisStatus.LABEL_BREAKS: ("bold red", "labels.status.label_breaks"),
    DiagnosisStatus.META_KEY_UNKNOWN: ("bold red", "labels.status.meta_key_unknown"),
    DiagnosisStatus.LABEL_AND_META_BREAK: ("bold red", "labels.status.label_and_meta_break"),
}


def _status_text(row) -> str:
    """Formuliert einen Befund fuer die Tabelle."""
    entry = _STATUS_STYLE.get(row.status)
    if entry is None:
        return str(row.status.value)
    style, key = entry
    return f"[{style}]{t(key, detail=row.status_detail or '')}[/{style}]"


@app.command(name="labels", help=t("cmd.labels.help"))
def labels_cmd(
    config_file: Path = typer.Argument(
        Path("markpublish.yaml"),
        help=t("opt.config_file.help"),
    ),
    target: str = typer.Option(
        "pdf",
        "--target",
        "-t",
        help=t("opt.target_labels.help"),
    ),
    theme: Optional[str] = typer.Option(
        None,
        "--theme",
        help=t("opt.theme_labels.help"),
    ),
    templates_dir: Optional[Path] = typer.Option(
        None,
        "--templates-dir",
        help=t("opt.templates_dir.help"),
    ),
    only_overridden: bool = typer.Option(
        False,
        "--overridden",
        help=t("opt.overridden.help"),
    ),
):
    """
    Shows the resolved static texts and which layer supplied each one.

    Cascade, later wins: markpublish/i18n.yaml -> <theme>/i18n.yaml ->
    <theme>/<target>/i18n.yaml -> i18n.yaml next to markpublish.yaml. The
    theme is the one the template resolution picked; the project level has
    the last word and is where a document names its own free metadata fields.
    """
    if not config_file.exists():
        console.print(
            f"[bold red]{t('label.error')}[/bold red] "
            + t("err.config.notfound", path=config_file)
        )
        raise typer.Exit(code=1)

    base_dir = config_file.parent.resolve()

    try:
        config = load_config(config_file)
    except Exception as e:
        console.print(f"[bold red]Configuration error:[/bold red] {e}")
        raise typer.Exit(code=1) from e

    if theme:
        config.theme = theme

    tgt = target.lower().strip()
    if tgt not in ("pdf", "html"):
        console.print(
            f"[bold red]{t('label.error')}[/bold red] "
            + t("err.target.unknown_labels", target=target)
        )
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
        console.print(f"[bold red]{t('label.template_error', target=tgt)}[/bold red] {e}")
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
        levels = context.label_levels
        resolved = describe_labels(
            config.document.language,
            template_dirs=[directory for _, directory in levels],
            level_names=[name for name, _ in levels],
        )
    except LabelFileError as e:
        console.print(f"[bold red]{t('label.label_file_error')}[/bold red] {e}")
        raise typer.Exit(code=1) from e

    console.print(
        Panel(
            t(
                "panel.labels.summary",
                language=f"[cyan]{config.document.language}[/cyan]",
                theme=f"[cyan]{config.theme}[/cyan]",
                target=f"[yellow]{tgt.upper()}[/yellow]",
            ),
            title=f"[bold blue]{t('panel.labels.title')}[/bold blue]",
            border_style="blue",
        )
    )

    contract = parse_theme_contract(tmpl_path)
    rows = diagnose_labels_and_metadata(contract, config.document, resolved)
    document_language = normalize_language(config.document.language)

    # Ein Theme, das `meta:` nicht deklariert, bricht beim Bauen ab. Dieser
    # Befehl soll das *vor* dem Bauen sagen. Geprueft wird gegen den echten
    # Aufruf -- derselbe Weg wie im Renderer, damit hier keine zweite,
    # nachzupflegende Parameterliste entsteht.
    probe = PDFRenderer()._assemble_typst_document(context, tmpl_path)
    signature_errors = check_theme_contract(contract, parse_sent_arguments(probe)).errors

    table = Table(show_header=True, header_style="bold blue")
    table.add_column(t("table.labels.key"), style="bold", no_wrap=True)
    table.add_column(t("table.labels.usage"), justify="center", no_wrap=True)
    table.add_column(t("table.labels.label"))
    table.add_column(t("table.labels.source"), no_wrap=True)
    table.add_column(t("table.labels.label_fallback"), style="dim")
    table.add_column(t("table.labels.value"))
    table.add_column(t("table.labels.value_fallback"), style="dim")
    table.add_column(t("table.labels.status"))

    breaking = [row.key for row in rows if row.severity is Severity.ERROR]
    warned = [row.key for row in rows if row.severity is Severity.WARNING]
    unused = [row.key for row in rows if row.status is DiagnosisStatus.UNUSED]

    for row in rows:
        entry = resolved.get(row.key)
        overridden = bool(entry) and entry["path"] != str(BUILTIN_I18N_PATH)

        # `--overridden` heisst wieder, was es sagt: nur Zeilen, bei denen eine
        # Theme-Ebene den Programmstandard ersetzt. Fehler bleiben immer
        # sichtbar -- ein Filter, der einen Abbruch verschweigt, waere eine
        # Falle.
        if only_overridden and not overridden and row.severity is not Severity.ERROR:
            continue

        if not row.applies_label:
            lbl_display = "[dim]n/a[/dim]"
        elif row.i18n_label is not None:
            lbl_display = row.i18n_label
        else:
            lbl_display = f"[red]\\{t('value.missing')}[/red]"

        if not entry:
            source_display = "[dim]-[/dim]"
        else:
            # Der Sprachblock steht nur dabei, wo er von der Dokumentsprache
            # abweicht -- also beim Rueckfall auf die Fallback-Sprache oder bei
            # "*". Sonst wiederholte jede Zeile, was im Kopf der Ausgabe steht.
            name = entry["source"]
            block = entry.get("language")
            if block and block != document_language:
                name = f"{name} ({block})"
            style = "green" if overridden else "dim"
            source_display = f"[{style}]{name}[/{style}]"

        if not row.applies_value:
            val_display = "[dim]n/a[/dim]"
        elif row.value is not None:
            val_display = row.value
        else:
            val_display = f"[dim]{t('value.not_set')}[/dim]"

        usage_display = (
            "[dim]-[/dim]"
            if row.theme_usage is ThemeUsage.NONE
            else f"[cyan]{row.theme_usage.value}[/cyan]"
        )

        table.add_row(
            row.key,
            usage_display,
            lbl_display,
            source_display,
            f'"{row.label_fallback}"' if row.label_fallback else "-",
            val_display,
            row.value_fallback or "-",
            _status_text(row),
        )

    console.print(table)

    if signature_errors:
        console.print(f"\n[bold red]{t('labels.signature_mismatch')}[/bold red]")
        for message in signature_errors:
            console.print(f"  {message}")
    if breaking:
        console.print(
            f"\n[bold red]{tn('labels.breaking', len(breaking))}[/bold red] "
            + ", ".join(breaking)
        )
    if warned:
        console.print(
            f"\n[yellow]{tn('labels.warned', len(warned))}[/yellow] "
            + ", ".join(warned)
        )
    if unused:
        console.print(
            f"\n[dim]{tn('labels.unused', len(unused))}[/dim] "
            + ", ".join(unused)
        )
    if not signature_errors and not breaking and not warned and not unused:
        console.print(f"\n[green]{t('labels.all_clear')}[/green]")

    # Mit dem Ebenennamen davor: die Spalte oben nennt nur "theme" oder
    # "projekt", hier steht, welche Datei das jeweils ist.
    console.print(f"\n[dim]{t('labels.cascade.intro')}[/dim]")
    console.print(
        f"  [bold]{LEVEL_BUILTIN:<8}[/bold] {BUILTIN_I18N_PATH}  "
        f"[dim]{t('labels.cascade.builtin')}[/dim]"
    )
    for name, directory in levels:
        path = directory / I18N_FILENAME
        marker = (
            f"[green]{t('labels.cascade.found')}[/green]"
            if path.is_file()
            else f"[dim]{t('labels.cascade.absent')}[/dim]"
        )
        console.print(f"  [bold]{name:<8}[/bold] {path}  {marker}")
