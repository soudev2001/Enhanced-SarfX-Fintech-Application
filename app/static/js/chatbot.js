/**
 * Widget Chatbot SarfX - Intégration universelle
 */

class SarfXChatbot {
    constructor() {
        this.isOpen = false;
        this.messages = [];
        this.init();
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
                            <span class="chatbot-status">En ligne</span>
                        </div>
                        <button class="chatbot-close" id="chatbot-close">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        </button>
                    </div>
                    
                    <div class="chatbot-messages" id="chatbot-messages">
                        <div class="chatbot-message bot-message">
                            <div class="message-avatar">🤖</div>
                            <div class="message-content">
                                <p>Bonjour ! Je suis l'assistant virtuel de SarfX. Comment puis-je vous aider aujourd'hui ?</p>
                            </div>
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
                    z-index: 9999;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
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
        const send = document.getElementById('chatbot-send');
        const input = document.getElementById('chatbot-input');

        toggle.addEventListener('click', () => this.toggleChat());
        close.addEventListener('click', () => this.toggleChat());
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
        } else {
            window.classList.remove('open');
            toggle.style.display = 'flex';
        }
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
            // Envoyer la requête à l'API
            const response = await fetch('/api/chatbot/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });

            const data = await response.json();

            // Retirer l'indicateur de saisie
            this.hideTypingIndicator();

            if (data.success) {
                this.addMessage(data.response, 'bot');
            } else {
                this.addMessage('Désolé, une erreur est survenue. Veuillez réessayer.', 'bot');
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
        new SarfXChatbot();
    });
} else {
    new SarfXChatbot();
}
