/**
 * SarfX Notification System
 * Gestion des notifications en temps réel
 */

class SarfXNotifications {
    constructor() {
        this.notifications = [];
        this.unreadCount = 0;
        this.container = null;
        this.bellBtn = null;
        this.panel = null;
        this.init();
    }

    init() {
        // Créer le conteneur de notifications
        this.createUI();
        
        // Demander la permission pour les notifications push
        this.requestNotificationPermission();
        
        // Charger les notifications existantes
        this.loadNotifications();
        
        // Écouter les événements
        this.attachEvents();
        
        // Vérifier périodiquement les nouvelles notifications
        setInterval(() => this.checkForNewNotifications(), 30000);
    }

    createUI() {
        // Créer le bouton de notification dans le header
        const notifHTML = `
            <div class="sarfx-notif-wrapper" id="sarfx-notifications">
                <button class="sarfx-notif-bell" id="notif-bell">
                    <i data-lucide="bell" class="w-5 h-5"></i>
                    <span class="sarfx-notif-badge" id="notif-badge" style="display: none;">0</span>
                </button>
                
                <div class="sarfx-notif-panel" id="notif-panel" style="display: none;">
                    <div class="sarfx-notif-header">
                        <h3>Notifications</h3>
                        <button id="mark-all-read" class="sarfx-notif-action">Tout marquer lu</button>
                    </div>
                    <div class="sarfx-notif-list" id="notif-list">
                        <div class="sarfx-notif-empty">
                            <i data-lucide="bell-off" class="w-8 h-8 mb-2 opacity-50"></i>
                            <p>Aucune notification</p>
                        </div>
                    </div>
                    <div class="sarfx-notif-footer">
                        <a href="/notifications">Voir toutes les notifications</a>
                    </div>
                </div>
            </div>
        `;

        // Injecter les styles
        this.injectStyles();

        // Ajouter dans le DOM (après le logo dans la sidebar ou dans le header)
        const sidebar = document.querySelector('.wise-sidebar-logo');
        if (sidebar) {
            sidebar.insertAdjacentHTML('afterend', notifHTML);
        } else {
            document.body.insertAdjacentHTML('afterbegin', `<div style="position: fixed; top: 20px; right: 80px; z-index: 9998;">${notifHTML}</div>`);
        }

        this.bellBtn = document.getElementById('notif-bell');
        this.panel = document.getElementById('notif-panel');
        
        // Réinitialiser les icônes
        if (window.lucide) {
            setTimeout(() => lucide.createIcons(), 100);
        }
    }

    injectStyles() {
        const styles = `
            <style>
                .sarfx-notif-wrapper {
                    position: relative;
                    margin: 10px 16px;
                }

                .sarfx-notif-bell {
                    position: relative;
                    width: 40px;
                    height: 40px;
                    border-radius: 10px;
                    background: var(--bg-secondary);
                    border: 1px solid var(--border-color);
                    color: var(--text-secondary);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .sarfx-notif-bell:hover {
                    background: var(--primary);
                    color: white;
                    border-color: var(--primary);
                }

                .sarfx-notif-badge {
                    position: absolute;
                    top: -4px;
                    right: -4px;
                    min-width: 18px;
                    height: 18px;
                    background: #ef4444;
                    color: white;
                    font-size: 11px;
                    font-weight: 600;
                    border-radius: 9px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 0 4px;
                    animation: pulse 2s infinite;
                }

                @keyframes pulse {
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.1); }
                }

                .sarfx-notif-panel {
                    position: absolute;
                    top: calc(100% + 8px);
                    left: 0;
                    width: 340px;
                    max-height: 450px;
                    background: var(--bg-primary);
                    border: 1px solid var(--border-color);
                    border-radius: 12px;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
                    overflow: hidden;
                    z-index: 1000;
                    animation: slideDown 0.2s ease;
                }

                @keyframes slideDown {
                    from {
                        opacity: 0;
                        transform: translateY(-10px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                .sarfx-notif-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 12px 16px;
                    border-bottom: 1px solid var(--border-color);
                }

                .sarfx-notif-header h3 {
                    font-size: 14px;
                    font-weight: 600;
                    margin: 0;
                }

                .sarfx-notif-action {
                    background: none;
                    border: none;
                    color: var(--primary);
                    font-size: 12px;
                    cursor: pointer;
                }

                .sarfx-notif-action:hover {
                    text-decoration: underline;
                }

                .sarfx-notif-list {
                    max-height: 350px;
                    overflow-y: auto;
                }

                .sarfx-notif-item {
                    display: flex;
                    gap: 12px;
                    padding: 12px 16px;
                    border-bottom: 1px solid var(--border-color);
                    cursor: pointer;
                    transition: background 0.2s;
                }

                .sarfx-notif-item:hover {
                    background: var(--bg-secondary);
                }

                .sarfx-notif-item.unread {
                    background: rgba(102, 126, 234, 0.05);
                }

                .sarfx-notif-icon {
                    width: 40px;
                    height: 40px;
                    border-radius: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-shrink: 0;
                }

                .sarfx-notif-icon.success { background: rgba(34, 197, 94, 0.1); color: #22c55e; }
                .sarfx-notif-icon.warning { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
                .sarfx-notif-icon.info { background: rgba(102, 126, 234, 0.1); color: #667eea; }
                .sarfx-notif-icon.error { background: rgba(239, 68, 68, 0.1); color: #ef4444; }

                .sarfx-notif-content {
                    flex: 1;
                    min-width: 0;
                }

                .sarfx-notif-title {
                    font-size: 13px;
                    font-weight: 500;
                    margin-bottom: 2px;
                    color: var(--text-primary);
                }

                .sarfx-notif-text {
                    font-size: 12px;
                    color: var(--text-secondary);
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }

                .sarfx-notif-time {
                    font-size: 11px;
                    color: var(--text-muted);
                    margin-top: 4px;
                }

                .sarfx-notif-empty {
                    padding: 40px 20px;
                    text-align: center;
                    color: var(--text-secondary);
                }

                .sarfx-notif-footer {
                    padding: 12px 16px;
                    text-align: center;
                    border-top: 1px solid var(--border-color);
                }

                .sarfx-notif-footer a {
                    color: var(--primary);
                    font-size: 13px;
                    text-decoration: none;
                }

                .sarfx-notif-footer a:hover {
                    text-decoration: underline;
                }

                @media (max-width: 768px) {
                    .sarfx-notif-panel {
                        position: fixed;
                        top: auto;
                        bottom: 70px;
                        left: 10px;
                        right: 10px;
                        width: auto;
                    }
                }
            </style>
        `;

        document.head.insertAdjacentHTML('beforeend', styles);
    }

    attachEvents() {
        if (this.bellBtn) {
            this.bellBtn.addEventListener('click', () => this.togglePanel());
        }

        // Fermer le panel en cliquant en dehors
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#sarfx-notifications')) {
                this.closePanel();
            }
        });

        // Marquer tout comme lu
        document.getElementById('mark-all-read')?.addEventListener('click', () => {
            this.markAllAsRead();
        });
    }

    togglePanel() {
        if (this.panel.style.display === 'none') {
            this.panel.style.display = 'block';
            if (window.lucide) {
                setTimeout(() => lucide.createIcons(), 100);
            }
        } else {
            this.closePanel();
        }
    }

    closePanel() {
        if (this.panel) {
            this.panel.style.display = 'none';
        }
    }

    async loadNotifications() {
        try {
            const response = await fetch('/api/notifications');
            const data = await response.json();
            
            if (data.success && data.notifications) {
                this.notifications = data.notifications;
                this.renderNotifications();
            }
        } catch (error) {
            // Utiliser des notifications mockées
            this.notifications = this.getMockNotifications();
            this.renderNotifications();
        }
    }

    getMockNotifications() {
        return [
            {
                id: '1',
                type: 'success',
                title: 'Transaction réussie',
                message: 'Votre échange de 500 USD vers MAD a été effectué',
                time: new Date(Date.now() - 10 * 60000).toISOString(),
                read: false
            },
            {
                id: '2',
                type: 'info',
                title: 'Taux favorable',
                message: 'Le taux USD/MAD a atteint 10.15, un plus haut de 7 jours',
                time: new Date(Date.now() - 30 * 60000).toISOString(),
                read: false
            },
            {
                id: '3',
                type: 'warning',
                title: 'Vérification requise',
                message: 'Veuillez compléter votre profil pour des limites plus élevées',
                time: new Date(Date.now() - 2 * 3600000).toISOString(),
                read: true
            }
        ];
    }

    renderNotifications() {
        const list = document.getElementById('notif-list');
        if (!list) return;

        this.unreadCount = this.notifications.filter(n => !n.read).length;
        this.updateBadge();

        if (this.notifications.length === 0) {
            list.innerHTML = `
                <div class="sarfx-notif-empty">
                    <i data-lucide="bell-off" class="w-8 h-8 mb-2 opacity-50"></i>
                    <p>Aucune notification</p>
                </div>
            `;
        } else {
            list.innerHTML = this.notifications.map(n => this.renderNotificationItem(n)).join('');
        }

        if (window.lucide) {
            setTimeout(() => lucide.createIcons(), 100);
        }
    }

    renderNotificationItem(notif) {
        const icons = {
            success: 'check-circle',
            warning: 'alert-triangle',
            info: 'info',
            error: 'x-circle'
        };

        const timeAgo = this.getTimeAgo(new Date(notif.time));

        return `
            <div class="sarfx-notif-item ${notif.read ? '' : 'unread'}" data-id="${notif.id}" onclick="window.sarfxNotifications.markAsRead('${notif.id}')">
                <div class="sarfx-notif-icon ${notif.type}">
                    <i data-lucide="${icons[notif.type] || 'bell'}" class="w-5 h-5"></i>
                </div>
                <div class="sarfx-notif-content">
                    <div class="sarfx-notif-title">${notif.title}</div>
                    <div class="sarfx-notif-text">${notif.message}</div>
                    <div class="sarfx-notif-time">${timeAgo}</div>
                </div>
            </div>
        `;
    }

    getTimeAgo(date) {
        const seconds = Math.floor((new Date() - date) / 1000);
        
        if (seconds < 60) return 'À l\'instant';
        if (seconds < 3600) return `Il y a ${Math.floor(seconds / 60)} min`;
        if (seconds < 86400) return `Il y a ${Math.floor(seconds / 3600)} h`;
        if (seconds < 604800) return `Il y a ${Math.floor(seconds / 86400)} j`;
        
        return date.toLocaleDateString('fr-FR');
    }

    updateBadge() {
        const badge = document.getElementById('notif-badge');
        if (badge) {
            if (this.unreadCount > 0) {
                badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
    }

    async markAsRead(id) {
        const notif = this.notifications.find(n => n.id === id);
        if (notif && !notif.read) {
            notif.read = true;
            this.renderNotifications();
            
            // Sync avec le serveur
            try {
                await fetch(`/api/notifications/${id}/read`, { method: 'POST' });
            } catch (error) {
                console.log('Notification sync skipped');
            }
        }
    }

    markAllAsRead() {
        this.notifications.forEach(n => n.read = true);
        this.renderNotifications();
        
        // Sync avec le serveur
        try {
            fetch('/api/notifications/read-all', { method: 'POST' });
        } catch (error) {
            console.log('Notifications sync skipped');
        }
    }

    async checkForNewNotifications() {
        try {
            const response = await fetch('/api/notifications/check');
            const data = await response.json();
            
            if (data.hasNew) {
                this.loadNotifications();
                this.showPushNotification(data.latest);
            }
        } catch (error) {
            // Silently fail
        }
    }

    async requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            try {
                await Notification.requestPermission();
            } catch (error) {
                console.log('Notification permission denied');
            }
        }
    }

    showPushNotification(notif) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(notif.title, {
                body: notif.message,
                icon: '/static/images/icons/notification.png',
                badge: '/static/images/icons/badge.png'
            });
        }
    }

    // Public method to add notifications programmatically
    addNotification(type, title, message) {
        const notif = {
            id: Date.now().toString(),
            type,
            title,
            message,
            time: new Date().toISOString(),
            read: false
        };
        
        this.notifications.unshift(notif);
        this.renderNotifications();
        
        // Show in-app toast
        if (window.showNotification) {
            window.showNotification(message, type);
        }
        
        // Show push notification
        this.showPushNotification(notif);
    }
}

// Initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.sarfxNotifications = new SarfXNotifications();
    });
} else {
    window.sarfxNotifications = new SarfXNotifications();
}
