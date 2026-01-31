"""
SarfX E2E Tests - Pytest Configuration & Fixtures
==================================================

This file contains all shared fixtures, hooks and configuration
for Playwright E2E tests with video recording and screenshots.

Usage:
    pytest tests/ --headed          # Run with browser visible
    pytest tests/ --video=on        # Record videos
    pytest tests/ --screenshot=on   # Take screenshots on failure
    pytest tests/ -k "auth"         # Run only auth tests
"""

import pytest
import os
import json
from datetime import datetime
from pathlib import Path
from playwright.sync_api import Page, Browser, BrowserContext, expect

# ============================================
# CONFIGURATION
# ============================================

# Base URL - Production or localhost
# Set TEST_BASE_URL env variable to override
BASE_URL = os.getenv("TEST_BASE_URL", "https://sarfx.io")

# Test accounts (from seed_demo_users.py)
TEST_ACCOUNTS = {
    "admin": {
        "email": "admin@sarfx.io",
        "password": "admin123",
        "role": "admin"
    },
    "bank_respo": {
        "email": "bank.respo@boa.ma",
        "password": "bank123",
        "role": "bank_respo"
    },
    "bank_user": {
        "email": "bank.user@boa.ma",
        "password": "bank123",
        "role": "bank_user"
    },
    "user": {
        "email": "user@demo.com",
        "password": "user123",
        "role": "user"
    }
}

# Output directories
RESULTS_DIR = Path("tests/results")
SCREENSHOTS_DIR = RESULTS_DIR / "screenshots"
VIDEOS_DIR = RESULTS_DIR / "videos"
TRACES_DIR = RESULTS_DIR / "traces"

# ============================================
# PYTEST HOOKS
# ============================================

def pytest_configure(config):
    """Create output directories and set up reporting."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Add custom markers
    config.addinivalue_line("markers", "e2e: End-to-end browser tests")
    config.addinivalue_line("markers", "auth: Authentication tests")
    config.addinivalue_line("markers", "converter: Currency converter tests")
    config.addinivalue_line("markers", "admin: Admin panel tests")
    config.addinivalue_line("markers", "api: API endpoint tests")


def pytest_html_report_title(report):
    """Custom HTML report title."""
    report.title = "SarfX E2E Test Report"


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Take screenshot on test failure."""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call" and report.failed:
        # Get page from test if available
        page = item.funcargs.get("page")
        if page:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = SCREENSHOTS_DIR / f"{item.name}_{timestamp}.png"
            try:
                page.screenshot(path=str(screenshot_path), full_page=True)
                print(f"\nScreenshot saved: {screenshot_path}")
            except Exception as e:
                print(f"\n\u26a0\ufe0f Could not save screenshot: {e}")


# ============================================
# PLAYWRIGHT FIXTURES
# ============================================

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context with video recording."""
    return {
        **browser_context_args,
        "record_video_dir": str(VIDEOS_DIR),
        "record_video_size": {"width": 1280, "height": 720},
        "viewport": {"width": 1280, "height": 720},
        "locale": "fr-FR",
        "timezone_id": "Africa/Casablanca",
    }


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Configure browser launch options."""
    return {
        **browser_type_launch_args,
        "slow_mo": 100,  # Slow down for visibility (ms)
    }


@pytest.fixture
def page(context: BrowserContext) -> Page:
    """Create a new page with base URL configured."""
    page = context.new_page()
    page.set_default_timeout(30000)  # 30 seconds
    page.set_default_navigation_timeout(30000)
    yield page
    page.close()


# ============================================
# AUTHENTICATION FIXTURES
# ============================================

@pytest.fixture
def login_page(page: Page) -> Page:
    """Navigate to login page."""
    page.goto(f"{BASE_URL}/auth/login")
    page.wait_for_load_state("networkidle")
    return page


def _perform_login(page: Page, email: str, password: str) -> Page:
    """Helper function to perform login."""
    page.goto(f"{BASE_URL}/auth/login")
    page.wait_for_load_state("networkidle")
    
    # Fill login form
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)
    
    # Submit
    page.click('button[type="submit"]')
    
    # Wait for redirect
    page.wait_for_load_state("networkidle")
    
    return page


@pytest.fixture
def logged_in_user(page: Page) -> Page:
    """Fixture providing a page logged in as regular user."""
    account = TEST_ACCOUNTS["user"]
    _perform_login(page, account["email"], account["password"])
    
    # Verify login success
    expect(page).to_have_url(f"{BASE_URL}/app/", timeout=10000)
    
    return page


@pytest.fixture
def logged_in_admin(page: Page) -> Page:
    """Fixture providing a page logged in as admin."""
    account = TEST_ACCOUNTS["admin"]
    _perform_login(page, account["email"], account["password"])
    
    # Verify login success - admin goes to admin dashboard or app
    page.wait_for_url(lambda url: "/app" in url or "/admin" in url, timeout=10000)
    
    return page


@pytest.fixture
def logged_in_bank_respo(page: Page) -> Page:
    """Fixture providing a page logged in as bank responsible."""
    account = TEST_ACCOUNTS["bank_respo"]
    _perform_login(page, account["email"], account["password"])
    
    page.wait_for_load_state("networkidle")
    
    return page


@pytest.fixture
def logged_in_bank_user(page: Page) -> Page:
    """Fixture providing a page logged in as bank user."""
    account = TEST_ACCOUNTS["bank_user"]
    _perform_login(page, account["email"], account["password"])
    
    page.wait_for_load_state("networkidle")
    
    return page


# ============================================
# UTILITY FIXTURES
# ============================================

@pytest.fixture
def api_context(playwright):
    """Fixture for API testing without browser."""
    context = playwright.request.new_context(base_url=BASE_URL)
    yield context
    context.dispose()


@pytest.fixture
def test_data():
    """Fixture providing test data for various scenarios."""
    return {
        "conversion": {
            "amount": 1000,
            "from_currency": "USD",
            "to_currency": "MAD",
            "expected_min_rate": 9.0,
            "expected_max_rate": 11.0
        },
        "new_user": {
            "email": f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com",
            "password": "TestPass123!"
        },
        "beneficiary": {
            "name": "Test Beneficiary",
            "iban": "MA12345678901234567890123456",
            "bank": "Bank of Africa"
        }
    }


# ============================================
# HELPER FUNCTIONS (available as fixtures)
# ============================================

@pytest.fixture
def helpers():
    """Collection of helper functions for tests."""
    
    class Helpers:
        @staticmethod
        def wait_for_toast(page: Page, toast_type: str = "success", timeout: int = 5000):
            """Wait for a toast notification to appear."""
            selector = f".toast-{toast_type}"
            page.wait_for_selector(selector, timeout=timeout)
            return page.locator(selector).first
        
        @staticmethod
        def close_toast(page: Page):
            """Close any visible toast notification."""
            close_btn = page.locator(".toast-close").first
            if close_btn.is_visible():
                close_btn.click()
        
        @staticmethod
        def get_notification_text(page: Page) -> str:
            """Get text from the most recent toast notification."""
            toast = page.locator(".toast").first
            if toast.is_visible():
                return toast.inner_text()
            return ""
        
        @staticmethod
        def navigate_to(page: Page, route: str):
            """Navigate to a route and wait for load."""
            page.goto(f"{BASE_URL}{route}")
            page.wait_for_load_state("networkidle")
        
        @staticmethod
        def fill_form(page: Page, fields: dict):
            """Fill a form with given field values."""
            for selector, value in fields.items():
                page.fill(selector, str(value))
        
        @staticmethod
        def select_currency(page: Page, selector: str, currency: str):
            """Select a currency from a dropdown."""
            page.select_option(selector, currency)
        
        @staticmethod
        def take_screenshot(page: Page, name: str):
            """Take a named screenshot."""
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = SCREENSHOTS_DIR / f"{name}_{timestamp}.png"
            page.screenshot(path=str(path), full_page=True)
            print(f"📸 Screenshot: {path}")
            return path
        
        @staticmethod
        def wait_for_api_response(page: Page, url_pattern: str, timeout: int = 10000):
            """Wait for an API response matching the pattern."""
            with page.expect_response(lambda r: url_pattern in r.url, timeout=timeout) as response_info:
                return response_info.value
    
    return Helpers()


# ============================================
# MOBILE VIEWPORT FIXTURES
# ============================================

@pytest.fixture
def mobile_page(context: BrowserContext) -> Page:
    """Page with mobile viewport (iPhone 12 Pro)."""
    page = context.new_page()
    page.set_viewport_size({"width": 390, "height": 844})
    yield page
    page.close()


@pytest.fixture
def tablet_page(context: BrowserContext) -> Page:
    """Page with tablet viewport (iPad)."""
    page = context.new_page()
    page.set_viewport_size({"width": 768, "height": 1024})
    yield page
    page.close()


# ============================================
# TEST DATA CLEANUP
# ============================================

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_artifacts():
    """Clean up old test artifacts before and after test session."""
    # Before tests: clean old videos (keep last 10)
    if VIDEOS_DIR.exists():
        videos = sorted(VIDEOS_DIR.glob("*.webm"), key=os.path.getmtime)
        for video in videos[:-10]:
            try:
                video.unlink()
            except:
                pass
    
    yield
    
    # After tests: generate summary
    print("\n" + "="*50)
    print("TEST RESULTS SUMMARY")
    print("="*50)
    print(f"Screenshots: {SCREENSHOTS_DIR}")
    print(f"Videos: {VIDEOS_DIR}")
    print(f"Traces: {TRACES_DIR}")
    print("="*50)
