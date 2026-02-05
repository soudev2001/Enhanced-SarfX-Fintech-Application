"""
SarfX Currency Flags Utility
============================

Provides currency flag images using FlagCDN with fallback to emoji flags.
Features:
- CDN-hosted flags for high quality
- Local caching for performance
- Emoji fallback for unsupported currencies
- ISO country code mapping for currencies
"""

from typing import Dict, Optional
import time

# Currency to Country ISO mapping (ISO 3166-1 alpha-2)
CURRENCY_COUNTRY_MAP: Dict[str, str] = {
    # Major currencies
    'USD': 'us',  # United States Dollar
    'EUR': 'eu',  # Euro (EU flag)
    'GBP': 'gb',  # British Pound
    'JPY': 'jp',  # Japanese Yen
    'CHF': 'ch',  # Swiss Franc
    'CAD': 'ca',  # Canadian Dollar
    'AUD': 'au',  # Australian Dollar
    'NZD': 'nz',  # New Zealand Dollar
    'CNY': 'cn',  # Chinese Yuan
    'HKD': 'hk',  # Hong Kong Dollar
    'SGD': 'sg',  # Singapore Dollar
    'INR': 'in',  # Indian Rupee
    'KRW': 'kr',  # South Korean Won
    'TWD': 'tw',  # Taiwan Dollar
    'THB': 'th',  # Thai Baht
    'MYR': 'my',  # Malaysian Ringgit
    'IDR': 'id',  # Indonesian Rupiah
    'PHP': 'ph',  # Philippine Peso
    'VND': 'vn',  # Vietnamese Dong

    # Middle East & Africa
    'MAD': 'ma',  # Moroccan Dirham
    'AED': 'ae',  # UAE Dirham
    'SAR': 'sa',  # Saudi Riyal
    'QAR': 'qa',  # Qatari Riyal
    'KWD': 'kw',  # Kuwaiti Dinar
    'BHD': 'bh',  # Bahraini Dinar
    'OMR': 'om',  # Omani Rial
    'EGP': 'eg',  # Egyptian Pound
    'TND': 'tn',  # Tunisian Dinar
    'DZD': 'dz',  # Algerian Dinar
    'ZAR': 'za',  # South African Rand
    'NGN': 'ng',  # Nigerian Naira
    'KES': 'ke',  # Kenyan Shilling
    'GHS': 'gh',  # Ghanaian Cedi
    'XOF': 'sn',  # West African CFA (Senegal flag)
    'XAF': 'cm',  # Central African CFA (Cameroon flag)

    # Europe
    'SEK': 'se',  # Swedish Krona
    'NOK': 'no',  # Norwegian Krone
    'DKK': 'dk',  # Danish Krone
    'PLN': 'pl',  # Polish Zloty
    'CZK': 'cz',  # Czech Koruna
    'HUF': 'hu',  # Hungarian Forint
    'RON': 'ro',  # Romanian Leu
    'BGN': 'bg',  # Bulgarian Lev
    'HRK': 'hr',  # Croatian Kuna
    'RUB': 'ru',  # Russian Ruble
    'UAH': 'ua',  # Ukrainian Hryvnia
    'TRY': 'tr',  # Turkish Lira
    'ISK': 'is',  # Icelandic Króna

    # Americas
    'MXN': 'mx',  # Mexican Peso
    'BRL': 'br',  # Brazilian Real
    'ARS': 'ar',  # Argentine Peso
    'CLP': 'cl',  # Chilean Peso
    'COP': 'co',  # Colombian Peso
    'PEN': 'pe',  # Peruvian Sol

    # Crypto (special cases - use generic icons)
    'BTC': 'xx',  # Bitcoin (no flag)
    'ETH': 'xx',  # Ethereum (no flag)
    'USDT': 'us', # Tether (USD-backed)
    'USDC': 'us', # USD Coin
}

# Emoji fallback flags
CURRENCY_EMOJI_MAP: Dict[str, str] = {
    'USD': '🇺🇸',
    'EUR': '🇪🇺',
    'GBP': '🇬🇧',
    'JPY': '🇯🇵',
    'CHF': '🇨🇭',
    'CAD': '🇨🇦',
    'AUD': '🇦🇺',
    'NZD': '🇳🇿',
    'CNY': '🇨🇳',
    'HKD': '🇭🇰',
    'SGD': '🇸🇬',
    'INR': '🇮🇳',
    'KRW': '🇰🇷',
    'MAD': '🇲🇦',
    'AED': '🇦🇪',
    'SAR': '🇸🇦',
    'QAR': '🇶🇦',
    'EGP': '🇪🇬',
    'TND': '🇹🇳',
    'DZD': '🇩🇿',
    'ZAR': '🇿🇦',
    'TRY': '🇹🇷',
    'RUB': '🇷🇺',
    'MXN': '🇲🇽',
    'BRL': '🇧🇷',
    'SEK': '🇸🇪',
    'NOK': '🇳🇴',
    'DKK': '🇩🇰',
    'PLN': '🇵🇱',
    'BTC': '₿',
    'ETH': 'Ξ',
}

# FlagCDN base URL
FLAGCDN_BASE = "https://flagcdn.com"

# Cache for generated URLs (in-memory)
_flag_url_cache: Dict[str, dict] = {}
_cache_ttl = 3600  # 1 hour


def get_flag_url(currency: str, size: int = 40) -> str:
    """
    Get flag image URL for a currency code.

    Args:
        currency: ISO 4217 currency code (e.g., 'USD', 'EUR', 'MAD')
        size: Flag width in pixels (available: 16, 20, 24, 28, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256)

    Returns:
        URL string for the flag image

    Example:
        >>> get_flag_url('USD', 40)
        'https://flagcdn.com/w40/us.png'
        >>> get_flag_url('MAD', 64)
        'https://flagcdn.com/w64/ma.png'
    """
    currency = currency.upper()
    cache_key = f"{currency}_{size}"

    # Check cache
    if cache_key in _flag_url_cache:
        cached = _flag_url_cache[cache_key]
        if time.time() - cached['timestamp'] < _cache_ttl:
            return cached['url']

    # Get country code
    country_code = CURRENCY_COUNTRY_MAP.get(currency)

    if country_code and country_code != 'xx':
        url = f"{FLAGCDN_BASE}/w{size}/{country_code}.png"
    else:
        # Return a placeholder or generic currency icon
        url = f"{FLAGCDN_BASE}/w{size}/xx.png"

    # Cache the result
    _flag_url_cache[cache_key] = {
        'url': url,
        'timestamp': time.time()
    }

    return url


def get_flag_emoji(currency: str) -> str:
    """
    Get emoji flag for a currency code.

    Args:
        currency: ISO 4217 currency code

    Returns:
        Emoji flag or currency symbol
    """
    currency = currency.upper()
    return CURRENCY_EMOJI_MAP.get(currency, '💱')


def get_flag_svg_url(currency: str) -> str:
    """
    Get SVG flag URL for higher quality (recommended for large displays).

    Args:
        currency: ISO 4217 currency code

    Returns:
        URL string for the SVG flag
    """
    currency = currency.upper()
    country_code = CURRENCY_COUNTRY_MAP.get(currency)

    if country_code and country_code != 'xx':
        return f"{FLAGCDN_BASE}/{country_code}.svg"
    return f"{FLAGCDN_BASE}/xx.svg"


def get_currency_with_flag(currency: str, size: int = 20) -> dict:
    """
    Get complete currency info with flag.

    Args:
        currency: ISO 4217 currency code
        size: Flag size in pixels

    Returns:
        Dict with currency, flag_url, flag_emoji, country_code
    """
    currency = currency.upper()
    return {
        'currency': currency,
        'flag_url': get_flag_url(currency, size),
        'flag_svg': get_flag_svg_url(currency),
        'flag_emoji': get_flag_emoji(currency),
        'country_code': CURRENCY_COUNTRY_MAP.get(currency, 'xx')
    }


def get_all_flags(currencies: list, size: int = 40) -> Dict[str, dict]:
    """
    Get flags for multiple currencies at once.

    Args:
        currencies: List of currency codes
        size: Flag size in pixels

    Returns:
        Dict mapping currency codes to their flag info
    """
    return {
        curr: get_currency_with_flag(curr, size)
        for curr in currencies
    }


# Jinja2 template filter
def currency_flag_filter(currency: str, size: int = 24) -> str:
    """
    Jinja2 filter for currency flags.
    Usage in template: {{ 'USD' | currency_flag }}

    Returns HTML img tag with flag.
    """
    url = get_flag_url(currency, size)
    emoji = get_flag_emoji(currency)
    return f'<img src="{url}" alt="{emoji}" class="currency-flag" style="width:{size}px;height:auto;border-radius:2px;" onerror="this.outerHTML=\'{emoji}\'">'


# Export list of supported currencies
SUPPORTED_CURRENCIES = list(CURRENCY_COUNTRY_MAP.keys())
