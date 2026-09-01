"""
Tests fuer das, was beim Veroeffentlichen ankommt - nicht fuer das, was
markpublish tut.

Diese Pruefungen greifen an einer Stelle, an der ein Fehler weder auffaellt
noch sich reparieren laesst: eine Version auf PyPI kann man zurueckziehen,
aber nicht ersetzen. Alles hier ist deshalb billig und laeuft bei jedem
Testlauf mit, statt erst im Release-Workflow.
"""

from __future__ import annotations

import re
from pathlib import Path

import markdown

# tomllib gibt es erst ab 3.11, markpublish unterstuetzt ab 3.10. tomli ist
# dieselbe Bibliothek unter altem Namen und steht als dev-Abhaengigkeit bereit.
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Praefixe, die einen Link ohne Bezugspunkt aufloesen.
ABSOLUTE_PREFIXES = ("http://", "https://", "mailto:", "#")


def _readme_targets() -> list[str]:
    """Jedes href/src aus der gerenderten README."""
    html = markdown.markdown((REPO_ROOT / "README.md").read_text(encoding="utf-8"))
    return re.findall(r'href="([^"]+)"', html) + re.findall(r'src="([^"]+)"', html)


def test_readme_has_no_relative_links():
    """
    Die README ist zugleich die Projektbeschreibung auf PyPI, und dort gibt es
    kein Repository, gegen das ein relativer Pfad aufloesen koennte: PyPI
    haengt ihn an die Projekt-URL, und der Link laeuft ins Leere.

    Auf GitHub funktionieren dieselben Links - der Fehler ist deshalb genau
    dort unsichtbar, wo man ihn suchen wuerde.
    """
    relative = [t for t in _readme_targets() if not t.startswith(ABSOLUTE_PREFIXES)]

    assert not relative, (
        "Relative Links in der README landen auf PyPI im 404:\n  "
        + "\n  ".join(
            f"{target}  ->  https://pypi.org/project/markpublish/{target}"
            for target in relative
        )
        + "\n\nAbsolut schreiben, z. B. "
        "https://github.com/fwdotcom/markpublish/blob/main/<pfad>"
    )


def test_readme_links_point_at_the_real_repository():
    """
    Ein falscher Owner faellt auf GitHub nicht auf, weil relative Links dort
    ohnehin greifen - auf PyPI ist er der einzige Weg zurueck zum Projekt.
    """
    urls = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]["urls"]
    repository = urls["Homepage"].rstrip("/")

    github_links = [
        target
        for target in _readme_targets()
        if target.startswith("https://github.com/")
    ]
    foreign = [link for link in github_links if not link.startswith(repository + "/")]

    assert not foreign, (
        f"README verweist auf ein anderes Repository als {repository}:\n  "
        + "\n  ".join(foreign)
    )


def test_project_metadata_is_complete():
    """
    Eine Tabellen-Ueberschrift wie [project.urls] mitten in [project]
    vereinnahmt in TOML alles, was danach folgt - dependencies inklusive.
    Heraus kaeme ein Paket, das seine Abhaengigkeiten nicht mitinstalliert;
    gemerkt haette es der erste Nutzer.
    """
    project = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]

    for key in ("dependencies", "classifiers", "requires-python", "urls"):
        assert project.get(key), f"pyproject.toml: [project] {key} fehlt oder ist leer"

    # Die urls-Tabelle darf nur URLs enthalten. Steht dort 'dependencies',
    # ist genau der oben beschriebene Fall eingetreten.
    for name, value in project["urls"].items():
        assert value.startswith("https://"), (
            f"[project.urls] {name} = {value!r} ist keine URL - "
            "steht die Tabelle an der falschen Stelle?"
        )
