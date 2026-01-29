"""
SarfX E2E Tests - Authentication Suite
======================================

Tests for login, logout, registration, and route protection.

Run with:
    pytest tests/e2e/test_auth.py -v --headed
    pytest tests/e2e/test_auth.py -k "login" --video=on
"""

import pytest
from playwright.sync_api import Page, expect
import re

# Import configuration
from tests.conftest import BASE_URL, TEST_ACCOUNTS


@pytest.mark.e2e
@pytest.mark.auth
class TestLogin:
    """Tests for user login functionality."""
    
    def test_login_page_loads(self, page: Page):
        """
        ✅ TEST: Login page loads correctly
        
        Vérifie que la page de connexion se charge avec tous les éléments requis.
        """
        page.goto(f"{BASE_URL}/auth/login")
        page.wait_for_load_state("networkidle")
        
        # Check page title
        expect(page).to_have_title(re.compile(".*SarfX.*", re.IGNORECASE))
        
        # Check login form elements
        expect(page.locator('input[name="email"]')).to_be_visible()
        expect(page.locator('input[name="password"]')).to_be_visible()
        expect(page.locator('button[type="submit"]')).to_be_visible()
        
        # Check logo
        expect(page.locator('.logo-text, .wise-logo-text')).to_be_visible()
    
    def test_login_success_user(self, page: Page, helpers):
        """
        ✅ TEST: Successful login as regular user
        
        Vérifie qu'un utilisateur peut se connecter et est redirigé vers le dashboard.
        """
        account = TEST_ACCOUNTS["user"]
        
        page.goto(f"{BASE_URL}/auth/login")
        page.wait_for_load_state("networkidle")
        
        # Fill login form
        page.fill('input[name="email"]', account["email"])
        page.fill('input[name="password"]', account["password"])
        
        # Take screenshot before submit
        helpers.take_screenshot(page, "login_form_filled")
        
        # Submit form
        page.click('button[type="submit"]')
        
        # Wait for redirect to app dashboard
        page.wait_for_url(lambda url: "/app" in url, timeout=15000)
        
        # Verify we're on the app page
        expect(page).to_have_url(re.compile(r".*/app.*"))
        
        # Take screenshot after login
        helpers.take_screenshot(page, "login_success_dashboard")
    
    def test_login_success_admin(self, page: Page, helpers):
        """
        ✅ TEST: Successful login as admin
        
        Vérifie qu'un admin peut se connecter et accéder à l'application.
        """
        account = TEST_ACCOUNTS["admin"]
        
        page.goto(f"{BASE_URL}/auth/login")
        page.fill('input[name="email"]', account["email"])
        page.fill('input[name="password"]', account["password"])
        page.click('button[type="submit"]')
        
        # Admin should be redirected to app or admin dashboard
        page.wait_for_url(lambda url: "/app" in url or "/admin" in url, timeout=15000)
        
        helpers.take_screenshot(page, "admin_login_success")
    
    def test_login_failure_wrong_password(self, page: Page, helpers):
        """
        ❌ TEST: Login fails with wrong password
        
        Vérifie que la connexion échoue avec un mauvais mot de passe
        et qu'un message d'erreur s'affiche.
        """
        page.goto(f"{BASE_URL}/auth/login")
        page.wait_for_load_state("networkidle")
        
        # Fill with wrong password
        page.fill('input[name="email"]', "user@demo.com")
        page.fill('input[name="password"]', "wrongpassword123")
        page.click('button[type="submit"]')
        
        # Wait for response
        page.wait_for_load_state("networkidle")
        
        # Should stay on login page or show error
        # Either URL stays on /auth/login or toast appears
        try:
            toast = page.locator(".toast-error, .alert-error, .flash-error")
            expect(toast.first).to_be_visible(timeout=5000)
            helpers.take_screenshot(page, "login_failure_wrong_password")
        except:
            # If no toast, check we're still on login page
            expect(page).to_have_url(re.compile(r".*/auth/login.*"))
    
    def test_login_failure_nonexistent_user(self, page: Page):
        """
        ❌ TEST: Login fails with non-existent user
        
        Vérifie que la connexion échoue pour un utilisateur inexistant.
        """
        page.goto(f"{BASE_URL}/auth/login")
        
        page.fill('input[name="email"]', "nonexistent@fake.com")
        page.fill('input[name="password"]', "anypassword")
        page.click('button[type="submit"]')
        
        page.wait_for_load_state("networkidle")
        
        # Should not redirect to app
        expect(page).not_to_have_url(re.compile(r".*/app.*"))
    
    def test_login_form_validation_empty_fields(self, page: Page):
        """
        ⚠️ TEST: Form validation for empty fields
        
        Vérifie que le formulaire valide les champs vides.
        """
        page.goto(f"{BASE_URL}/auth/login")
        
        # Try to submit without filling fields
        page.click('button[type="submit"]')
        
        # HTML5 validation should prevent submission
        # Check that email input is still focused or has validation error
        email_input = page.locator('input[name="email"]')
        
        # Should still be on login page
        expect(page).to_have_url(re.compile(r".*/auth/login.*"))
    
    def test_password_toggle_visibility(self, page: Page):
        """
        👁️ TEST: Password visibility toggle
        
        Vérifie que le bouton pour afficher/masquer le mot de passe fonctionne.
        """
        page.goto(f"{BASE_URL}/auth/login")
        
        password_input = page.locator('input[name="password"], #password')
        toggle_btn = page.locator('button[aria-label*="mot de passe"], button[onclick*="togglePassword"], .password-toggle')
        
        # Initially password should be hidden (type="password")
        expect(password_input).to_have_attribute("type", "password")
        
        # If toggle button exists, test it
        if toggle_btn.count() > 0:
            toggle_btn.first.click()
            # After click, should show password (type="text")
            expect(password_input).to_have_attribute("type", "text")
            
            # Click again to hide
            toggle_btn.first.click()
            expect(password_input).to_have_attribute("type", "password")


@pytest.mark.e2e
@pytest.mark.auth
class TestRegistration:
    """Tests for user registration functionality."""
    
    def test_registration_form_loads(self, page: Page):
        """
        ✅ TEST: Registration form loads correctly
        
        Vérifie que le formulaire d'inscription se charge correctement.
        """
        # Try different possible registration URLs
        page.goto(f"{BASE_URL}/auth/login?mode=register")
        page.wait_for_load_state("networkidle")
        
        # Check for register tab or form
        register_tab = page.locator('button:has-text("S\'inscrire"), a:has-text("S\'inscrire"), [data-tab="register"]')
        if register_tab.count() > 0:
            register_tab.first.click()
            page.wait_for_timeout(500)
        
        # Form should be visible
        expect(page.locator('input[name="email"]')).to_be_visible()
    
    def test_registration_new_user(self, page: Page, test_data, helpers):
        """
        ✅ TEST: Register a new user
        
        Vérifie qu'un nouvel utilisateur peut s'inscrire.
        """
        page.goto(f"{BASE_URL}/auth/login?mode=register")
        page.wait_for_load_state("networkidle")
        
        # Switch to register mode if needed
        register_tab = page.locator('button:has-text("S\'inscrire"), [data-tab="register"]')
        if register_tab.count() > 0 and register_tab.first.is_visible():
            register_tab.first.click()
            page.wait_for_timeout(500)
        
        # Fill registration form
        new_user = test_data["new_user"]
        page.fill('input[name="email"]', new_user["email"])
        page.fill('input[name="password"]', new_user["password"])
        
        helpers.take_screenshot(page, "registration_form_filled")
        
        # Submit
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        
        helpers.take_screenshot(page, "registration_result")


@pytest.mark.e2e
@pytest.mark.auth
class TestLogout:
    """Tests for logout functionality."""
    
    def test_logout_redirects_to_login(self, logged_in_user: Page, helpers):
        """
        ✅ TEST: Logout redirects to login page
        
        Vérifie que la déconnexion redirige vers la page de connexion.
        """
        page = logged_in_user
        
        # Navigate to logout
        page.goto(f"{BASE_URL}/auth/logout")
        page.wait_for_load_state("networkidle")
        
        # Should be redirected to login
        expect(page).to_have_url(re.compile(r".*/auth/login.*"))
        
        helpers.take_screenshot(page, "after_logout")
    
    def test_cannot_access_app_after_logout(self, page: Page, helpers):
        """
        🔒 TEST: Cannot access protected routes after logout
        
        Vérifie qu'on ne peut pas accéder aux pages protégées après déconnexion.
        """
        # First login
        account = TEST_ACCOUNTS["user"]
        page.goto(f"{BASE_URL}/auth/login")
        page.fill('input[name="email"]', account["email"])
        page.fill('input[name="password"]', account["password"])
        page.click('button[type="submit"]')
        page.wait_for_url(lambda url: "/app" in url, timeout=15000)
        
        # Now logout
        page.goto(f"{BASE_URL}/auth/logout")
        page.wait_for_load_state("networkidle")
        
        # Try to access protected page
        page.goto(f"{BASE_URL}/app/")
        page.wait_for_load_state("networkidle")
        
        # Should be redirected to login
        expect(page).to_have_url(re.compile(r".*/auth/login.*"))
        
        helpers.take_screenshot(page, "protected_route_after_logout")


@pytest.mark.e2e
@pytest.mark.auth
class TestRouteProtection:
    """Tests for route protection and access control."""
    
    def test_unauthenticated_user_redirected(self, page: Page):
        """
        🔒 TEST: Unauthenticated user is redirected to login
        
        Vérifie qu'un utilisateur non connecté est redirigé vers login.
        """
        # Try to access protected routes directly
        protected_routes = [
            "/app/",
            "/app/converter",
            "/app/wallets",
            "/app/transactions",
            "/app/profile"
        ]
        
        for route in protected_routes:
            page.goto(f"{BASE_URL}{route}")
            page.wait_for_load_state("networkidle")
            
            # Should be on login page
            expect(page).to_have_url(re.compile(r".*/auth/login.*"))
    
    def test_user_cannot_access_admin(self, logged_in_user: Page):
        """
        🔒 TEST: Regular user cannot access admin routes
        
        Vérifie qu'un utilisateur normal ne peut pas accéder aux routes admin.
        """
        page = logged_in_user
        
        # Try to access admin
        page.goto(f"{BASE_URL}/admin/")
        page.wait_for_load_state("networkidle")
        
        # Should not be on admin page
        # Either redirected or shown forbidden
        expect(page).not_to_have_url(re.compile(r".*/admin/$"))
    
    def test_admin_can_access_admin_routes(self, logged_in_admin: Page, helpers):
        """
        ✅ TEST: Admin can access admin routes
        
        Vérifie qu'un admin peut accéder aux routes admin.
        """
        page = logged_in_admin
        
        # Navigate to admin dashboard
        page.goto(f"{BASE_URL}/admin/")
        page.wait_for_load_state("networkidle")
        
        # Should be on admin page
        expect(page).to_have_url(re.compile(r".*/admin.*"))
        
        # Check for admin badge or dashboard elements
        admin_indicator = page.locator('.badge:has-text("Admin"), .badge-error:has-text("Admin"), h1:has-text("Admin")')
        expect(admin_indicator.first).to_be_visible()
        
        helpers.take_screenshot(page, "admin_dashboard_access")


@pytest.mark.e2e
@pytest.mark.auth
class TestDemoLogin:
    """Tests for demo account quick login buttons."""
    
    def test_admin_demo_button(self, page: Page, helpers):
        """
        ⚡ TEST: Admin demo quick login
        
        Vérifie que le bouton de démo admin fonctionne.
        """
        page.goto(f"{BASE_URL}/auth/login")
        page.wait_for_load_state("networkidle")
        
        # Look for demo buttons
        admin_demo_btn = page.locator('button:has-text("Admin Demo"), button:has-text("Admin")')
        
        if admin_demo_btn.count() > 0 and admin_demo_btn.first.is_visible():
            admin_demo_btn.first.click()
            page.wait_for_load_state("networkidle")
            
            # Should either fill the form or redirect
            page.wait_for_timeout(1000)
            
            # If form is filled, submit it
            submit_btn = page.locator('button[type="submit"]')
            if submit_btn.is_visible():
                submit_btn.click()
                page.wait_for_load_state("networkidle")
            
            helpers.take_screenshot(page, "admin_demo_login")
    
    def test_user_demo_button(self, page: Page, helpers):
        """
        ⚡ TEST: User demo quick login
        
        Vérifie que le bouton de démo utilisateur fonctionne.
        """
        page.goto(f"{BASE_URL}/auth/login")
        page.wait_for_load_state("networkidle")
        
        user_demo_btn = page.locator('button:has-text("User Demo"), button:has-text("Utilisateur")')
        
        if user_demo_btn.count() > 0 and user_demo_btn.first.is_visible():
            user_demo_btn.first.click()
            page.wait_for_load_state("networkidle")
            
            helpers.take_screenshot(page, "user_demo_login")


@pytest.mark.e2e
@pytest.mark.auth
class TestMobileAuth:
    """Tests for authentication on mobile viewport."""
    
    def test_login_mobile_responsive(self, mobile_page: Page, helpers):
        """
        📱 TEST: Login page is responsive on mobile
        
        Vérifie que la page de login est correctement affichée sur mobile.
        """
        page = mobile_page
        
        page.goto(f"{BASE_URL}/auth/login")
        page.wait_for_load_state("networkidle")
        
        # Check form is visible and properly sized
        form = page.locator('form, .login-form, .auth-form')
        expect(form.first).to_be_visible()
        
        # Check inputs are accessible
        expect(page.locator('input[name="email"]')).to_be_visible()
        expect(page.locator('input[name="password"]')).to_be_visible()
        expect(page.locator('button[type="submit"]')).to_be_visible()
        
        helpers.take_screenshot(page, "login_mobile_view")
    
    def test_login_works_on_mobile(self, mobile_page: Page, helpers):
        """
        📱 TEST: Login works on mobile viewport
        
        Vérifie que la connexion fonctionne sur mobile.
        """
        page = mobile_page
        account = TEST_ACCOUNTS["user"]
        
        page.goto(f"{BASE_URL}/auth/login")
        page.wait_for_load_state("networkidle")
        
        page.fill('input[name="email"]', account["email"])
        page.fill('input[name="password"]', account["password"])
        page.click('button[type="submit"]')
        
        page.wait_for_url(lambda url: "/app" in url, timeout=15000)
        
        helpers.take_screenshot(page, "login_success_mobile")
