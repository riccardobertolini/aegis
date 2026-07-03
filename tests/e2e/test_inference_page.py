"""
E2E smoke tests — InferencePage (/inference)
Requires: pytest-playwright, running admin-studio dev server on http://localhost:5173
Run with: pytest tests/e2e/ --base-url=http://localhost:5173
"""
import re

import pytest
from playwright.sync_api import Page, expect

BASE = "http://localhost:5173"


@pytest.fixture(autouse=True)
def login(page: Page):
    """Log in once before each test in this module."""
    page.goto(f"{BASE}/login")
    page.fill('[name="username"]', "admin")
    page.fill('[name="password"]', "password")
    page.click('button[type="submit"]')
    page.wait_for_url(re.compile(r"/(dashboard|inference|documents|memory)"))


def test_inference_page_renders(page: Page):
    page.goto(f"{BASE}/inference")
    expect(page.locator("h1, h2")).to_contain_text(re.compile(r"[Ii]nference", re.I))


def test_inference_sidebar_link_active(page: Page):
    page.goto(f"{BASE}/inference")
    sidebar_link = page.locator('a[href="/inference"], a[href*="inference"]').first
    expect(sidebar_link).to_have_class(re.compile(r"active|current|selected", re.I))


def test_inference_prompt_textarea_present(page: Page):
    page.goto(f"{BASE}/inference")
    textarea = page.locator("textarea").first
    expect(textarea).to_be_visible()


def test_inference_generate_button_present(page: Page):
    page.goto(f"{BASE}/inference")
    btn = page.locator('button', has_text=re.compile(r"[Gg]enerat", re.I)).first
    expect(btn).to_be_visible()


def test_inference_sliders_present(page: Page):
    """Temperature, top-p and max-tokens sliders should all be in the DOM."""
    page.goto(f"{BASE}/inference")
    sliders = page.locator('input[type="range"]')
    expect(sliders).to_have_count(3)


def test_inference_submit_shows_output(page: Page):
    """Typing a prompt and clicking Generate should reveal an output area."""
    page.goto(f"{BASE}/inference")
    page.locator("textarea").first.fill("Hello Mamba!")
    page.locator('button', has_text=re.compile(r"[Gg]enerat", re.I)).first.click()
    output = page.locator('[data-testid="inference-output"], .output, pre')
    expect(output.first).to_be_visible(timeout=15_000)
