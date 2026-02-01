"""
SarfX Rate Alert Service
Service pour la gestion des alertes de taux de change
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from bson import ObjectId
import uuid
import logging

logger = logging.getLogger(__name__)


class RateAlertService:
    """Service de gestion des alertes de taux de change"""

    # Types d'alertes supportés
    ALERT_TYPES = {
        'above': 'Au-dessus de',
        'below': 'En-dessous de',
        'change_percent': 'Variation de %',
        'daily_summary': 'Résumé quotidien'
    }

    # Statuts des alertes
    ALERT_STATUSES = {
        'active': 'Actif',
        'triggered': 'Déclenché',
        'paused': 'En pause',
        'expired': 'Expiré',
        'deleted': 'Supprimé'
    }

    # Paires de devises populaires
    POPULAR_PAIRS = [
        ('EUR', 'MAD'),
        ('USD', 'MAD'),
        ('GBP', 'MAD'),
        ('EUR', 'USD'),
        ('CAD', 'MAD'),
        ('CHF', 'MAD'),
        ('AED', 'MAD'),
        ('SAR', 'MAD')
    ]

    def __init__(self):
        pass

    @property
    def db(self):
        """Obtient une connexion DB fraîche à chaque accès"""
        from app.services.db_service import get_db
        return get_db()

    # ==================== CRUD Operations ====================

    def create_alert(
        self,
        user_id: str,
        from_currency: str,
        to_currency: str,
        alert_type: str,
        target_rate: float,
        notification_channels: List[str] = None,
        expiry_date: datetime = None,
        name: str = None,
        notes: str = None
    ) -> Dict[str, Any]:
        """
        Créer une nouvelle alerte de taux

        Args:
            user_id: ID de l'utilisateur
            from_currency: Devise source (ex: EUR)
            to_currency: Devise cible (ex: MAD)
            alert_type: Type d'alerte (above, below, change_percent, daily_summary)
            target_rate: Taux cible ou pourcentage de variation
            notification_channels: Canaux de notification ['email', 'push', 'sms']
            expiry_date: Date d'expiration de l'alerte
            name: Nom personnalisé de l'alerte
            notes: Notes supplémentaires

        Returns:
            Dict avec success et alert_id ou error
        """
        db = self.db
        if db is None:
            return {"success": False, "error": "Database unavailable"}

        # Validation du type d'alerte
        if alert_type not in self.ALERT_TYPES:
            return {
                "success": False,
                "error": f"Type d'alerte invalide. Valeurs acceptées: {list(self.ALERT_TYPES.keys())}"
            }

        # Validation des devises
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return {"success": False, "error": "Les devises source et cible doivent être différentes"}

        # Vérifier limite d'alertes actives par utilisateur (max 20)
        active_count = db.rate_alerts.count_documents({
            "user_id": user_id,
            "status": "active"
        })

        if active_count >= 20:
            return {
                "success": False,
                "error": "Limite atteinte: maximum 20 alertes actives par utilisateur"
            }

        # Récupérer le taux actuel pour référence
        current_rate = self._get_current_rate(from_currency, to_currency)

        # Canaux de notification par défaut
        if notification_channels is None:
            notification_channels = ['email', 'push']

        # Créer l'alerte
        alert_id = str(uuid.uuid4())[:8].upper()

        alert = {
            "alert_id": alert_id,
            "user_id": user_id,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "pair": f"{from_currency}/{to_currency}",
            "alert_type": alert_type,
            "target_rate": float(target_rate),
            "current_rate_at_creation": current_rate,
            "notification_channels": notification_channels,
            "name": name or f"Alerte {from_currency}/{to_currency}",
            "notes": notes,
            "status": "active",
            "trigger_count": 0,
            "last_triggered": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "expiry_date": expiry_date,
            "is_recurring": alert_type == 'daily_summary',
            "metadata": {
                "created_from": "web",
                "user_agent": None
            }
        }

        db.rate_alerts.insert_one(alert)

        logger.info(f"Rate alert created: {alert_id} for user {user_id} - {from_currency}/{to_currency}")

        return {
            "success": True,
            "alert_id": alert_id,
            "message": f"Alerte créée avec succès pour {from_currency}/{to_currency}",
            "alert": self._format_alert(alert)
        }

    def get_user_alerts(
        self,
        user_id: str,
        status: str = None,
        pair: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """Récupère les alertes d'un utilisateur"""
        db = self.db
        if db is None:
            return []

        query = {"user_id": user_id}

        if status:
            query["status"] = status
        else:
            # Par défaut, exclure les alertes supprimées
            query["status"] = {"$ne": "deleted"}

        if pair:
            query["pair"] = pair.upper()

        alerts = list(db.rate_alerts.find(query)
                     .sort("created_at", -1)
                     .limit(limit))

        # Enrichir avec le taux actuel
        for alert in alerts:
            alert['current_rate'] = self._get_current_rate(
                alert['from_currency'],
                alert['to_currency']
            )

        return [self._format_alert(a) for a in alerts]

    def get_alert_by_id(self, user_id: str, alert_id: str) -> Optional[Dict]:
        """Récupère une alerte spécifique"""
        db = self.db
        if db is None:
            return None

        alert = db.rate_alerts.find_one({
            "alert_id": alert_id,
            "user_id": user_id
        })

        if alert:
            alert['current_rate'] = self._get_current_rate(
                alert['from_currency'],
                alert['to_currency']
            )
            return self._format_alert(alert)

        return None

    def update_alert(
        self,
        user_id: str,
        alert_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Met à jour une alerte existante"""
        db = self.db
        if db is None:
            return {"success": False, "error": "Database unavailable"}

        # Champs modifiables
        allowed_fields = [
            'target_rate', 'notification_channels', 'name',
            'notes', 'expiry_date', 'status'
        ]

        # Filtrer les champs autorisés
        safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}

        if not safe_updates:
            return {"success": False, "error": "Aucun champ valide à mettre à jour"}

        # Validation du status
        if 'status' in safe_updates and safe_updates['status'] not in ['active', 'paused']:
            return {"success": False, "error": "Statut invalide. Utilisez 'active' ou 'paused'"}

        safe_updates['updated_at'] = datetime.utcnow()

        result = db.rate_alerts.update_one(
            {"alert_id": alert_id, "user_id": user_id, "status": {"$ne": "deleted"}},
            {"$set": safe_updates}
        )

        if result.modified_count > 0:
            return {
                "success": True,
                "message": "Alerte mise à jour avec succès"
            }

        return {"success": False, "error": "Alerte non trouvée"}

    def delete_alert(self, user_id: str, alert_id: str) -> Dict[str, Any]:
        """Supprime (soft delete) une alerte"""
        db = self.db
        if db is None:
            return {"success": False, "error": "Database unavailable"}

        result = db.rate_alerts.update_one(
            {"alert_id": alert_id, "user_id": user_id},
            {"$set": {"status": "deleted", "deleted_at": datetime.utcnow()}}
        )

        if result.modified_count > 0:
            return {"success": True, "message": "Alerte supprimée"}

        return {"success": False, "error": "Alerte non trouvée"}

    def pause_alert(self, user_id: str, alert_id: str) -> Dict[str, Any]:
        """Met en pause une alerte"""
        return self.update_alert(user_id, alert_id, {"status": "paused"})

    def resume_alert(self, user_id: str, alert_id: str) -> Dict[str, Any]:
        """Réactive une alerte"""
        return self.update_alert(user_id, alert_id, {"status": "active"})

    # ==================== Alert Checking ====================

    def check_alerts(self) -> Dict[str, Any]:
        """
        Vérifie toutes les alertes actives et déclenche celles qui correspondent
        Cette méthode devrait être appelée périodiquement (ex: toutes les 5 minutes)
        """
        db = self.db
        if db is None:
            return {"success": False, "error": "Database unavailable"}

        now = datetime.utcnow()
        triggered_count = 0
        expired_count = 0

        # Récupérer toutes les alertes actives
        active_alerts = list(db.rate_alerts.find({"status": "active"}))

        for alert in active_alerts:
            # Vérifier expiration
            if alert.get('expiry_date') and alert['expiry_date'] < now:
                db.rate_alerts.update_one(
                    {"_id": alert["_id"]},
                    {"$set": {"status": "expired"}}
                )
                expired_count += 1
                continue

            # Récupérer le taux actuel
            current_rate = self._get_current_rate(
                alert['from_currency'],
                alert['to_currency']
            )

            if current_rate is None:
                continue

            # Vérifier si l'alerte doit être déclenchée
            should_trigger = self._should_trigger_alert(alert, current_rate)

            if should_trigger:
                self._trigger_alert(alert, current_rate)
                triggered_count += 1

        logger.info(f"Alert check completed: {triggered_count} triggered, {expired_count} expired")

        return {
            "success": True,
            "checked": len(active_alerts),
            "triggered": triggered_count,
            "expired": expired_count
        }

    def _should_trigger_alert(self, alert: Dict, current_rate: float) -> bool:
        """Détermine si une alerte doit être déclenchée"""
        alert_type = alert['alert_type']
        target = alert['target_rate']

        # Éviter les déclenchements multiples dans un court laps de temps
        if alert.get('last_triggered'):
            cooldown = timedelta(hours=1)  # Minimum 1h entre deux déclenchements
            if datetime.utcnow() - alert['last_triggered'] < cooldown:
                return False

        if alert_type == 'above':
            return current_rate >= target

        elif alert_type == 'below':
            return current_rate <= target

        elif alert_type == 'change_percent':
            # Calculer le changement par rapport au taux de création
            original_rate = alert.get('current_rate_at_creation', current_rate)
            if original_rate == 0:
                return False

            change_percent = abs((current_rate - original_rate) / original_rate) * 100
            return change_percent >= target

        elif alert_type == 'daily_summary':
            # Vérifier si le résumé quotidien n'a pas déjà été envoyé aujourd'hui
            if alert.get('last_triggered'):
                last = alert['last_triggered']
                today = datetime.utcnow().date()
                if last.date() == today:
                    return False
            return True

        return False

    def _trigger_alert(self, alert: Dict, current_rate: float):
        """Déclenche une alerte et envoie les notifications"""
        db = self.db
        if db is None:
            return

        now = datetime.utcnow()

        # Créer un enregistrement de déclenchement
        trigger_record = {
            "alert_id": alert['alert_id'],
            "user_id": alert['user_id'],
            "pair": alert['pair'],
            "target_rate": alert['target_rate'],
            "triggered_rate": current_rate,
            "alert_type": alert['alert_type'],
            "triggered_at": now
        }

        db.rate_alert_triggers.insert_one(trigger_record)

        # Mettre à jour l'alerte
        update_data = {
            "trigger_count": alert.get('trigger_count', 0) + 1,
            "last_triggered": now,
            "last_triggered_rate": current_rate
        }

        # Pour les alertes one-time (above/below), marquer comme triggered
        if alert['alert_type'] in ['above', 'below']:
            update_data['status'] = 'triggered'

        db.rate_alerts.update_one(
            {"_id": alert["_id"]},
            {"$set": update_data}
        )

        # Envoyer les notifications
        self._send_alert_notifications(alert, current_rate)

        logger.info(f"Alert triggered: {alert['alert_id']} - {alert['pair']} at {current_rate}")

    def _send_alert_notifications(self, alert: Dict, current_rate: float):
        """Envoie les notifications pour une alerte déclenchée"""
        db = self.db
        if db is None:
            return

        user = db.users.find_one({"_id": ObjectId(alert['user_id'])})
        if not user:
            return

        channels = alert.get('notification_channels', ['email', 'push'])

        # Préparer le message
        alert_type_label = self.ALERT_TYPES.get(alert['alert_type'], alert['alert_type'])

        if alert['alert_type'] == 'above':
            message = f"🔔 Le taux {alert['pair']} a atteint {current_rate:.4f} (cible: {alert['target_rate']:.4f})"
        elif alert['alert_type'] == 'below':
            message = f"🔔 Le taux {alert['pair']} est descendu à {current_rate:.4f} (cible: {alert['target_rate']:.4f})"
        elif alert['alert_type'] == 'change_percent':
            message = f"🔔 Le taux {alert['pair']} a varié de plus de {alert['target_rate']}% - Taux actuel: {current_rate:.4f}"
        else:
            message = f"📊 Résumé quotidien - {alert['pair']}: {current_rate:.4f}"

        # Créer une notification interne
        notification = {
            "user_id": alert['user_id'],
            "type": "rate_alert",
            "title": f"Alerte taux {alert['pair']}",
            "message": message,
            "data": {
                "alert_id": alert['alert_id'],
                "pair": alert['pair'],
                "current_rate": current_rate,
                "target_rate": alert['target_rate']
            },
            "is_read": False,
            "created_at": datetime.utcnow()
        }

        db.notifications.insert_one(notification)

        # Email
        if 'email' in channels and user.get('email'):
            try:
                from app.services.notification_service import NotificationService
                notif_service = NotificationService()
                notif_service.send_rate_alert_email(
                    user['email'],
                    user.get('name', 'Utilisateur'),
                    alert['pair'],
                    current_rate,
                    alert['target_rate'],
                    alert['alert_type']
                )
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")

        # Push notification
        if 'push' in channels:
            try:
                from app.services.notification_service import NotificationService
                notif_service = NotificationService()
                notif_service.send_push_notification(
                    alert['user_id'],
                    f"Alerte {alert['pair']}",
                    message
                )
            except Exception as e:
                logger.error(f"Failed to send push notification: {e}")

    # ==================== Statistics ====================

    def get_alert_statistics(self, user_id: str) -> Dict[str, Any]:
        """Récupère les statistiques des alertes d'un utilisateur"""
        db = self.db
        if db is None:
            return {}

        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]

        status_counts = {r['_id']: r['count'] for r in db.rate_alerts.aggregate(pipeline)}

        # Compter les déclenchements
        total_triggers = db.rate_alert_triggers.count_documents({"user_id": user_id})

        # Derniers déclenchements
        recent_triggers = list(db.rate_alert_triggers.find({"user_id": user_id})
                              .sort("triggered_at", -1)
                              .limit(5))

        # Paires les plus surveillées
        pair_pipeline = [
            {"$match": {"user_id": user_id, "status": {"$ne": "deleted"}}},
            {"$group": {
                "_id": "$pair",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]

        top_pairs = [r['_id'] for r in db.rate_alerts.aggregate(pair_pipeline)]

        return {
            "total": sum(status_counts.values()),
            "active": status_counts.get('active', 0),
            "triggered": status_counts.get('triggered', 0),
            "paused": status_counts.get('paused', 0),
            "expired": status_counts.get('expired', 0),
            "total_triggers": total_triggers,
            "top_pairs": top_pairs,
            "recent_triggers": [
                {
                    "pair": t['pair'],
                    "rate": t['triggered_rate'],
                    "triggered_at": t['triggered_at'].isoformat()
                }
                for t in recent_triggers
            ]
        }

    def get_trigger_history(
        self,
        user_id: str,
        alert_id: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """Récupère l'historique des déclenchements"""
        db = self.db
        if db is None:
            return []

        query = {"user_id": user_id}
        if alert_id:
            query["alert_id"] = alert_id

        triggers = list(db.rate_alert_triggers.find(query)
                       .sort("triggered_at", -1)
                       .limit(limit))

        return [
            {
                "id": str(t['_id']),
                "alert_id": t['alert_id'],
                "pair": t['pair'],
                "target_rate": t['target_rate'],
                "triggered_rate": t['triggered_rate'],
                "alert_type": t['alert_type'],
                "triggered_at": t['triggered_at'].isoformat()
            }
            for t in triggers
        ]

    # ==================== Helper Methods ====================

    def _get_current_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Récupère le taux de change actuel via exchange_service"""
        try:
            from app.services.exchange_service import get_live_rate
            rate_data = get_live_rate(from_currency, to_currency)

            if rate_data and rate_data.get('success') and 'rate' in rate_data:
                return rate_data['rate']
        except Exception as e:
            logger.error(f"Error getting rate {from_currency}/{to_currency}: {e}")

        # Fallback: taux par défaut
        default_rates = {
            ('EUR', 'MAD'): 10.82, ('USD', 'MAD'): 10.05, ('GBP', 'MAD'): 12.67,
            ('CHF', 'MAD'): 11.23, ('CAD', 'MAD'): 7.45, ('AED', 'MAD'): 2.74,
            ('SAR', 'MAD'): 2.68, ('EUR', 'USD'): 1.08, ('GBP', 'USD'): 1.26,
            ('MAD', 'EUR'): 0.092, ('MAD', 'USD'): 0.099, ('MAD', 'GBP'): 0.079
        }
        return default_rates.get((from_currency, to_currency))

    def _format_alert(self, alert: Dict) -> Dict:
        """Formate une alerte pour l'API"""
        return {
            "id": str(alert.get('_id', '')),
            "alert_id": alert.get('alert_id'),
            "from_currency": alert.get('from_currency'),
            "to_currency": alert.get('to_currency'),
            "pair": alert.get('pair'),
            "alert_type": alert.get('alert_type'),
            "alert_type_label": self.ALERT_TYPES.get(alert.get('alert_type'), ''),
            "target_rate": alert.get('target_rate'),
            "current_rate": alert.get('current_rate'),
            "current_rate_at_creation": alert.get('current_rate_at_creation'),
            "notification_channels": alert.get('notification_channels', []),
            "name": alert.get('name'),
            "notes": alert.get('notes'),
            "status": alert.get('status'),
            "status_label": self.ALERT_STATUSES.get(alert.get('status'), ''),
            "trigger_count": alert.get('trigger_count', 0),
            "last_triggered": alert.get('last_triggered').isoformat() if alert.get('last_triggered') else None,
            "last_triggered_rate": alert.get('last_triggered_rate'),
            "is_recurring": alert.get('is_recurring', False),
            "expiry_date": alert.get('expiry_date').isoformat() if alert.get('expiry_date') else None,
            "created_at": alert.get('created_at').isoformat() if alert.get('created_at') else None,
            "updated_at": alert.get('updated_at').isoformat() if alert.get('updated_at') else None
        }

    def get_popular_pairs(self) -> List[Dict]:
        """Récupère les paires populaires avec leurs taux actuels"""
        pairs = []

        for from_curr, to_curr in self.POPULAR_PAIRS:
            rate = self._get_current_rate(from_curr, to_curr)
            pairs.append({
                "from": from_curr,
                "to": to_curr,
                "pair": f"{from_curr}/{to_curr}",
                "rate": rate
            })

        return pairs

    def get_suggested_alerts(self, user_id: str) -> List[Dict]:
        """Suggère des alertes basées sur l'activité de l'utilisateur"""
        db = self.db
        if db is None:
            return []

        suggestions = []

        # Récupérer les devises des transactions récentes
        recent_transactions = list(db.transactions.find({"user_id": user_id})
                                  .sort("created_at", -1)
                                  .limit(20))

        currencies_used = set()
        for tx in recent_transactions:
            if tx.get('from_currency'):
                currencies_used.add(tx['from_currency'])
            if tx.get('to_currency'):
                currencies_used.add(tx['to_currency'])

        # Générer des suggestions
        for from_curr in currencies_used:
            for to_curr in ['MAD', 'EUR', 'USD']:
                if from_curr != to_curr:
                    current_rate = self._get_current_rate(from_curr, to_curr)
                    if current_rate:
                        # Suggérer une alerte -2% et +2%
                        suggestions.append({
                            "pair": f"{from_curr}/{to_curr}",
                            "from": from_curr,
                            "to": to_curr,
                            "current_rate": current_rate,
                            "suggested_type": "below",
                            "suggested_target": round(current_rate * 0.98, 4),
                            "reason": f"Alerte si le taux baisse de 2%"
                        })

        return suggestions[:5]  # Limiter à 5 suggestions


def get_rate_alert_service() -> RateAlertService:
    """Récupère une nouvelle instance du service Rate Alert"""
    return RateAlertService()