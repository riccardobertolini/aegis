"""
Shared Playwright fixtures for Aegis e2e tests.

Usage:
    pip install pytest pytest-playwright
    playwright install chromium
    pytest tests/e2e/ --base-url=http://localhost:5173 --headed
"""
import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright


@pytest.fixture(scope="session")
def browser_type_launch_args():
    """Force headless mode in CI; override locally with --headed flag."""
    return {"headless": True}


@pytest.fixture(scope="session")
def browser(playwright: Playwright) -> Browser:
    return playwright.chromium.launch(headless=True, slow_mo=50)


@pytest.fixture
def context(browser: Browser) -> BrowserContext:
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 800},
        locale="en-US",
    )
    yield ctx
    ctx.close()


@pytest.fixture
def page(context: BrowserContext) -> Page:
    pg = context.new_page()
    yield pg
    pg.close()
