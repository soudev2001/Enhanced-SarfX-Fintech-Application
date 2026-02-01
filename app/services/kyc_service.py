"""
Service de vérification KYC (Know Your Customer) automatique
Gère la validation des documents d'identité et la vérification des utilisateurs
"""
import os
import re
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from bson import ObjectId

from app.services.db_service import get_db, safe_object_id
from app.services.email_service import send_email

logger = logging.getLogger(__name__)

# Configuration KYC
KYC_CONFIG = {
    "allowed_extensions": {"pdf", "jpg", "jpeg", "png", "webp"},
    "max_file_size_mb": 10,
    "document_types": {
        "id_card": {"name": "Carte d'identité", "required": True},
        "passport": {"name": "Passeport", "required": False},
        "proof_of_address": {"name": "Justificatif de domicile", "required": True},
        "selfie": {"name": "Selfie avec document", "required": False},
    },
    "verification_levels": {
        "basic": {"documents": ["id_card"], "limits": {"daily": 1000, "monthly": 5000}},
        "standard": {"documents": ["id_card", "proof_of_address"], "limits": {"daily": 5000, "monthly": 25000}},
        "premium": {"documents": ["id_card", "proof_of_address", "selfie"], "limits": {"daily": 50000, "monthly": 200000}},
    },
    "auto_verification_enabled": True,
    "expiry_days": 365,  # Documents expire après 1 an
}


class KYCService:
    """Service de gestion KYC"""

    def __init__(self):
        self._db = None

    @property
    def db(self):
        """Obtient une connexion DB fraîche à chaque accès"""
        if self._db is not None:
            return self._db
        return get_db()

    def get_user_kyc_status(self, user_id: str) -> Dict[str, Any]:
        """Récupère le statut KYC complet d'un utilisateur"""
        if self.db is None:
            return {"error": "Database unavailable", "status": "unknown"}

        try:
            user = self.db.users.find_one({"_id": safe_object_id(user_id)})
            if not user:
                return {"error": "User not found", "status": "unknown"}

            # Récupérer les documents KYC
            documents = list(self.db.kyc_documents.find({"user_id": user_id}))

            # Calculer le niveau de vérification
            verified_docs = [d for d in documents if d.get("status") == "verified"]
            doc_types = set(d.get("document_type") for d in verified_docs)

            level = self._calculate_verification_level(doc_types)
            limits = KYC_CONFIG["verification_levels"].get(level, {}).get("limits", {})

            # Vérifier l'expiration
            has_expired = any(
                d.get("expires_at") and d["expires_at"] < datetime.utcnow()
                for d in verified_docs
            )

            return {
                "user_id": user_id,
                "status": user.get("kyc_status", "not_started"),
                "level": level,
                "verified": user.get("kyc_verified", False),
                "verified_at": user.get("kyc_verified_at"),
                "documents": [
                    {
                        "id": str(d["_id"]),
                        "type": d.get("document_type"),
                        "type_name": KYC_CONFIG["document_types"].get(d.get("document_type"), {}).get("name", "Document"),
                        "status": d.get("status"),
                        "uploaded_at": d.get("uploaded_at"),
                        "verified_at": d.get("verified_at"),
                        "expires_at": d.get("expires_at"),
                        "rejection_reason": d.get("rejection_reason"),
                    }
                    for d in documents
                ],
                "documents_count": len(documents),
                "verified_count": len(verified_docs),
                "pending_count": len([d for d in documents if d.get("status") == "pending"]),
                "has_expired_docs": has_expired,
                "limits": limits,
                "required_documents": self._get_required_documents(level),
                "next_level_requirements": self._get_next_level_requirements(level),
            }

        except Exception as e:
            logger.error(f"Error getting KYC status: {e}")
            return {"error": str(e), "status": "error"}

    def _calculate_verification_level(self, doc_types: set) -> str:
        """Calcule le niveau de vérification basé sur les documents vérifiés"""
        if {"id_card", "proof_of_address", "selfie"}.issubset(doc_types):
            return "premium"
        elif {"id_card", "proof_of_address"}.issubset(doc_types):
            return "standard"
        elif "id_card" in doc_types:
            return "basic"
        return "none"

    def _get_required_documents(self, level: str) -> List[Dict]:
        """Retourne la liste des documents requis pour un niveau"""
        required = []
        for doc_type, config in KYC_CONFIG["document_types"].items():
            required.append({
                "type": doc_type,
                "name": config["name"],
                "required": config["required"],
            })
        return required

    def _get_next_level_requirements(self, current_level: str) -> Optional[Dict]:
        """Retourne les exigences pour le niveau suivant"""
        levels = ["none", "basic", "standard", "premium"]
        try:
            current_idx = levels.index(current_level)
            if current_idx < len(levels) - 1:
                next_level = levels[current_idx + 1]
                return {
                    "level": next_level,
                    "documents": KYC_CONFIG["verification_levels"].get(next_level, {}).get("documents", []),
                    "limits": KYC_CONFIG["verification_levels"].get(next_level, {}).get("limits", {}),
                }
        except ValueError:
            pass
        return None

    def upload_document(self, user_id: str, document_type: str, file_data: Dict) -> Dict[str, Any]:
        """
        Enregistre un document KYC uploadé

        Args:
            user_id: ID de l'utilisateur
            document_type: Type de document (id_card, passport, etc.)
            file_data: Données du fichier (filename, content_type, file_path, file_hash)
        """
        if self.db is None:
            return {"success": False, "error": "Database unavailable"}

        try:
            # Valider le type de document
            if document_type not in KYC_CONFIG["document_types"]:
                return {"success": False, "error": f"Type de document invalide: {document_type}"}

            # Vérifier si un document du même type existe déjà en pending
            existing = self.db.kyc_documents.find_one({
                "user_id": user_id,
                "document_type": document_type,
                "status": "pending"
            })

            if existing:
                return {"success": False, "error": "Un document de ce type est déjà en attente de vérification"}

            # Créer l'enregistrement du document
            document = {
                "user_id": user_id,
                "document_type": document_type,
                "filename": file_data.get("filename"),
                "content_type": file_data.get("content_type"),
                "file_path": file_data.get("file_path"),
                "file_hash": file_data.get("file_hash"),
                "file_size": file_data.get("file_size"),
                "status": "pending",
                "uploaded_at": datetime.utcnow(),
                "verified_at": None,
                "verified_by": None,
                "rejection_reason": None,
                "expires_at": None,
                "metadata": file_data.get("metadata", {}),
            }

            result = self.db.kyc_documents.insert_one(document)
            document_id = str(result.inserted_id)

            # Mettre à jour le statut KYC de l'utilisateur
            self.db.users.update_one(
                {"_id": safe_object_id(user_id)},
                {
                    "$set": {
                        "kyc_status": "pending",
                        "kyc_updated_at": datetime.utcnow()
                    }
                }
            )

            # Lancer la vérification automatique si activée
            if KYC_CONFIG["auto_verification_enabled"]:
                self._auto_verify_document(document_id)

            # Enregistrer l'événement
            self._log_kyc_event(user_id, "document_uploaded", {
                "document_id": document_id,
                "document_type": document_type,
            })

            return {
                "success": True,
                "document_id": document_id,
                "status": "pending",
                "message": "Document uploadé avec succès. Vérification en cours..."
            }

        except Exception as e:
            logger.error(f"Error uploading KYC document: {e}")
            return {"success": False, "error": str(e)}

    def _auto_verify_document(self, document_id: str) -> Dict[str, Any]:
        """
        Vérification automatique d'un document
        Simule une vérification basique (dans un vrai système, utiliser un service externe)
        """
        try:
            document = self.db.kyc_documents.find_one({"_id": safe_object_id(document_id)})
            if not document:
                return {"success": False, "error": "Document not found"}

            # Vérifications basiques automatiques
            checks = {
                "file_exists": bool(document.get("file_path")),
                "valid_type": document.get("document_type") in KYC_CONFIG["document_types"],
                "valid_size": (document.get("file_size", 0) / (1024 * 1024)) <= KYC_CONFIG["max_file_size_mb"],
                "valid_format": self._check_file_extension(document.get("filename", "")),
            }

            # Score de vérification (simulation)
            verification_score = sum(checks.values()) / len(checks) * 100

            # Décision automatique
            if verification_score >= 75:
                # Auto-approve avec score élevé
                status = "verified"
                expires_at = datetime.utcnow() + timedelta(days=KYC_CONFIG["expiry_days"])
            elif verification_score >= 50:
                # Nécessite une vérification manuelle
                status = "pending_review"
                expires_at = None
            else:
                # Rejet automatique
                status = "rejected"
                expires_at = None

            # Mettre à jour le document
            update_data = {
                "status": status,
                "verification_score": verification_score,
                "auto_checks": checks,
                "verified_at": datetime.utcnow() if status == "verified" else None,
                "verified_by": "auto_system" if status == "verified" else None,
                "expires_at": expires_at,
            }

            if status == "rejected":
                update_data["rejection_reason"] = "Le document n'a pas passé les vérifications automatiques"

            self.db.kyc_documents.update_one(
                {"_id": safe_object_id(document_id)},
                {"$set": update_data}
            )

            # Mettre à jour le statut global de l'utilisateur si vérifié
            if status == "verified":
                self._update_user_kyc_status(document.get("user_id"))

            return {
                "success": True,
                "status": status,
                "score": verification_score,
                "checks": checks
            }

        except Exception as e:
            logger.error(f"Auto-verification error: {e}")
            return {"success": False, "error": str(e)}

    def _check_file_extension(self, filename: str) -> bool:
        """Vérifie si l'extension du fichier est autorisée"""
        if not filename:
            return False
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        return ext in KYC_CONFIG["allowed_extensions"]

    def verify_document(self, document_id: str, admin_id: str, approved: bool, reason: str = None) -> Dict[str, Any]:
        """
        Vérification manuelle d'un document par un admin

        Args:
            document_id: ID du document
            admin_id: ID de l'admin qui vérifie
            approved: True si approuvé, False si rejeté
            reason: Raison du rejet (si rejeté)
        """
        if self.db is None:
            return {"success": False, "error": "Database unavailable"}

        try:
            document = self.db.kyc_documents.find_one({"_id": safe_object_id(document_id)})
            if not document:
                return {"success": False, "error": "Document not found"}

            update_data = {
                "verified_at": datetime.utcnow(),
                "verified_by": admin_id,
            }

            if approved:
                update_data["status"] = "verified"
                update_data["expires_at"] = datetime.utcnow() + timedelta(days=KYC_CONFIG["expiry_days"])
                update_data["rejection_reason"] = None
            else:
                update_data["status"] = "rejected"
                update_data["rejection_reason"] = reason or "Document rejeté par l'administrateur"
                update_data["expires_at"] = None

            self.db.kyc_documents.update_one(
                {"_id": safe_object_id(document_id)},
                {"$set": update_data}
            )

            # Mettre à jour le statut de l'utilisateur
            user_id = document.get("user_id")
            self._update_user_kyc_status(user_id)

            # Enregistrer l'événement
            self._log_kyc_event(user_id, "document_reviewed", {
                "document_id": document_id,
                "approved": approved,
                "admin_id": admin_id,
                "reason": reason,
            })

            # Envoyer une notification à l'utilisateur
            self._notify_user_kyc_update(user_id, approved, document.get("document_type"))

            return {
                "success": True,
                "status": "verified" if approved else "rejected",
                "message": "Document vérifié avec succès" if approved else "Document rejeté"
            }

        except Exception as e:
            logger.error(f"Error verifying document: {e}")
            return {"success": False, "error": str(e)}

    def _update_user_kyc_status(self, user_id: str):
        """Met à jour le statut KYC global de l'utilisateur"""
        try:
            documents = list(self.db.kyc_documents.find({"user_id": user_id}))

            verified_docs = [d for d in documents if d.get("status") == "verified"]
            pending_docs = [d for d in documents if d.get("status") in ["pending", "pending_review"]]
            rejected_docs = [d for d in documents if d.get("status") == "rejected"]

            doc_types = set(d.get("document_type") for d in verified_docs)
            level = self._calculate_verification_level(doc_types)

            # Déterminer le statut global
            if level in ["basic", "standard", "premium"]:
                status = "verified"
                is_verified = True
            elif pending_docs:
                status = "pending"
                is_verified = False
            elif rejected_docs and not verified_docs:
                status = "rejected"
                is_verified = False
            else:
                status = "not_started"
                is_verified = False

            # Mettre à jour l'utilisateur
            self.db.users.update_one(
                {"_id": safe_object_id(user_id)},
                {
                    "$set": {
                        "kyc_status": status,
                        "kyc_verified": is_verified,
                        "kyc_level": level,
                        "kyc_verified_at": datetime.utcnow() if is_verified else None,
                        "kyc_updated_at": datetime.utcnow(),
                    }
                }
            )

        except Exception as e:
            logger.error(f"Error updating user KYC status: {e}")

    def _log_kyc_event(self, user_id: str, event_type: str, data: Dict):
        """Enregistre un événement KYC pour l'audit"""
        try:
            self.db.kyc_events.insert_one({
                "user_id": user_id,
                "event_type": event_type,
                "data": data,
                "created_at": datetime.utcnow(),
            })
        except Exception as e:
            logger.error(f"Error logging KYC event: {e}")

    def _notify_user_kyc_update(self, user_id: str, approved: bool, document_type: str):
        """Envoie une notification à l'utilisateur"""
        try:
            user = self.db.users.find_one({"_id": safe_object_id(user_id)})
            if not user or not user.get("email"):
                return

            doc_name = KYC_CONFIG["document_types"].get(document_type, {}).get("name", "Document")

            if approved:
                subject = "✅ SarfX - Document vérifié"
                message = f"""
                Bonjour {user.get('name', 'Cher client')},

                Bonne nouvelle ! Votre {doc_name} a été vérifié avec succès.

                Votre niveau de vérification a été mis à jour et vous pouvez maintenant
                profiter de limites de transaction plus élevées.

                Connectez-vous à votre compte pour voir votre nouveau statut.

                L'équipe SarfX
                """
            else:
                subject = "⚠️ SarfX - Document non validé"
                message = f"""
                Bonjour {user.get('name', 'Cher client')},

                Votre {doc_name} n'a pas pu être validé.

                Veuillez vous connecter à votre compte pour soumettre un nouveau document
                ou contacter notre support pour plus d'informations.

                L'équipe SarfX
                """

            # Utiliser le service email existant
            send_email(user.get("email"), subject, message)

        except Exception as e:
            logger.error(f"Error notifying user: {e}")

    def get_pending_documents(self, limit: int = 50) -> List[Dict]:
        """Récupère les documents en attente de vérification (pour admin)"""
        if self.db is None:
            return []

        try:
            pipeline = [
                {"$match": {"status": {"$in": ["pending", "pending_review"]}}},
                {"$sort": {"uploaded_at": 1}},
                {"$limit": limit},
                {"$lookup": {
                    "from": "users",
                    "let": {"user_id": "$user_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": [{"$toString": "$_id"}, "$$user_id"]}}}
                    ],
                    "as": "user"
                }},
                {"$unwind": {"path": "$user", "preserveNullAndEmptyArrays": True}},
            ]

            documents = list(self.db.kyc_documents.aggregate(pipeline))

            return [
                {
                    "id": str(d["_id"]),
                    "user_id": d.get("user_id"),
                    "user_name": d.get("user", {}).get("name", "N/A"),
                    "user_email": d.get("user", {}).get("email", "N/A"),
                    "document_type": d.get("document_type"),
                    "document_type_name": KYC_CONFIG["document_types"].get(d.get("document_type"), {}).get("name", "Document"),
                    "status": d.get("status"),
                    "uploaded_at": d.get("uploaded_at"),
                    "file_path": d.get("file_path"),
                    "verification_score": d.get("verification_score"),
                }
                for d in documents
            ]

        except Exception as e:
            logger.error(f"Error getting pending documents: {e}")
            return []

    def get_kyc_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques KYC pour le dashboard admin"""
        if self.db is None:
            return {}

        try:
            # Comptage par statut
            status_counts = {}
            for status in ["pending", "pending_review", "verified", "rejected"]:
                status_counts[status] = self.db.kyc_documents.count_documents({"status": status})

            # Comptage par niveau de vérification
            level_counts = {
                "none": 0,
                "basic": 0,
                "standard": 0,
                "premium": 0,
            }

            users = self.db.users.find({"kyc_level": {"$exists": True}})
            for user in users:
                level = user.get("kyc_level", "none")
                if level in level_counts:
                    level_counts[level] += 1

            # Documents expirés
            expired_count = self.db.kyc_documents.count_documents({
                "status": "verified",
                "expires_at": {"$lt": datetime.utcnow()}
            })

            # Documents uploadés aujourd'hui
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_count = self.db.kyc_documents.count_documents({
                "uploaded_at": {"$gte": today_start}
            })

            return {
                "by_status": status_counts,
                "by_level": level_counts,
                "total_documents": sum(status_counts.values()),
                "pending_total": status_counts.get("pending", 0) + status_counts.get("pending_review", 0),
                "expired_count": expired_count,
                "today_uploads": today_count,
                "verification_rate": round(
                    status_counts.get("verified", 0) / max(sum(status_counts.values()), 1) * 100, 1
                ),
            }

        except Exception as e:
            logger.error(f"Error getting KYC statistics: {e}")
            return {}


def get_kyc_service() -> KYCService:
    """Récupère une nouvelle instance du service KYC"""
    return KYCService()
