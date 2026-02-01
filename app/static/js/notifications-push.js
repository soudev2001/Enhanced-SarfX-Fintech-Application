/**
 * SarfX Notification Manager
 * Gère les notifications push, in-app et les préférences utilisateur
 */

class NotificationManager {
    constructor() {
        this.swRegistration = null;
        this.isSubscribed = false;
        this.notificationPermission = 'default';
        this.unreadCount = 0;
        this.notifications = [];
        this.pollInterval = null;

        // VAPID public key (à remplacer par votre clé)
        this.vapidPublicKey = 'BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U';
    }

    /**
     * Initialise le gestionnaire de notifications
     */
    async init() {
        console.log('[Notifications] Initializing...');

        // Vérifier le support des notifications
        if (!('Notification' in window)) {
            console.warn('[Notifications] Not supported in this browser');
            return;
        }

        this.notificationPermission = Notification.permission;

        // Enregistrer le Service Worker
        if ('serviceWorker' in navigator) {
            try {
                this.swRegistration = await navigator.serviceWorker.register('/static/js/sw.js');
                console.log('[Notifications] Service Worker registered');

                // Vérifier l'état de l'abonnement push
                await this.checkSubscription();
            } catch (error) {
                console.error('[Notifications] SW registration failed:', error);
            }
        }

        // Charger les notifications initiales
        await this.loadNotifications();

        // Démarrer le polling pour les nouvelles notifications
        this.startPolling();

        // Initialiser l'UI
        this.initUI();
    }

    /**
     * Initialise les éléments UI
     */
    initUI() {
        // Badge de notification dans le header
        this.updateBadge();

        // Bouton de notification
        const notifBtn = document.getElementById('notification-bell');
        if (notifBtn) {
            notifBtn.addEventListener('click', () => this.togglePanel());
        }

        // Panel de notifications
        this.createNotificationPanel();
    }

    /**
     * Crée le panneau de notifications
     */
    createNotificationPanel() {
        // Vérifier si le panneau existe déjà
        if (document.getElementById('notification-panel')) return;

        const panel = document.createElement('div');
        panel.id = 'notification-panel';
        panel.className = 'notification-panel';
        panel.innerHTML = `
            <div class="notification-panel-header">
                <h3>Notifications</h3>
                <div class="notification-panel-actions">
                    <button onclick="notificationManager.markAllAsRead()" class="btn-ghost-sm" title="Tout marquer comme lu">
                        <i data-lucide="check-check"></i>
                    </button>
                    <button onclick="notificationManager.togglePanel()" class="btn-ghost-sm" title="Fermer">
                        <i data-lucide="x"></i>
                    </button>
                </div>
            </div>
            <div class="notification-panel-body" id="notification-list">
                <div class="notification-loading">
                    <div class="spinner"></div>
                    <span>Chargement...</span>
                </div>
            </div>
            <div class="notification-panel-footer">
                <a href="/app/notifications" class="notification-view-all">
                    Voir toutes les notifications
                </a>
            </div>
        `;

        document.body.appendChild(panel);

        // Fermer le panneau en cliquant à l'extérieur
        document.addEventListener('click', (e) => {
            if (!panel.contains(e.target) && !e.target.closest('#notification-bell')) {
                panel.classList.remove('active');
            }
        });
    }

    /**
     * Toggle le panneau de notifications
     */
    togglePanel() {
        const panel = document.getElementById('notification-panel');
        if (panel) {
            panel.classList.toggle('active');

            if (panel.classList.contains('active')) {
                this.renderNotifications();

                // Réinitialiser les icônes Lucide
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            }
        }
    }

    /**
     * Charge les notifications depuis l'API
     */
    async loadNotifications() {
        try {
            const response = await fetch('/api/notifications?limit=20');
            const data = await response.json();

            if (data.success) {
                this.notifications = data.notifications || [];
                this.unreadCount = data.unread_count || 0;
                this.updateBadge();
            }
        } catch (error) {
            console.error('[Notifications] Error loading:', error);
        }
    }

    /**
     * Rend la liste des notifications
     */
    renderNotifications() {
        const container = document.getElementById('notification-list');
        if (!container) return;

        if (this.notifications.length === 0) {
            container.innerHTML = `
                <div class="notification-empty">
                    <i data-lucide="bell-off" style="width: 32px; height: 32px;"></i>
                    <p>Aucune notification</p>
                </div>
            `;
        } else {
            container.innerHTML = this.notifications.map(notif => `
                <div class="notification-item ${notif.read ? '' : 'unread'}"
                     data-id="${notif.id}"
                     onclick="notificationManager.handleNotificationClick('${notif.id}', '${notif.action_url || ''}')">
                    <div class="notification-icon" style="background: ${notif.color}20;">
                        <i data-lucide="${notif.icon}" style="width: 18px; height: 18px; color: ${notif.color};"></i>
                    </div>
                    <div class="notification-content">
                        <p class="notification-title">${notif.title}</p>
                        <p class="notification-message">${notif.message}</p>
                        <span class="notification-time">${this.formatTime(notif.created_at)}</span>
                    </div>
                    ${!notif.read ? '<span class="notification-dot"></span>' : ''}
                </div>
            `).join('');
        }

        // Réinitialiser les icônes Lucide
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    /**
     * Gère le clic sur une notification
     */
    async handleNotificationClick(notificationId, actionUrl) {
        // Marquer comme lu
        await this.markAsRead(notificationId);

        // Naviguer vers l'URL d'action si définie
        if (actionUrl && actionUrl !== '') {
            window.location.href = actionUrl;
        }
    }

    /**
     * Marque une notification comme lue
     */
    async markAsRead(notificationId) {
        try {
            const response = await fetch(`/api/notifications/${notificationId}/read`, {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                // Mettre à jour localement
                const notif = this.notifications.find(n => n.id === notificationId);
                if (notif) {
                    notif.read = true;
                    this.unreadCount = Math.max(0, this.unreadCount - 1);
                    this.updateBadge();
                    this.renderNotifications();
                }
            }
        } catch (error) {
            console.error('[Notifications] Error marking as read:', error);
        }
    }

    /**
     * Marque toutes les notifications comme lues
     */
    async markAllAsRead() {
        try {
            const response = await fetch('/api/notifications/read-all', {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                this.notifications.forEach(n => n.read = true);
                this.unreadCount = 0;
                this.updateBadge();
                this.renderNotifications();

                this.showToast('Toutes les notifications marquées comme lues', 'success');
            }
        } catch (error) {
            console.error('[Notifications] Error marking all as read:', error);
        }
    }

    /**
     * Met à jour le badge de notifications
     */
    updateBadge() {
        const badge = document.getElementById('notification-badge');
        if (badge) {
            if (this.unreadCount > 0) {
                badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        }
    }

    /**
     * Démarre le polling pour les nouvelles notifications
     */
    startPolling(interval = 30000) {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }

        this.pollInterval = setInterval(async () => {
            const prevCount = this.unreadCount;
            await this.loadNotifications();

            // Afficher une notification si nouvelles
            if (this.unreadCount > prevCount) {
                this.showToast('Nouvelle notification', 'info');
            }
        }, interval);
    }

    /**
     * Arrête le polling
     */
    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    /**
     * Vérifie l'abonnement push actuel
     */
    async checkSubscription() {
        if (!this.swRegistration) return;

        try {
            const subscription = await this.swRegistration.pushManager.getSubscription();
            this.isSubscribed = subscription !== null;
            console.log('[Notifications] Push subscription status:', this.isSubscribed);
        } catch (error) {
            console.error('[Notifications] Error checking subscription:', error);
        }
    }

    /**
     * Demande la permission pour les notifications
     */
    async requestPermission() {
        if (!('Notification' in window)) {
            return false;
        }

        try {
            const permission = await Notification.requestPermission();
            this.notificationPermission = permission;

            if (permission === 'granted') {
                await this.subscribeToPush();
                return true;
            }

            return false;
        } catch (error) {
            console.error('[Notifications] Error requesting permission:', error);
            return false;
        }
    }

    /**
     * S'abonne aux notifications push
     */
    async subscribeToPush() {
        if (!this.swRegistration) return;

        try {
            const subscription = await this.swRegistration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(this.vapidPublicKey)
            });

            // Envoyer la subscription au serveur
            const response = await fetch('/api/notifications/subscribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ subscription })
            });

            const data = await response.json();

            if (data.success) {
                this.isSubscribed = true;
                console.log('[Notifications] Successfully subscribed to push');
                this.showToast('Notifications push activées', 'success');
            }
        } catch (error) {
            console.error('[Notifications] Error subscribing to push:', error);
        }
    }

    /**
     * Se désabonne des notifications push
     */
    async unsubscribeFromPush() {
        if (!this.swRegistration) return;

        try {
            const subscription = await this.swRegistration.pushManager.getSubscription();

            if (subscription) {
                await subscription.unsubscribe();

                // Notifier le serveur
                await fetch('/api/notifications/unsubscribe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ endpoint: subscription.endpoint })
                });

                this.isSubscribed = false;
                console.log('[Notifications] Unsubscribed from push');
                this.showToast('Notifications push désactivées', 'info');
            }
        } catch (error) {
            console.error('[Notifications] Error unsubscribing:', error);
        }
    }

    /**
     * Affiche une notification in-app (toast)
     */
    showToast(message, type = 'info') {
        const existingToast = document.querySelector('.notif-toast');
        if (existingToast) existingToast.remove();

        const icons = {
            success: 'check-circle',
            error: 'x-circle',
            warning: 'alert-triangle',
            info: 'info'
        };

        const toast = document.createElement('div');
        toast.className = `notif-toast notif-toast-${type}`;
        toast.innerHTML = `
            <i data-lucide="${icons[type] || 'bell'}" style="width: 18px; height: 18px;"></i>
            <span>${message}</span>
        `;

        document.body.appendChild(toast);

        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }

        setTimeout(() => {
            toast.classList.add('hide');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /**
     * Formate le temps relatif
     */
    formatTime(dateStr) {
        if (!dateStr) return '';

        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 1) return 'À l\'instant';
        if (diffMins < 60) return `Il y a ${diffMins} min`;
        if (diffHours < 24) return `Il y a ${diffHours}h`;
        if (diffDays < 7) return `Il y a ${diffDays}j`;

        return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
    }

    /**
     * Convertit une clé VAPID base64 en Uint8Array
     */
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }

        return outputArray;
    }
}

// Instance globale
const notificationManager = new NotificationManager();

// Initialiser au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    notificationManager.init();
});

// Exporter pour utilisation globale
window.notificationManager = notificationManager;
