#!/usr/bin/env python3
"""
Baut das offizielle markpublish-Referenzdokument (DE & EN) und erzeugt
sowohl die druckreifen Gesamt-PDFs unter www/manuals/ als auch die
einzelnen Vektor-Seiten (SVG & Retina-PNG) unter www/assets/showcase/.
"""

from __future__ import annotations

import pathlib
import shutil
import tempfile

import zipfile

import typst

from markpublish.config.loader import load_config
from markpublish.markdown.engine import MarkdownPipeline
from markpublish.renderers.base import DocumentContext
from markpublish.renderers.pdf import PDFRenderer
from markpublish.templates.resolver import resolve_template_path

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
SAMPLE_DIR = ROOT_DIR / "www" / "sample"
MANUALS_DIR = ROOT_DIR / "www" / "manuals"
SHOWCASE_DIR = ROOT_DIR / "www" / "assets" / "showcase"

DOCUMENTS = {
    "de": {
        "src": SAMPLE_DIR / "de",
        "pdf_name": "markpublish_beispieldokument.pdf",
        "zip_name": "markpublish_beispielprojekt.zip",
        "prefix": "de",
    },
    "en": {
        "src": SAMPLE_DIR / "en",
        "pdf_name": "markpublish_sample_document.pdf",
        "zip_name": "markpublish_sample_project.zip",
        "prefix": "en",
    },
}


def build_showcase_assets(
    manuals_dir: pathlib.Path = MANUALS_DIR,
    showcase_dir: pathlib.Path = SHOWCASE_DIR,
) -> None:
    manuals_dir.mkdir(parents=True, exist_ok=True)
    showcase_dir.mkdir(parents=True, exist_ok=True)

    for lang_code, info in DOCUMENTS.items():
        doc_dir = info["src"]
        cfg_file = doc_dir / "markpublish.yaml"
        if not cfg_file.is_file():
            raise FileNotFoundError(f"Konfigurationsdatei fehlt: {cfg_file}")

        config = load_config(cfg_file)
        tmpl_path = resolve_template_path("pdf", theme="default", config_base_dir=doc_dir, package_only=True)
        ctx = DocumentContext(
            config=config,
            content_items=[],
            toc_tree=[],
            template_path=tmpl_path,
            base_dir=doc_dir,
            target="pdf",
        )
        pipeline = MarkdownPipeline(config, base_dir=doc_dir, labels=ctx.labels)
        ctx.content_items, ctx.toc_tree = pipeline.process_document()

        # 1. Gesamt-PDF nach www/manuals/ rendern
        pdf_out = manuals_dir / info["pdf_name"]
        renderer = PDFRenderer()
        renderer.render(ctx, pdf_out)
        print(f"[OK] Referenz-PDF erzeugt: {pdf_out} ({pdf_out.stat().st_size / 1024:.1f} kB)")

        # 2. Beispielprojekt als ZIP-Archiv nach www/manuals/ packen
        zip_out = manuals_dir / info["zip_name"]
        with zipfile.ZipFile(zip_out, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in sorted(doc_dir.glob("*")):
                if file_path.is_file():
                    zf.write(file_path, arcname=file_path.name)
        print(f"[OK] Beispielprojekt-Zip erzeugt: {zip_out} ({zip_out.stat().st_size / 1024:.1f} kB)")

        # 2. Vektor-Seiten (SVG) und Retina-PNGs nach www/assets/showcase/ erzeugen
        with tempfile.TemporaryDirectory() as td:
            tmp_build = pathlib.Path(td) / "build"
            tmp_build.mkdir()
            for item in tmpl_path.iterdir():
                if item.is_dir():
                    shutil.copytree(item, tmp_build / item.name)
                else:
                    shutil.copy2(item, tmp_build / item.name)

            typst_src = renderer._assemble_typst_document(ctx, tmp_build)
            main_typ = tmp_build / "main.typ"
            main_typ.write_text(typst_src, encoding="utf-8")

            font_paths = []
            theme_fonts = tmpl_path / "fonts"
            if theme_fonts.is_dir():
                font_paths.append(theme_fonts)

            svg_pattern = tmp_build / f"{info['prefix']}_page_{{n}}.svg"
            typst.compile(
                main_typ,
                output=svg_pattern,
                root=tmp_build,
                font_paths=font_paths,
                format="svg",
            )

            png_pattern = tmp_build / f"{info['prefix']}_page_{{n}}.png"
            typst.compile(
                main_typ,
                output=png_pattern,
                root=tmp_build,
                font_paths=font_paths,
                format="png",
                ppi=144.0,
            )

            for page_svg in tmp_build.glob(f"{info['prefix']}_page_*.svg"):
                dest = showcase_dir / page_svg.name
                shutil.copy2(page_svg, dest)

            for page_png in tmp_build.glob(f"{info['prefix']}_page_*.png"):
                dest = showcase_dir / page_png.name
                shutil.copy2(page_png, dest)

        print(f"[OK] Showcase-Einzelseiten für '{lang_code}' nach {showcase_dir} exportiert.")


if __name__ == "__main__":
    build_showcase_assets()
