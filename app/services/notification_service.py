"""
Service de notifications push et in-app pour SarfX
Gère les notifications utilisateurs, admin et système
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from bson import ObjectId

logger = logging.getLogger(__name__)

# Configuration des notifications
NOTIFICATION_CONFIG = {
    "types": {
        "transaction": {"icon": "receipt", "color": "#22c55e", "priority": "normal"},
        "kyc": {"icon": "shield-check", "color": "#f59e0b", "priority": "high"},
        "security": {"icon": "shield-alert", "color": "#ef4444", "priority": "urgent"},
        "rate_alert": {"icon": "trending-up", "color": "#3b82f6", "priority": "normal"},
        "system": {"icon": "bell", "color": "#6366f1", "priority": "low"},
        "promo": {"icon": "gift", "color": "#ec4899", "priority": "low"},
        "wallet": {"icon": "wallet", "color": "#8b5cf6", "priority": "normal"},
    },
    "channels": ["in_app", "email", "push"],
    "retention_days": 30,
    "max_unread": 100,
}


def _get_db():
    """Helper pour obtenir la DB de manière sécurisée"""
    try:
        from app.services.db_service import get_db
        return get_db()
    except RuntimeError:
        # Hors contexte Flask
        return None


def _safe_object_id(id_str):
    """Helper pour convertir un ID en ObjectId de manière sécurisée"""
    try:
        from app.services.db_service import safe_object_id
        return safe_object_id(id_str)
    except RuntimeError:
        # Hors contexte Flask
        if isinstance(id_str, ObjectId):
            return id_str
        try:
            return ObjectId(str(id_str))
        except Exception:
            return None


class NotificationService:
    """Service de gestion des notifications"""

    def __init__(self, db=None):
        self.db = db or _get_db()

    def create_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: str = "system",
        data: Optional[Dict] = None,
        channels: Optional[List[str]] = None,
        action_url: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Crée une nouvelle notification pour un utilisateur

        Args:
            user_id: ID de l'utilisateur destinataire
            title: Titre de la notification
            message: Message de la notification
            notification_type: Type (transaction, kyc, security, etc.)
            data: Données additionnelles
            channels: Canaux de diffusion (in_app, email, push)
            action_url: URL d'action au clic
            expires_at: Date d'expiration
        """
        if self.db is None:
            return {"success": False, "error": "Database unavailable"}

        try:
            type_config = NOTIFICATION_CONFIG["types"].get(
                notification_type,
                NOTIFICATION_CONFIG["types"]["system"]
            )

            notification = {
                "user_id": user_id,
                "title": title,
                "message": message,
                "type": notification_type,
                "icon": type_config["icon"],
                "color": type_config["color"],
                "priority": type_config["priority"],
                "data": data or {},
                "channels": channels or ["in_app"],
                "action_url": action_url,
                "read": False,
                "read_at": None,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at or (datetime.utcnow() + timedelta(days=NOTIFICATION_CONFIG["retention_days"])),
            }

            result = self.db.notifications.insert_one(notification)
            notification_id = str(result.inserted_id)

            # Envoyer via les canaux appropriés
            if "push" in notification.get("channels", []):
                self._send_push_notification(user_id, notification)

            if "email" in notification.get("channels", []):
                self._send_email_notification(user_id, notification)

            return {
                "success": True,
                "notification_id": notification_id,
                "message": "Notification créée"
            }

        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return {"success": False, "error": str(e)}

    def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
        notification_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Récupère les notifications d'un utilisateur"""
        if self.db is None:
            return {"success": False, "notifications": [], "error": "Database unavailable"}

        try:
            query = {
                "user_id": user_id,
                "expires_at": {"$gt": datetime.utcnow()}
            }

            if unread_only:
                query["read"] = False

            if notification_type:
                query["type"] = notification_type

            notifications = list(
                self.db.notifications
                .find(query)
                .sort("created_at", -1)
                .skip(offset)
                .limit(limit)
            )

            # Compter les non lues
            unread_count = self.db.notifications.count_documents({
                "user_id": user_id,
                "read": False,
                "expires_at": {"$gt": datetime.utcnow()}
            })

            return {
                "success": True,
                "notifications": [
                    {
                        "id": str(n["_id"]),
                        "title": n.get("title"),
                        "message": n.get("message"),
                        "type": n.get("type"),
                        "icon": n.get("icon"),
                        "color": n.get("color"),
                        "priority": n.get("priority"),
                        "read": n.get("read", False),
                        "action_url": n.get("action_url"),
                        "created_at": n.get("created_at"),
                        "data": n.get("data", {}),
                    }
                    for n in notifications
                ],
                "unread_count": unread_count,
                "total": len(notifications)
            }

        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            return {"success": False, "notifications": [], "error": str(e)}

    def mark_as_read(self, notification_id: str, user_id: str) -> Dict[str, Any]:
        """Marque une notification comme lue"""
        if self.db is None:
            return {"success": False, "error": "Database unavailable"}

        try:
            result = self.db.notifications.update_one(
                {"_id": _safe_object_id(notification_id), "user_id": user_id},
                {"$set": {"read": True, "read_at": datetime.utcnow()}}
            )

            return {
                "success": result.modified_count > 0,
                "message": "Notification marquée comme lue" if result.modified_count > 0 else "Notification non trouvée"
            }

        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return {"success": False, "error": str(e)}

    def mark_all_as_read(self, user_id: str) -> Dict[str, Any]:
        """Marque toutes les notifications comme lues"""
        if self.db is None:
            return {"success": False, "error": "Database unavailable"}

        try:
            result = self.db.notifications.update_many(
                {"user_id": user_id, "read": False},
                {"$set": {"read": True, "read_at": datetime.utcnow()}}
            )

            return {
                "success": True,
                "count": result.modified_count,
                "message": f"{result.modified_count} notifications marquées comme lues"
            }

        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}")
            return {"success": False, "error": str(e)}

    def delete_notification(self, notification_id: str, user_id: str) -> Dict[str, Any]:
        """Supprime une notification"""
        if self.db is None:
            return {"success": False, "error": "Database unavailable"}

        try:
            result = self.db.notifications.delete_one(
                {"_id": _safe_object_id(notification_id), "user_id": user_id}
            )

            return {
                "success": result.deleted_count > 0,
                "message": "Notification supprimée" if result.deleted_count > 0 else "Notification non trouvée"
            }

        except Exception as e:
            logger.error(f"Error deleting notification: {e}")
            return {"success": False, "error": str(e)}

    def get_unread_count(self, user_id: str) -> int:
        """Récupère le nombre de notifications non lues"""
        if self.db is None:
            return 0

        try:
            return self.db.notifications.count_documents({
                "user_id": user_id,
                "read": False,
                "expires_at": {"$gt": datetime.utcnow()}
            })
        except Exception:
            return 0

    def _send_push_notification(self, user_id: str, notification: Dict):
        """Envoie une notification push (via Service Worker)"""
        try:
            # Récupérer les subscriptions push de l'utilisateur
            subscriptions = list(self.db.push_subscriptions.find({"user_id": user_id}))

            for sub in subscriptions:
                # Stocker dans une queue pour envoi batch
                self.db.push_queue.insert_one({
                    "subscription": sub.get("subscription"),
                    "payload": {
                        "title": notification.get("title"),
                        "body": notification.get("message"),
                        "icon": f"/static/images/icons/{notification.get('icon', 'bell')}.png",
                        "badge": "/static/images/badge.png",
                        "data": {
                            "url": notification.get("action_url", "/app/home"),
                            "type": notification.get("type")
                        }
                    },
                    "created_at": datetime.utcnow(),
                    "sent": False
                })

        except Exception as e:
            logger.error(f"Error queuing push notification: {e}")

    def _send_email_notification(self, user_id: str, notification: Dict):
        """Envoie une notification par email"""
        try:
            from app.services.email_service import send_email

            user = self.db.users.find_one({"_id": _safe_object_id(user_id)})
            if not user or not user.get("email"):
                return

            # Vérifier les préférences email de l'utilisateur
            preferences = user.get("notification_preferences", {})
            if not preferences.get("email_notifications", True):
                return

            send_email(
                user.get("email"),
                f"SarfX - {notification.get('title')}",
                notification.get("message")
            )

        except Exception as e:
            logger.error(f"Error sending email notification: {e}")

    def register_push_subscription(self, user_id: str, subscription: Dict) -> Dict[str, Any]:
        """Enregistre une subscription push pour un utilisateur"""
        if self.db is None:
            return {"success": False, "error": "Database unavailable"}

        try:
            # Vérifier si la subscription existe déjà
            existing = self.db.push_subscriptions.find_one({
                "user_id": user_id,
                "subscription.endpoint": subscription.get("endpoint")
            })

            if existing:
                return {"success": True, "message": "Subscription déjà enregistrée"}

            self.db.push_subscriptions.insert_one({
                "user_id": user_id,
                "subscription": subscription,
                "created_at": datetime.utcnow(),
                "last_used": datetime.utcnow()
            })

            return {"success": True, "message": "Subscription enregistrée"}

        except Exception as e:
            logger.error(f"Error registering push subscription: {e}")
            return {"success": False, "error": str(e)}

    def unregister_push_subscription(self, user_id: str, endpoint: str) -> Dict[str, Any]:
        """Supprime une subscription push"""
        if self.db is None:
            return {"success": False, "error": "Database unavailable"}

        try:
            result = self.db.push_subscriptions.delete_one({
                "user_id": user_id,
                "subscription.endpoint": endpoint
            })

            return {
                "success": result.deleted_count > 0,
                "message": "Subscription supprimée"
            }

        except Exception as e:
            logger.error(f"Error unregistering push subscription: {e}")
            return {"success": False, "error": str(e)}

    def update_preferences(self, user_id: str, preferences: Dict) -> Dict[str, Any]:
        """Met à jour les préférences de notification d'un utilisateur"""
        if self.db is None:
            return {"success": False, "error": "Database unavailable"}

        try:
            result = self.db.users.update_one(
                {"_id": _safe_object_id(user_id)},
                {"$set": {"notification_preferences": preferences}}
            )

            return {
                "success": result.modified_count > 0,
                "message": "Préférences mises à jour"
            }

        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
            return {"success": False, "error": str(e)}

    def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """Récupère les préférences de notification d'un utilisateur"""
        if self.db is None:
            return self._default_preferences()

        try:
            user = self.db.users.find_one({"_id": _safe_object_id(user_id)})
            if user:
                return user.get("notification_preferences", self._default_preferences())
            return self._default_preferences()

        except Exception:
            return self._default_preferences()

    def _default_preferences(self) -> Dict[str, Any]:
        """Retourne les préférences par défaut"""
        return {
            "email_notifications": True,
            "push_notifications": True,
            "transaction_alerts": True,
            "rate_alerts": True,
            "security_alerts": True,
            "marketing": False,
        }

    def cleanup_old_notifications(self) -> int:
        """Nettoie les anciennes notifications expirées"""
        if self.db is None:
            return 0

        try:
            result = self.db.notifications.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            return result.deleted_count
        except Exception:
            return 0

    # ========== NOTIFICATION TEMPLATES ==========

    def notify_transaction_complete(self, user_id: str, transaction: Dict):
        """Notification de transaction complète"""
        amount = transaction.get("amount", 0)
        from_curr = transaction.get("from_currency", "")
        to_curr = transaction.get("to_currency", "")

        return self.create_notification(
            user_id=user_id,
            title="Transaction réussie",
            message=f"Votre échange de {amount} {from_curr} vers {to_curr} a été effectué avec succès.",
            notification_type="transaction",
            data={"transaction_id": str(transaction.get("_id", ""))},
            action_url="/app/transactions",
            channels=["in_app", "push"]
        )

    def notify_kyc_status(self, user_id: str, status: str, document_type: str = None):
        """Notification de changement de statut KYC"""
        if status == "verified":
            title = "Document vérifié ✓"
            message = f"Votre {document_type or 'document'} a été vérifié avec succès."
        elif status == "rejected":
            title = "Document non validé"
            message = f"Votre {document_type or 'document'} n'a pas pu être validé. Veuillez soumettre un nouveau document."
        else:
            title = "Document en cours de vérification"
            message = "Votre document est en cours d'examen par notre équipe."

        return self.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type="kyc",
            action_url="/app/profile",
            channels=["in_app", "email", "push"]
        )

    def notify_rate_alert(self, user_id: str, pair: str, rate: float, change: float):
        """Notification d'alerte de taux"""
        direction = "↑" if change > 0 else "↓"
        change_text = f"+{change:.2f}%" if change > 0 else f"{change:.2f}%"

        return self.create_notification(
            user_id=user_id,
            title=f"Alerte taux {pair}",
            message=f"Le taux {pair} est maintenant à {rate:.4f} ({direction} {change_text})",
            notification_type="rate_alert",
            data={"pair": pair, "rate": rate, "change": change},
            action_url="/app/converter",
            channels=["in_app", "push"]
        )

    def notify_security_alert(self, user_id: str, event: str, details: str = None):
        """Notification de sécurité"""
        return self.create_notification(
            user_id=user_id,
            title="Alerte de sécurité",
            message=details or f"Événement de sécurité détecté: {event}",
            notification_type="security",
            data={"event": event},
            action_url="/app/settings",
            channels=["in_app", "email", "push"]
        )

    def notify_wallet_update(self, user_id: str, currency: str, amount: float, action: str):
        """Notification de mise à jour de wallet"""
        if action == "credit":
            title = "Crédit reçu"
            message = f"Votre wallet {currency} a été crédité de {amount} {currency}"
        else:
            title = "Débit effectué"
            message = f"{amount} {currency} ont été débités de votre wallet"

        return self.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type="wallet",
            data={"currency": currency, "amount": amount, "action": action},
            action_url="/app/wallets",
            channels=["in_app", "push"]
        )


# Instance singleton
_notification_service = None

def get_notification_service() -> NotificationService:
    """Récupère l'instance du service de notifications"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
