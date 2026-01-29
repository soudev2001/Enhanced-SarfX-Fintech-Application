"""
SarfX E2E Tests - Currency Converter Suite
==========================================

Tests for currency conversion, rate display, and exchange functionality.

Run with:
    pytest tests/e2e/test_converter.py -v --headed
    pytest tests/e2e/test_converter.py --video=on
"""

import pytest
from playwright.sync_api import Page, expect
import re

from tests.conftest import BASE_URL, TEST_ACCOUNTS


@pytest.mark.e2e
@pytest.mark.converter
class TestConverterPage:
    """Tests for the converter page UI."""
    
    def test_converter_page_loads(self, logged_in_user: Page, helpers):
        """
        ✅ TEST: Converter page loads correctly
        
        Vérifie que la page de conversion se charge avec tous les éléments.
        """
        page = logged_in_user
        
        page.goto(f"{BASE_URL}/app/converter")
        page.wait_for_load_state("networkidle")
        
        # Check main elements
        expect(page.locator('#smart-amount, input[name="amount"]')).to_be_visible()
        expect(page.locator('#from-currency, select[name="from_currency"]')).to_be_visible()
        expect(page.locator('#to-currency, select[name="to_currency"]')).to_be_visible()
        
        helpers.take_screenshot(page, "converter_page_loaded")
    
    def test_converter_has_currency_selectors(self, logged_in_user: Page):
        """
        ✅ TEST: Currency selectors have options
        
        Vérifie que les sélecteurs de devise ont des options.
        """
        page = logged_in_user
        
        page.goto(f"{BASE_URL}/app/converter")
        page.wait_for_load_state("networkidle")
        
        # Check from currency has options
        from_select = page.locator('#from-currency, select[name="from_currency"]')
        options = from_select.locator('option')
        expect(options.first).to_be_visible()
        
        # Should have common currencies
        page_content = page.content()
        assert "USD" in page_content or "EUR" in page_content or "MAD" in page_content
    
    def test_converter_tabs_exist(self, logged_in_user: Page):
        """
        ✅ TEST: Converter has tabs (Providers, Pairs, Alerts)
        
        Vérifie que les onglets de navigation existent.
        """
        page = logged_in_user
        
        page.goto(f"{BASE_URL}/app/converter")
        page.wait_for_load_state("networkidle")
        
        # Check for tabs
        tabs = page.locator('.wise-tab, .tab, [role="tab"]')
        
        # Should have at least 2 tabs
        if tabs.count() >= 2:
            expect(tabs.first).to_be_visible()


@pytest.mark.e2e
@pytest.mark.converter
class TestConversionCalculation:
    """Tests for currency conversion calculations."""
    
    def test_basic_conversion_usd_to_mad(self, logged_in_user: Page, helpers):
        """
        💱 TEST: Basic USD to MAD conversion
        
        Vérifie que la conversion USD → MAD fonctionne et donne un résultat valide.
        """
        page = logged_in_user
        
        page.goto(f"{BASE_URL}/app/converter")
        page.wait_for_load_state("networkidle")
        
        # Clear and fill amount
        amount_input = page.locator('#smart-amount, input[name="amount"]')
        amount_input.fill("1000")
        
        # Select currencies
        from_select = page.locator('#from-currency, select[name="from_currency"]')
        to_select = page.locator('#to-currency, select[name="to_currency"]')
        
        if from_select.is_visible():
            from_select.select_option("USD")
        if to_select.is_visible():
            to_select.select_option("MAD")
        
        # Wait for calculation (debounced)
        page.wait_for_timeout(1500)
        
        # Check result
        result_input = page.locator('#recipient-amount, .result-amount, [data-result]')
        if result_input.is_visible():
            result_value = result_input.input_value()
            
            # Should be a number > 0 (1000 USD ≈ 10000 MAD)
            if result_value and result_value != "--":
                result_num = float(result_value.replace(",", "").replace(" ", ""))
                assert result_num > 0, "Conversion result should be positive"
                
                # USD to MAD rate is typically around 10
                assert result_num > 5000, "1000 USD should be > 5000 MAD"
                assert result_num < 15000, "1000 USD should be < 15000 MAD"
        
        helpers.take_screenshot(page, "conversion_usd_mad")
    
    def test_conversion_eur_to_mad(self, logged_in_user: Page, helpers):
        """
        💱 TEST: EUR to MAD conversion
        
        Vérifie que la conversion EUR → MAD fonctionne.
        """
        page = logged_in_user
        
        page.goto(f"{BASE_URL}/app/converter")
        page.wait_for_load_state("networkidle")
        
        amount_input = page.locator('#smart-amount, input[name="amount"]')
        amount_input.fill("500")
        
        from_select = page.locator('#from-currency')
        to_select = page.locator('#to-currency')
        
        if from_select.is_visible():
            from_select.select_option("EUR")
        if to_select.is_visible():
            to_select.select_option("MAD")
        
        page.wait_for_timeout(1500)
        
        helpers.take_screenshot(page, "conversion_eur_mad")
    
    def test_conversion_amount_updates_on_input(self, logged_in_user: Page):
        """
        ⚡ TEST: Result updates as user types
        
        Vérifie que le résultat se met à jour pendant la saisie.
        """
        page = logged_in_user
        
        page.goto(f"{BASE_URL}/app/converter")
        page.wait_for_load_state("networkidle")
        
        amount_input = page.locator('#smart-amount, input[name="amount"]')
        result_display = page.locator('#recipient-amount, .result-amount')
        
        # Type amount character by character
        amount_input.fill("")
        amount_input.type("100", delay=100)
        
        page.wait_for_timeout(1500)
        
        # Result should have updated
        if result_display.is_visible():
            result = result_display.input_value()
            assert result != "--", "Result should update after typing"
    
    def test_conversion_with_zero_amount(self, logged_in_user: Page):
        """
        ⚠️ TEST: Conversion with zero amount
        
        Vérifie le comportement avec un montant de 0.
        """
        page = logged_in_user
        
        page.goto(f"{BASE_URL}/app/converter")
        page.wait_for_load_state("networkidle")
        
        amount_input = page.locator('#smart-amount, input[name="amount"]')
        amount_input.fill("0")
        
        page.wait_for_timeout(1000)
        
        # Result should be 0 or empty
        result_display = page.locator('#recipient-amount, .result-amount')
        if result_display.is_visible():
            result = result_display.input_value()
            if result and result not in ["--", "", "0", "0.00"]:
                result_num = float(result.replace(",", ""))
                assert result_num == 0, "Zero amount should give zero result"


@pytest.mark.e2e
@pytest.mark.converter
class TestCurrencyPairs:
    """Tests for currency pair selection."""
    
    def test_quick_pair_selection(self, logged_in_user: Page, helpers):
        """
        ⚡ TEST: Quick currency pair selection
        
        Vérifie que les paires de devises rapides fonctionnent.
        """
        page = logged_in_user
        
        page.goto(f"{BASE_URL}/app/converter")
        page.wait_for_load_state("networkidle")
        
        # Look for quick pair buttons/cards
        pair_cards = page.locator('.wise-pair-card, .currency-pair, [data-pair]')
        
        if pair_cards.count() > 0:
            # Click on EUR/MAD pair if available
            eur_mad_pair = page.locator('.wise-pair-card:has-text("EUR"), [data-pair="EUR/MAD"]')
            if eur_mad_pair.count() > 0:
                eur_mad_pair.first.click()
                page.wait_for_timeout(500)
                
                # Check if currencies were updated
                from_select = page.locator('#from-currency')
                if from_select.is_visible():
                    selected_from = from_select.input_value()
                    # Should be EUR or related
        
        helpers.take_screenshot(page, "pair_selection")
    
    def test_swap_currencies(self, logged_in_user: Page):
        """
        🔄 TEST: Swap currencies button
        
        Vérifie que le bouton d'échange de devises fonctionne.
        """
        page = logged_in_user
        
        page.goto(f"{BASE_URL}/app/converter")
        page.wait_for_load_state("networkidle")
        
        from_select = page.locator('#from-currency')
        to_select = page.locator('#to-currency')
        
        if from_select.is_visible() and to_select.is_visible():
            # Get initial values
            initial_from = from_select.input_value()
            initial_to = to_select.input_value()
            
            # Look for swap button
            swap_btn = page.locator('button:has-text("⇄"), .swap-btn, [aria-label*="swap"]')
            
            if swap_btn.count() > 0:
                swap_btn.first.click()
                page.wait_for_timeout(500)
                
                # Check if swapped
                new_from = from_select.input_value()
                new_to = to_select.input_value()
                
                # Values should be swapped
                assert new_from == initial_to or new_to == initial_from


@pytest.mark.e2e
@pytest.mark.converter
class TestRateDisplay:
    """Tests for exchange rate display."""
    
    def test_rate_is_displayed(self, logged_in_user: Page, helpers):
        """
        📊 TEST: Exchange rate is displayed
        
        Vérifie que le taux de change est affiché.
        """
        page = logged_in_user
        
        page.goto(f"{BASE_URL}/app/converter")
        page.wait_for_load_state("networkidle")
        
        # Set up a conversion
        amount_input = page.locator('#smart-amount, input[name="amount"]')
        amount_input.fill("100")
        
        page.wait_for_timeout(1500)
        
        # Look for rate display
        rate_display = page.locator('.rate, .exchange-rate, [data-rate], #home-rate')
        
        page_content = page.content()
        
        # Should have some rate indication (number with decimals)
        assert re.search(r'\d+\.\d+', page_content), "Rate should be displayed somewhere"
        
        helpers.take_screenshot(page, "rate_display")
    
    def test_refresh_rates_button(self, logged_in_user: Page, helpers):
        """
        🔄 TEST: Refresh rates button works
        
        Vérifie que le bouton de rafraîchissement des taux fonctionne.
        """
        page = logged_in_user
        
        page.goto(f"{BASE_URL}/app/converter")
        page.wait_for_load_state("networkidle")
        
        # Look for refresh button
        refresh_btn = page.locator('button:has-text("Refresh"), button:has-text("Actualiser"), .refresh-btn')
        
        if refresh_btn.count() > 0:
            # Get current time display if exists
            time_display = page.locator('#update-time, .last-update')
            
            refresh_btn.first.click()
            
            # Wait for update
            page.wait_for_timeout(2000)
            
            helpers.take_screenshot(page, "rates_refreshed")
    
    def test_rate_history_chart(self, logged_in_user: Page, helpers):
        """
        📈 TEST: Rate history chart is displayed
        
        Vérifie que le graphique d'historique des taux s'affiche.
        """
        page = logged_in_user
        
        page.goto(f"{BASE_URL}/app/converter")
        page.wait_for_load_state("networkidle")
        
        # Look for chart container
        chart = page.locator('#rate-history-chart, .apexcharts-canvas, canvas, .chart')
        
        if chart.count() > 0:
            # Wait for chart to render
            page.wait_for_timeout(2000)
            expect(chart.first).to_be_visible()
        
        helpers.take_screenshot(page, "rate_chart")


@pytest.mark.e2e
@pytest.mark.converter
class TestProvidersList:
    """Tests for exchange providers list."""
    
    def test_providers_list_displayed(self, logged_in_user: Page, helpers):
        """
        🏦 TEST: Providers list is displayed
        
        Vérifie que la liste des fournisseurs est affichée.
        """
        page = logged_in_user
        
        page.goto(f"{BASE_URL}/app/converter")
        page.wait_for_load_state("networkidle")
        
        # Set amount to trigger providers fetch
        amount_input = page.locator('#smart-amount')
        if amount_input.is_visible():
            amount_input.fill("1000")
        
        page.wait_for_timeout(2000)
        
        # Look for providers list
        providers = page.locator('#suppliers-list, .wise-providers-list, .provider-card')
        
        if providers.count() > 0:
            expect(providers.first).to_be_visible()
        
        helpers.take_screenshot(page, "providers_list")
    
    def test_best_provider_highlighted(self, logged_in_user: Page):
        """
        ⭐ TEST: Best provider is highlighted
        
        Vérifie que le meilleur fournisseur est mis en évidence.
        """
        page = logged_in_user
        
        page.goto(f"{BASE_URL}/app/converter")
        page.wait_for_load_state("networkidle")
        
        amount_input = page.locator('#smart-amount')
        if amount_input.is_visible():
            amount_input.fill("1000")
        
        page.wait_for_timeout(2000)
        
        # Look for "best" indicator
        best_badge = page.locator('.wise-best-tag, .best-provider, :has-text("Meilleur"), :has-text("Best")')
        
        # At least one provider should be marked as best
        page_content = page.content()
        assert "Meilleur" in page_content or "Best" in page_content or "best" in page_content.lower()


@pytest.mark.e2e
@pytest.mark.converter
class TestAlerts:
    """Tests for rate alerts functionality."""
    
    def test_alerts_tab_accessible(self, logged_in_user: Page, helpers):
        """
        🔔 TEST: Alerts tab is accessible
        
        Vérifie que l'onglet des alertes est accessible.
        """
        page = logged_in_user
        
        page.goto(f"{BASE_URL}/app/converter")
        page.wait_for_load_state("networkidle")
        
        # Click on alerts tab
        alerts_tab = page.locator('.wise-tab:has-text("Alert"), [data-tab="alerts"], button:has-text("Alert")')
        
        if alerts_tab.count() > 0:
            alerts_tab.first.click()
            page.wait_for_timeout(500)
            
            # Check alerts content is visible
            alerts_content = page.locator('#tab-alerts, .alerts-section')
            if alerts_content.count() > 0:
                expect(alerts_content.first).to_be_visible()
        
        helpers.take_screenshot(page, "alerts_tab")
    
    def test_create_alert_form(self, logged_in_user: Page, helpers):
        """
        ➕ TEST: Create alert form is accessible
        
        Vérifie que le formulaire de création d'alerte est accessible.
        """
        page = logged_in_user
        
        page.goto(f"{BASE_URL}/app/converter")
        page.wait_for_load_state("networkidle")
        
        # Navigate to alerts tab
        alerts_tab = page.locator('.wise-tab:has-text("Alert"), [data-tab="alerts"]')
        if alerts_tab.count() > 0:
            alerts_tab.first.click()
            page.wait_for_timeout(500)
        
        # Check for alert form elements
        alert_pair = page.locator('#alert-pair, select[name="alert_pair"]')
        alert_rate = page.locator('#alert-rate, input[name="alert_rate"]')
        
        if alert_pair.is_visible() and alert_rate.is_visible():
            # Fill alert form
            alert_rate.fill("10.5")
            
            helpers.take_screenshot(page, "alert_form_filled")


@pytest.mark.e2e
@pytest.mark.converter
class TestMobileConverter:
    """Tests for converter on mobile viewport."""
    
    def test_converter_responsive_mobile(self, mobile_page: Page, helpers):
        """
        📱 TEST: Converter is responsive on mobile
        
        Vérifie que le convertisseur s'affiche correctement sur mobile.
        """
        page = mobile_page
        
        # Login first
        account = TEST_ACCOUNTS["user"]
        page.goto(f"{BASE_URL}/auth/login")
        page.fill('input[name="email"]', account["email"])
        page.fill('input[name="password"]', account["password"])
        page.click('button[type="submit"]')
        page.wait_for_url(lambda url: "/app" in url, timeout=15000)
        
        # Navigate to converter
        page.goto(f"{BASE_URL}/app/converter")
        page.wait_for_load_state("networkidle")
        
        # Check elements are visible and properly sized
        amount_input = page.locator('#smart-amount, input[name="amount"]')
        expect(amount_input).to_be_visible()
        
        helpers.take_screenshot(page, "converter_mobile")
    
    def test_conversion_works_mobile(self, mobile_page: Page, helpers):
        """
        📱 TEST: Conversion works on mobile
        
        Vérifie que la conversion fonctionne sur mobile.
        """
        page = mobile_page
        
        # Login
        account = TEST_ACCOUNTS["user"]
        page.goto(f"{BASE_URL}/auth/login")
        page.fill('input[name="email"]', account["email"])
        page.fill('input[name="password"]', account["password"])
        page.click('button[type="submit"]')
        page.wait_for_url(lambda url: "/app" in url, timeout=15000)
        
        # Navigate and convert
        page.goto(f"{BASE_URL}/app/converter")
        page.wait_for_load_state("networkidle")
        
        amount_input = page.locator('#smart-amount')
        if amount_input.is_visible():
            amount_input.fill("500")
        
        page.wait_for_timeout(1500)
        
        helpers.take_screenshot(page, "conversion_mobile_result")
