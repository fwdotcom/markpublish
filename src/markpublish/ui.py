"""
Sprache der Programmoberflaeche -- Terminalausgaben, Hilfetexte, Fehlermeldungen.

Nicht zu verwechseln mit i18n.py: das ist die Sprache des *Dokuments*. Die
beiden sind absichtlich getrennt, denn sie sind es auch in der Wirklichkeit --
wer ein englisches Handbuch setzt, will englische Ueberschriften im PDF und
trotzdem deutsche Meldungen im Terminal.

Getrennt ist deshalb auch der Katalog. Die Kaskade in i18n.py laesst Theme und
Projekt Texte ueberschreiben; duerfte ein Projekt auf demselben Weg an die
Meldungen des Programms, koennte ausgerechnet das fehlerhafte Projekt
formulieren, womit markpublish seinen eigenen Fehler meldet. Geteilt wird
zwischen beiden genau eine Sache: die Erkennung der Systemsprache.

Die Sprache wird in dieser Reihenfolge bestimmt:

    1. --ui-lang de           ausdruecklich fuer diesen Aufruf
    2. MARKPUBLISH_UI_LANG    fuer diese Shell
    3. Systemsprache          LANGUAGE/LC_ALL/LC_MESSAGES/LANG, sonst die
                              UI-Sprache von Windows bzw. locale.getlocale()
    4. UI_FALLBACK ("en")

Bewusst *nicht* dabei: die markpublish.yaml. Die Terminalsprache gehoert dem
Menschen vor dem Rechner, nicht dem Repository -- zwei Kollegen an einem
Projekt haetten sonst Streit ueber eine Zeile.

Gesetzt wird sie einmal, vom Einsprung (entry.py), bevor die CLI ueberhaupt
importiert ist. Das ist keine Stilfrage: Typer wertet `help=` beim Import aus,
ein spaeter gesetzter Wert erreicht die Hilfetexte nicht mehr.

Benutzung:

    t("err.config.notfound", path=config_file)
    tn("manual.updated", n)      # Plural ueber die Schluessel .one / .other

Drei Regeln halten den Katalog gesund:

* Benannte Platzhalter, keine Positionen -- eine Uebersetzung darf die
  Reihenfolge aendern.
* Keine zusammengeklebten Halbsaetze. Wortstellung ist sprachabhaengig; was
  im Deutschen hinten steht, steht im Englischen mittendrin.
* Kein Rich-Markup im Katalog. `[bold red]` bleibt an der Aufrufstelle, sonst
  zerschiesst eine vergessene schliessende Klammer in einer Uebersetzung die
  ganze Ausgabe.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

import yaml

from markpublish.syslang import clean_locale, detect_system_language

#: Sprache, in der jeder Schluessel vorhanden sein muss. Sie liegt unter jeder
#: anderen: eine unvollstaendige Uebersetzung erzeugt dadurch nie einen leeren
#: Text, sondern faellt fuer den fehlenden Schluessel auf Englisch zurueck.
UI_FALLBACK = "en"

#: Umgebungsvariable fuer die Sprache der Oberflaeche. Eigene Variable statt
#: LANG: wer LANG auf en setzt, meint sein System, nicht dieses Programm.
UI_ENV_VAR = "MARKPUBLISH_UI_LANG"

#: Verzeichnis der mitgelieferten Kataloge, eine Datei je Sprache.
LOCALE_DIR = Path(__file__).resolve().parent / "locale"


class UICatalogError(RuntimeError):
    """
    Der Katalog der Oberflaechentexte ist unbrauchbar.

    Bewusst kein uebersetzter Text: waere der Katalog kaputt, koennte diese
    Meldung sich nicht selbst nachschlagen.
    """


def _read_catalog(path: Path) -> Dict[str, str]:
    """Liest einen Katalog als flaches {Schluessel: Text}."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise UICatalogError(f"{path}: cannot be read ({exc}).") from exc

    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise UICatalogError(f"{path}: expected a mapping of key to text.")

    flat: Dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(value, Mapping):
            raise UICatalogError(
                f"{path}: '{key}' is nested. UI catalogs are flat; "
                "use dotted keys such as 'err.config.notfound'."
            )
        flat[str(key)] = str(value)
    return flat


def _load_catalogs() -> Dict[str, Dict[str, str]]:
    """
    Laedt alle mitgelieferten Kataloge. Ein Paketfehler muss laut scheitern.
    """
    if not LOCALE_DIR.is_dir():
        raise UICatalogError(
            f"Bundled UI texts not found: {LOCALE_DIR}. This looks like an "
            "incomplete package - locale/*.yaml belongs to markpublish's "
            "package-data."
        )
    catalogs = {p.stem.lower(): _read_catalog(p) for p in sorted(LOCALE_DIR.glob("*.yaml"))}
    if UI_FALLBACK not in catalogs:
        raise UICatalogError(f"{LOCALE_DIR}: the fallback language '{UI_FALLBACK}' is missing.")
    return catalogs


#: Beim Import einmal geladen.
CATALOGS: Dict[str, Dict[str, str]] = _load_catalogs()

#: Die gewaehlte Sprache. None heisst "noch nicht bestimmt" -- der erste
#: Zugriff bestimmt sie dann selbst, damit auch ein Aufruf als Bibliothek
#: (ohne entry.py) uebersetzte Meldungen bekommt.
_language: Optional[str] = None


def available_ui_languages() -> List[str]:
    """Sprachcodes, in denen die Oberflaeche vorliegt."""
    return sorted(CATALOGS)


def resolve_ui_language(explicit: Optional[str] = None) -> str:
    """
    Bestimmt die Sprache der Oberflaeche, ohne sie zu setzen.

    Eine regionale Form faellt auf ihre Basissprache zurueck: 'de-AT' und
    'de_DE' landen beide auf 'de'. Was kein Katalog kennt, landet auf
    UI_FALLBACK -- geraten wird nicht.
    """
    for candidate in (explicit, os.environ.get(UI_ENV_VAR), detect_system_language()):
        if not candidate:
            continue
        code = clean_locale(candidate)
        if not code:
            continue
        code = code.lower()
        if code in CATALOGS:
            return code
        base = code.split("-", 1)[0]
        if base in CATALOGS:
            return base
    return UI_FALLBACK


def set_ui_language(explicit: Optional[str] = None) -> str:
    """
    Setzt die Sprache der Oberflaeche und gibt den gewaehlten Code zurueck.

    Aufgerufen vom Einsprung, bevor die CLI importiert wird.
    """
    global _language
    _language = resolve_ui_language(explicit)
    return _language


def ui_language() -> str:
    """Die geltende Sprache; bestimmt sie beim ersten Zugriff selbst."""
    return _language if _language is not None else set_ui_language()


def t(key: str, /, **params: Any) -> str:
    """
    Der Text zu einem Schluessel in der Sprache der Oberflaeche.

    Ein Schluessel, den die gewaehlte Sprache nicht kennt, kommt aus
    UI_FALLBACK. Ein Schluessel, den auch die nicht kennt, ist ein Fehler im
    Programm und keiner der Uebersetzung -- er bricht ab, statt eine leere
    Zeile zu drucken, die niemandem auffaellt.
    """
    catalog = CATALOGS.get(ui_language(), {})
    text = catalog.get(key)
    if text is None:
        text = CATALOGS[UI_FALLBACK].get(key)
    if text is None:
        raise KeyError(f"unknown UI text key: {key!r}")
    if not params:
        return text
    try:
        return text.format(**params)
    except (KeyError, IndexError) as exc:
        raise KeyError(f"UI text {key!r} has a placeholder no caller filled: {exc}") from exc


def tn(key: str, n: int, /, **params: Any) -> str:
    """
    Der Text zu einem Schluessel in der Zahlform, die zu `n` passt.

    Erwartet die Schluessel `<key>.one` und `<key>.other`; `n` steht in beiden
    als Platzhalter bereit. Deutsch und Englisch teilen sich diese zwei Formen
    -- eine Sprache mit mehr davon braucht hier eine Erweiterung, keine
    Umgehung an der Aufrufstelle.
    """
    return t(f"{key}.one" if abs(n) == 1 else f"{key}.other", n=n, **params)
