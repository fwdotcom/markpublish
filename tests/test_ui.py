"""
Tests fuer die Sprache der Programmoberflaeche.

Drei Dinge werden hier festgehalten, und jedes hat einen eigenen Grund:

* Die Kataloge muessen deckungsgleich sein. Eine Uebersetzung verrottet sonst
  still -- ein Schluessel wird auf Englisch ergaenzt, auf Deutsch vergessen,
  und niemand merkt es, weil der Rueckfall greift.
* Die Reihenfolge der Aufloesung ist eine Zusage an den Benutzer und keine
  Nebensaechlichkeit der Umsetzung.
* Es darf keinen Text mehr geben, der an der Aufrufstelle festgeschrieben ist.
  Der Katalog kann nur uebersetzen, was ueberhaupt durch ihn hindurchgeht.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest

from markpublish import entry, ui

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "src" / "markpublish"

PLACEHOLDER = re.compile(r"\{(\w+)")


# --------------------------------------------------------------------------
# Die Kataloge gegeneinander
# --------------------------------------------------------------------------


def test_every_language_carries_the_same_keys():
    """
    Kein Katalog darf einen Schluessel fuehren, den ein anderer nicht hat.

    Der Rueckfall auf Englisch faengt eine Luecke zwar auf -- aber still. Ein
    Test, der sie benennt, ist der Unterschied zwischen einer Uebersetzung,
    die gepflegt wird, und einer, die man fuer gepflegt haelt.
    """
    reference = set(ui.CATALOGS[ui.UI_FALLBACK])
    for language, catalog in ui.CATALOGS.items():
        missing = sorted(reference - set(catalog))
        extra = sorted(set(catalog) - reference)
        assert not missing, f"{language}.yaml fehlen: {missing}"
        assert not extra, f"{language}.yaml fuehrt unbekannte Schluessel: {extra}"


def test_placeholders_match_across_languages():
    """
    Eine Uebersetzung darf keinen Platzhalter erfinden oder verlieren.

    Ein erfundener bricht zur Laufzeit ab, ein verlorener unterschlaegt die
    Angabe, um die es in der Meldung ging -- den Pfad etwa.
    """
    reference = ui.CATALOGS[ui.UI_FALLBACK]
    for language, catalog in ui.CATALOGS.items():
        for key, text in catalog.items():
            assert set(PLACEHOLDER.findall(text)) == set(PLACEHOLDER.findall(reference[key])), (
                f"{language}.yaml: '{key}' hat andere Platzhalter als {ui.UI_FALLBACK}.yaml"
            )


def test_plural_keys_come_in_pairs():
    """Zu jedem .one gehoert ein .other und umgekehrt."""
    for language, catalog in ui.CATALOGS.items():
        for key in catalog:
            if key.endswith(".one"):
                assert key[: -len(".one")] + ".other" in catalog, f"{language}: {key} ohne .other"
            if key.endswith(".other"):
                assert key[: -len(".other")] + ".one" in catalog, f"{language}: {key} ohne .one"


def test_catalog_carries_no_rich_markup():
    """
    Gestaltung gehoert an die Aufrufstelle, nicht in den Katalog.

    Eine Uebersetzung, die eine Klammer nicht schliesst, wuerde sonst die
    ganze Ausgabe verfaerben -- und der Uebersetzer saehe im Katalog nur
    Zeichen, deren Bedeutung er nicht kennt.
    """
    markup = re.compile(r"\[/?(?:bold|dim|green|red|yellow|cyan|blue|italic)\b")
    for language, catalog in ui.CATALOGS.items():
        offenders = [key for key, text in catalog.items() if markup.search(text)]
        assert not offenders, f"{language}.yaml enthaelt Markup: {offenders}"


# --------------------------------------------------------------------------
# Aufloesung der Sprache
# --------------------------------------------------------------------------


def test_explicit_language_beats_environment(monkeypatch):
    monkeypatch.setenv(ui.UI_ENV_VAR, "de")
    assert ui.resolve_ui_language("en") == "en"


def test_environment_beats_system(monkeypatch):
    monkeypatch.setenv(ui.UI_ENV_VAR, "de")
    monkeypatch.setattr(ui, "detect_system_language", lambda: "en")
    assert ui.resolve_ui_language() == "de"


def test_system_language_applies_when_nothing_else_is_set(monkeypatch):
    monkeypatch.delenv(ui.UI_ENV_VAR, raising=False)
    monkeypatch.setattr(ui, "detect_system_language", lambda: "de")
    assert ui.resolve_ui_language() == "de"


def test_regional_form_falls_back_to_its_base_language(monkeypatch):
    monkeypatch.delenv(ui.UI_ENV_VAR, raising=False)
    monkeypatch.setattr(ui, "detect_system_language", lambda: "de-AT")
    assert ui.resolve_ui_language() == "de"


@pytest.mark.parametrize("code", ["fr", "fr-CA", "zz"])
def test_unknown_language_falls_back_to_english(monkeypatch, code):
    """Geraten wird nicht: was kein Katalog fuehrt, wird Englisch."""
    monkeypatch.delenv(ui.UI_ENV_VAR, raising=False)
    monkeypatch.setattr(ui, "detect_system_language", lambda: code)
    assert ui.resolve_ui_language() == ui.UI_FALLBACK


def test_no_language_anywhere_falls_back_to_english(monkeypatch):
    monkeypatch.delenv(ui.UI_ENV_VAR, raising=False)
    monkeypatch.setattr(ui, "detect_system_language", lambda: None)
    assert ui.resolve_ui_language() == ui.UI_FALLBACK


# --------------------------------------------------------------------------
# Nachschlagen
# --------------------------------------------------------------------------


def test_translation_differs_between_languages(monkeypatch):
    monkeypatch.setattr(ui, "_language", "de")
    assert ui.t("err.config.notfound", path="a.yaml") == "Konfigurationsdatei 'a.yaml' nicht gefunden."
    monkeypatch.setattr(ui, "_language", "en")
    assert ui.t("err.config.notfound", path="a.yaml") == "Configuration file 'a.yaml' not found."


def test_missing_key_in_a_translation_falls_back(monkeypatch):
    """Eine Luecke ergibt englischen Text, nie einen leeren."""
    monkeypatch.setitem(ui.CATALOGS, "de", {})
    monkeypatch.setattr(ui, "_language", "de")
    assert ui.t("labels.all_clear") == ui.CATALOGS["en"]["labels.all_clear"]


def test_unknown_key_aborts():
    """Ein Schluessel, den kein Katalog fuehrt, ist ein Fehler im Programm."""
    with pytest.raises(KeyError):
        ui.t("gibt.es.nicht")


@pytest.mark.parametrize(
    "language, n, expected",
    [
        ("de", 1, "1 Schlüssel bricht den Build ab:"),
        ("de", 3, "3 Schlüssel brechen den Build ab:"),
        ("en", 1, "1 key breaks the build:"),
        ("en", 3, "3 keys break the build:"),
    ],
)
def test_plural_forms(monkeypatch, language, n, expected):
    monkeypatch.setattr(ui, "_language", language)
    assert ui.tn("labels.breaking", n).endswith(expected)


# --------------------------------------------------------------------------
# Der Einsprung
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "argv, rest, language",
    [
        (["build"], ["build"], None),
        (["--ui-lang", "de", "build"], ["build"], "de"),
        (["--ui-lang=de", "build"], ["build"], "de"),
        (["build", "--ui-lang", "en", "-t", "pdf"], ["build", "-t", "pdf"], "en"),
        (["--ui-lang", "de", "--ui-lang", "en"], [], "en"),
        (["build", "--ui-lang"], ["build"], None),
    ],
)
def test_split_ui_lang(argv, rest, language):
    assert entry.split_ui_lang(argv) == (rest, language)


# --------------------------------------------------------------------------
# Der Hilfetext, durch den echten Einsprung
# --------------------------------------------------------------------------


#: Was rich zur Einfaerbung in die Ausgabe schreibt.
_ANSI_SEQUENCE = re.compile(r"\x1b\[[0-9;]*m")


def _run_cli(args, env_language=None):
    """
    Ruft die CLI in einem eigenen Prozess auf.

    Ein eigener Prozess ist hier keine Umstaendlichkeit, sondern der
    Gegenstand des Tests: Typer wertet `help=` beim Import aus. Wer die
    Sprache im laufenden Prozess umstellt, sieht die Hilfe von vorhin und
    haette den Fehler, um den es geht, gerade nicht gefunden.
    """
    import os
    import subprocess
    import sys

    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop(ui.UI_ENV_VAR, None)
    if env_language is not None:
        env[ui.UI_ENV_VAR] = env_language
    # COLUMNS breit genug, damit rich einen Satz nicht mitten im Wort umbricht.
    env["COLUMNS"] = "200"

    result = subprocess.run(
        [sys.executable, "-c", "from markpublish.entry import main; main()", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        cwd=str(REPO_ROOT),
    )

    # Farbe raus, bevor jemand im Text sucht. Typer faerbt Optionsnamen ueber
    # zwei ineinandergreifende Muster ein, und rich schreibt an jeder Grenze
    # eine eigene Sequenz: '--ui-lang' verlaesst den Prozess dann als
    # '\x1b[1;36m-\x1b[0m\x1b[1;36m-ui\x1b[0m\x1b[1;36m-lang\x1b[0m'. Wer darin
    # nach der Flagge sucht, findet sie nicht. Ob ueberhaupt gefaerbt wird,
    # entscheidet die Umgebung -- auf GitHub Actions ja, in einer umgeleiteten
    # Windows-Konsole nein --, und damit haetten diese Tests sonst am
    # Betriebssystem gehangen statt an markpublish.
    result.stdout = _ANSI_SEQUENCE.sub("", result.stdout)
    result.stderr = _ANSI_SEQUENCE.sub("", result.stderr)
    return result


@pytest.mark.parametrize(
    "args, env_language, expected",
    [
        (["--ui-lang", "de", "build", "--help"], None, "Baut das Dokument"),
        (["--ui-lang", "en", "build", "--help"], None, "Builds document"),
        (["build", "--help"], "de", "Baut das Dokument"),
        (["build", "--help"], "en", "Builds document"),
        # Die Flagge sticht die Umgebung -- auch fuer die Hilfe.
        (["--ui-lang", "en", "build", "--help"], "de", "Builds document"),
    ],
)
def test_help_is_translated(args, env_language, expected):
    result = _run_cli(args, env_language)
    assert result.returncode == 0, result.stderr
    assert expected in result.stdout


def test_ui_lang_is_documented_in_the_help():
    """Wer die Flagge nicht kennt, soll sie in der Hilfe finden."""
    result = _run_cli(["--help"], "en")
    assert "--ui-lang" in result.stdout


def test_runtime_message_is_translated_end_to_end(tmp_path):
    result = _run_cli(["--ui-lang", "de", "build", str(tmp_path / "fehlt.yaml")])
    assert result.returncode == 1
    assert "nicht gefunden" in result.stdout


# --------------------------------------------------------------------------
# Kein Text bleibt an der Aufrufstelle stehen
# --------------------------------------------------------------------------

#: Aufrufe, deren Zeichenketten der Benutzer zu sehen bekommt.
_USER_FACING = ("console.print", "typer.Option", "typer.Argument", "typer.Typer")

#: Was hier steht, ist kein uebersetzbarer Text, sondern Geruest: Markup,
#: Trennzeichen, Formatfragmente.
_MARKUP = re.compile(r"\[/?[a-z ]+\]")
_WORD = re.compile(r"[A-Za-zÄÖÜäöüß]{3,}")

#: ui.py meldet einen kaputten Katalog -- die Meldung kann sich nicht selbst
#: nachschlagen und bleibt deshalb englisch.
_EXEMPT_FILES = {"ui.py"}


def _sentence_literals(path: pathlib.Path):
    """Liefert (Zeile, Text) jeder benutzersichtbaren Zeichenkette einer Datei."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []

    def collect(node, lineno):
        """
        Sammelt Zeichenketten, steigt aber nicht in `t()`/`tn()` hinab.

        Deren erstes Argument ist ein Katalogschluessel und kein Text. Wer
        `err.config.notfound` als Prosa zaehlte, meldete ausgerechnet die
        bereits uebersetzten Stellen als unuebersetzt.
        """
        if isinstance(node, ast.Call) and ast.unparse(node.func) in ("t", "tn"):
            for keyword in node.keywords:
                collect(keyword.value, lineno)
            return
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            found.append((lineno, node.value))
            return
        if isinstance(node, ast.JoinedStr):
            text = "".join(p.value for p in node.values if isinstance(p, ast.Constant))
            found.append((lineno, text))
            for part in node.values:
                if isinstance(part, ast.FormattedValue):
                    collect(part.value, lineno)
            return
        for child in ast.iter_child_nodes(node):
            collect(child, lineno)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = ast.unparse(node.func)
            if any(marker in name for marker in _USER_FACING):
                collect(node, node.lineno)
        elif isinstance(node, ast.Raise) and node.exc is not None:
            collect(node.exc, node.lineno)

    sentences = []
    for lineno, text in found:
        bare = _MARKUP.sub("", text).strip()
        # Ein Leerzeichen trennt Prosa vom Bezeichner: 'parts.break_before'
        # zaehlt drei Woerter und ist trotzdem kein Satz.
        if " " in bare and len(_WORD.findall(bare)) >= 3:
            sentences.append((lineno, bare))
    return sentences


def _source_files():
    files = [p for p in PACKAGE_ROOT.rglob("*.py") if "__pycache__" not in str(p)]
    files.append(REPO_ROOT / "build_manuals.py")
    return [p for p in files if p.is_file() and p.name not in _EXEMPT_FILES]


def test_no_user_facing_text_is_hardcoded():
    """
    Jeder Text, den ein Benutzer sieht, geht durch den Katalog.

    Der Katalog kann nur uebersetzen, was ihn erreicht. Ohne diese Schranke
    schleicht sich der naechste festgeschriebene Satz beim naechsten Feature
    wieder ein -- und faellt erst auf, wenn jemand die Sprache umstellt.
    """
    offenders = []
    for path in _source_files():
        for lineno, text in _sentence_literals(path):
            offenders.append(f"{path.relative_to(REPO_ROOT)}:{lineno}: {text[:80]}")
    assert not offenders, "Nicht uebersetzte Texte:\n" + "\n".join(offenders)
