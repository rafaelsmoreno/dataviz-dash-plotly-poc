"""
Smoke tests — verify the Dash application can be imported and the server
object is correctly constructed without requiring data files or a running
DuckDB database.

Run:
    pytest tests/
"""

import importlib
import sys
from pathlib import Path

import pytest

# Put app/ on the path so imports inside app.py resolve (mirrors the
# sys.path.insert in app.py itself).
APP_DIR = Path(__file__).resolve().parent.parent / "app"
sys.path.insert(0, str(APP_DIR))


def test_app_module_imports():
    """app.py must be importable without error."""
    mod = importlib.import_module("app")
    assert mod is not None, "app module failed to import"


def test_server_is_flask_app():
    """app.server must be a Flask WSGI application (gunicorn entry point)."""
    from flask import Flask

    mod = importlib.import_module("app")
    assert hasattr(mod, "server"), (
        "app.server not found — gunicorn entry point is missing"
    )
    assert isinstance(mod.server, Flask), (
        f"app.server is {type(mod.server)}, expected flask.Flask"
    )


def test_dash_instance_has_pages():
    """Dash app must have use_pages=True and at least 3 registered pages."""
    import dash

    mod = importlib.import_module("app")
    assert hasattr(mod, "app"), "app.app (Dash instance) not found"
    pages = dash.page_registry
    assert len(pages) >= 3, (
        f"Expected at least 3 registered pages, got {len(pages)}: {list(pages.keys())}"
    )


def test_page_paths_registered():
    """The three dashboard paths must be present in the page registry."""
    import dash

    importlib.import_module("app")  # ensure pages are registered
    paths = {p["path"] for p in dash.page_registry.values()}
    for expected in ("/", "/nyc-taxi", "/world-energy", "/brazil-economy"):
        assert expected in paths, f"Page path '{expected}' not registered"
