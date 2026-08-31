"""
Tests fuer die fontconfig-Initialisierung des PDF-Renderers.

Hintergrund: GTK-Runtimes wie darktable oder GIMP liefern libfontconfig-1.dll
ohne die etc/fonts/fonts.conf mit, die fontconfig neben der Installation
erwartet. Ergebnis war die Meldung "Fontconfig error: Cannot load default
config file: File not found" bei jedem Build - und generische Familien
(sans-serif, monospace) fielen auf einen beliebigen Font zurueck.

Die Tests laufen ohne GTK/Pango: geprueft wird die Pfadlogik, nicht das
Rendering.
"""

from __future__ import annotations

import os
from pathlib import Path
from xml.etree import ElementTree

import pytest

from markpublish.renderers.pdf import BUNDLED_FONTS_CONF, _init_fontconfig


@pytest.fixture(autouse=True)
def _clean_fontconfig_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("FONTCONFIG_FILE", raising=False)
    monkeypatch.delenv("FONTCONFIG_PATH", raising=False)


def test_bundled_config_is_valid_xml_and_shipped():
    assert BUNDLED_FONTS_CONF.is_file(), f"{BUNDLED_FONTS_CONF} fehlt im Paket"
    root = ElementTree.parse(BUNDLED_FONTS_CONF).getroot()
    assert root.tag == "fontconfig"
    aliased = {alias.findtext("family") for alias in root.findall("alias")}
    assert {"sans-serif", "serif", "monospace"} <= aliased


def test_falls_back_to_bundled_config_when_runtime_ships_none(tmp_path: Path):
    """darktable & Co: bin/ vorhanden, etc/fonts/fonts.conf fehlt."""
    gtk_bin = tmp_path / "darktable" / "bin"
    gtk_bin.mkdir(parents=True)

    _init_fontconfig(gtk_bin)

    assert os.environ["FONTCONFIG_FILE"] == str(BUNDLED_FONTS_CONF)
    assert os.environ["FONTCONFIG_PATH"] == str(BUNDLED_FONTS_CONF.parent)


def test_prefers_config_shipped_with_the_runtime(tmp_path: Path):
    """GTK3-Runtime/MSYS2 bringen eine eigene fonts.conf mit - die gewinnt."""
    gtk_bin = tmp_path / "GTK3-Runtime Win64" / "bin"
    gtk_bin.mkdir(parents=True)
    runtime_conf = tmp_path / "GTK3-Runtime Win64" / "etc" / "fonts" / "fonts.conf"
    runtime_conf.parent.mkdir(parents=True)
    runtime_conf.write_text("<fontconfig/>", encoding="utf-8")

    _init_fontconfig(gtk_bin)

    assert os.environ["FONTCONFIG_FILE"] == str(runtime_conf)
    assert os.environ["FONTCONFIG_PATH"] == str(runtime_conf.parent)


def test_existing_user_setup_is_never_overwritten(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FONTCONFIG_FILE", r"C:\eigene\fonts.conf")
    gtk_bin = tmp_path / "bin"
    gtk_bin.mkdir()

    _init_fontconfig(gtk_bin)

    assert os.environ["FONTCONFIG_FILE"] == r"C:\eigene\fonts.conf"
    assert "FONTCONFIG_PATH" not in os.environ
