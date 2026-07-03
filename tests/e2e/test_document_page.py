"""
E2E smoke tests — DocumentPage (/documents)
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


def test_document_page_renders(page: Page):
    page.goto(f"{BASE}/documents")
    expect(page.locator("h1, h2")).to_contain_text(re.compile(r"[Dd]ocument", re.I))


def test_document_sidebar_link_active(page: Page):
    page.goto(f"{BASE}/documents")
    link = page.locator('a[href="/documents"], a[href*="documents"]').first
    expect(link).to_have_class(re.compile(r"active|current|selected", re.I))


def test_document_dropzone_present(page: Page):
    page.goto(f"{BASE}/documents")
    dropzone = page.locator(
        '[data-testid="dropzone"], .dropzone, input[type="file"]'
    ).first
    expect(dropzone).to_be_attached()


def test_document_table_headers(page: Page):
    page.goto(f"{BASE}/documents")
    headers = page.locator("th")
    texts = [h.inner_text() for h in headers.all()]
    assert any(re.search(r"[Nn]ame", t) for t in texts), f"No 'Name' header found in {texts}"
    assert any(re.search(r"[Ss]tat", t) for t in texts), f"No 'Status' header found in {texts}"


def test_document_search_input_present(page: Page):
    page.goto(f"{BASE}/documents")
    search = page.locator('input[type="search"], input[placeholder*="earch"]').first
    expect(search).to_be_visible()
