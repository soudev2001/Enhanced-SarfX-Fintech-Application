"""
Service de chatbot avancé utilisant l'API Gemini de Google
Avec RBAC, Function Calling, Mémoire de conversation et Rate Limiting
"""
import requests
import os
import re
import time
import hashlib
from datetime import datetime, timedelta
from flask import current_app

# ==================== CONFIGURATION ====================
MAX_CONVERSATION_HISTORY = 10  # Nombre max de messages en mémoire
RATE_LIMIT_ANONYMOUS = 5  # Requêtes par minute pour anonymes
RATE_LIMIT_AUTHENTICATED = 30  # Requêtes par minute pour utilisateurs connectés
RATE_LIMIT_WINDOW = 60  # Fenêtre en secondes

# ==================== SUGGESTIONS CONTEXTUELLES ====================
CONTEXTUAL_SUGGESTIONS = {
    'landing': [
        "C'est quoi SarfX ?",
        "Où sont les ATMs ?",
        "Taux de change actuel",
        "Comment s'inscrire ?",
        "Devises supportées",
        "Frais de conversion"
    ],
    'app': {
        'user': [
            "Mon solde",
            "Mes transactions",
            "Localiser un ATM",
            "Taux EUR/MAD",
            "Mes bénéficiaires",
            "Convertir des devises"
        ],
        'bank_user': [
            "Mon solde",
            "Info de ma banque",
            "Taux de change",
            "Mes transactions",
            "ATMs de ma banque",
            "Aide API"
        ],
        'bank_respo': [
            "Stats de ma banque",
            "ATMs de ma banque",
            "Mon solde",
            "Taux de change",
            "Transactions bancaires",
            "Configurer API"
        ]
    },
    'backoffice': {
        'admin': [
            "Nombre d'utilisateurs",
            "Stats du système",
            "Dernières inscriptions",
            "Liste des banques",
            "Transactions globales",
            "Status des services"
        ],
        'admin_sr_bank': [
            "Stats toutes banques",
            "Liste des banques",
            "Utilisateurs actifs",
            "Transactions globales",
            "Nouveaux utilisateurs",
            "Rapports"
        ],
        'admin_associate_bank': [
            "Stats de ma banque",
            "Status API banque",
            "ATMs de ma banque",
            "Utilisateurs banque",
            "Taux de change",
            "Transactions banque"
        ]
    }
}


class ChatbotService:
    """Service pour interagir avec l'API Gemini avec RBAC, Tools et Mémoire"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY', 'AIzaSyC4q4-n7tdL8cU9srm8q9aodCG0hTqUcoA')
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
        # Rate limiting en mémoire (pour prod, utiliser Redis)
        self._rate_limits = {}
        
        # Patterns de détection de demandes sensibles
        self.sensitive_patterns = [
            r'mot de passe|password|mdp|pwd',
            r'carte bancaire|credit card|numéro de carte|card number',
            r'code pin|pin code|code secret',
            r'iban|rib|compte bancaire|account number',
            r'code cvv|cvv|cvc|code sécurité carte',
            r'api[_\s]?key|clé api|secret key',
            r'token|jwt|bearer|auth token',
            r'credential|identifiant secret',
            r'admin password|mot de passe admin',
            r'base de données|database|mongodb|connection string',
            r'données utilisateur|user data|informations personnelles',
            r'liste des utilisateurs|all users|dump users',
            r'données financières|financial data|transactions privées',
            r'clé privée|private key|ssh key',
            r'bypass|contourner|hack|injection|exploit'
        ]
        
        # Réponses pour demandes sensibles
        self.security_response = "🔒 Pour des raisons de sécurité, je ne peux pas fournir d'informations sensibles comme des mots de passe, numéros de carte, IBAN ou données personnelles. Si vous avez besoin d'aide avec votre compte, veuillez contacter notre support sécurisé à support@sarfx.ma ou accéder à votre espace client pour gérer vos informations de manière sécurisée."
        
        # Réponses de fallback intelligentes par contexte
        self.fallback_responses = {
            "taux": "📊 Les taux de change actuels sont disponibles sur la page Converter. Nous offrons les meilleures conversions EUR/MAD, USD/MAD et GBP/MAD avec des mises à jour en temps réel.",
            "wallet": "💳 Pour créer un wallet, connectez-vous à votre compte et accédez à la section 'Wallets'. Vous pouvez gérer plusieurs devises (EUR, USD, MAD, GBP) dans un seul portefeuille.",
            "atm": "🏧 Trouvez un ATM partenaire près de vous sur la page 'Find ATMs'. Nous avons plus de 1000 distributeurs partenaires au Maroc avec accès 24/7.",
            "bénéficiaire": "👥 Pour ajouter un bénéficiaire, allez dans 'Bénéficiaires' et cliquez sur 'Ajouter'. Renseignez le nom, la banque et l'IBAN du destinataire.",
            "api": "🔌 L'API SarfX permet aux banques partenaires d'intégrer nos services de conversion. Contactez votre administrateur pour les credentials API.",
            "frais": "💰 SarfX applique des frais transparents de 0.5% sur les conversions. Aucun frais caché ! Consultez le détail avant chaque transaction.",
            "solde": "💳 Je n'ai pas pu récupérer votre solde. Veuillez consulter la page Wallets pour voir vos soldes en temps réel.",
            "transaction": "📊 Impossible de charger vos transactions. Consultez la page Transactions pour l'historique complet.",
            "stats": "📈 Les statistiques ne sont pas disponibles actuellement. Consultez le tableau de bord pour des informations en temps réel.",
            "default": "👋 Je suis l'assistant SarfX ! Je peux vous aider avec : les taux de change, les wallets, la localisation d'ATMs, les bénéficiaires et l'API. Que souhaitez-vous savoir ?"
        }
        
    def _is_sensitive_request(self, message):
        """Vérifie si le message demande des informations sensibles"""
        message_lower = message.lower()
        for pattern in self.sensitive_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        return False
    
    def _sanitize_response(self, response):
        """Nettoie la réponse pour masquer toute donnée sensible potentielle"""
        sanitize_patterns = [
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[email masqué]'),
            (r'\b(?:MA|FR|DE|ES|IT|GB)[0-9]{2}[A-Z0-9]{4,30}\b', '[IBAN masqué]'),
            (r'\b(?:\d{4}[-\s]?){3}\d{4}\b', '[carte masquée]'),
            (r'\b\d{3,4}\b(?=.*(?:cvv|cvc|code))', '***'),
            (r'(?:api[_\s]?key|token|secret)[:\s]*["\']?[A-Za-z0-9_-]{20,}["\']?', '[clé masquée]'),
            (r'mongodb(?:\+srv)?://[^\s]+', '[connexion masquée]'),
            (r'(?:password|pwd|mdp)[:\s]*["\']?[^\s"\']+["\']?', '[mot de passe masqué]'),
        ]
        
        sanitized = response
        for pattern, replacement in sanitize_patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    # ==================== RATE LIMITING ====================
    
    def _get_client_id(self, user_context, ip_address=None):
        """Génère un identifiant unique pour le client"""
        if user_context and user_context.get('user_id'):
            return f"user_{user_context['user_id']}"
        elif ip_address:
            return f"ip_{hashlib.md5(ip_address.encode()).hexdigest()[:16]}"
        return "anonymous"
    
    def check_rate_limit(self, user_context=None, ip_address=None):
        """
        Vérifie si le client n'a pas dépassé la limite de requêtes
        
        Returns:
            tuple: (is_allowed, remaining_requests, reset_time)
        """
        client_id = self._get_client_id(user_context, ip_address)
        current_time = time.time()
        
        # Déterminer la limite selon le type d'utilisateur
        is_authenticated = user_context and user_context.get('user_id')
        limit = RATE_LIMIT_AUTHENTICATED if is_authenticated else RATE_LIMIT_ANONYMOUS
        
        # Nettoyer les anciennes entrées
        if client_id in self._rate_limits:
            self._rate_limits[client_id] = [
                t for t in self._rate_limits[client_id]
                if current_time - t < RATE_LIMIT_WINDOW
            ]
        else:
            self._rate_limits[client_id] = []
        
        # Vérifier la limite
        request_count = len(self._rate_limits[client_id])
        
        if request_count >= limit:
            oldest_request = min(self._rate_limits[client_id])
            reset_time = int(oldest_request + RATE_LIMIT_WINDOW - current_time)
            return False, 0, reset_time
        
        # Enregistrer la requête
        self._rate_limits[client_id].append(current_time)
        
        return True, limit - request_count - 1, RATE_LIMIT_WINDOW
    
    def get_rate_limit_response(self, reset_time):
        """Retourne le message d'erreur pour rate limit"""
        return {
            'success': False,
            'error': 'rate_limited',
            'response': f"⏱️ Vous avez atteint la limite de requêtes. Veuillez patienter {reset_time} secondes avant de réessayer. Connectez-vous pour bénéficier d'une limite plus élevée.",
            'retry_after': reset_time
        }
    
    # ==================== MÉMOIRE DE CONVERSATION ====================
    
    def save_message_to_history(self, db, session_id, role, content, user_context=None):
        """
        Sauvegarde un message dans l'historique de conversation
        
        Args:
            db: Instance de la base de données
            session_id: ID de session unique
            role: 'user' ou 'assistant'
            content: Contenu du message
            user_context: Contexte utilisateur optionnel
        """
        if db is None:
            return None
            
        try:
            message = {
                'session_id': session_id,
                'role': role,
                'content': content,
                'timestamp': datetime.utcnow(),
                'user_id': user_context.get('user_id') if user_context else None,
                'user_role': user_context.get('role') if user_context else 'anonymous'
            }
            
            result = db.chat_history.insert_one(message)
            
            # Nettoyer les anciens messages (garder MAX_CONVERSATION_HISTORY par session)
            self._cleanup_old_messages(db, session_id)
            
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error saving chat message: {e}")
            return None
    
    def _cleanup_old_messages(self, db, session_id):
        """Supprime les messages excédentaires pour une session"""
        try:
            # Compter les messages de la session
            count = db.chat_history.count_documents({'session_id': session_id})
            
            if count > MAX_CONVERSATION_HISTORY:
                # Trouver les IDs des messages à supprimer (les plus anciens)
                excess = count - MAX_CONVERSATION_HISTORY
                old_messages = list(db.chat_history.find(
                    {'session_id': session_id},
                    {'_id': 1}
                ).sort('timestamp', 1).limit(excess))
                
                if old_messages:
                    ids_to_delete = [m['_id'] for m in old_messages]
                    db.chat_history.delete_many({'_id': {'$in': ids_to_delete}})
        except Exception as e:
            print(f"Error cleaning chat history: {e}")
    
    def get_conversation_history(self, db, session_id, limit=MAX_CONVERSATION_HISTORY):
        """
        Récupère l'historique de conversation pour une session
        
        Returns:
            list: Liste des messages [{role, content, timestamp}, ...]
        """
        if db is None:
            return []
            
        try:
            messages = list(db.chat_history.find(
                {'session_id': session_id},
                {'role': 1, 'content': 1, 'timestamp': 1, '_id': 0}
            ).sort('timestamp', -1).limit(limit))
            
            # Inverser pour avoir l'ordre chronologique
            return list(reversed(messages))
        except Exception as e:
            print(f"Error fetching chat history: {e}")
            return []
    
    def format_history_for_prompt(self, history):
        """Formate l'historique pour inclusion dans le prompt"""
        if not history:
            return ""
        
        formatted = "\n\nHistorique de conversation récent:\n"
        for msg in history[-5:]:  # Derniers 5 messages seulement pour le prompt
            role_label = "Utilisateur" if msg['role'] == 'user' else "Assistant"
            content = msg['content'][:200]  # Tronquer les longs messages
            formatted += f"- {role_label}: {content}\n"
        
        return formatted
    
    def clear_conversation_history(self, db, session_id):
        """Efface l'historique de conversation d'une session"""
        if db is None:
            return False
            
        try:
            db.chat_history.delete_many({'session_id': session_id})
            return True
        except Exception as e:
            print(f"Error clearing chat history: {e}")
            return False
        
    # ==================== GÉNÉRATION DE RÉPONSE AVEC TOOLS ====================
        
    def generate_response(self, message, user_context=None, db=None, session_id=None, ip_address=None):
        """
        Génère une réponse du chatbot avec RBAC, Tools et Mémoire
        
        Args:
            message (str): Message de l'utilisateur
            user_context (dict): Contexte utilisateur {user_id, role, email, bank_code, ...}
            db: Instance de la base de données
            session_id (str): ID de session pour la mémoire de conversation
            ip_address (str): Adresse IP pour rate limiting
            
        Returns:
            dict: Réponse avec 'success', 'response', 'tool_used' ou 'error'
        """
        # 1. RATE LIMITING
        is_allowed, remaining, reset_time = self.check_rate_limit(user_context, ip_address)
        if not is_allowed:
            return self.get_rate_limit_response(reset_time)
        
        # 2. SÉCURITÉ - Vérifier demandes sensibles
        if self._is_sensitive_request(message):
            return {'success': True, 'response': self.security_response}
        
        # 3. SAUVEGARDER LE MESSAGE UTILISATEUR
        if db is not None and session_id:
            self.save_message_to_history(db, session_id, 'user', message, user_context)
        
        # 4. DÉTECTION D'INTENTION ET EXÉCUTION DE TOOL
        from app.services.chatbot_tools import detect_intent, get_chatbot_tools
        
        intent, params = detect_intent(message)
        tool_result = None
        
        if intent and db is not None:
            tools = get_chatbot_tools(db)
            tool_result = tools.execute_tool(intent, params, user_context or {'role': 'anonymous'})
            
            # Si le tool a réussi, utiliser sa réponse
            if tool_result.get('success'):
                response_text = tool_result.get('message', '')
                
                # Sauvegarder la réponse
                if session_id:
                    self.save_message_to_history(db, session_id, 'assistant', response_text, user_context)
                
                return {
                    'success': True,
                    'response': response_text,
                    'tool_used': intent,
                    'data': tool_result.get('data'),
                    'remaining_requests': remaining
                }
            elif tool_result.get('error') == 'permission_denied':
                # Permission refusée - retourner le message d'erreur
                return {
                    'success': True,
                    'response': tool_result.get('message'),
                    'tool_used': intent,
                    'remaining_requests': remaining
                }
        
        # 5. FALLBACK VERS GEMINI AI
        if not self.api_key:
            fallback = self._get_fallback_response(message, user_context)
            if db is not None and session_id:
                self.save_message_to_history(db, session_id, 'assistant', fallback['response'], user_context)
            return fallback
            
        try:
            # Récupérer l'historique de conversation
            history = []
            if db is not None and session_id:
                history = self.get_conversation_history(db, session_id, limit=5)
            
            # Construire le prompt maître
            master_prompt = self._build_master_prompt(user_context, history)
            
            prompt = f"{master_prompt}\n\nMessage utilisateur: {message}\n\nRéponds de manière utile, concise et sécurisée:"
            
            # Préparer la requête
            headers = {
                'Content-Type': 'application/json',
                'X-goog-api-key': self.api_key
            }
            
            data = {
                "contents": [{"parts": [{"text": prompt}]}],
                "safetySettings": [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
                ]
            }
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            
            if response.status_code != 200:
                print(f"Gemini API error: {response.status_code} - {response.text[:200]}")
                fallback = self._get_fallback_response(message, user_context)
                return fallback
            
            result = response.json()
            
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    text = candidate['content']['parts'][0].get('text', '')
                    sanitized_text = self._sanitize_response(text)
                    
                    # Sauvegarder la réponse
                    if db is not None and session_id:
                        self.save_message_to_history(db, session_id, 'assistant', sanitized_text, user_context)
                    
                    return {
                        'success': True,
                        'response': sanitized_text,
                        'remaining_requests': remaining
                    }
            
            return self._get_fallback_response(message, user_context)
            
        except requests.exceptions.RequestException as e:
            print(f"Chatbot connection error: {e}")
            return self._get_fallback_response(message, user_context)
        except Exception as e:
            print(f"Chatbot error: {e}")
            return self._get_fallback_response(message, user_context)
    
    def _build_master_prompt(self, user_context, history=None):
        """
        Construit le System Prompt "Maître" avec identité, règles et contexte
        """
        user_name = user_context.get('email', 'Visiteur').split('@')[0] if user_context else 'Visiteur'
        user_role = user_context.get('role', 'anonymous') if user_context else 'anonymous'
        bank_code = user_context.get('bank_code', '') if user_context else ''
        
        # Capacités selon le rôle
        role_capabilities = {
            'anonymous': "Peut consulter les taux de change, localiser des ATMs, et obtenir des informations générales sur SarfX.",
            'user': "Peut consulter ses soldes, historique de transactions, localiser des ATMs, gérer ses bénéficiaires, et effectuer des conversions.",
            'bank_user': "Peut consulter ses soldes, historique, informations de sa banque partenaire, et accéder aux fonctionnalités bancaires.",
            'bank_respo': "Peut gérer les ATMs de sa banque, consulter les statistiques bancaires, et accéder aux rapports.",
            'admin_associate_bank': "Accès aux statistiques de la banque, contrôle API, gestion des paramètres bancaires.",
            'admin_sr_bank': "Accès aux statistiques de toutes les banques, gestion des partenariats bancaires.",
            'admin': "Accès complet : statistiques système, gestion des utilisateurs, monitoring des services, et configuration globale."
        }
        
        history_text = self.format_history_for_prompt(history) if history else ""
        
        return f"""Identité : Tu es l'expert IA de l'écosystème SarfX, une plateforme fintech marocaine de conversion de devises. 
Ton objectif est d'aider les utilisateurs (Banking) et les administrateurs (Back-office) avec précision et courtoisie.

Règles de Conduite :
1. Analyse le rôle de l'utilisateur via le contexte fourni et adapte tes réponses.
2. Ne divulgue JAMAIS d'informations sensibles (mots de passe, clés API, IBAN, numéros de carte).
3. Si une information n'est pas disponible, dis-le clairement au lieu d'inventer.
4. Pour les questions techniques (API, intégration), fournis des explications claires.
5. Réponds en français par défaut, mais adapte-toi à la langue de l'utilisateur.
6. Sois concis et professionnel, avec une touche amicale (utilise des emojis avec modération).

Capacités par Rôle :
- [Rôle: ANONYMOUS] : Infos générales SarfX, taux de change publics, localisation ATMs.
- [Rôle: USER] : Soldes, transactions, bénéficiaires, conversions, ATMs.
- [Rôle: BANK_USER/BANK_RESPO] : + Infos banque partenaire, stats bancaires.
- [Rôle: ADMIN] : Accès total - stats système, gestion utilisateurs, monitoring.

Contexte actuel :
- Utilisateur : {user_name}
- Rôle : {user_role.upper()}
- Banque associée : {bank_code if bank_code else 'Aucune'}
- Capacités : {role_capabilities.get(user_role, role_capabilities['anonymous'])}
{history_text}

RÈGLES DE SÉCURITÉ STRICTES :
1. Ne JAMAIS divulguer de mots de passe, codes PIN, ou credentials
2. Ne JAMAIS afficher d'IBAN, numéros de carte bancaire ou CVV
3. Ne JAMAIS révéler de clés API, tokens ou secrets
4. Rediriger vers le support (support@sarfx.ma) pour les questions sensibles"""
    
    def _get_fallback_response(self, message, user_context=None):
        """Retourne une réponse intelligente basée sur des mots-clés et le contexte"""
        message_lower = message.lower().strip()
        role = user_context.get('role', 'anonymous') if user_context else 'anonymous'
        
        # Gestion des salutations courtes
        greetings = ['hi', 'hy', 'hey', 'hello', 'bonjour', 'salut', 'slt', 'coucou', 'bonsoir', 'yo', 'cc']
        if message_lower in greetings or any(message_lower.startswith(g + ' ') for g in greetings):
            return {
                'success': True, 
                'response': "👋 Bonjour ! Je suis l'assistant SarfX. Comment puis-je vous aider aujourd'hui ?\n\nVoici quelques exemples de ce que je peux faire :\n• Consulter les taux de change\n• Trouver un ATM près de vous\n• Expliquer comment créer un wallet\n• Répondre à vos questions sur SarfX"
            }
        
        # Réponses spécifiques pour les admins
        if role in ['admin', 'admin_sr_bank', 'admin_associate_bank']:
            if any(word in message_lower for word in ['stat', 'utilisateur', 'user', 'nombre']):
                return {'success': True, 'response': self.fallback_responses['stats']}
        
        # Réponses générales par mots-clés
        for keyword, response in self.fallback_responses.items():
            if keyword != "default" and keyword in message_lower:
                return {'success': True, 'response': response}
        
        # Vérifier d'autres mots-clés courants
        if any(word in message_lower for word in ['change', 'conversion', 'euro', 'dollar', 'dirham', 'taux']):
            return {'success': True, 'response': self.fallback_responses['taux']}
        if any(word in message_lower for word in ['portefeuille', 'solde', 'balance', 'argent']):
            return {'success': True, 'response': self.fallback_responses['solde']}
        if any(word in message_lower for word in ['distributeur', 'retrait', 'cash', 'atm', 'dab']):
            return {'success': True, 'response': self.fallback_responses['atm']}
        if any(word in message_lower for word in ['transfert', 'envoyer', 'destinataire', 'bénéficiaire']):
            return {'success': True, 'response': self.fallback_responses['bénéficiaire']}
        if any(word in message_lower for word in ['commission', 'coût', 'prix', 'frais']):
            return {'success': True, 'response': self.fallback_responses['frais']}
        if any(word in message_lower for word in ['transaction', 'historique', 'opération']):
            return {'success': True, 'response': self.fallback_responses['transaction']}
        
        return {'success': True, 'response': self.fallback_responses['default']}
    
    # ==================== SUGGESTIONS CONTEXTUELLES ====================
    
    def get_contextual_suggestions(self, context_type='landing', user_role='anonymous'):
        """
        Retourne des suggestions adaptées au contexte et au rôle
        
        Args:
            context_type: 'landing', 'app', ou 'backoffice'
            user_role: Rôle de l'utilisateur
            
        Returns:
            list: Liste de suggestions (max 6)
        """
        if context_type == 'landing':
            return CONTEXTUAL_SUGGESTIONS['landing']
        
        if context_type == 'app':
            role_suggestions = CONTEXTUAL_SUGGESTIONS['app'].get(user_role)
            if role_suggestions:
                return role_suggestions
            return CONTEXTUAL_SUGGESTIONS['app']['user']
        
        if context_type == 'backoffice':
            role_suggestions = CONTEXTUAL_SUGGESTIONS['backoffice'].get(user_role)
            if role_suggestions:
                return role_suggestions
            # Fallback pour les autres rôles admin
            if user_role.startswith('admin'):
                return CONTEXTUAL_SUGGESTIONS['backoffice']['admin']
            return CONTEXTUAL_SUGGESTIONS['landing']
        
        return CONTEXTUAL_SUGGESTIONS['landing']

    def get_suggestions(self, db=None, user=None, context_type='landing'):
        """
        Retourne des suggestions personnalisées (rétro-compatible)
        
        Args:
            db: Instance de la base de données
            user: Utilisateur courant
            context_type: Type de contexte ('landing', 'app', 'backoffice')
        """
        role = user.get('role', 'user') if user else 'anonymous'
        suggestions = self.get_contextual_suggestions(context_type, role)
        
        # Personnalisation additionnelle basée sur les données
        if db is not None and user:
            try:
                user_id = str(user.get('_id'))
                
                # Si l'utilisateur n'a pas de transactions, suggérer la première
                if 'transactions' in db.list_collection_names():
                    tx_count = db.transactions.count_documents({"user_id": user_id})
                    if tx_count == 0:
                        suggestions = list(suggestions)
                        if "Comment effectuer ma première transaction ?" not in suggestions:
                            suggestions[-1] = "Comment effectuer ma première transaction ?"
                
                # Si l'utilisateur n'a pas de wallet
                if 'wallets' in db.list_collection_names():
                    wallet = db.wallets.find_one({"user_id": user_id})
                    if not wallet:
                        suggestions = list(suggestions)
                        if "Comment créer un wallet ?" not in suggestions:
                            suggestions[-1] = "Comment créer un wallet ?"
                            
            except Exception as e:
                print(f"Error personalizing suggestions: {e}")
        
        return suggestions[:6]

    def get_sarfx_context(self):
        """Retourne le contexte SarfX de base (rétro-compatible)"""
        return """Tu es un assistant virtuel de SarfX, une plateforme fintech de conversion de devises et de gestion de portefeuilles multi-devises.
        
SarfX propose:
- Conversion de devises en temps réel (USD, EUR, MAD, GBP, CHF)
- Gestion de portefeuilles multi-devises
- Localisation de distributeurs automatiques (ATM)
- Gestion de bénéficiaires pour les transferts
- Accès API pour les banques partenaires
- Tableau de bord admin pour la gestion

Réponds aux questions des utilisateurs de manière claire, concise et professionnelle en français."""


# Instance globale du service
chatbot_service = ChatbotService()
