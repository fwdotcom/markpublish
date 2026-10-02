"""
`!file` in der Konfiguration: Werte aus anderen Dateien oder URLs nachladen.
"""

import functools
import http.server
import threading
from pathlib import Path

import pytest
import yaml

from markpublish.config.loader import load_config

HEAD = """\
document:
  title: "T"
  language: de
"""

PARTS = """\
parts:
  - part: "P"
    chapters:
      - file: c.md
"""


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _config(tmp_path: Path, custom: str) -> Path:
    return _write(tmp_path / "markpublish.yaml", HEAD + "  custom:\n" + custom + PARTS)


def test_inline_values_and_file_reference_mix(tmp_path):
    _write(tmp_path / "verfahren.yaml", 'name: "Verfahren X"\nnr: 7\n')
    config = load_config(_config(tmp_path, '    a: "xxx"\n    c: !file "verfahren.yaml"\n'))
    assert config.document.custom == {"a": "xxx", "c": {"name": "Verfahren X", "nr": 7}}


def test_file_reference_reaches_document_fields(tmp_path):
    _write(tmp_path / "v.yaml", 'name: "Verfahren X"\n')
    yaml_text = HEAD.replace('"T"', '"{{custom.v.name}}"') + '  custom:\n    v: !file "v.yaml"\n' + PARTS
    config = load_config(_write(tmp_path / "markpublish.yaml", yaml_text))
    assert config.document.title == "Verfahren X"


def test_nested_references_resolve_relative_to_their_own_file(tmp_path):
    _write(tmp_path / "gemeinsam" / "verfahren.yaml", 'name: "X"\nbetreiber: !file "betreiber.yaml"\n')
    _write(tmp_path / "gemeinsam" / "betreiber.yaml", 'name: "ZIT-BB"\n')
    config = load_config(_config(tmp_path / "konzept", '    v: !file "../gemeinsam/verfahren.yaml"\n'))
    assert config.document.custom["v"]["betreiber"]["name"] == "ZIT-BB"


def test_same_file_in_two_branches_is_no_cycle(tmp_path):
    _write(tmp_path / "shared.yaml", "x: 1\n")
    _write(tmp_path / "a.yaml", 's: !file "shared.yaml"\n')
    _write(tmp_path / "b.yaml", 's: !file "shared.yaml"\n')
    config = load_config(_config(tmp_path, '    a: !file "a.yaml"\n    b: !file "b.yaml"\n'))
    assert config.document.custom == {"a": {"s": {"x": 1}}, "b": {"s": {"x": 1}}}


def test_non_yaml_file_is_inserted_as_text(tmp_path):
    _write(tmp_path / "zweck.txt", "Ein längerer Absatz.\n")
    config = load_config(_config(tmp_path, '    zweck: !file "zweck.txt"\n'))
    assert config.document.custom["zweck"] == "Ein längerer Absatz."


def test_cycle_is_reported(tmp_path):
    _write(tmp_path / "a.yaml", 'b: !file "b.yaml"\n')
    _write(tmp_path / "b.yaml", 'a: !file "a.yaml"\n')
    with pytest.raises(ValueError, match="a.yaml"):
        load_config(_config(tmp_path, '    a: !file "a.yaml"\n'))


def test_reference_back_to_the_config_itself_is_a_cycle(tmp_path):
    with pytest.raises(ValueError, match="markpublish.yaml"):
        load_config(_config(tmp_path, '    me: !file "markpublish.yaml"\n'))


def test_missing_file_names_the_reference(tmp_path):
    with pytest.raises(FileNotFoundError, match="fehlt.yaml"):
        load_config(_config(tmp_path, '    x: !file "fehlt.yaml"\n'))


def test_yaml_string_config_resolves_against_working_directory(tmp_path, monkeypatch):
    _write(tmp_path / "v.yaml", "n: 1\n")
    monkeypatch.chdir(tmp_path)
    config = load_config(HEAD + '  custom:\n    v: !file "v.yaml"\n' + PARTS)
    assert config.document.custom == {"v": {"n": 1}}


def test_loading_stays_safe(tmp_path):
    with pytest.raises(yaml.YAMLError):
        load_config(_config(tmp_path, "    x: !!python/object/apply:os.getcwd []\n"))


@pytest.fixture
def http_root(tmp_path):
    """Liefert tmp_path/www ueber einen lokalen HTTP-Server aus."""
    root = tmp_path / "www"
    root.mkdir()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    handler.log_message = lambda *args: None
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield root, f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def test_url_reference_with_relative_reference_inside(tmp_path, http_root):
    root, url = http_root
    _write(root / "daten" / "verfahren.yaml", 'name: "X"\nbetreiber: !file "betreiber.yaml"\n')
    _write(root / "daten" / "betreiber.yaml", 'name: "ZIT-BB"\n')
    config = load_config(_config(tmp_path, f'    v: !file "{url}/daten/verfahren.yaml"\n'))
    assert config.document.custom["v"] == {"name": "X", "betreiber": {"name": "ZIT-BB"}}


def test_failing_url_is_reported(tmp_path, http_root):
    _, url = http_root
    with pytest.raises(ValueError, match="gibt-es-nicht.yaml"):
        load_config(_config(tmp_path, f'    v: !file "{url}/gibt-es-nicht.yaml"\n'))
