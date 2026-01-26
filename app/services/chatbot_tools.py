"""
Chatbot Tools - Système de Function Calling avec RBAC pour SarfX
Permet au chatbot d'exécuter des actions en fonction du rôle utilisateur
"""
from datetime import datetime, timedelta
from bson import ObjectId
import re

# ==================== PERMISSIONS PAR RÔLE ====================
ROLE_PERMISSIONS = {
    'anonymous': [
        'get_exchange_rate', 'convert_currency', 'get_supported_currencies', 'get_sarfx_info',
        'search_atms', 'get_cities_with_atms', 'get_best_rate'
    ],
    'user': [
        'get_exchange_rate', 'convert_currency', 'get_supported_currencies', 'get_sarfx_info',
        'get_my_balance', 'get_my_transactions', 'find_nearest_atm', 'list_my_beneficiaries',
        'get_rate_history', 'search_atms', 'get_cities_with_atms', 'get_best_rate',
        'add_beneficiary', 'get_all_suppliers', 'get_rate_analytics'
    ],
    'bank_user': [
        'get_exchange_rate', 'convert_currency', 'get_supported_currencies', 'get_sarfx_info',
        'get_my_balance', 'get_my_transactions', 'find_nearest_atm', 'list_my_beneficiaries',
        'get_rate_history', 'get_my_bank_info', 'search_atms', 'get_cities_with_atms', 'get_best_rate',
        'add_beneficiary', 'get_all_suppliers', 'get_rate_analytics'
    ],
    'bank_respo': [
        'get_exchange_rate', 'convert_currency', 'get_supported_currencies', 'get_sarfx_info',
        'get_my_balance', 'get_my_transactions', 'find_nearest_atm', 'list_my_beneficiaries',
        'get_rate_history', 'get_my_bank_info', 'get_bank_atms', 'get_bank_stats',
        'search_atms', 'get_cities_with_atms', 'get_best_rate', 'add_beneficiary', 
        'get_all_suppliers', 'get_rate_analytics'
    ],
    'admin_associate_bank': [
        'get_exchange_rate', 'convert_currency', 'get_supported_currencies', 'get_sarfx_info',
        'get_my_balance', 'get_my_transactions', 'find_nearest_atm', 'list_my_beneficiaries',
        'get_rate_history', 'get_my_bank_info', 'get_bank_atms', 'get_bank_stats', 'get_bank_api_status',
        'search_atms', 'get_cities_with_atms', 'get_best_rate', 'add_beneficiary',
        'get_all_suppliers', 'get_rate_analytics'
    ],
    'admin_sr_bank': [
        'get_exchange_rate', 'convert_currency', 'get_supported_currencies', 'get_sarfx_info',
        'get_my_balance', 'get_my_transactions', 'find_nearest_atm', 'list_my_beneficiaries',
        'get_rate_history', 'get_all_banks', 'get_all_banks_stats', 'get_my_bank_info',
        'get_bank_atms', 'get_bank_stats', 'search_atms', 'get_cities_with_atms', 'get_best_rate',
        'get_all_suppliers', 'get_rate_analytics', 'get_transaction_volume'
    ],
    'admin': ['*']  # Accès total à tous les tools
}

# ==================== REGISTRE DES TOOLS ====================
TOOLS_REGISTRY = {
    # Tools publics
    'get_exchange_rate': {
        'description': 'Obtenir le taux de change entre deux devises',
        'params': ['from_currency', 'to_currency'],
        'example': 'Quel est le taux EUR/MAD ?'
    },
    'convert_currency': {
        'description': 'Convertir un montant d\'une devise à une autre',
        'params': ['amount', 'from_currency', 'to_currency'],
        'example': 'Convertir 100 EUR en MAD'
    },
    'get_supported_currencies': {
        'description': 'Liste des devises supportées',
        'params': [],
        'example': 'Quelles devises sont disponibles ?'
    },
    'get_sarfx_info': {
        'description': 'Informations générales sur SarfX',
        'params': [],
        'example': 'C\'est quoi SarfX ?'
    },
    
    # Tools utilisateur
    'get_my_balance': {
        'description': 'Consulter le solde du wallet',
        'params': ['user_id'],
        'example': 'Quel est mon solde ?'
    },
    'get_my_transactions': {
        'description': 'Historique des transactions',
        'params': ['user_id', 'limit'],
        'example': 'Mes dernières transactions'
    },
    'find_nearest_atm': {
        'description': 'Trouver les ATMs à proximité',
        'params': ['latitude', 'longitude', 'limit'],
        'example': 'ATM près de moi'
    },
    'list_my_beneficiaries': {
        'description': 'Liste des bénéficiaires enregistrés',
        'params': ['user_id'],
        'example': 'Mes bénéficiaires'
    },
    'get_rate_history': {
        'description': 'Historique des taux de change',
        'params': ['from_currency', 'to_currency', 'days'],
        'example': 'Évolution EUR/MAD sur 30 jours'
    },
    
    # Tools banque
    'get_my_bank_info': {
        'description': 'Informations sur ma banque',
        'params': ['bank_code'],
        'example': 'Infos de ma banque'
    },
    'get_bank_atms': {
        'description': 'Liste des ATMs de ma banque',
        'params': ['bank_code'],
        'example': 'ATMs de ma banque'
    },
    'get_bank_stats': {
        'description': 'Statistiques de ma banque',
        'params': ['bank_code'],
        'example': 'Stats de ma banque'
    },
    'get_bank_api_status': {
        'description': 'Statut API de ma banque',
        'params': ['bank_code'],
        'example': 'Status API banque'
    },
    
    # Tools admin
    'count_active_users': {
        'description': 'Nombre d\'utilisateurs actifs',
        'params': [],
        'example': 'Combien d\'utilisateurs ?'
    },
    'get_system_stats': {
        'description': 'Statistiques système globales',
        'params': [],
        'example': 'Stats du système'
    },
    'get_recent_signups': {
        'description': 'Dernières inscriptions',
        'params': ['limit'],
        'example': 'Dernières inscriptions'
    },
    'get_all_banks': {
        'description': 'Liste de toutes les banques',
        'params': [],
        'example': 'Liste des banques'
    },
    'get_all_banks_stats': {
        'description': 'Statistiques de toutes les banques',
        'params': [],
        'example': 'Stats de toutes les banques'
    },
    
    # Nouveaux tools publics
    'search_atms': {
        'description': 'Rechercher des ATMs par ville ou nom',
        'params': ['query', 'limit'],
        'example': 'ATMs à Casablanca'
    },
    'get_cities_with_atms': {
        'description': 'Liste des villes avec ATMs',
        'params': ['country'],
        'example': 'Quelles villes ont des ATMs ?'
    },
    'get_best_rate': {
        'description': 'Meilleur taux parmi les fournisseurs',
        'params': ['from_currency', 'to_currency', 'amount'],
        'example': 'Meilleur taux EUR/MAD'
    },
    
    # Nouveaux tools utilisateur
    'add_beneficiary': {
        'description': 'Ajouter un bénéficiaire',
        'params': ['name', 'bank_name', 'account_number'],
        'example': 'Ajouter un bénéficiaire'
    },
    'get_all_suppliers': {
        'description': 'Liste des fournisseurs de change',
        'params': ['currency'],
        'example': 'Quels bureaux de change ?'
    },
    'get_rate_analytics': {
        'description': 'Analyse d\'une paire de devises',
        'params': ['from_currency', 'to_currency', 'period'],
        'example': 'Analyse EUR/MAD'
    },
    
    # Nouveaux tools admin
    'get_transaction_volume': {
        'description': 'Volume de transactions par période',
        'params': ['period'],
        'example': 'Volume transactions ce mois'
    },
    'search_users': {
        'description': 'Rechercher un utilisateur',
        'params': ['query', 'field'],
        'example': 'Chercher utilisateur email@example.com'
    }
}


class ChatbotTools:
    """Classe pour exécuter les tools du chatbot avec vérification RBAC"""
    
    def __init__(self, db):
        self.db = db
        
    def has_permission(self, role, tool_name):
        """Vérifie si un rôle a la permission d'utiliser un tool"""
        if role == 'admin':
            return True
        permissions = ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS['anonymous'])
        if '*' in permissions:
            return True
        return tool_name in permissions
    
    def execute_tool(self, tool_name, params, user_context):
        """
        Exécute un tool avec vérification des permissions
        
        Args:
            tool_name: Nom du tool à exécuter
            params: Paramètres du tool
            user_context: Contexte utilisateur (user_id, role, bank_code, etc.)
            
        Returns:
            dict: {'success': bool, 'data': any, 'message': str}
        """
        role = user_context.get('role', 'anonymous')
        
        # Vérification des permissions
        if not self.has_permission(role, tool_name):
            return {
                'success': False,
                'error': 'permission_denied',
                'message': f"🔒 Désolé, cette information est réservée aux {self._get_required_role(tool_name)}. Vous pouvez consulter votre espace personnel pour accéder à vos données."
            }
        
        # Exécution du tool
        try:
            method = getattr(self, f'_tool_{tool_name}', None)
            if method:
                return method(params, user_context)
            else:
                return {
                    'success': False,
                    'error': 'tool_not_found',
                    'message': "Je ne connais pas cette action. Puis-je vous aider autrement ?"
                }
        except Exception as e:
            print(f"Tool execution error [{tool_name}]: {e}")
            return {
                'success': False,
                'error': 'execution_error',
                'message': self._get_graceful_fallback(tool_name)
            }
    
    def _get_required_role(self, tool_name):
        """Retourne le rôle minimum requis pour un tool"""
        for role, tools in ROLE_PERMISSIONS.items():
            if tool_name in tools:
                role_names = {
                    'admin': 'administrateurs',
                    'admin_sr_bank': 'administrateurs bancaires seniors',
                    'admin_associate_bank': 'administrateurs associés de banque',
                    'bank_respo': 'responsables bancaires',
                    'bank_user': 'utilisateurs bancaires',
                    'user': 'utilisateurs connectés'
                }
                return role_names.get(role, 'utilisateurs autorisés')
        return 'administrateurs'
    
    def _get_graceful_fallback(self, tool_name):
        """Retourne un message de fallback gracieux selon le tool"""
        fallbacks = {
            'get_my_balance': "💳 Je n'ai pas pu récupérer votre solde. Veuillez consulter la page Wallets pour voir vos soldes en temps réel.",
            'get_my_transactions': "📊 Impossible de charger vos transactions. Consultez la page Transactions pour l'historique complet.",
            'find_nearest_atm': "🏧 Je n'ai pas pu localiser les ATMs. Utilisez la page 'Find ATMs' avec la carte interactive.",
            'list_my_beneficiaries': "👥 Impossible de charger vos bénéficiaires. Accédez à la page Bénéficiaires pour les gérer.",
            'get_exchange_rate': "📈 Je n'ai pas pu obtenir le taux actuel. Consultez la page Converter pour les taux en temps réel.",
            'convert_currency': "💱 La conversion n'a pas pu être calculée. Utilisez le convertisseur sur la page Converter.",
            'count_active_users': "📊 Impossible de récupérer les statistiques utilisateurs. Consultez le tableau de bord Admin.",
            'get_system_stats': "📈 Les statistiques système ne sont pas disponibles. Vérifiez le dashboard administrateur.",
            'get_bank_stats': "🏦 Impossible de charger les stats de votre banque. Consultez votre dashboard bancaire.",
        }
        return fallbacks.get(tool_name, "Une erreur s'est produite. Veuillez réessayer ou contacter le support.")
    
    # ==================== TOOLS PUBLICS ====================
    
    def _tool_get_exchange_rate(self, params, user_context):
        """Obtenir le taux de change entre deux devises"""
        from_curr = params.get('from_currency', 'EUR').upper()
        to_curr = params.get('to_currency', 'MAD').upper()
        
        try:
            from app.services.exchange_service import exchange_service
            result = exchange_service.get_rate(from_curr, to_curr)
            
            if result.get('success'):
                rate = result['rate']
                return {
                    'success': True,
                    'data': {'rate': rate, 'from': from_curr, 'to': to_curr},
                    'message': f"📊 Taux de change actuel:\n**1 {from_curr} = {rate:.4f} {to_curr}**\n\nCe taux est mis à jour en temps réel."
                }
            else:
                return {
                    'success': False,
                    'error': 'rate_unavailable',
                    'message': f"Je n'ai pas pu obtenir le taux {from_curr}/{to_curr}. Consultez la page Converter."
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': self._get_graceful_fallback('get_exchange_rate')
            }
    
    def _tool_convert_currency(self, params, user_context):
        """Convertir un montant"""
        amount = float(params.get('amount', 0))
        from_curr = params.get('from_currency', 'EUR').upper()
        to_curr = params.get('to_currency', 'MAD').upper()
        
        try:
            from app.services.exchange_service import exchange_service
            result = exchange_service.convert(amount, from_curr, to_curr)
            
            if result.get('success'):
                converted = result['converted_amount']
                rate = result['rate']
                return {
                    'success': True,
                    'data': result,
                    'message': f"💱 Conversion:\n**{amount:,.2f} {from_curr} = {converted:,.2f} {to_curr}**\n\nTaux appliqué: 1 {from_curr} = {rate:.4f} {to_curr}"
                }
            else:
                return {
                    'success': False,
                    'error': 'conversion_failed',
                    'message': self._get_graceful_fallback('convert_currency')
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': self._get_graceful_fallback('convert_currency')
            }
    
    def _tool_get_supported_currencies(self, params, user_context):
        """Liste des devises supportées"""
        currencies = {
            'EUR': '🇪🇺 Euro',
            'USD': '🇺🇸 Dollar américain',
            'MAD': '🇲🇦 Dirham marocain',
            'GBP': '🇬🇧 Livre sterling',
            'CHF': '🇨🇭 Franc suisse',
            'CAD': '🇨🇦 Dollar canadien',
            'AUD': '🇦🇺 Dollar australien',
            'JPY': '🇯🇵 Yen japonais',
            'AED': '🇦🇪 Dirham émirati',
            'SAR': '🇸🇦 Riyal saoudien'
        }
        
        currency_list = '\n'.join([f"• {code}: {name}" for code, name in currencies.items()])
        return {
            'success': True,
            'data': list(currencies.keys()),
            'message': f"💰 Devises supportées par SarfX:\n\n{currency_list}\n\nConvertissez entre toutes ces devises sur la page Converter!"
        }
    
    def _tool_get_sarfx_info(self, params, user_context):
        """Informations générales sur SarfX"""
        return {
            'success': True,
            'data': {'name': 'SarfX', 'type': 'fintech'},
            'message': """🌟 **SarfX - Votre plateforme de change intelligente**

SarfX est une solution fintech marocaine qui révolutionne l'échange de devises:

✅ **Conversion en temps réel** - Taux compétitifs EUR, USD, MAD, GBP et plus
✅ **Wallets multi-devises** - Gérez plusieurs devises dans un seul compte
✅ **1000+ ATMs partenaires** - Retirez partout au Maroc
✅ **Transferts faciles** - Envoyez de l'argent à vos bénéficiaires
✅ **API pour banques** - Intégration pour partenaires bancaires

📱 Application mobile disponible Q2 2026!

Que souhaitez-vous faire aujourd'hui ?"""
        }
    
    # ==================== TOOLS UTILISATEUR ====================
    
    def _tool_get_my_balance(self, params, user_context):
        """Consulter le solde du wallet utilisateur"""
        user_id = user_context.get('user_id')
        if not user_id:
            return {
                'success': False,
                'error': 'not_authenticated',
                'message': "🔒 Connectez-vous pour consulter votre solde."
            }
        
        try:
            wallet = self.db.wallets.find_one({"user_id": str(user_id)})
            if not wallet:
                return {
                    'success': True,
                    'data': {'balances': {}},
                    'message': "💳 Vous n'avez pas encore de wallet. Créez-en un sur la page Wallets!"
                }
            
            balances = wallet.get('balances', {})
            balance_lines = []
            total_mad = 0
            
            # Taux approximatifs pour calcul total
            rates_to_mad = {'MAD': 1, 'EUR': 10.8, 'USD': 10.0, 'GBP': 12.7}
            
            for currency, amount in balances.items():
                if amount > 0:
                    balance_lines.append(f"• {currency}: **{amount:,.2f}**")
                    total_mad += amount * rates_to_mad.get(currency, 10)
            
            if not balance_lines:
                balance_lines = ["Tous vos soldes sont à 0"]
            
            return {
                'success': True,
                'data': {'balances': balances, 'total_mad': total_mad},
                'message': f"💰 **Vos soldes actuels:**\n\n" + '\n'.join(balance_lines) + f"\n\n📊 Valeur totale estimée: ~{total_mad:,.2f} MAD"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': self._get_graceful_fallback('get_my_balance')
            }
    
    def _tool_get_my_transactions(self, params, user_context):
        """Historique des transactions utilisateur"""
        user_id = user_context.get('user_id')
        limit = int(params.get('limit', 5))
        
        if not user_id:
            return {
                'success': False,
                'error': 'not_authenticated',
                'message': "🔒 Connectez-vous pour voir vos transactions."
            }
        
        try:
            transactions = list(self.db.transactions.find(
                {"user_id": str(user_id)}
            ).sort("created_at", -1).limit(limit))
            
            if not transactions:
                return {
                    'success': True,
                    'data': {'transactions': []},
                    'message': "📊 Vous n'avez pas encore de transactions. Effectuez votre première conversion sur la page Converter!"
                }
            
            tx_lines = []
            for tx in transactions:
                date = tx.get('created_at', datetime.now()).strftime('%d/%m/%Y')
                amount = tx.get('amount', 0)
                from_curr = tx.get('from_currency', 'EUR')
                to_curr = tx.get('to_currency', 'MAD')
                status = '✅' if tx.get('status') == 'completed' else '⏳'
                tx_lines.append(f"{status} {date}: {amount:,.2f} {from_curr} → {to_curr}")
            
            return {
                'success': True,
                'data': {'transactions': transactions, 'count': len(transactions)},
                'message': f"📜 **Vos {len(transactions)} dernières transactions:**\n\n" + '\n'.join(tx_lines) + "\n\nVoir plus sur la page Transactions."
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': self._get_graceful_fallback('get_my_transactions')
            }
    
    def _tool_find_nearest_atm(self, params, user_context):
        """Trouver les ATMs à proximité"""
        lat = params.get('latitude')
        lng = params.get('longitude')
        limit = int(params.get('limit', 5))
        
        try:
            from app.services.atm_service import ATMService
            atm_service = ATMService(self.db)
            
            if lat and lng:
                atms = atm_service.find_nearby(float(lat), float(lng), limit=limit)
            else:
                # Sans coordonnées, retourner des ATMs populaires
                atms = atm_service.search_atms("Casablanca")
            
            if not atms:
                return {
                    'success': True,
                    'data': {'atms': []},
                    'message': "🏧 Aucun ATM trouvé dans cette zone. Essayez la carte interactive sur la page 'Find ATMs'."
                }
            
            atm_lines = []
            for atm in atms[:5]:
                name = atm.get('name', 'ATM')
                bank = atm.get('bank_name', '')
                city = atm.get('city', '')
                atm_lines.append(f"🏧 **{name}** ({bank}) - {city}")
            
            return {
                'success': True,
                'data': {'atms': atms, 'count': len(atms)},
                'message': f"🏧 **ATMs trouvés:**\n\n" + '\n'.join(atm_lines) + "\n\n📍 Utilisez la carte sur 'Find ATMs' pour navigation GPS."
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': self._get_graceful_fallback('find_nearest_atm')
            }
    
    def _tool_list_my_beneficiaries(self, params, user_context):
        """Liste des bénéficiaires de l'utilisateur"""
        user_id = user_context.get('user_id')
        
        if not user_id:
            return {
                'success': False,
                'error': 'not_authenticated',
                'message': "🔒 Connectez-vous pour voir vos bénéficiaires."
            }
        
        try:
            beneficiaries = list(self.db.beneficiaries.find(
                {"user_id": str(user_id)}
            ).limit(10))
            
            if not beneficiaries:
                return {
                    'success': True,
                    'data': {'beneficiaries': []},
                    'message': "👥 Vous n'avez pas encore de bénéficiaires. Ajoutez-en un sur la page Bénéficiaires!"
                }
            
            ben_lines = []
            for ben in beneficiaries:
                name = ben.get('name', 'Inconnu')
                bank = ben.get('bank_name', '')
                ben_lines.append(f"👤 {name} - {bank}")
            
            return {
                'success': True,
                'data': {'beneficiaries': beneficiaries, 'count': len(beneficiaries)},
                'message': f"👥 **Vos bénéficiaires ({len(beneficiaries)}):**\n\n" + '\n'.join(ben_lines)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': self._get_graceful_fallback('list_my_beneficiaries')
            }
    
    def _tool_get_rate_history(self, params, user_context):
        """Historique des taux de change"""
        from_curr = params.get('from_currency', 'EUR').upper()
        to_curr = params.get('to_currency', 'MAD').upper()
        days = int(params.get('days', 7))
        
        try:
            from app.services.exchange_service import exchange_service
            result = exchange_service.get_rate_history(from_curr, to_curr, days)
            
            if result.get('success') and result.get('history'):
                history = result['history']
                trend = result.get('trend', 'stable')
                trend_emoji = {'up': '📈', 'down': '📉', 'stable': '➡️'}.get(trend, '➡️')
                
                return {
                    'success': True,
                    'data': result,
                    'message': f"{trend_emoji} **Évolution {from_curr}/{to_curr} sur {days} jours:**\n\nTendance: {trend}\nConsultez le graphique complet sur la page Rate History."
                }
            else:
                return {
                    'success': True,
                    'data': {},
                    'message': f"📊 L'historique {from_curr}/{to_curr} n'est pas disponible. Consultez la page Rate History."
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': "Impossible de charger l'historique. Consultez la page Rate History."
            }
    
    # ==================== TOOLS ADMIN ====================
    
    def _tool_count_active_users(self, params, user_context):
        """Nombre d'utilisateurs actifs (Admin uniquement)"""
        try:
            total_users = self.db.users.count_documents({})
            active_users = self.db.users.count_documents({"is_active": True})
            verified_users = self.db.users.count_documents({"verified": True})
            
            # Nouveaux utilisateurs aujourd'hui
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            new_today = self.db.users.count_documents({"created_at": {"$gte": today}})
            
            return {
                'success': True,
                'data': {
                    'total': total_users,
                    'active': active_users,
                    'verified': verified_users,
                    'new_today': new_today
                },
                'message': f"""📊 **Statistiques Utilisateurs:**

👥 Total: **{total_users:,}** utilisateurs
✅ Actifs: **{active_users:,}**
🔐 Vérifiés: **{verified_users:,}**
🆕 Nouveaux aujourd'hui: **{new_today}**"""
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': self._get_graceful_fallback('count_active_users')
            }
    
    def _tool_get_system_stats(self, params, user_context):
        """Statistiques système globales (Admin uniquement)"""
        try:
            stats = {
                'users': self.db.users.count_documents({}),
                'transactions': self.db.transactions.count_documents({}) if 'transactions' in self.db.list_collection_names() else 0,
                'wallets': self.db.wallets.count_documents({}) if 'wallets' in self.db.list_collection_names() else 0,
                'atms': self.db.atms.count_documents({}) if 'atms' in self.db.list_collection_names() else 0,
                'banks': self.db.banks.count_documents({}) if 'banks' in self.db.list_collection_names() else 0,
                'beneficiaries': self.db.beneficiaries.count_documents({}) if 'beneficiaries' in self.db.list_collection_names() else 0
            }
            
            return {
                'success': True,
                'data': stats,
                'message': f"""📈 **Statistiques Système SarfX:**

👥 Utilisateurs: **{stats['users']:,}**
💳 Wallets: **{stats['wallets']:,}**
📊 Transactions: **{stats['transactions']:,}**
🏧 ATMs: **{stats['atms']:,}**
🏦 Banques: **{stats['banks']:,}**
👤 Bénéficiaires: **{stats['beneficiaries']:,}**"""
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': self._get_graceful_fallback('get_system_stats')
            }
    
    def _tool_get_recent_signups(self, params, user_context):
        """Dernières inscriptions (Admin uniquement)"""
        limit = int(params.get('limit', 5))
        
        try:
            recent_users = list(self.db.users.find(
                {},
                {"email": 1, "role": 1, "created_at": 1}
            ).sort("created_at", -1).limit(limit))
            
            user_lines = []
            for user in recent_users:
                email = user.get('email', 'N/A')
                # Masquer partiellement l'email
                parts = email.split('@')
                masked_email = parts[0][:3] + '***@' + parts[1] if len(parts) == 2 else '***'
                
                role = user.get('role', 'user')
                date = user.get('created_at', datetime.now()).strftime('%d/%m %H:%M')
                user_lines.append(f"• {masked_email} ({role}) - {date}")
            
            return {
                'success': True,
                'data': {'count': len(recent_users)},
                'message': f"🆕 **Dernières inscriptions:**\n\n" + '\n'.join(user_lines)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': "Impossible de charger les dernières inscriptions."
            }
    
    def _tool_get_all_banks(self, params, user_context):
        """Liste de toutes les banques (Admin SR Bank)"""
        try:
            banks = list(self.db.banks.find({}, {"name": 1, "code": 1, "is_active": 1}).limit(20))
            
            if not banks:
                return {
                    'success': True,
                    'data': {'banks': []},
                    'message': "🏦 Aucune banque configurée dans le système."
                }
            
            bank_lines = []
            for bank in banks:
                status = '✅' if bank.get('is_active', True) else '❌'
                name = bank.get('name', 'N/A')
                code = bank.get('code', '')
                bank_lines.append(f"{status} {name} ({code})")
            
            return {
                'success': True,
                'data': {'banks': banks, 'count': len(banks)},
                'message': f"🏦 **Banques partenaires ({len(banks)}):**\n\n" + '\n'.join(bank_lines)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': "Impossible de charger la liste des banques."
            }

    # ==================== TOOLS BANQUE ====================
    
    def _tool_get_my_bank_info(self, params, user_context):
        """Informations sur la banque de l'utilisateur"""
        bank_id = user_context.get('bank_id')
        bank_code = params.get('bank_code') or user_context.get('bank_code')
        
        if not bank_id and not bank_code:
            return {
                'success': False,
                'error': 'no_bank',
                'message': "🏦 Vous n'êtes associé à aucune banque. Contactez votre administrateur."
            }
        
        try:
            query = {"_id": ObjectId(bank_id)} if bank_id else {"code": bank_code}
            bank = self.db.banks.find_one(query)
            
            if not bank:
                return {
                    'success': False,
                    'error': 'bank_not_found',
                    'message': "🏦 Banque introuvable. Vérifiez votre affiliation."
                }
            
            status = '✅ Active' if bank.get('is_active', True) else '❌ Inactive'
            api_status = bank.get('api_status', 'unknown')
            api_emoji = {'active': '🟢', 'inactive': '🔴', 'maintenance': '🟡'}.get(api_status, '⚪')
            
            return {
                'success': True,
                'data': {
                    'name': bank.get('name'),
                    'code': bank.get('code'),
                    'is_active': bank.get('is_active'),
                    'api_status': api_status
                },
                'message': f"""🏦 **Informations de votre banque:**

📛 Nom: **{bank.get('name', 'N/A')}**
🔤 Code: **{bank.get('code', 'N/A')}**
📊 Statut: {status}
{api_emoji} API: {api_status.capitalize()}
📧 Contact: {bank.get('contact_email', 'N/A')}
📍 Adresse: {bank.get('address', 'N/A')}"""
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': "Impossible de charger les infos de la banque."
            }
    
    def _tool_get_bank_atms(self, params, user_context):
        """Liste des ATMs de la banque"""
        bank_id = user_context.get('bank_id')
        bank_code = params.get('bank_code') or user_context.get('bank_code')
        limit = int(params.get('limit', 10))
        
        if not bank_id and not bank_code:
            return {
                'success': False,
                'error': 'no_bank',
                'message': "🏦 Vous n'êtes associé à aucune banque."
            }
        
        try:
            # Trouver la banque
            query = {"_id": ObjectId(bank_id)} if bank_id else {"code": bank_code}
            bank = self.db.banks.find_one(query)
            
            if not bank:
                return {
                    'success': False,
                    'error': 'bank_not_found',
                    'message': "🏦 Banque introuvable."
                }
            
            # Chercher les ATMs par bank_id ou bank_name
            atm_query = {"$or": [
                {"bank_id": str(bank['_id'])},
                {"bank_name": bank.get('name')},
                {"bank_code": bank.get('code')}
            ]}
            atms = list(self.db.atms.find(atm_query).limit(limit))
            
            if not atms:
                return {
                    'success': True,
                    'data': {'atms': [], 'count': 0},
                    'message': f"🏧 Aucun ATM trouvé pour {bank.get('name')}."
                }
            
            # Compter par ville
            cities = {}
            for atm in atms:
                city = atm.get('city', 'Autre')
                cities[city] = cities.get(city, 0) + 1
            
            city_lines = [f"• {city}: {count} ATMs" for city, count in sorted(cities.items(), key=lambda x: -x[1])[:5]]
            
            return {
                'success': True,
                'data': {'atms': atms, 'count': len(atms), 'by_city': cities},
                'message': f"""🏧 **ATMs de {bank.get('name')}:**

📊 Total: **{len(atms)}** ATMs

**Par ville:**
{chr(10).join(city_lines)}

📍 Voir la carte complète sur 'Find ATMs'."""
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': self._get_graceful_fallback('get_bank_atms')
            }
    
    def _tool_get_bank_stats(self, params, user_context):
        """Statistiques de la banque"""
        bank_id = user_context.get('bank_id')
        bank_code = params.get('bank_code') or user_context.get('bank_code')
        
        if not bank_id and not bank_code:
            return {
                'success': False,
                'error': 'no_bank',
                'message': "🏦 Vous n'êtes associé à aucune banque."
            }
        
        try:
            query = {"_id": ObjectId(bank_id)} if bank_id else {"code": bank_code}
            bank = self.db.banks.find_one(query)
            
            if not bank:
                return {
                    'success': False,
                    'error': 'bank_not_found',
                    'message': "🏦 Banque introuvable."
                }
            
            bank_id_str = str(bank['_id'])
            bank_name = bank.get('name', '')
            
            # Compter les ATMs
            atm_count = self.db.atms.count_documents({"$or": [
                {"bank_id": bank_id_str},
                {"bank_name": bank_name}
            ]}) if 'atms' in self.db.list_collection_names() else 0
            
            # Compter les utilisateurs de la banque
            user_count = self.db.users.count_documents({"bank_id": bank_id_str})
            
            # Compter les transactions liées (si collection existe)
            tx_count = 0
            tx_volume = 0
            if 'transactions' in self.db.list_collection_names():
                tx_count = self.db.transactions.count_documents({"bank_id": bank_id_str})
                # Calculer volume MAD
                pipeline = [
                    {"$match": {"bank_id": bank_id_str}},
                    {"$group": {"_id": None, "total": {"$sum": "$amount_mad"}}}
                ]
                result = list(self.db.transactions.aggregate(pipeline))
                if result:
                    tx_volume = result[0].get('total', 0)
            
            return {
                'success': True,
                'data': {
                    'atms': atm_count,
                    'users': user_count,
                    'transactions': tx_count,
                    'volume_mad': tx_volume
                },
                'message': f"""📊 **Statistiques de {bank_name}:**

🏧 ATMs: **{atm_count:,}**
👥 Utilisateurs: **{user_count:,}**
📈 Transactions: **{tx_count:,}**
💰 Volume: **{tx_volume:,.2f} MAD**

📈 Voir le dashboard complet pour plus de détails."""
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': self._get_graceful_fallback('get_bank_stats')
            }
    
    def _tool_get_bank_api_status(self, params, user_context):
        """Statut de l'API de la banque"""
        bank_id = user_context.get('bank_id')
        bank_code = params.get('bank_code') or user_context.get('bank_code')
        
        if not bank_id and not bank_code:
            return {
                'success': False,
                'error': 'no_bank',
                'message': "🏦 Vous n'êtes associé à aucune banque."
            }
        
        try:
            query = {"_id": ObjectId(bank_id)} if bank_id else {"code": bank_code}
            bank = self.db.banks.find_one(query)
            
            if not bank:
                return {
                    'success': False,
                    'error': 'bank_not_found',
                    'message': "🏦 Banque introuvable."
                }
            
            api_status = bank.get('api_status', 'unknown')
            api_key_set = bool(bank.get('api_key'))
            last_sync = bank.get('last_sync')
            last_sync_str = last_sync.strftime('%d/%m/%Y %H:%M') if last_sync else 'Jamais'
            
            status_info = {
                'active': ('🟢', 'Opérationnel', 'L\'API fonctionne normalement.'),
                'inactive': ('🔴', 'Inactif', 'L\'API est désactivée.'),
                'maintenance': ('🟡', 'Maintenance', 'L\'API est en maintenance planifiée.'),
                'error': ('🔴', 'Erreur', 'L\'API rencontre des problèmes.'),
                'unknown': ('⚪', 'Inconnu', 'Statut non défini.')
            }
            
            emoji, status_label, description = status_info.get(api_status, status_info['unknown'])
            
            return {
                'success': True,
                'data': {
                    'status': api_status,
                    'api_key_configured': api_key_set,
                    'last_sync': last_sync_str
                },
                'message': f"""🔌 **Statut API de {bank.get('name')}:**

{emoji} Statut: **{status_label}**
📝 {description}

🔑 Clé API: {'✅ Configurée' if api_key_set else '❌ Non configurée'}
🔄 Dernière sync: {last_sync_str}

Contactez le support technique pour toute assistance."""
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': "Impossible de vérifier le statut API."
            }
    
    def _tool_get_all_banks_stats(self, params, user_context):
        """Statistiques globales de toutes les banques (Admin SR Bank)"""
        try:
            banks = list(self.db.banks.find({}))
            
            if not banks:
                return {
                    'success': True,
                    'data': {},
                    'message': "🏦 Aucune banque configurée."
                }
            
            total_atms = 0
            total_users = 0
            active_banks = 0
            bank_stats = []
            
            for bank in banks:
                bank_id_str = str(bank['_id'])
                bank_name = bank.get('name', 'N/A')
                is_active = bank.get('is_active', True)
                
                if is_active:
                    active_banks += 1
                
                # ATMs par banque
                atm_count = self.db.atms.count_documents({"$or": [
                    {"bank_id": bank_id_str},
                    {"bank_name": bank_name}
                ]}) if 'atms' in self.db.list_collection_names() else 0
                total_atms += atm_count
                
                # Users par banque
                user_count = self.db.users.count_documents({"bank_id": bank_id_str})
                total_users += user_count
                
                status = '✅' if is_active else '❌'
                bank_stats.append(f"{status} {bank_name}: {atm_count} ATMs, {user_count} users")
            
            return {
                'success': True,
                'data': {
                    'total_banks': len(banks),
                    'active_banks': active_banks,
                    'total_atms': total_atms,
                    'total_users': total_users
                },
                'message': f"""📊 **Statistiques Globales Banques:**

🏦 Banques: **{len(banks)}** ({active_banks} actives)
🏧 ATMs total: **{total_atms:,}**
👥 Utilisateurs bancaires: **{total_users:,}**

**Détail par banque:**
{chr(10).join(bank_stats[:10])}
{'...' if len(bank_stats) > 10 else ''}"""
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': "Impossible de charger les stats bancaires globales."
            }

    # ==================== NOUVEAUX TOOLS PUBLICS ====================
    
    def _tool_search_atms(self, params, user_context):
        """Rechercher des ATMs par ville ou nom"""
        query = params.get('query', '')
        limit = int(params.get('limit', 10))
        
        if not query:
            return {
                'success': False,
                'error': 'missing_query',
                'message': "🔍 Précisez une ville ou un nom d'ATM à rechercher."
            }
        
        try:
            from app.services.atm_service import ATMService
            atm_service = ATMService(self.db)
            atms = atm_service.search_atms(query)
            
            if not atms:
                return {
                    'success': True,
                    'data': {'atms': []},
                    'message': f"🏧 Aucun ATM trouvé pour '{query}'. Essayez une autre ville ou utilisez la carte."
                }
            
            atm_lines = []
            for atm in atms[:8]:
                name = atm.get('name', 'ATM')
                bank = atm.get('bank_name', '')
                address = atm.get('address', '')[:40]
                atm_lines.append(f"🏧 **{name}** ({bank})\n   📍 {address}")
            
            return {
                'success': True,
                'data': {'atms': atms, 'count': len(atms)},
                'message': f"🔍 **{len(atms)} ATMs trouvés pour '{query}':**\n\n" + '\n\n'.join(atm_lines) + "\n\n📍 Voir sur la carte 'Find ATMs'."
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': self._get_graceful_fallback('find_nearest_atm')
            }
    
    def _tool_get_cities_with_atms(self, params, user_context):
        """Liste des villes avec ATMs disponibles"""
        country = params.get('country', 'Morocco')
        
        try:
            from app.services.atm_service import ATMService
            atm_service = ATMService(self.db)
            cities_data = atm_service.get_cities_with_atms()
            
            if not cities_data:
                return {
                    'success': True,
                    'data': {'cities': []},
                    'message': "🏙️ Aucune ville avec ATMs trouvée."
                }
            
            # Extraire les noms de ville avec le nombre d'ATMs
            city_lines = [f"• {c.get('city', 'N/A')} ({c.get('atm_count', 0)} ATMs)" for c in cities_data[:15]]
            cities = [c.get('city') for c in cities_data]
            
            return {
                'success': True,
                'data': {'cities': cities, 'count': len(cities)},
                'message': f"🏙️ **Villes avec ATMs SarfX ({len(cities)}):**\n\n" + '\n'.join(city_lines) + f"\n{'...' if len(cities) > 15 else ''}\n\n📍 Recherchez par ville sur 'Find ATMs'."
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': "Impossible de charger la liste des villes."
            }
    
    def _tool_get_best_rate(self, params, user_context):
        """Obtenir le meilleur taux parmi les fournisseurs"""
        from_curr = params.get('from_currency', 'EUR').upper()
        to_curr = params.get('to_currency', 'MAD').upper()
        amount = float(params.get('amount', 100))
        
        try:
            from app.services.rate_service import calculate_best_rate
            result = calculate_best_rate(amount, from_curr, to_curr)
            
            if result and result.get('best'):
                best = result['best']
                supplier_name = best['supplier'].get('name', 'SarfX')
                rate = best['rate']
                final_amount = best['final_amount']
                fee = best['fee']
                
                return {
                    'success': True,
                    'data': {'rate': rate, 'supplier': supplier_name, 'final_amount': final_amount},
                    'message': f"""🏆 **Meilleur taux {from_curr}/{to_curr}:**

📊 Taux: **1 {from_curr} = {rate:.4f} {to_curr}**
🏪 Fournisseur: {supplier_name}
💰 {amount:,.2f} {from_curr} = **{final_amount:,.2f} {to_curr}**
💳 Frais: {fee:.2f} {from_curr}

Utilisez le Converter pour effectuer la conversion."""
                }
            else:
                # Fallback vers exchange_service
                from app.services.exchange_service import exchange_service
                result = exchange_service.get_rate(from_curr, to_curr)
                if result.get('success'):
                    rate = result['rate']
                    return {
                        'success': True,
                        'data': {'rate': rate, 'supplier': 'SarfX'},
                        'message': f"📊 Taux {from_curr}/{to_curr}: **{rate:.4f}**"
                    }
                
            return {
                'success': False,
                'error': 'no_rate',
                'message': f"Impossible de trouver un taux pour {from_curr}/{to_curr}."
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': self._get_graceful_fallback('get_exchange_rate')
            }
    
    def _tool_add_beneficiary(self, params, user_context):
        """Ajouter un nouveau bénéficiaire"""
        user_id = user_context.get('user_id')
        
        if not user_id:
            return {
                'success': False,
                'error': 'not_authenticated',
                'message': "🔒 Connectez-vous pour ajouter un bénéficiaire."
            }
        
        name = params.get('name')
        bank_name = params.get('bank_name')
        account_number = params.get('account_number')
        
        if not name:
            return {
                'success': False,
                'error': 'missing_params',
                'message': "👥 Pour ajouter un bénéficiaire, rendez-vous sur la page Bénéficiaires et remplissez le formulaire avec: nom, banque et numéro de compte."
            }
        
        try:
            # Vérifier si déjà existant
            existing = self.db.beneficiaries.find_one({
                "user_id": str(user_id),
                "name": {"$regex": f"^{name}$", "$options": "i"}
            })
            
            if existing:
                return {
                    'success': False,
                    'error': 'already_exists',
                    'message': f"👥 Un bénéficiaire nommé '{name}' existe déjà."
                }
            
            beneficiary = {
                "user_id": str(user_id),
                "name": name,
                "bank_name": bank_name or "Non spécifié",
                "account_number": account_number or "Non spécifié",
                "created_at": datetime.utcnow(),
                "is_active": True
            }
            
            result = self.db.beneficiaries.insert_one(beneficiary)
            
            return {
                'success': True,
                'data': {'id': str(result.inserted_id), 'name': name},
                'message': f"✅ Bénéficiaire **{name}** ajouté avec succès!\n\nGérez vos bénéficiaires sur la page dédiée."
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': "Impossible d'ajouter le bénéficiaire. Utilisez la page Bénéficiaires."
            }
    
    def _tool_get_all_suppliers(self, params, user_context):
        """Liste des fournisseurs de change"""
        currency = params.get('currency')
        
        try:
            query = {}
            if currency:
                query["currencies"] = {"$in": [currency.upper()]}
            
            suppliers = list(self.db.suppliers.find(query).limit(10)) if 'suppliers' in self.db.list_collection_names() else []
            
            if not suppliers:
                return {
                    'success': True,
                    'data': {'suppliers': []},
                    'message': "🏪 SarfX est votre fournisseur principal de change avec les meilleurs taux!"
                }
            
            supplier_lines = []
            for s in suppliers:
                name = s.get('name', 'N/A')
                status = '✅' if s.get('is_active', True) else '❌'
                currencies = ', '.join(s.get('currencies', [])[:4])
                supplier_lines.append(f"{status} **{name}** - {currencies}")
            
            return {
                'success': True,
                'data': {'suppliers': suppliers, 'count': len(suppliers)},
                'message': f"🏪 **Fournisseurs de change ({len(suppliers)}):**\n\n" + '\n'.join(supplier_lines)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': "Impossible de charger les fournisseurs."
            }
    
    def _tool_get_rate_analytics(self, params, user_context):
        """Analyse d'une paire de devises"""
        from_curr = params.get('from_currency', 'EUR').upper()
        to_curr = params.get('to_currency', 'MAD').upper()
        
        try:
            from app.services.exchange_service import exchange_service
            
            # Obtenir le taux actuel
            result = exchange_service.get_rate(from_curr, to_curr)
            
            if result.get('success'):
                rate = result['rate']
                
                # Obtenir l'historique si disponible
                history_result = exchange_service.get_rate_history(from_curr, to_curr, days=7)
                
                if history_result.get('success') and history_result.get('history'):
                    history = history_result['history']
                    rates = [h.get('rate', rate) for h in history]
                    high = max(rates)
                    low = min(rates)
                    avg = sum(rates) / len(rates)
                    trend = 'up' if rates[-1] > rates[0] else 'down' if rates[-1] < rates[0] else 'stable'
                    trend_text = '📈 Tendance: À la hausse' if trend == 'up' else '📉 Tendance: À la baisse' if trend == 'down' else '➡️ Tendance: Stable'
                    
                    return {
                        'success': True,
                        'data': {'current': rate, 'high': high, 'low': low, 'average': avg, 'trend': trend},
                        'message': f"""📈 **Analyse {from_curr}/{to_curr}:**

📊 Taux actuel: **{rate:.4f}**
📈 Plus haut (7j): {high:.4f}
📉 Plus bas (7j): {low:.4f}
📊 Moyenne: {avg:.4f}
{trend_text}

Voir graphique complet sur Rate History."""
                    }
                else:
                    return {
                        'success': True,
                        'data': {'current': rate},
                        'message': f"📊 Taux actuel {from_curr}/{to_curr}: **{rate:.4f}**\n\nConsultez Rate History pour l'analyse complète."
                    }
                
            return {
                'success': False,
                'error': 'no_data',
                'message': f"Analyse non disponible pour {from_curr}/{to_curr}. Consultez Rate History."
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': "Impossible de charger l'analyse. Consultez Rate History."
            }

    # ==================== NOUVEAUX TOOLS ADMIN ====================
    
    def _tool_get_transaction_volume(self, params, user_context):
        """Volume de transactions par période (Admin)"""
        period = params.get('period', 'day').lower()
        
        try:
            # Calculer la date de début
            now = datetime.utcnow()
            if period == 'week':
                start_date = now - timedelta(days=7)
                period_label = "cette semaine"
            elif period == 'month':
                start_date = now - timedelta(days=30)
                period_label = "ce mois"
            else:  # day
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                period_label = "aujourd'hui"
            
            if 'transactions' not in self.db.list_collection_names():
                return {
                    'success': True,
                    'data': {'count': 0, 'volume': 0},
                    'message': f"📊 Aucune transaction {period_label}."
                }
            
            # Compter les transactions
            tx_count = self.db.transactions.count_documents({
                "created_at": {"$gte": start_date}
            })
            
            # Calculer le volume
            pipeline = [
                {"$match": {"created_at": {"$gte": start_date}}},
                {"$group": {
                    "_id": None,
                    "total_mad": {"$sum": "$amount_mad"},
                    "total_original": {"$sum": "$amount"}
                }}
            ]
            result = list(self.db.transactions.aggregate(pipeline))
            volume_mad = result[0].get('total_mad', 0) if result else 0
            
            # Par devise
            currency_pipeline = [
                {"$match": {"created_at": {"$gte": start_date}}},
                {"$group": {
                    "_id": "$from_currency",
                    "count": {"$sum": 1},
                    "total": {"$sum": "$amount"}
                }},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]
            by_currency = list(self.db.transactions.aggregate(currency_pipeline))
            
            currency_lines = []
            for c in by_currency:
                curr = c.get('_id', 'N/A')
                count = c.get('count', 0)
                total = c.get('total', 0)
                currency_lines.append(f"• {curr}: {count} tx ({total:,.2f})")
            
            return {
                'success': True,
                'data': {
                    'count': tx_count,
                    'volume_mad': volume_mad,
                    'period': period,
                    'by_currency': by_currency
                },
                'message': f"""📊 **Volume de transactions {period_label}:**

📈 Transactions: **{tx_count:,}**
💰 Volume: **{volume_mad:,.2f} MAD**

**Par devise:**
{chr(10).join(currency_lines) if currency_lines else '• Aucune donnée'}

Voir le dashboard admin pour plus de détails."""
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': "Impossible de calculer le volume de transactions."
            }
    
    def _tool_search_users(self, params, user_context):
        """Rechercher un utilisateur (Admin)"""
        query = params.get('query', '')
        field = params.get('field', 'email')
        
        if not query:
            return {
                'success': False,
                'error': 'missing_query',
                'message': "🔍 Précisez un email ou nom à rechercher."
            }
        
        try:
            # Recherche par email ou nom
            search_query = {
                "$or": [
                    {"email": {"$regex": query, "$options": "i"}},
                    {"first_name": {"$regex": query, "$options": "i"}},
                    {"last_name": {"$regex": query, "$options": "i"}}
                ]
            }
            
            users = list(self.db.users.find(
                search_query,
                {"email": 1, "first_name": 1, "last_name": 1, "role": 1, "is_active": 1, "created_at": 1}
            ).limit(10))
            
            if not users:
                return {
                    'success': True,
                    'data': {'users': []},
                    'message': f"🔍 Aucun utilisateur trouvé pour '{query}'."
                }
            
            user_lines = []
            for u in users:
                email = u.get('email', 'N/A')
                # Masquer partiellement
                parts = email.split('@')
                masked = parts[0][:3] + '***@' + parts[1] if len(parts) == 2 else '***'
                
                name = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip() or 'N/A'
                role = u.get('role', 'user')
                status = '✅' if u.get('is_active', True) else '❌'
                user_lines.append(f"{status} {masked} - {name} ({role})")
            
            return {
                'success': True,
                'data': {'users': users, 'count': len(users)},
                'message': f"🔍 **{len(users)} utilisateur(s) trouvé(s):**\n\n" + '\n'.join(user_lines) + "\n\nConsultez Admin > Users pour plus de détails."
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': "Impossible de rechercher les utilisateurs."
            }


# ==================== DÉTECTION D'INTENTION ====================

INTENT_PATTERNS = {
    'get_my_balance': [
        r'solde|balance|combien.*(j\'ai|ai-je)|mon argent|mes fonds',
        r'what.*balance|how much.*have|my money|my funds|my wallet'
    ],
    'get_exchange_rate': [
        r'taux.*(change|conversion)|cours|rate.*(eur|usd|mad|gbp)',
        r'exchange rate|conversion rate|what.*rate|combien.*vaut'
    ],
    'convert_currency': [
        r'convertir?|conversion|combien.*(eur|usd|mad|gbp).*(en|to|font)',
        r'convert|how much.*in|transformer'
    ],
    'find_nearest_atm': [
        r'atm.*(près|proche|nearby)|distributeur.*(près|proche)|où.*retirer',
        r'nearest.*atm|closest.*atm|find.*atm.*near'
    ],
    'search_atms': [
        r'atm.*(à|a|in|dans)\s+\w+|distributeur.*(à|a)\s+\w+',
        r'atm.*casablanca|atm.*rabat|atm.*marrakech|atm.*fes|atm.*tanger',
        r'chercher.*atm|trouver.*atm|search.*atm'
    ],
    'get_cities_with_atms': [
        r'(quelles?|which).*villes?.*(atm|distributeur)',
        r'villes.*disponibles|cities.*with.*atm|où.*(y.a|sont).*atm'
    ],
    'get_my_transactions': [
        r'transaction|historique|opération|mouvement|mes.*opérations',
        r'history|transactions|recent.*operations|mes.*transferts'
    ],
    'list_my_beneficiaries': [
        r'bénéficiaire|destinataire|recipient|beneficiar',
        r'who.*send|mes contacts|à qui.*envoyer'
    ],
    'add_beneficiary': [
        r'ajouter.*(bénéficiaire|destinataire|contact)',
        r'add.*(beneficiary|recipient)|nouveau.*bénéficiaire'
    ],
    'get_rate_history': [
        r'historique.*(taux|rate)|évolution.*(taux|cours)',
        r'rate history|tendance|trend|graphique.*taux'
    ],
    'get_rate_analytics': [
        r'analyse.*(taux|devises?|eur|usd)|analytics',
        r'prévision|forecast|min.*max|moyenne.*taux'
    ],
    'get_best_rate': [
        r'meilleur.*(taux|rate)|best.*rate|optimal',
        r'où.*meilleur|cheapest|moins cher'
    ],
    'get_all_suppliers': [
        r'fournisseur|supplier|bureau.*(change|exchange)',
        r'who.*provides|partenaires|providers'
    ],
    'count_active_users': [
        r'combien.*(utilisateur|user|inscrit)|nombre.*(user|utilisateur)',
        r'how many.*(user|registered)|user count|total users'
    ],
    'get_system_stats': [
        r'stat(istique)?s?.*(système|system|global)|dashboard',
        r'system stats|overview|rapport|kpi'
    ],
    'get_recent_signups': [
        r'(dernier|nouveau|recent).*(inscription|utilisateur|signup)',
        r'new users|recent signups|who.*joined'
    ],
    'get_sarfx_info': [
        r'c\'est quoi sarfx|what is sarfx|présent|about sarfx',
        r'qui êtes vous|who are you|aide générale|à propos'
    ],
    'get_my_bank_info': [
        r'info.*(ma|my).*banque|ma banque|my bank info',
        r'détail.*banque|bank.*details|quelle.*banque'
    ],
    'get_bank_atms': [
        r'atm.*(ma|de ma|notre).*banque|nos atms',
        r'our.*atms|bank.*atms|atm.*notre'
    ],
    'get_bank_stats': [
        r'stat.*(ma|notre|my).*banque|performance.*banque',
        r'bank.*stats|statistiques.*banque'
    ],
    'get_bank_api_status': [
        r'(statut|status).*api|api.*(marche|fonctionne|works)',
        r'api.*status|connexion.*api|api.*active'
    ],
    'get_all_banks': [
        r'list.*(banques?|banks)|toutes.*banques',
        r'all.*banks|quelles.*banques|partenaires.*bancaires'
    ],
    'get_all_banks_stats': [
        r'stat.*toutes.*banques|global.*banks.*stats',
        r'all.*banks.*stats|performances.*banques'
    ],
    'get_transaction_volume': [
        r'volume.*(transaction|échange)|combien.*transactions',
        r'transaction.*volume|daily.*volume|how many.*transactions'
    ],
    'search_users': [
        r'chercher.*(utilisateur|user)|trouver.*(utilisateur|user)',
        r'search.*user|find.*user|look.*up.*user'
    ]
}


def detect_intent(message):
    """
    Détecte l'intention de l'utilisateur à partir du message
    
    Returns:
        tuple: (tool_name, extracted_params) ou (None, None) si pas d'intention claire
    """
    message_lower = message.lower()
    params = {}
    
    # Extraire les devises mentionnées
    currencies = re.findall(r'\b(eur|usd|mad|gbp|chf|cad|aud|jpy|aed|sar)\b', message_lower)
    if len(currencies) >= 2:
        params['from_currency'] = currencies[0].upper()
        params['to_currency'] = currencies[1].upper()
    elif len(currencies) == 1:
        params['to_currency'] = currencies[0].upper()
        params['from_currency'] = 'EUR'  # Default
    
    # Extraire les montants
    amounts = re.findall(r'(\d+(?:[.,]\d+)?)', message)
    if amounts:
        params['amount'] = float(amounts[0].replace(',', '.'))
    
    # Extraire les villes marocaines
    moroccan_cities = [
        'casablanca', 'rabat', 'marrakech', 'fes', 'fès', 'tanger', 'agadir',
        'meknes', 'meknès', 'oujda', 'kenitra', 'tetouan', 'tétouan', 'el jadida',
        'safi', 'mohammedia', 'khouribga', 'beni mellal', 'nador', 'taza'
    ]
    for city in moroccan_cities:
        if city in message_lower:
            params['query'] = city.title()
            params['city'] = city.title()
            break
    
    # Extraire la période
    if 'jour' in message_lower or 'today' in message_lower or "aujourd'hui" in message_lower:
        params['period'] = 'day'
    elif 'semaine' in message_lower or 'week' in message_lower:
        params['period'] = 'week'
    elif 'mois' in message_lower or 'month' in message_lower:
        params['period'] = 'month'
    
    # Extraire les jours pour historique
    days_match = re.search(r'(\d+)\s*(jours?|days?|j)', message_lower)
    if days_match:
        params['days'] = int(days_match.group(1))
    
    # Extraire limit
    limit_match = re.search(r'(\d+)\s*(dernier|dernière|last|recent)', message_lower)
    if limit_match:
        params['limit'] = int(limit_match.group(1))
    
    # Extraire email pour recherche
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', message)
    if email_match:
        params['query'] = email_match.group(0)
        params['field'] = 'email'
    
    # Détecter l'intention
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, message_lower):
                return intent, params
    
    return None, params


# Instance globale (sera initialisée avec la DB)
chatbot_tools = None

def get_chatbot_tools(db):
    """Factory pour obtenir l'instance des tools avec la DB"""
    global chatbot_tools
    if chatbot_tools is None or chatbot_tools.db != db:
        chatbot_tools = ChatbotTools(db)
    return chatbot_tools
