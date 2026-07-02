"""
E2E smoke tests — MemoryPage (/memory)
"""
import re
import pytest
from playwright.sync_api import Page, expect


BASE = "http://localhost:5173"


@pytest.fixture(autouse=True)
def login(page: Page):
    page.goto(f"{BASE}/login")
    page.fill('[name="username"]', "admin")
    page.fill('[name="password"]', "password")
    page.click('button[type="submit"]')
    page.wait_for_url(re.compile(r"/"))


def test_memory_page_renders(page: Page):
    page.goto(f"{BASE}/memory")
    expect(page.locator("h1, h2")).to_contain_text(re.compile(r"[Mm]emory", re.I))


def test_memory_sidebar_link_active(page: Page):
    page.goto(f"{BASE}/memory")
    link = page.locator('a[href="/memory"], a[href*="memory"]').first
    expect(link).to_have_class(re.compile(r"active|current|selected", re.I))


def test_memory_stats_cards_present(page: Page):
    """Stats bar should render at least 2 stat cards."""
    page.goto(f"{BASE}/memory")
    cards = page.locator('[data-testid="stat-card"], .statCard, .stat-card')
    assert cards.count() >= 2


def test_memory_session_filter_present(page: Page):
    page.goto(f"{BASE}/memory")
    filter_input = page.locator(
        'input[placeholder*="ession"], input[data-testid="session-filter"]'
    ).first
    expect(filter_input).to_be_visible()


def test_memory_flush_button_present(page: Page):
    page.goto(f"{BASE}/memory")
    btn = page.locator('button', has_text=re.compile(r"[Ff]lush|[Cc]lear", re.I)).first
    expect(btn).to_be_visible()
