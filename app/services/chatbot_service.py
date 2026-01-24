"""Service de chatbot utilisant l'API Gemini de Google"""
import requests
import os
from flask import current_app

class ChatbotService:
    """Service pour interagir avec l'API Gemini"""
    
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
        
    def generate_response(self, message, context=None):
        """
        Génère une réponse du chatbot
        
        Args:
            message (str): Message de l'utilisateur
            context (str): Contexte optionnel pour améliorer la réponse
            
        Returns:
            dict: Réponse avec 'success', 'response' ou 'error'
        """
        # Vérifier si API key est configurée
        if not self.api_key:
            return self._get_fallback_response(message)
            
        try:
            # Construire le prompt avec contexte si fourni
            prompt = message
            if context:
                prompt = f"Contexte: {context}\n\nQuestion: {message}"
            
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
                    return {
                        'success': True,
                        'response': text
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
