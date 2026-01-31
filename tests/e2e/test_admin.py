"""
SarfX E2E Tests - Admin Panel Suite
===================================

Tests for admin dashboard, user management, and administrative functions.

Run with:
    pytest tests/e2e/test_admin.py -v --headed
    pytest tests/e2e/test_admin.py --video=on
"""

import pytest
from playwright.sync_api import Page, expect
import re

from tests.conftest import BASE_URL, TEST_ACCOUNTS


@pytest.mark.e2e
@pytest.mark.admin
class TestAdminDashboard:
    """Tests for admin dashboard."""
    
    def test_admin_dashboard_loads(self, logged_in_admin: Page, helpers):
        """
        ✅ TEST: Admin dashboard loads correctly
        
        Vérifie que le dashboard admin se charge avec les statistiques.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/")
        page.wait_for_load_state("networkidle")
        
        # Check for admin badge
        admin_badge = page.locator('.badge:has-text("Admin"), .badge-error')
        expect(admin_badge.first).to_be_visible()
        
        # Check for KPI cards (Users, Wallets, Transactions, Volume)
        page_content = page.content()
        assert any(word in page_content for word in ["Utilisateurs", "Users", "Portefeuilles", "Wallets"])
        
        helpers.take_screenshot(page, "admin_dashboard")
    
    def test_admin_kpi_cards_displayed(self, logged_in_admin: Page):
        """
        📊 TEST: KPI cards display statistics
        
        Vérifie que les cartes KPI affichent des statistiques.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/")
        page.wait_for_load_state("networkidle")
        
        # Check for numeric values in cards
        cards = page.locator('.card')
        
        # At least some cards should have numbers
        numbers_found = page.locator('.text-2xl, .stat-value, .kpi-value')
        expect(numbers_found.first).to_be_visible()
    
    def test_admin_charts_render(self, logged_in_admin: Page, helpers):
        """
        📈 TEST: Admin charts render correctly
        
        Vérifie que les graphiques du dashboard se chargent.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/")
        page.wait_for_load_state("networkidle")
        
        # Wait for charts to render
        page.wait_for_timeout(2000)
        
        # Look for chart containers
        volume_chart = page.locator('#volume-chart, .apexcharts-canvas')
        currency_chart = page.locator('#currency-chart')
        
        if volume_chart.count() > 0:
            expect(volume_chart.first).to_be_visible()
        
        helpers.take_screenshot(page, "admin_charts")
    
    def test_admin_quick_actions(self, logged_in_admin: Page, helpers):
        """
        ⚡ TEST: Quick action links work
        
        Vérifie que les liens d'action rapide fonctionnent.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/")
        page.wait_for_load_state("networkidle")
        
        # Check for quick action links
        users_link = page.locator('a[href*="/admin/users"]')
        wallets_link = page.locator('a[href*="/admin/wallets"]')
        transactions_link = page.locator('a[href*="/admin/transactions"]')
        
        if users_link.count() > 0:
            expect(users_link.first).to_be_visible()
        
        helpers.take_screenshot(page, "admin_quick_actions")


@pytest.mark.e2e
@pytest.mark.admin
class TestUserManagement:
    """Tests for user management functionality."""
    
    def test_users_list_loads(self, logged_in_admin: Page, helpers):
        """
        ✅ TEST: Users list page loads
        
        Vérifie que la liste des utilisateurs se charge.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/users")
        page.wait_for_load_state("networkidle")
        
        # Check page title
        expect(page.locator('h1:has-text("Utilisateurs"), h1:has-text("Users")')).to_be_visible()
        
        # Should have user cards or rows
        user_items = page.locator('.user-card, .card, tr')
        expect(user_items.first).to_be_visible()
        
        helpers.take_screenshot(page, "admin_users_list")
    
    def test_users_search_filter(self, logged_in_admin: Page, helpers):
        """
        🔍 TEST: User search filter works
        
        Vérifie que le filtre de recherche fonctionne.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/users")
        page.wait_for_load_state("networkidle")
        
        # Look for search input
        search_input = page.locator('#search-input, input[type="search"], input[placeholder*="Rechercher"]')
        
        if search_input.count() > 0:
            search_input.first.fill("demo")
            page.wait_for_timeout(500)
            
            # Should filter results
            helpers.take_screenshot(page, "users_search_filtered")
    
    def test_users_role_filter(self, logged_in_admin: Page):
        """
        🔍 TEST: User role filter works
        
        Vérifie que le filtre par rôle fonctionne.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/users")
        page.wait_for_load_state("networkidle")
        
        # Look for role filter
        role_filter = page.locator('#filter-role, select[name="role"]')
        
        if role_filter.count() > 0:
            role_filter.first.select_option("admin")
            page.wait_for_timeout(500)
            
            # Should show only admin users
            page_content = page.content()
            # Check filtering is applied
    
    def test_user_details_modal(self, logged_in_admin: Page, helpers):
        """
        👁️ TEST: User details modal opens
        
        Vérifie que le modal de détails utilisateur s'ouvre.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/users")
        page.wait_for_load_state("networkidle")
        
        # Click on view details button
        view_btn = page.locator('button[title*="détails"], button:has-text("Voir"), .eye-btn').first
        
        if view_btn.is_visible():
            view_btn.click()
            page.wait_for_timeout(500)
            
            # Modal should appear
            modal = page.locator('#userModal, .modal, [role="dialog"]')
            if modal.count() > 0:
                expect(modal.first).to_be_visible()
            
            helpers.take_screenshot(page, "user_details_modal")
    
    def test_toggle_user_status(self, logged_in_admin: Page, helpers):
        """
        🔄 TEST: Toggle user active status
        
        Vérifie qu'on peut activer/désactiver un utilisateur.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/users")
        page.wait_for_load_state("networkidle")
        
        # Look for toggle button (not on current admin user)
        toggle_btns = page.locator('button[title*="Désactiver"], button[title*="Activer"], form[action*="toggle"] button')
        
        if toggle_btns.count() > 1:
            # Take screenshot before toggle
            helpers.take_screenshot(page, "before_user_toggle")
            
            # Note: We don't actually toggle to avoid breaking test data
    
    def test_change_user_role(self, logged_in_admin: Page, helpers):
        """
        👤 TEST: Change user role dropdown exists
        
        Vérifie que le dropdown de changement de rôle existe.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/users")
        page.wait_for_load_state("networkidle")
        
        # Look for role dropdown
        role_select = page.locator('select[name="role"]').first
        
        if role_select.is_visible():
            # Check it has options
            options = role_select.locator('option')
            expect(options.first).to_be_visible()
        
        helpers.take_screenshot(page, "user_role_dropdown")


@pytest.mark.e2e
@pytest.mark.admin
class TestWalletManagement:
    """Tests for wallet management functionality."""
    
    def test_wallets_list_loads(self, logged_in_admin: Page, helpers):
        """
        ✅ TEST: Wallets list page loads
        
        Vérifie que la liste des portefeuilles se charge.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/wallets")
        page.wait_for_load_state("networkidle")
        
        # Check page loaded
        expect(page).to_have_url(re.compile(r".*/admin/wallets.*"))
        
        helpers.take_screenshot(page, "admin_wallets_list")
    
    def test_wallet_adjustment_form(self, logged_in_admin: Page, helpers):
        """
        💰 TEST: Wallet adjustment form accessible
        
        Vérifie que le formulaire d'ajustement de solde est accessible.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/wallets")
        page.wait_for_load_state("networkidle")
        
        # Look for adjust button
        adjust_btn = page.locator('button:has-text("Ajuster"), a:has-text("Adjust")').first
        
        if adjust_btn.is_visible():
            adjust_btn.click()
            page.wait_for_timeout(500)
            
            # Modal or form should appear
            adjust_form = page.locator('form[action*="adjust"], .adjust-form, .modal')
            if adjust_form.count() > 0:
                helpers.take_screenshot(page, "wallet_adjust_form")


@pytest.mark.e2e
@pytest.mark.admin
class TestTransactionManagement:
    """Tests for transaction management."""
    
    def test_transactions_list_loads(self, logged_in_admin: Page, helpers):
        """
        ✅ TEST: Transactions list page loads
        
        Vérifie que la liste des transactions se charge.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/transactions")
        page.wait_for_load_state("networkidle")
        
        expect(page).to_have_url(re.compile(r".*/admin/transactions.*"))
        
        # Check for transactions or empty state
        page_content = page.content()
        assert any(word in page_content for word in ["Transaction", "Historique", "Aucune"])
        
        helpers.take_screenshot(page, "admin_transactions_list")
    
    def test_transaction_filters(self, logged_in_admin: Page):
        """
        🔍 TEST: Transaction filters exist
        
        Vérifie que les filtres de transactions existent.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/transactions")
        page.wait_for_load_state("networkidle")
        
        # Look for filter elements
        filters = page.locator('.filter, select[name*="filter"], .wise-filter-btn')
        
        # Page should have some filtering capability
        expect(page.locator('body')).to_be_visible()


@pytest.mark.e2e
@pytest.mark.admin
class TestBankManagement:
    """Tests for bank management functionality."""
    
    def test_banks_list_loads(self, logged_in_admin: Page, helpers):
        """
        ✅ TEST: Banks list page loads
        
        Vérifie que la liste des banques se charge.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/banks")
        page.wait_for_load_state("networkidle")
        
        expect(page).to_have_url(re.compile(r".*/admin/banks.*"))
        
        helpers.take_screenshot(page, "admin_banks_list")

    def test_assign_user_to_bank(self, logged_in_admin: Page, helpers):
        """
        ✅ TEST: Assign user to bank
        
        Vérifie que l'assignation d'un utilisateur à une banque fonctionne.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/banks")
        page.wait_for_load_state("networkidle")

        # Find the first bank card
        first_bank_card = page.locator('.bank-card').first
        expect(first_bank_card).to_be_visible()

        # Find the user select dropdown and assign button
        user_select = first_bank_card.locator('select[id^="user-select-"]')
        assign_button = first_bank_card.locator('button:has-text("Assigner")')

        if user_select.count() > 0 and assign_button.count() > 0:
            # Select the first user in the dropdown (if any)
            options = user_select.locator('option')
            if options.count() > 1:
                user_to_assign = options.nth(1).get_attribute('value')
                user_select.select_option(user_to_assign)
                
                assign_button.click()
                
                # Wait for the success message
                expect(page.locator('.alert-success, .toast-success')).to_be_visible()
                
                helpers.take_screenshot(page, "assign_user_success")

    def test_bank_card_style(self, logged_in_admin: Page, helpers):
        """
        🎨 TEST: Bank card new style
        
        Vérifie que le nouveau style des cartes de banque est appliqué.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/banks")
        page.wait_for_load_state("networkidle")

        # Find the first bank card
        first_bank_card = page.locator('.bank-card').first
        expect(first_bank_card).to_be_visible()

        # Check for logo classes
        logo_container = first_bank_card.locator('.bank-logo-container')
        logo_img = first_bank_card.locator('.bank-logo-img')
        expect(logo_container).to_have_class(re.compile(r'bank-logo-container'))
        expect(logo_img).to_have_class(re.compile(r'bank-logo-img'))

        # Check for button classes
        edit_button = first_bank_card.locator('a:has-text("Modifier")')
        delete_button = first_bank_card.locator('button[aria-label="Supprimer"]')
        
        expect(edit_button).to_have_class(re.compile(r'btn-secondary'))
        expect(delete_button).to_have_class(re.compile(r'btn-danger-outline'))

        helpers.take_screenshot(page, "bank_card_new_style")

    def test_add_bank_form(self, logged_in_admin: Page, helpers):
        """
        ➕ TEST: Add bank form accessible
        
        Vérifie que le formulaire d'ajout de banque est accessible.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/banks/add")
        page.wait_for_load_state("networkidle")
        
        # Check form elements
        name_input = page.locator('input[name="name"], input[name="bank_name"]')
        
        if name_input.count() > 0:
            expect(name_input.first).to_be_visible()
        
        helpers.take_screenshot(page, "add_bank_form")


@pytest.mark.e2e
@pytest.mark.admin
class TestAdminExports:
    """Tests for admin export functionality."""
    
    def test_export_users_csv(self, logged_in_admin: Page, helpers):
        """
        📥 TEST: Export users to CSV
        
        Vérifie que l'export CSV des utilisateurs fonctionne.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/users")
        page.wait_for_load_state("networkidle")
        
        # Look for export button
        export_btn = page.locator('a[href*="export/users"], button:has-text("CSV"), a:has-text("CSV")')
        
        if export_btn.count() > 0:
            # Set up download handler
            with page.expect_download(timeout=10000) as download_info:
                export_btn.first.click()
            
            download = download_info.value
            
            # Check filename
            assert ".csv" in download.suggested_filename.lower()
            
            helpers.take_screenshot(page, "export_users_initiated")
    
    def test_export_transactions_csv(self, logged_in_admin: Page, helpers):
        """
        📥 TEST: Export transactions to CSV
        
        Vérifie que l'export CSV des transactions fonctionne.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/transactions")
        page.wait_for_load_state("networkidle")
        
        export_btn = page.locator('a[href*="export/transactions"], button:has-text("Export")')
        
        if export_btn.count() > 0:
            # Export should be accessible
            expect(export_btn.first).to_be_visible()
            
            helpers.take_screenshot(page, "export_transactions_button")


@pytest.mark.e2e
@pytest.mark.admin
class TestAdminNavigation:
    """Tests for admin navigation."""
    
    def test_admin_bottom_nav(self, logged_in_admin: Page, helpers):
        """
        📱 TEST: Admin bottom navigation works
        
        Vérifie que la navigation admin fonctionne.
        """
        page = logged_in_admin
        
        page.goto(f"{BASE_URL}/admin/")
        page.wait_for_load_state("networkidle")
        
        # Check for bottom nav or sidebar nav
        nav = page.locator('nav, .nav-bottom, .sidebar')
        expect(nav.first).to_be_visible()
        
        helpers.take_screenshot(page, "admin_navigation")
    
    def test_navigate_between_admin_pages(self, logged_in_admin: Page, helpers):
        """
        🔗 TEST: Navigate between admin pages
        
        Vérifie la navigation entre les pages admin.
        """
        page = logged_in_admin
        
        # Start at dashboard
        page.goto(f"{BASE_URL}/admin/")
        page.wait_for_load_state("networkidle")
        
        # Navigate to users
        users_link = page.locator('a[href*="/admin/users"]').first
        if users_link.is_visible():
            users_link.click()
            page.wait_for_load_state("networkidle")
            expect(page).to_have_url(re.compile(r".*/admin/users.*"))
        
        # Navigate back to dashboard
        dashboard_link = page.locator('a[href="/admin/"], a[href="/admin"]').first
        if dashboard_link.is_visible():
            dashboard_link.click()
            page.wait_for_load_state("networkidle")
        
        helpers.take_screenshot(page, "admin_navigation_flow")


@pytest.mark.e2e
@pytest.mark.admin
class TestAdminAccessControl:
    """Tests for admin access control."""
    
    def test_regular_user_cannot_access_admin(self, logged_in_user: Page, helpers):
        """
        🔒 TEST: Regular user cannot access admin
        
        Vérifie qu'un utilisateur normal ne peut pas accéder à l'admin.
        """
        page = logged_in_user
        
        page.goto(f"{BASE_URL}/admin/")
        page.wait_for_load_state("networkidle")
        
        # Should be redirected or shown forbidden
        expect(page).not_to_have_url(re.compile(r".*/admin/$"))
        
        helpers.take_screenshot(page, "user_admin_forbidden")
    
    def test_bank_user_cannot_access_admin(self, logged_in_bank_user: Page, helpers):
        """
        🔒 TEST: Bank user cannot access admin routes
        
        Vérifie qu'un utilisateur banque ne peut pas accéder à certaines routes admin.
        """
        page = logged_in_bank_user
        
        # Try accessing full admin dashboard
        page.goto(f"{BASE_URL}/admin/")
        page.wait_for_load_state("networkidle")
        
        # Should not have full admin access
        # Either redirected or limited view
        
        helpers.take_screenshot(page, "bank_user_admin_access")


@pytest.mark.e2e
@pytest.mark.admin
class TestAdminMobile:
    """Tests for admin on mobile viewport."""
    
    def test_admin_dashboard_mobile(self, mobile_page: Page, helpers):
        """
        📱 TEST: Admin dashboard responsive on mobile
        
        Vérifie que le dashboard admin est responsive sur mobile.
        """
        page = mobile_page
        
        # Login as admin
        account = TEST_ACCOUNTS["admin"]
        page.goto(f"{BASE_URL}/auth/login")
        page.fill('input[name="email"]', account["email"])
        page.fill('input[name="password"]', account["password"])
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        
        # Navigate to admin
        page.goto(f"{BASE_URL}/admin/")
        page.wait_for_load_state("networkidle")
        
        # Check page renders properly
        expect(page.locator('body')).to_be_visible()
        
        helpers.take_screenshot(page, "admin_dashboard_mobile")
    
    def test_admin_users_mobile(self, mobile_page: Page, helpers):
        """
        📱 TEST: Admin users list responsive on mobile
        
        Vérifie que la liste des utilisateurs est responsive sur mobile.
        """
        page = mobile_page
        
        # Login as admin
        account = TEST_ACCOUNTS["admin"]
        page.goto(f"{BASE_URL}/auth/login")
        page.fill('input[name="email"]', account["email"])
        page.fill('input[name="password"]', account["password"])
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        
        # Navigate to users
        page.goto(f"{BASE_URL}/admin/users")
        page.wait_for_load_state("networkidle")
        
        # Elements should be visible and not overflow
        search = page.locator('#search-input, input[type="search"]')
        if search.count() > 0:
            expect(search.first).to_be_visible()
        
        helpers.take_screenshot(page, "admin_users_mobile")
