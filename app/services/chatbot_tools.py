"""
Chatbot Tools - Système de Function Calling avec RBAC pour SarfX
Permet au chatbot d'exécuter des actions en fonction du rôle utilisateur
"""
from datetime import datetime, timedelta
from bson import ObjectId
import re

# ==================== PERMISSIONS PAR RÔLE ====================
ROLE_PERMISSIONS = {
    'anonymous': ['get_exchange_rate', 'convert_currency', 'get_supported_currencies', 'get_sarfx_info'],
    'user': [
        'get_exchange_rate', 'convert_currency', 'get_supported_currencies', 'get_sarfx_info',
        'get_my_balance', 'get_my_transactions', 'find_nearest_atm', 'list_my_beneficiaries',
        'get_rate_history'
    ],
    'bank_user': [
        'get_exchange_rate', 'convert_currency', 'get_supported_currencies', 'get_sarfx_info',
        'get_my_balance', 'get_my_transactions', 'find_nearest_atm', 'list_my_beneficiaries',
        'get_rate_history', 'get_my_bank_info'
    ],
    'bank_respo': [
        'get_exchange_rate', 'convert_currency', 'get_supported_currencies', 'get_sarfx_info',
        'get_my_balance', 'get_my_transactions', 'find_nearest_atm', 'list_my_beneficiaries',
        'get_rate_history', 'get_my_bank_info', 'get_bank_atms', 'get_bank_stats'
    ],
    'admin_associate_bank': [
        'get_exchange_rate', 'convert_currency', 'get_supported_currencies', 'get_sarfx_info',
        'get_my_balance', 'get_my_transactions', 'find_nearest_atm', 'list_my_beneficiaries',
        'get_rate_history', 'get_my_bank_info', 'get_bank_atms', 'get_bank_stats', 'get_bank_api_status'
    ],
    'admin_sr_bank': [
        'get_exchange_rate', 'convert_currency', 'get_supported_currencies', 'get_sarfx_info',
        'get_my_balance', 'get_my_transactions', 'find_nearest_atm', 'list_my_beneficiaries',
        'get_rate_history', 'get_all_banks', 'get_all_banks_stats'
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
            from app.services.atm_service import atm_service
            
            if lat and lng:
                atms = atm_service.find_nearby(float(lat), float(lng), limit=limit)
            else:
                # Sans coordonnées, retourner des ATMs populaires
                atms = atm_service.search_atms("Casablanca", limit=limit)
            
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


# ==================== DÉTECTION D'INTENTION ====================

INTENT_PATTERNS = {
    'get_my_balance': [
        r'solde|balance|combien.*(j\'ai|ai-je)|mon argent|mes fonds',
        r'what.*balance|how much.*have|my money|my funds'
    ],
    'get_exchange_rate': [
        r'taux.*(change|conversion)|cours|rate.*(eur|usd|mad|gbp)',
        r'exchange rate|conversion rate|what.*rate'
    ],
    'convert_currency': [
        r'convertir?|conversion|combien.*(eur|usd|mad|gbp).*(en|to)',
        r'convert|how much.*in'
    ],
    'find_nearest_atm': [
        r'atm|distributeur|dab|retirer|withdrawal|cash',
        r'où.*atm|find.*atm|nearest.*atm|closest.*atm'
    ],
    'get_my_transactions': [
        r'transaction|historique|opération|mouvement',
        r'history|transactions|recent.*operations'
    ],
    'list_my_beneficiaries': [
        r'bénéficiaire|destinataire|recipient|beneficiar',
        r'who.*send|mes contacts'
    ],
    'count_active_users': [
        r'combien.*(utilisateur|user|inscrit)|nombre.*(user|utilisateur)',
        r'how many.*(user|registered)|user count|total users'
    ],
    'get_system_stats': [
        r'stat(istique)?s?.*(système|system|global)',
        r'system stats|dashboard|overview|rapport'
    ],
    'get_sarfx_info': [
        r'c\'est quoi sarfx|what is sarfx|présent|about',
        r'qui êtes vous|who are you|aide|help'
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
