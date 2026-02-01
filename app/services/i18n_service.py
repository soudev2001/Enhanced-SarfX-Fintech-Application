"""
Service d'internationalisation (i18n) pour SarfX
Gère les traductions multi-langues FR/EN/AR
"""
import json
import os
from functools import wraps
from flask import session, request, g
import logging

logger = logging.getLogger(__name__)

# Langues supportées
SUPPORTED_LANGUAGES = {
    'fr': {
        'name': 'Français',
        'native_name': 'Français',
        'flag': '🇫🇷',
        'rtl': False,
        'default': True
    },
    'en': {
        'name': 'English',
        'native_name': 'English',
        'flag': '🇬🇧',
        'rtl': False,
        'default': False
    },
    'ar': {
        'name': 'Arabic',
        'native_name': 'العربية',
        'flag': '🇲🇦',
        'rtl': True,
        'default': False
    }
}

DEFAULT_LANGUAGE = 'fr'

# Cache des traductions
_translations_cache = {}


def get_translations_dir():
    """Retourne le chemin vers le dossier des traductions"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, 'translations')


def load_translations(lang: str) -> dict:
    """Charge les traductions pour une langue donnée"""
    if lang in _translations_cache:
        return _translations_cache[lang]

    translations_dir = get_translations_dir()
    file_path = os.path.join(translations_dir, f'{lang}.json')

    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                translations = json.load(f)
                _translations_cache[lang] = translations
                return translations
    except Exception as e:
        logger.error(f"Error loading translations for {lang}: {e}")

    return {}


def clear_translations_cache():
    """Vide le cache des traductions"""
    global _translations_cache
    _translations_cache = {}


def get_current_language() -> str:
    """Récupère la langue courante"""
    # 1. Check session
    if 'language' in session:
        return session['language']

    # 2. Check Accept-Language header
    if request:
        accept_lang = request.accept_languages.best_match(SUPPORTED_LANGUAGES.keys())
        if accept_lang:
            return accept_lang

    # 3. Default
    return DEFAULT_LANGUAGE


def set_language(lang: str) -> bool:
    """Définit la langue pour la session"""
    if lang in SUPPORTED_LANGUAGES:
        session['language'] = lang
        return True
    return False


def is_rtl() -> bool:
    """Vérifie si la langue courante est RTL"""
    lang = get_current_language()
    return SUPPORTED_LANGUAGES.get(lang, {}).get('rtl', False)


def t(key: str, **kwargs) -> str:
    """
    Fonction de traduction principale

    Args:
        key: Clé de traduction (ex: "nav.home", "button.submit")
        **kwargs: Variables pour interpolation

    Returns:
        Texte traduit ou clé si non trouvé
    """
    lang = get_current_language()
    translations = load_translations(lang)

    # Navigation dans les clés imbriquées
    keys = key.split('.')
    value = translations

    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            # Fallback vers la langue par défaut
            if lang != DEFAULT_LANGUAGE:
                default_translations = load_translations(DEFAULT_LANGUAGE)
                value = default_translations
                for k2 in keys:
                    if isinstance(value, dict) and k2 in value:
                        value = value[k2]
                    else:
                        return key  # Retourne la clé si non trouvé
            else:
                return key

    # Interpolation des variables
    if isinstance(value, str) and kwargs:
        try:
            value = value.format(**kwargs)
        except KeyError:
            pass

    return value if isinstance(value, str) else key


def tn(key: str, count: int, **kwargs) -> str:
    """
    Traduction avec gestion du pluriel

    Args:
        key: Clé de traduction (cherche key.one, key.few, key.many, key.other)
        count: Nombre pour déterminer la forme plurielle
        **kwargs: Variables pour interpolation
    """
    lang = get_current_language()

    # Déterminer la forme plurielle
    if lang == 'ar':
        # Règles de pluriel arabe
        if count == 0:
            plural_key = 'zero'
        elif count == 1:
            plural_key = 'one'
        elif count == 2:
            plural_key = 'two'
        elif 3 <= count <= 10:
            plural_key = 'few'
        elif 11 <= count <= 99:
            plural_key = 'many'
        else:
            plural_key = 'other'
    else:
        # Règles de pluriel simples (FR, EN)
        plural_key = 'one' if count == 1 else 'other'

    full_key = f"{key}.{plural_key}"
    translated = t(full_key, count=count, **kwargs)

    # Si la clé plurielle n'existe pas, essayer 'other'
    if translated == full_key:
        translated = t(f"{key}.other", count=count, **kwargs)

    return translated


def get_language_info(lang: str = None) -> dict:
    """Retourne les informations sur une langue"""
    if lang is None:
        lang = get_current_language()
    return SUPPORTED_LANGUAGES.get(lang, SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE])


def get_all_languages() -> dict:
    """Retourne toutes les langues supportées"""
    return SUPPORTED_LANGUAGES


class I18nService:
    """Service d'internationalisation"""

    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialise l'extension Flask"""
        self.app = app

        # Ajouter les fonctions au contexte Jinja2
        app.jinja_env.globals['t'] = t
        app.jinja_env.globals['tn'] = tn
        app.jinja_env.globals['get_current_language'] = get_current_language
        app.jinja_env.globals['is_rtl'] = is_rtl
        app.jinja_env.globals['get_language_info'] = get_language_info
        app.jinja_env.globals['get_all_languages'] = get_all_languages
        app.jinja_env.globals['SUPPORTED_LANGUAGES'] = SUPPORTED_LANGUAGES

        # Before request: charger la langue
        @app.before_request
        def before_request():
            g.lang = get_current_language()
            g.is_rtl = is_rtl()

        logger.info("I18n service initialized")

    @staticmethod
    def translate(key: str, **kwargs) -> str:
        """Alias pour la fonction t()"""
        return t(key, **kwargs)

    @staticmethod
    def t(key: str, lang: str = None, **kwargs) -> str:
        """Fonction de traduction avec langue optionnelle"""
        if lang:
            # Temporairement charger la langue spécifique
            translations = load_translations(lang)
            keys = key.split('.')
            value = translations
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return key
            if isinstance(value, str) and kwargs:
                try:
                    value = value.format(**kwargs)
                except KeyError:
                    pass
            return value if isinstance(value, str) else key
        return t(key, **kwargs)

    @staticmethod
    def tn(key: str, count: int, **kwargs) -> str:
        """Alias pour la fonction tn()"""
        return tn(key, count, **kwargs)

    @staticmethod
    def get_locale():
        """Retourne la locale courante"""
        return get_current_language()

    @staticmethod
    def get_current_language() -> str:
        """Retourne la langue courante"""
        return get_current_language()

    @staticmethod
    def set_language(lang: str) -> bool:
        """Définit la langue"""
        return set_language(lang)

    @staticmethod
    def is_rtl(lang: str = None) -> bool:
        """Vérifie si une langue est RTL"""
        if lang:
            return SUPPORTED_LANGUAGES.get(lang, {}).get('rtl', False)
        return is_rtl()

    @staticmethod
    def get_available_languages() -> dict:
        """Retourne toutes les langues disponibles"""
        return SUPPORTED_LANGUAGES

    @staticmethod
    def is_supported_language(lang: str) -> bool:
        """Vérifie si une langue est supportée"""
        return lang in SUPPORTED_LANGUAGES

    @staticmethod
    def get_translations(lang: str = None) -> dict:
        """Retourne les traductions pour une langue"""
        if lang is None:
            lang = get_current_language()
        return load_translations(lang)


# Instance globale
i18n = I18nService()
