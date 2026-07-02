"""
Unit tests — sidebar navigation items.

Verifies that Sidebar.tsx (or wherever NAV_ITEMS lives) exposes links for the
three new sections: inference, documents, memory.
"""
import pathlib
import re

import pytest

# Sidebar may be at different paths depending on refactor history
_CANDIDATES = [
    pathlib.Path(__file__).parent.parent.parent
    / "admin-studio" / "src" / "components" / "Sidebar.tsx",
    pathlib.Path(__file__).parent.parent.parent
    / "admin-studio" / "src" / "components" / "layout" / "Sidebar.tsx",
    pathlib.Path(__file__).parent.parent.parent
    / "admin-studio" / "src" / "Sidebar.tsx",
]


@pytest.fixture(scope="module")
def sidebar_source() -> str:
    for candidate in _CANDIDATES:
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
    pytest.skip("Sidebar.tsx not found in expected locations")


@pytest.mark.parametrize("href", ["/inference", "/documents", "/memory"])
def test_nav_item_href_present(sidebar_source: str, href: str):
    """Each new section must have a navigation link in the sidebar."""
    assert href in sidebar_source, (
        f"Sidebar is missing href '{href}'. "
        "Update NAV_ITEMS in Sidebar.tsx."
    )


@pytest.mark.parametrize("label", ["Inference", "Documents", "Memory"]):
def test_nav_item_label_present(sidebar_source: str, label: str):
    """Each link must display a human-readable label."""
    assert label in sidebar_source, (
        f"Sidebar NAV_ITEMS missing label '{label}'."
    )
