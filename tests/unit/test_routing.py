"""
Unit tests — frontend routing manifest.

Verifies that App.tsx declares routes for the three pages added in Push 11b:
  /inference, /documents, /memory

These tests parse the raw TSX source — no need to build the frontend.
"""
import pathlib
import re

import pytest

APP_TSX = (
    pathlib.Path(__file__).parent.parent.parent
    / "admin-studio" / "src" / "App.tsx"
)


@pytest.fixture(scope="module")
def app_source() -> str:
    if not APP_TSX.exists():
        pytest.skip(f"App.tsx not found at {APP_TSX}")
    return APP_TSX.read_text(encoding="utf-8")


@pytest.mark.parametrize("route", ["/inference", "/documents", "/memory"])
def test_route_declared(app_source: str, route: str):
    """Each new route must appear as a <Route path=\"...\"> in App.tsx."""
    pattern = re.compile(
        rf'path\s*=\s*["\']{{0,1}}{re.escape(route.lstrip("/"))}["\']{{0,1}}',
        re.IGNORECASE,
    )
    assert pattern.search(app_source), (
        f"Route '{route}' not found in App.tsx. "
        "Make sure App.tsx was updated in Push 11b."
    )


@pytest.mark.parametrize(
    "component",
    ["InferencePage", "DocumentPage", "MemoryPage"],
)
def test_page_component_imported(app_source: str, component: str):
    """Each page component must be imported in App.tsx."""
    assert component in app_source, (
        f"Component '{component}' not imported in App.tsx."
    )
