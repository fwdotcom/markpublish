"""
Erkennung der Sprache, die das System mit dem Benutzer spricht.

Ein eigenes Modul, weil zwei voneinander unabhaengige Dinge dieselbe Erkennung
brauchen: i18n.py fuer die Sprache eines Dokuments, das selbst keine angibt,
und ui.py fuer die Sprache der Programmoberflaeche. Laege sie in einem der
beiden, muesste das andere es importieren -- und da ui.py seinerseits die
Meldungen von i18n.py stellt, waere das ein Zirkelschluss.
"""

from __future__ import annotations

import locale
import os
import sys
from typing import Optional


def _normalize_language_key(value) -> str:
    return str(value).strip().lower().replace("_", "-")


#: Umgebungsvariablen, in denen POSIX die Sprachwahl fuehrt, spezifisch zuerst.
#: LANGUAGE darf eine Prioritaetsliste sein ("de:en"); genommen wird der erste
#: Eintrag.
_LOCALE_ENV_VARS = ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")

#: Werte, die "keine Sprache gewaehlt" bedeuten und keine sind.
_NEUTRAL_LOCALES = frozenset({"c", "posix", "c.utf-8", "und"})


def clean_locale(value: str) -> Optional[str]:
    """
    Schaelt aus 'de_DE.UTF-8@euro' den Sprachcode 'de-DE'.

    Geschrieben wird die uebliche Form -- Sprache klein, Region gross. Fuer die
    Aufloesung ist das gleichgueltig, jede Suche normalisiert selbst; hier geht
    es darum, dass der Wert in einer markpublish.yaml landen kann, ohne dass
    jemand ueber ein 'de-de' stolpert.
    """
    code = value.split(":", 1)[0].split(".", 1)[0].split("@", 1)[0].strip()
    if not code or code.lower() in _NEUTRAL_LOCALES:
        return None

    language, _, region = _normalize_language_key(code).partition("-")
    return f"{language}-{region.upper()}" if region else language


def detect_system_language() -> Optional[str]:
    """
    Sprache der Benutzeroberflaeche des Systems, oder None.

    Reihenfolge: erst die POSIX-Umgebungsvariablen -- sie sind die einzige
    Stelle, an der ein Benutzer die Sprache pro Aufruf oder pro Shell
    uebersteuern kann, und wer sie setzt, meint sie auch. Danach fragt Windows
    seine UI-Sprache ueber die API ab; `locale.getlocale()` liefert dort
    'German_Germany' statt eines ISO-Codes und waere unbrauchbar. Auf allen
    anderen Systemen bleibt getlocale() als Rueckfallebene.

    Zurueckgegeben wird ein roher Code wie "de", "de-AT" oder "pt-BR" -- ob es
    ihn ueberhaupt gibt, entscheidet der Aufrufer: normalize_language() fuer die
    Labels, das Vorhandensein eines Verzeichnisses fuer die mitgelieferten
    Dokumente. Erkennung, die nichts findet, gibt None zurueck statt zu raten.
    """
    for var in _LOCALE_ENV_VARS:
        value = os.environ.get(var)
        if value and (code := clean_locale(value)):
            return code

    if sys.platform == "win32":
        try:
            import ctypes

            lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            windows_code = locale.windows_locale.get(lcid)
        except Exception:
            windows_code = None
        return clean_locale(windows_code) if windows_code else None

    try:
        code = locale.getlocale()[0]
    except (TypeError, ValueError):
        return None
    return clean_locale(code) if code else None
