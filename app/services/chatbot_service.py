"""Service de chatbot utilisant l'API Gemini de Google"""
import requests
import os
from flask import current_app

class ChatbotService:
    """Service pour interagir avec l'API Gemini"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY', 'AIzaSyB5LeO-IZ2OHzec8XgxqVxXMgWMHOwQKag')
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
    def generate_response(self, message, context=None):
        """
        Génère une réponse du chatbot
        
        Args:
            message (str): Message de l'utilisateur
            context (str): Contexte optionnel pour améliorer la réponse
            
        Returns:
            dict: Réponse avec 'success', 'response' ou 'error'
        """
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
            response.raise_for_status()
            
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
            
            return {
                'success': False,
                'error': 'Aucune réponse générée'
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Erreur de connexion: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur: {str(e)}'
            }
    
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

Réponds aux questions des utilisateurs de manière claire, concise et professionnelle."""

# Instance globale du service
chatbot_service = ChatbotService()
