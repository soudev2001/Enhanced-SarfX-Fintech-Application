"""Service de chatbot utilisant l'API Gemini de Google"""
import requests
import os
import re
from flask import current_app

class ChatbotService:
    """Service pour interagir avec l'API Gemini avec sécurité renforcée"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY', 'AIzaSyC4q4-n7tdL8cU9srm8q9aodCG0hTqUcoA')
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        self.suggestions = [
            "Quels sont les taux de change actuels ?",
            "Comment créer un wallet ?",
            "Où trouver un ATM près de moi ?",
            "Comment ajouter un bénéficiaire ?",
            "Comment fonctionne l'API banque ?",
            "Quels sont les frais de conversion ?"
        ]
        
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
        
        # Réponses de fallback intelligentes
        self.fallback_responses = {
            "taux": "📊 Les taux de change actuels sont disponibles sur la page Converter. Nous offrons les meilleures conversions EUR/MAD, USD/MAD et GBP/MAD avec des mises à jour en temps réel.",
            "wallet": "💳 Pour créer un wallet, connectez-vous à votre compte et accédez à la section 'Wallets'. Vous pouvez gérer plusieurs devises (EUR, USD, MAD, GBP) dans un seul portefeuille.",
            "atm": "🏧 Trouvez un ATM partenaire près de vous sur la page 'Find ATMs'. Nous avons plus de 1000 distributeurs partenaires au Maroc avec accès 24/7.",
            "bénéficiaire": "👥 Pour ajouter un bénéficiaire, allez dans 'Bénéficiaires' et cliquez sur 'Ajouter'. Renseignez le nom, la banque et l'IBAN du destinataire.",
            "api": "🔌 L'API SarfX permet aux banques partenaires d'intégrer nos services de conversion. Contactez votre administrateur pour les credentials API.",
            "frais": "💰 SarfX applique des frais transparents de 0.5% sur les conversions. Aucun frais caché ! Consultez le détail avant chaque transaction.",
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
        # Patterns de données sensibles à masquer
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
        
    def generate_response(self, message, context=None):
        """
        Génère une réponse du chatbot avec sécurité renforcée
        
        Args:
            message (str): Message de l'utilisateur
            context (str): Contexte optionnel pour améliorer la réponse
            
        Returns:
            dict: Réponse avec 'success', 'response' ou 'error'
        """
        # SÉCURITÉ: Vérifier si le message demande des informations sensibles
        if self._is_sensitive_request(message):
            return {'success': True, 'response': self.security_response}
        
        # Vérifier si API key est configurée
        if not self.api_key:
            return self._get_fallback_response(message)
            
        try:
            # Construire le prompt avec contexte sécurisé
            secure_context = self.get_sarfx_context()
            
            # Ajouter des instructions de sécurité strictes
            security_instructions = """
            
RÈGLES DE SÉCURITÉ STRICTES (À RESPECTER ABSOLUMENT):
1. Ne JAMAIS divulguer de mots de passe, codes PIN, ou credentials
2. Ne JAMAIS afficher d'IBAN, numéros de carte bancaire ou CVV
3. Ne JAMAIS révéler de clés API, tokens ou secrets
4. Ne JAMAIS partager des données personnelles d'utilisateurs
5. Ne JAMAIS expliquer comment contourner la sécurité
6. Toujours rediriger vers le support pour les questions sensibles
7. Réponses générales et éducatives uniquement
8. En cas de doute, répondre de manière générique"""
            
            full_context = secure_context + security_instructions
            
            prompt = f"{full_context}\n\nQuestion utilisateur: {message}\n\nRéponds de manière utile, concise et sécurisée:"
            
            # Préparer la requête
            headers = {
                'Content-Type': 'application/json',
                'X-goog-api-key': self.api_key
            }
            
            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "safetySettings": [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
                ]
            }
            
            # Faire la requête
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            
            # Si erreur API (403, 429, etc.), utiliser fallback
            if response.status_code != 200:
                print(f"Gemini API error: {response.status_code} - {response.text[:200]}")
                return self._get_fallback_response(message)
            
            # Extraire la réponse
            result = response.json()
            
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    text = candidate['content']['parts'][0].get('text', '')
                    # SÉCURITÉ: Sanitiser la réponse avant de l'envoyer
                    sanitized_text = self._sanitize_response(text)
                    return {
                        'success': True,
                        'response': sanitized_text
                    }
            
            return self._get_fallback_response(message)
            
        except requests.exceptions.RequestException as e:
            print(f"Chatbot connection error: {e}")
            return self._get_fallback_response(message)
        except Exception as e:
            print(f"Chatbot error: {e}")
            return self._get_fallback_response(message)
    
    def _get_fallback_response(self, message):
        """Retourne une réponse intelligente basée sur des mots-clés"""
        message_lower = message.lower()
        
        for keyword, response in self.fallback_responses.items():
            if keyword != "default" and keyword in message_lower:
                return {'success': True, 'response': response}
        
        # Vérifier d'autres mots-clés courants
        if any(word in message_lower for word in ['change', 'conversion', 'euro', 'dollar', 'dirham']):
            return {'success': True, 'response': self.fallback_responses['taux']}
        if any(word in message_lower for word in ['portefeuille', 'solde', 'balance']):
            return {'success': True, 'response': self.fallback_responses['wallet']}
        if any(word in message_lower for word in ['distributeur', 'retrait', 'cash']):
            return {'success': True, 'response': self.fallback_responses['atm']}
        if any(word in message_lower for word in ['transfert', 'envoyer', 'destinataire']):
            return {'success': True, 'response': self.fallback_responses['bénéficiaire']}
        if any(word in message_lower for word in ['commission', 'coût', 'prix']):
            return {'success': True, 'response': self.fallback_responses['frais']}
        
        return {'success': True, 'response': self.fallback_responses['default']}
    
    def get_sarfx_context(self):
        """Retourne le contexte SarfX pour le chatbot"""
        return """Tu es un assistant virtuel de SarfX, une plateforme fintech de conversion de devises et de gestion de portefeuilles multi-devises.
        
SarfX propose:
- Conversion de devises en temps réel (USD, EUR, MAD, GBP, CHF)
- Gestion de portefeuilles multi-devises
- Localisation de distributeurs automatiques (ATM)
- Gestion de bénéficiaires pour les transferts
- Accès API pour les banques partenaires
- Tableau de bord admin pour la gestion

Rôles utilisateurs:
- User: Utilisateur standard avec accès aux conversions et wallets
- Bank User: Utilisateur associé à une banque avec accès aux paramètres de la banque
- Admin: Administrateur système avec accès complet
- Admin SR Bank: Administrateur senior de banque
- Admin Associate Bank: Administrateur associé de banque avec contrôle des APIs

Réponds aux questions des utilisateurs de manière claire, concise et professionnelle en français."""

    def get_suggestions(self, db=None, user=None):
        """Retourne des suggestions personnalisées basées sur la DB et l'utilisateur"""
        suggestions = self.suggestions.copy()
        
        if db and user:
            try:
                # Suggestions basées sur le rôle
                role = user.get('role', 'user')
                if role in ['admin', 'admin_sr_bank']:
                    suggestions.extend([
                        "Comment gérer les utilisateurs ?",
                        "Comment voir les statistiques ?",
                        "Comment ajouter un ATM ?"
                    ])
                elif role in ['admin_associate_bank', 'bank_user']:
                    suggestions.extend([
                        "Comment configurer l'API de ma banque ?",
                        "Comment voir les transactions de ma banque ?"
                    ])
                    
                # Suggestions basées sur les données récentes
                if 'transactions' in db.list_collection_names():
                    tx_count = db.transactions.count_documents({"user_id": str(user.get('_id'))})
                    if tx_count == 0:
                        suggestions.append("Comment effectuer ma première transaction ?")
                        
            except Exception:
                pass
                
        return suggestions[:6]  # Limiter à 6 suggestions

# Instance globale du service
chatbot_service = ChatbotService()
