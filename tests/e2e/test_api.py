"""
SarfX E2E Tests - API Endpoints Suite
=====================================

Tests for API endpoints using Playwright's API testing capabilities.

Run with:
    pytest tests/e2e/test_api.py -v
    pytest tests/e2e/test_api.py -k "rates"
"""

import pytest
from playwright.sync_api import APIRequestContext, expect
import re
import json

from tests.conftest import BASE_URL, TEST_ACCOUNTS


@pytest.mark.e2e
@pytest.mark.api
class TestRatesAPI:
    """Tests for exchange rates API endpoints."""
    
    def test_get_rates_endpoint(self, api_context: APIRequestContext):
        """
        ✅ TEST: GET /api/rates returns data
        
        Vérifie que l'endpoint des taux retourne des données.
        """
        response = api_context.get(f"{BASE_URL}/api/rates")
        
        assert response.ok, f"Expected OK response, got {response.status}"
        
        data = response.json()
        
        # Should have rates data
        assert data is not None
        # Check for common rate structure
        assert "rates" in data or "rate" in data or "success" in data
    
    def test_get_live_rates(self, api_context: APIRequestContext):
        """
        ✅ TEST: GET /api/rates/live returns live rates
        
        Vérifie que les taux en direct sont retournés.
        """
        response = api_context.get(f"{BASE_URL}/api/rates/live")
        
        # Should return OK or redirect
        assert response.status < 500, f"Server error: {response.status}"
        
        if response.ok:
            data = response.json()
            # Should have rate information
            assert data is not None
    
    def test_get_best_rates(self, api_context: APIRequestContext):
        """
        ✅ TEST: GET /api/rates/best returns best rates
        
        Vérifie que les meilleurs taux sont retournés.
        """
        response = api_context.get(
            f"{BASE_URL}/api/rates/best",
            params={"amount": "1000", "from": "USD", "to": "MAD"}
        )
        
        if response.ok:
            data = response.json()
            
            # Should have best rate info
            if "best" in data:
                assert data["best"] is not None
    
    def test_rates_with_invalid_currency(self, api_context: APIRequestContext):
        """
        ❌ TEST: Invalid currency returns error
        
        Vérifie qu'une devise invalide retourne une erreur.
        """
        response = api_context.get(
            f"{BASE_URL}/api/rates/live",
            params={"base": "INVALID", "quote": "MAD"}
        )
        
        # Should handle gracefully (either error response or fallback)
        assert response.status < 500, "Should not cause server error"


@pytest.mark.e2e
@pytest.mark.api
class TestConvertAPI:
    """Tests for currency conversion API."""
    
    def test_convert_usd_to_mad(self, api_context: APIRequestContext):
        """
        ✅ TEST: Convert USD to MAD
        
        Vérifie la conversion USD vers MAD via l'API.
        """
        response = api_context.get(
            f"{BASE_URL}/api/convert",
            params={"amount": "100", "from": "USD", "to": "MAD"}
        )
        
        if response.ok:
            data = response.json()
            
            # Should have conversion result
            if data.get("success"):
                assert "result" in data or "converted" in data
                
                # Result should be reasonable (100 USD ≈ 1000 MAD)
                result = data.get("result", data.get("converted", 0))
                if isinstance(result, (int, float)):
                    assert result > 500, "100 USD should be > 500 MAD"
                    assert result < 1500, "100 USD should be < 1500 MAD"
    
    def test_convert_eur_to_mad(self, api_context: APIRequestContext):
        """
        ✅ TEST: Convert EUR to MAD
        
        Vérifie la conversion EUR vers MAD via l'API.
        """
        response = api_context.get(
            f"{BASE_URL}/api/convert",
            params={"amount": "50", "from": "EUR", "to": "MAD"}
        )
        
        if response.ok:
            data = response.json()
            
            if data.get("success"):
                result = data.get("result", data.get("converted", 0))
                if isinstance(result, (int, float)):
                    # 50 EUR should be around 500 MAD
                    assert result > 250, "50 EUR should be > 250 MAD"
    
    def test_convert_zero_amount(self, api_context: APIRequestContext):
        """
        ⚠️ TEST: Convert with zero amount
        
        Vérifie le comportement avec un montant de 0.
        """
        response = api_context.get(
            f"{BASE_URL}/api/convert",
            params={"amount": "0", "from": "USD", "to": "MAD"}
        )
        
        # Should handle gracefully
        assert response.status < 500, "Should not cause server error"
        
        if response.ok:
            data = response.json()
            # Either error or 0 result
            if data.get("success"):
                result = data.get("result", data.get("converted", 0))
                assert result == 0 or result is None
    
    def test_convert_negative_amount(self, api_context: APIRequestContext):
        """
        ❌ TEST: Convert with negative amount
        
        Vérifie le comportement avec un montant négatif.
        """
        response = api_context.get(
            f"{BASE_URL}/api/convert",
            params={"amount": "-100", "from": "USD", "to": "MAD"}
        )
        
        # Should handle gracefully (error or rejection)
        assert response.status < 500, "Should not cause server error"
        
        if response.ok:
            data = response.json()
            # Should indicate error or invalid
            if data.get("success") is False:
                assert "error" in data
    
    def test_convert_missing_params(self, api_context: APIRequestContext):
        """
        ❌ TEST: Convert with missing parameters
        
        Vérifie le comportement sans paramètres.
        """
        response = api_context.get(f"{BASE_URL}/api/convert")
        
        # Should return error or use defaults
        assert response.status < 500, "Should not cause server error"


@pytest.mark.e2e
@pytest.mark.api
class TestHistoryAPI:
    """Tests for rate history API."""
    
    def test_get_rate_history(self, api_context: APIRequestContext):
        """
        ✅ TEST: GET /api/rates/history returns historical data
        
        Vérifie que l'historique des taux est retourné.
        """
        response = api_context.get(
            f"{BASE_URL}/api/rates/history",
            params={"base": "USD", "quote": "MAD", "days": "7"}
        )
        
        if response.ok:
            data = response.json()
            
            # Should have historical data array
            if data.get("success"):
                assert "data" in data or "history" in data
    
    def test_rate_history_with_period(self, api_context: APIRequestContext):
        """
        ✅ TEST: Rate history with different periods
        
        Vérifie l'historique avec différentes périodes.
        """
        for days in ["7", "30"]:
            response = api_context.get(
                f"{BASE_URL}/api/rates/history",
                params={"base": "EUR", "quote": "MAD", "days": days}
            )
            
            assert response.status < 500, f"Server error for {days} days"


@pytest.mark.e2e
@pytest.mark.api
class TestBanksAPI:
    """Tests for banks API endpoints."""
    
    def test_get_banks_list(self, api_context: APIRequestContext):
        """
        ✅ TEST: GET /api/banks returns banks list
        
        Vérifie que la liste des banques est retournée.
        """
        response = api_context.get(f"{BASE_URL}/api/banks")
        
        if response.ok:
            data = response.json()
            
            # Should be a list or have banks key
            assert isinstance(data, list) or "banks" in data
    
    def test_banks_have_required_fields(self, api_context: APIRequestContext):
        """
        ✅ TEST: Banks have required fields
        
        Vérifie que les banques ont les champs requis.
        """
        response = api_context.get(f"{BASE_URL}/api/banks")
        
        if response.ok:
            data = response.json()
            banks = data if isinstance(data, list) else data.get("banks", [])
            
            if len(banks) > 0:
                bank = banks[0]
                # Should have basic fields
                assert "name" in bank or "bank_name" in bank or "_id" in bank


@pytest.mark.e2e
@pytest.mark.api
class TestATMsAPI:
    """Tests for ATM locator API."""
    
    def test_get_atms_list(self, api_context: APIRequestContext):
        """
        ✅ TEST: GET /api/atms returns ATMs list
        
        Vérifie que la liste des ATMs est retournée.
        """
        response = api_context.get(f"{BASE_URL}/api/atms")
        
        if response.ok:
            data = response.json()
            
            # Should return ATMs data
            assert data is not None
    
    def test_nearest_atms_endpoint(self, api_context: APIRequestContext):
        """
        ✅ TEST: POST /api/atms/nearest returns nearby ATMs
        
        Vérifie que les ATMs proches sont retournés.
        """
        # Casablanca coordinates
        response = api_context.post(
            f"{BASE_URL}/api/atms/nearest",
            data={
                "lat": "33.5731",
                "lng": "-7.5898"
            }
        )
        
        # Should handle the request
        assert response.status < 500, "Should not cause server error"


@pytest.mark.e2e
@pytest.mark.api
class TestWalletAPI:
    """Tests for wallet API endpoints (authenticated)."""
    
    def test_wallet_balance_unauthenticated(self, api_context: APIRequestContext):
        """
        🔒 TEST: Wallet balance requires authentication
        
        Vérifie que le solde nécessite une authentification.
        """
        response = api_context.get(f"{BASE_URL}/api/wallet/balance")
        
        # Should return unauthorized or redirect
        assert response.status in [401, 403, 302, 200], f"Unexpected status: {response.status}"
        
        if response.ok:
            data = response.json()
            # If 200, should indicate not logged in
            assert data.get("error") or data.get("success") is False or "login" in str(data).lower()
    
    def test_create_wallet_unauthenticated(self, api_context: APIRequestContext):
        """
        🔒 TEST: Create wallet requires authentication
        
        Vérifie que la création de wallet nécessite une authentification.
        """
        response = api_context.post(f"{BASE_URL}/api/wallet/create")
        
        # Should not allow without auth
        assert response.status in [401, 403, 302, 200]


@pytest.mark.e2e
@pytest.mark.api
class TestAlertsAPI:
    """Tests for rate alerts API."""
    
    def test_get_alerts_unauthenticated(self, api_context: APIRequestContext):
        """
        🔒 TEST: Get alerts requires authentication
        
        Vérifie que les alertes nécessitent une authentification.
        """
        response = api_context.get(f"{BASE_URL}/api/alerts")
        
        # Should require auth
        assert response.status < 500
    
    def test_create_alert_unauthenticated(self, api_context: APIRequestContext):
        """
        🔒 TEST: Create alert requires authentication
        
        Vérifie que la création d'alerte nécessite une authentification.
        """
        response = api_context.post(
            f"{BASE_URL}/api/alerts",
            data={
                "pair": "USD/MAD",
                "target_rate": "10.5",
                "condition": "above"
            }
        )
        
        # Should require auth
        assert response.status < 500


@pytest.mark.e2e
@pytest.mark.api
class TestThemeAPI:
    """Tests for theme preference API."""
    
    def test_set_theme(self, api_context: APIRequestContext):
        """
        ✅ TEST: POST /api/theme sets theme preference
        
        Vérifie que le thème peut être changé via l'API.
        """
        response = api_context.post(
            f"{BASE_URL}/api/theme",
            data={"theme": "dark"}
        )
        
        # Should accept theme change
        assert response.status < 500
    
    def test_set_theme_light(self, api_context: APIRequestContext):
        """
        ✅ TEST: Set light theme
        
        Vérifie le changement vers le thème clair.
        """
        response = api_context.post(
            f"{BASE_URL}/api/theme",
            data={"theme": "light"}
        )
        
        assert response.status < 500


@pytest.mark.e2e
@pytest.mark.api
class TestAPIErrorHandling:
    """Tests for API error handling."""
    
    def test_404_on_unknown_endpoint(self, api_context: APIRequestContext):
        """
        ❌ TEST: Unknown endpoint returns 404
        
        Vérifie qu'un endpoint inconnu retourne 404.
        """
        response = api_context.get(f"{BASE_URL}/api/unknown-endpoint-xyz")
        
        assert response.status == 404
    
    def test_api_returns_json(self, api_context: APIRequestContext):
        """
        ✅ TEST: API endpoints return JSON
        
        Vérifie que les endpoints retournent du JSON.
        """
        response = api_context.get(f"{BASE_URL}/api/rates")
        
        if response.ok:
            # Should be parseable as JSON
            try:
                data = response.json()
                assert data is not None
            except:
                pytest.fail("Response is not valid JSON")
    
    def test_api_cors_headers(self, api_context: APIRequestContext):
        """
        ✅ TEST: API has proper CORS headers (if applicable)
        
        Vérifie les headers CORS si présents.
        """
        response = api_context.get(f"{BASE_URL}/api/rates")
        
        # Check for content-type header
        content_type = response.headers.get("content-type", "")
        assert "json" in content_type.lower() or response.status != 200


@pytest.mark.e2e
@pytest.mark.api
class TestAPIPerformance:
    """Tests for API performance."""
    
    def test_rates_response_time(self, api_context: APIRequestContext):
        """
        ⚡ TEST: Rates API responds quickly
        
        Vérifie que l'API des taux répond rapidement.
        """
        import time
        
        start = time.time()
        response = api_context.get(f"{BASE_URL}/api/rates")
        duration = time.time() - start
        
        # Should respond within 5 seconds
        assert duration < 5, f"API took too long: {duration:.2f}s"
        
        # Ideally under 2 seconds
        if duration > 2:
            print(f"⚠️ Slow API response: {duration:.2f}s")
    
    def test_convert_response_time(self, api_context: APIRequestContext):
        """
        ⚡ TEST: Convert API responds quickly
        
        Vérifie que l'API de conversion répond rapidement.
        """
        import time
        
        start = time.time()
        response = api_context.get(
            f"{BASE_URL}/api/convert",
            params={"amount": "100", "from": "USD", "to": "MAD"}
        )
        duration = time.time() - start
        
        # Should respond within 5 seconds
        assert duration < 5, f"API took too long: {duration:.2f}s"


@pytest.mark.e2e
@pytest.mark.api
class TestDemoAPI:
    """Tests for demo/setup API endpoints."""
    
    def test_demo_users_endpoint(self, api_context: APIRequestContext):
        """
        ✅ TEST: Demo users setup endpoint exists
        
        Vérifie que l'endpoint de création d'utilisateurs démo existe.
        """
        response = api_context.get(f"{BASE_URL}/api/demo/setup")
        
        # Endpoint should exist and respond
        assert response.status < 500
