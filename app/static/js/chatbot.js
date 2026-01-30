/**
 * Widget Chatbot SarfX - Intégration universelle
 * Avec support RBAC, Tools, Mémoire de conversation et Rate Limiting
 */

class SarfXChatbot {
    constructor(options = {}) {
        this.isOpen = false;
        this.messages = [];
        this.sessionId = null;
        this.context = options.context || this.detectContext();
        this.remainingRequests = null;
        this.init();
    }

    /**
     * Détecte automatiquement le contexte (landing, app, backoffice)
     */
    detectContext() {
        const path = window.location.pathname;
        if (path.includes('/admin') || path.includes('/backoffice')) {
            return 'backoffice';
        } else if (path.includes('/app') || path.includes('/dashboard') || path.includes('/wallets')) {
            return 'app';
        }
        return 'landing';
    }

    init() {
        // Créer le HTML du chatbot
        const chatbotHTML = `
            <div id="sarfx-chatbot" class="sarfx-chatbot">
                <div class="chatbot-toggle" id="chatbot-toggle">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                </div>
                
                <div class="chatbot-window" id="chatbot-window">
                    <div class="chatbot-header">
                        <div class="chatbot-header-info">
                            <h3>Assistant SarfX</h3>
                            <span class="chatbot-status" id="chatbot-status">En ligne</span>
                        </div>
                        <div class="chatbot-header-actions">
                            <button class="chatbot-clear" id="chatbot-clear" title="Nouvelle conversation">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M3 6h18"></path>
                                    <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                                </svg>
                            </button>
                            <button class="chatbot-close" id="chatbot-close">
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <line x1="18" y1="6" x2="6" y2="18"></line>
                                    <line x1="6" y1="6" x2="18" y2="18"></line>
                                </svg>
                            </button>
                        </div>
                    </div>
                    
                    <div class="chatbot-messages" id="chatbot-messages">
                        <div class="chatbot-message bot-message">
                            <div class="message-avatar">🤖</div>
                            <div class="message-content">
                                <p>Bonjour ! Je suis l'assistant virtuel de SarfX. Comment puis-je vous aider aujourd'hui ?</p>
                            </div>
                        </div>
                        <div class="chatbot-suggestions" id="chatbot-suggestions">
                            <p class="suggestions-title">Questions fréquentes :</p>
                            <div class="suggestions-list"></div>
                        </div>
                    </div>
                    
                    <div class="chatbot-input-area">
                        <input 
                            type="text" 
                            id="chatbot-input" 
                            class="chatbot-input" 
                            placeholder="Posez votre question..."
                            autocomplete="off"
                        />
                        <button class="chatbot-send" id="chatbot-send">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="22" y1="2" x2="11" y2="13"></line>
                                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Ajouter le chatbot au body
        document.body.insertAdjacentHTML('beforeend', chatbotHTML);

        // Ajouter les styles
        this.injectStyles();

        // Attacher les événements
        this.attachEvents();
    }

    injectStyles() {
        const styles = `
            <style>
                .sarfx-chatbot {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    z-index: 999;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                }
                
                /* Mobile: position chatbot above bottom nav */
                @media (max-width: 1023px) {
                    .sarfx-chatbot {
                        bottom: 90px;
                    }
                    
                    .chatbot-toggle {
                        width: 52px;
                        height: 52px;
                    }
                    
                    .chatbot-window {
                        width: calc(100vw - 24px);
                        max-width: 380px;
                        right: -8px;
                        height: calc(100vh - 180px);
                        max-height: 500px;
                        bottom: 70px;
                    }
                }
                
                @media (max-width: 480px) {
                    .sarfx-chatbot {
                        right: 12px;
                    }
                    
                    .chatbot-window {
                        right: -4px;
                        width: calc(100vw - 16px);
                    }
                }

                .chatbot-toggle {
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    transition: all 0.3s ease;
                }

                .chatbot-toggle:hover {
                    transform: scale(1.1);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.2);
                }

                .chatbot-window {
                    position: absolute;
                    bottom: 80px;
                    right: 0;
                    width: 380px;
                    height: 500px;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    display: none;
                    flex-direction: column;
                    overflow: hidden;
                }

                .chatbot-window.open {
                    display: flex;
                }

                .chatbot-header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 16px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }

                .chatbot-header-info h3 {
                    margin: 0;
                    font-size: 16px;
                    font-weight: 600;
                }

                .chatbot-status {
                    font-size: 12px;
                    opacity: 0.9;
                }

                .chatbot-close {
                    background: rgba(255,255,255,0.2);
                    border: none;
                    color: white;
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: background 0.2s;
                }

                .chatbot-close:hover {
                    background: rgba(255,255,255,0.3);
                }

                .chatbot-header-actions {
                    display: flex;
                    gap: 8px;
                }

                .chatbot-clear {
                    background: rgba(255,255,255,0.2);
                    border: none;
                    color: white;
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: background 0.2s;
                }

                .chatbot-clear:hover {
                    background: rgba(255,255,255,0.3);
                }

                .chatbot-messages {
                    flex: 1;
                    padding: 16px;
                    overflow-y: auto;
                    background: #f8f9fa;
                }

                .chatbot-message {
                    display: flex;
                    margin-bottom: 16px;
                    animation: slideIn 0.3s ease;
                }

                @keyframes slideIn {
                    from {
                        opacity: 0;
                        transform: translateY(10px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                .message-avatar {
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 18px;
                    margin-right: 8px;
                    flex-shrink: 0;
                }

                .message-content {
                    background: white;
                    padding: 10px 14px;
                    border-radius: 12px;
                    max-width: 70%;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                }

                .user-message {
                    flex-direction: row-reverse;
                }

                .user-message .message-avatar {
                    margin-right: 0;
                    margin-left: 8px;
                    background: #667eea;
                    color: white;
                }

                .user-message .message-content {
                    background: #667eea;
                    color: white;
                }

                .message-content p {
                    margin: 0;
                    font-size: 14px;
                    line-height: 1.5;
                }

                .chatbot-input-area {
                    display: flex;
                    padding: 12px;
                    background: white;
                    border-top: 1px solid #e9ecef;
                }

                .chatbot-input {
                    flex: 1;
                    border: 1px solid #dee2e6;
                    border-radius: 20px;
                    padding: 10px 16px;
                    font-size: 14px;
                    outline: none;
                    transition: border-color 0.2s;
                }

                .chatbot-input:focus {
                    border-color: #667eea;
                }

                .chatbot-suggestions {
                    margin-top: 8px;
                    padding: 10px;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                }

                .suggestions-title {
                    font-size: 12px;
                    color: #6c757d;
                    margin: 0 0 8px 0;
                    font-weight: 500;
                }

                .suggestions-list {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 6px;
                }

                .suggestion-btn {
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    border: 1px solid #dee2e6;
                    color: #495057;
                    padding: 6px 12px;
                    border-radius: 16px;
                    font-size: 12px;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .suggestion-btn:hover {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-color: transparent;
                }

                .chatbot-send {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border: none;
                    color: white;
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    margin-left: 8px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: transform 0.2s;
                }

                .chatbot-send:hover {
                    transform: scale(1.1);
                }

                .chatbot-send:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                .typing-indicator {
                    display: flex;
                    align-items: center;
                    padding: 10px 14px;
                    background: white;
                    border-radius: 12px;
                    width: fit-content;
                }

                .typing-indicator span {
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #667eea;
                    margin: 0 2px;
                    animation: typing 1.4s infinite;
                }

                .typing-indicator span:nth-child(2) {
                    animation-delay: 0.2s;
                }

                .typing-indicator span:nth-child(3) {
                    animation-delay: 0.4s;
                }

                @keyframes typing {
                    0%, 60%, 100% {
                        transform: translateY(0);
                    }
                    30% {
                        transform: translateY(-10px);
                    }
                }

                @media (max-width: 480px) {
                    .chatbot-window {
                        width: calc(100vw - 40px);
                        height: calc(100vh - 120px);
                    }
                }
            </style>
        `;

        document.head.insertAdjacentHTML('beforeend', styles);
    }

    attachEvents() {
        const toggle = document.getElementById('chatbot-toggle');
        const close = document.getElementById('chatbot-close');
        const clear = document.getElementById('chatbot-clear');
        const send = document.getElementById('chatbot-send');
        const input = document.getElementById('chatbot-input');

        toggle.addEventListener('click', () => this.toggleChat());
        close.addEventListener('click', () => this.toggleChat());
        clear.addEventListener('click', () => this.clearConversation());
        send.addEventListener('click', () => this.sendMessage());
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    toggleChat() {
        this.isOpen = !this.isOpen;
        const window = document.getElementById('chatbot-window');
        const toggle = document.getElementById('chatbot-toggle');
        
        if (this.isOpen) {
            window.classList.add('open');
            toggle.style.display = 'none';
            // Charger les suggestions avec contexte
            this.loadSuggestions();
        } else {
            window.classList.remove('open');
            toggle.style.display = 'flex';
        }
    }

    async clearConversation() {
        try {
            // Effacer côté serveur
            await fetch('/api/chatbot/history', { method: 'DELETE' });
            this.sessionId = null;
            
            // Effacer l'affichage
            const messagesContainer = document.getElementById('chatbot-messages');
            messagesContainer.innerHTML = `
                <div class="chatbot-message bot-message">
                    <div class="message-avatar">🤖</div>
                    <div class="message-content">
                        <p>Conversation effacée. Comment puis-je vous aider ?</p>
                    </div>
                </div>
                <div class="chatbot-suggestions" id="chatbot-suggestions">
                    <p class="suggestions-title">Questions fréquentes :</p>
                    <div class="suggestions-list"></div>
                </div>
            `;
            
            // Recharger les suggestions
            this.loadSuggestions();
        } catch (error) {
            console.log('Erreur lors de l\'effacement de la conversation');
        }
    }

    async loadSuggestions() {
        try {
            const response = await fetch(`/api/chatbot/suggestions?context=${this.context}`);
            const data = await response.json();
            
            if (data.success && data.suggestions) {
                const suggestionsContainer = document.querySelector('.suggestions-list');
                if (suggestionsContainer) {
                    suggestionsContainer.innerHTML = data.suggestions.map(s => 
                        `<button class="suggestion-btn" onclick="window.sarfxChatbot.useSuggestion('${this.escapeHtml(s)}')">${this.escapeHtml(s)}</button>`
                    ).join('');
                }
                
                // Mettre à jour le statut si info de rôle disponible
                if (data.user_role && data.user_role !== 'anonymous') {
                    const statusEl = document.getElementById('chatbot-status');
                    if (statusEl) {
                        statusEl.textContent = `Connecté (${data.user_role})`;
                    }
                }
            }
        } catch (error) {
            console.log('Impossible de charger les suggestions');
        }
    } 

    useSuggestion(text) {
        const input = document.getElementById('chatbot-input');
        input.value = text;
        // Masquer les suggestions après utilisation
        const suggestionsDiv = document.getElementById('chatbot-suggestions');
        if (suggestionsDiv) {
            suggestionsDiv.style.display = 'none';
        }
        this.sendMessage();
    }

    async sendMessage() {
        const input = document.getElementById('chatbot-input');
        const message = input.value.trim();
        
        if (!message) return;

        // Afficher le message de l'utilisateur
        this.addMessage(message, 'user');
        input.value = '';

        // Désactiver le bouton d'envoi
        const sendBtn = document.getElementById('chatbot-send');
        sendBtn.disabled = true;

        // Afficher l'indicateur de saisie
        this.showTypingIndicator();

        try {
            // Envoyer la requête à l'API avec contexte et session
            const response = await fetch('/api/chatbot/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    message,
                    context: this.context,
                    session_id: this.sessionId
                })
            });

            const data = await response.json();

            // Retirer l'indicateur de saisie
            this.hideTypingIndicator();

            // Gérer le rate limiting
            if (response.status === 429) {
                this.addMessage(data.response || `⏱️ Trop de requêtes. Réessayez dans ${data.retry_after || 60} secondes.`, 'bot');
                return;
            }

            // Mettre à jour la session ID
            if (data.session_id) {
                this.sessionId = data.session_id;
            }

            // Mettre à jour les requêtes restantes
            if (data.remaining_requests !== undefined) {
                this.remainingRequests = data.remaining_requests;
            }

            if (data.success) {
                this.addMessage(data.response, 'bot');
                
                // Si un tool a été utilisé, on peut afficher un badge
                if (data.tool_used) {
                    console.log(`Tool utilisé: ${data.tool_used}`);
                }
            } else {
                this.addMessage(data.response || 'Désolé, une erreur est survenue. Veuillez réessayer.', 'bot');
            }
        } catch (error) {
            this.hideTypingIndicator();
            this.addMessage('Erreur de connexion. Veuillez vérifier votre connexion internet.', 'bot');
        }

        // Réactiver le bouton d'envoi
        sendBtn.disabled = false;
    }

    addMessage(text, type) {
        const messagesContainer = document.getElementById('chatbot-messages');
        const messageClass = type === 'user' ? 'user-message' : 'bot-message';
        const avatar = type === 'user' ? '👤' : '🤖';

        const messageHTML = `
            <div class="chatbot-message ${messageClass}">
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">
                    <p>${this.escapeHtml(text)}</p>
                </div>
            </div>
        `;

        messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('chatbot-messages');
        const indicatorHTML = `
            <div class="chatbot-message bot-message" id="typing-indicator">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        `;
        messagesContainer.insertAdjacentHTML('beforeend', indicatorHTML);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialiser le chatbot automatiquement
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.sarfxChatbot = new SarfXChatbot();
    });
} else {
    window.sarfxChatbot = new SarfXChatbot();
}
