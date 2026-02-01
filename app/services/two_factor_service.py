"""
Service d'authentification à deux facteurs (2FA) pour SarfX
Gère TOTP via pyotp avec QR codes
"""
import io
import base64
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Configuration 2FA
TWO_FACTOR_CONFIG = {
    'issuer_name': 'SarfX',
    'digits': 6,
    'interval': 30,  # secondes
    'algorithm': 'SHA1',
    'backup_codes_count': 10,
    'backup_code_length': 8,
    'remember_device_days': 30,
}


def _get_db():
    """Helper pour obtenir la DB de manière sécurisée"""
    try:
        from app.services.db_service import get_db
        return get_db()
    except RuntimeError:
        return None


def _safe_object_id(id_str):
    """Helper pour convertir un ID en ObjectId"""
    try:
        from bson import ObjectId
        if isinstance(id_str, ObjectId):
            return id_str
        return ObjectId(str(id_str))
    except Exception:
        return None


class TwoFactorService:
    """Service de gestion 2FA"""

    def __init__(self, db=None):
        self._db = db
        self.config = TWO_FACTOR_CONFIG

    @property
    def db(self):
        """Obtient une connexion DB fraîche à chaque accès"""
        if self._db is not None:
            return self._db
        return _get_db()

    # =====================================================
    # GÉNÉRATION SECRET & QR CODE
    # =====================================================

    def generate_secret(self) -> str:
        """Génère un secret TOTP aléatoire"""
        try:
            import pyotp
            return pyotp.random_base32()
        except ImportError:
            # Fallback si pyotp n'est pas installé
            return base64.b32encode(secrets.token_bytes(20)).decode('utf-8')

    def get_totp_uri(self, secret: str, email: str) -> str:
        """Génère l'URI TOTP pour le QR code"""
        try:
            import pyotp
            totp = pyotp.TOTP(secret)
            return totp.provisioning_uri(
                name=email,
                issuer_name=self.config['issuer_name']
            )
        except ImportError:
            # Fallback manuel
            return f"otpauth://totp/{self.config['issuer_name']}:{email}?secret={secret}&issuer={self.config['issuer_name']}"

    def generate_qr_code(self, secret: str, email: str) -> str:
        """Génère un QR code en base64 pour le setup 2FA"""
        try:
            import qrcode
            from qrcode.image.pure import PyPNGImage

            uri = self.get_totp_uri(secret, email)

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(uri)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)

            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except ImportError:
            logger.warning("qrcode library not installed, returning URI only")
            return None

    def generate_backup_codes(self) -> list:
        """Génère des codes de secours"""
        codes = []
        for _ in range(self.config['backup_codes_count']):
            code = secrets.token_hex(self.config['backup_code_length'] // 2).upper()
            # Format: XXXX-XXXX
            formatted = f"{code[:4]}-{code[4:]}"
            codes.append(formatted)
        return codes

    # =====================================================
    # ACTIVATION 2FA
    # =====================================================

    def setup_2fa(self, user_id: str) -> Dict[str, Any]:
        """
        Initialise le setup 2FA pour un utilisateur
        Retourne le secret et le QR code (ne sauvegarde pas encore)
        """
        if not self.db:
            return {'success': False, 'error': 'Database not available'}

        try:
            user_oid = _safe_object_id(user_id)
            if not user_oid:
                return {'success': False, 'error': 'Invalid user ID'}

            user = self.db.users.find_one({'_id': user_oid})
            if not user:
                return {'success': False, 'error': 'User not found'}

            # Vérifier si 2FA déjà activé
            if user.get('two_factor_enabled'):
                return {'success': False, 'error': '2FA already enabled'}

            # Générer nouveau secret
            secret = self.generate_secret()
            email = user.get('email', user.get('username', 'user'))

            # Générer QR code
            qr_code = self.generate_qr_code(secret, email)
            uri = self.get_totp_uri(secret, email)

            # Stocker temporairement le secret (pas encore activé)
            self.db.users.update_one(
                {'_id': user_oid},
                {'$set': {
                    'two_factor_temp_secret': secret,
                    'two_factor_setup_started': datetime.utcnow()
                }}
            )

            return {
                'success': True,
                'secret': secret,
                'qr_code': qr_code,
                'uri': uri,
                'manual_entry_key': secret
            }

        except Exception as e:
            logger.error(f"Error setting up 2FA: {e}")
            return {'success': False, 'error': str(e)}

    def verify_and_enable_2fa(self, user_id: str, code: str) -> Dict[str, Any]:
        """
        Vérifie le code TOTP et active le 2FA si correct
        Retourne les codes de secours
        """
        if not self.db:
            return {'success': False, 'error': 'Database not available'}

        try:
            user_oid = _safe_object_id(user_id)
            if not user_oid:
                return {'success': False, 'error': 'Invalid user ID'}

            user = self.db.users.find_one({'_id': user_oid})
            if not user:
                return {'success': False, 'error': 'User not found'}

            temp_secret = user.get('two_factor_temp_secret')
            if not temp_secret:
                return {'success': False, 'error': '2FA setup not initiated'}

            # Vérifier le code
            if not self.verify_totp(temp_secret, code):
                return {'success': False, 'error': 'Invalid verification code'}

            # Générer codes de secours
            backup_codes = self.generate_backup_codes()

            # Hasher les codes de secours pour stockage
            import hashlib
            hashed_backup_codes = [
                hashlib.sha256(c.replace('-', '').encode()).hexdigest()
                for c in backup_codes
            ]

            # Activer 2FA
            self.db.users.update_one(
                {'_id': user_oid},
                {
                    '$set': {
                        'two_factor_enabled': True,
                        'two_factor_secret': temp_secret,
                        'two_factor_backup_codes': hashed_backup_codes,
                        'two_factor_enabled_at': datetime.utcnow()
                    },
                    '$unset': {
                        'two_factor_temp_secret': '',
                        'two_factor_setup_started': ''
                    }
                }
            )

            # Log l'événement
            self._log_2fa_event(user_id, '2fa_enabled')

            return {
                'success': True,
                'message': '2FA successfully enabled',
                'backup_codes': backup_codes
            }

        except Exception as e:
            logger.error(f"Error enabling 2FA: {e}")
            return {'success': False, 'error': str(e)}

    def disable_2fa(self, user_id: str, code: str) -> Dict[str, Any]:
        """Désactive le 2FA après vérification"""
        if not self.db:
            return {'success': False, 'error': 'Database not available'}

        try:
            user_oid = _safe_object_id(user_id)
            if not user_oid:
                return {'success': False, 'error': 'Invalid user ID'}

            user = self.db.users.find_one({'_id': user_oid})
            if not user:
                return {'success': False, 'error': 'User not found'}

            if not user.get('two_factor_enabled'):
                return {'success': False, 'error': '2FA not enabled'}

            secret = user.get('two_factor_secret')

            # Vérifier le code (TOTP ou backup)
            if not self.verify_totp(secret, code) and not self._verify_backup_code(user, code):
                return {'success': False, 'error': 'Invalid verification code'}

            # Désactiver 2FA
            self.db.users.update_one(
                {'_id': user_oid},
                {
                    '$set': {
                        'two_factor_enabled': False,
                        'two_factor_disabled_at': datetime.utcnow()
                    },
                    '$unset': {
                        'two_factor_secret': '',
                        'two_factor_backup_codes': '',
                        'two_factor_enabled_at': ''
                    }
                }
            )

            # Supprimer les appareils de confiance
            self.db.trusted_devices.delete_many({'user_id': user_oid})

            # Log l'événement
            self._log_2fa_event(user_id, '2fa_disabled')

            return {'success': True, 'message': '2FA successfully disabled'}

        except Exception as e:
            logger.error(f"Error disabling 2FA: {e}")
            return {'success': False, 'error': str(e)}

    # =====================================================
    # VÉRIFICATION TOTP
    # =====================================================

    def verify_totp(self, secret: str, code: str, window: int = 1) -> bool:
        """Vérifie un code TOTP avec une fenêtre de tolérance"""
        if not secret or not code:
            return False

        # Nettoyer le code
        code = code.replace(' ', '').replace('-', '')

        try:
            import pyotp
            totp = pyotp.TOTP(secret)
            return totp.verify(code, valid_window=window)
        except ImportError:
            # Fallback basique (moins sécurisé)
            logger.warning("pyotp not installed, using basic verification")
            return self._basic_totp_verify(secret, code)
        except Exception as e:
            logger.error(f"TOTP verification error: {e}")
            return False

    def _basic_totp_verify(self, secret: str, code: str) -> bool:
        """Vérification TOTP basique sans pyotp"""
        import hmac
        import hashlib
        import struct
        import time

        try:
            # Décoder le secret base32
            key = base64.b32decode(secret.upper())

            # Calculer le counter
            counter = int(time.time()) // self.config['interval']

            # Vérifier avec une fenêtre
            for i in range(-1, 2):
                c = counter + i
                msg = struct.pack('>Q', c)
                h = hmac.new(key, msg, hashlib.sha1).digest()
                o = h[-1] & 0x0F
                otp = (struct.unpack('>I', h[o:o+4])[0] & 0x7FFFFFFF) % 1000000
                if str(otp).zfill(6) == code:
                    return True
            return False
        except Exception:
            return False

    def _verify_backup_code(self, user: Dict, code: str) -> bool:
        """Vérifie et consomme un code de secours"""
        import hashlib

        backup_codes = user.get('two_factor_backup_codes', [])
        if not backup_codes:
            return False

        # Hasher le code fourni
        code_clean = code.replace('-', '').replace(' ', '').upper()
        code_hash = hashlib.sha256(code_clean.encode()).hexdigest()

        if code_hash in backup_codes:
            # Supprimer le code utilisé
            self.db.users.update_one(
                {'_id': user['_id']},
                {'$pull': {'two_factor_backup_codes': code_hash}}
            )
            self._log_2fa_event(str(user['_id']), 'backup_code_used')
            return True

        return False

    # =====================================================
    # APPAREILS DE CONFIANCE
    # =====================================================

    def add_trusted_device(
        self,
        user_id: str,
        device_info: Dict[str, str],
        ip_address: str
    ) -> Dict[str, Any]:
        """Ajoute un appareil de confiance"""
        if not self.db:
            return {'success': False, 'error': 'Database not available'}

        try:
            user_oid = _safe_object_id(user_id)
            if not user_oid:
                return {'success': False, 'error': 'Invalid user ID'}

            # Générer un token unique pour l'appareil
            device_token = secrets.token_urlsafe(32)

            device = {
                'user_id': user_oid,
                'token': device_token,
                'user_agent': device_info.get('user_agent', ''),
                'browser': device_info.get('browser', ''),
                'os': device_info.get('os', ''),
                'device_type': device_info.get('device_type', 'unknown'),
                'ip_address': ip_address,
                'created_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(days=self.config['remember_device_days']),
                'last_used': datetime.utcnow()
            }

            self.db.trusted_devices.insert_one(device)

            return {
                'success': True,
                'device_token': device_token,
                'expires_in_days': self.config['remember_device_days']
            }

        except Exception as e:
            logger.error(f"Error adding trusted device: {e}")
            return {'success': False, 'error': str(e)}

    def verify_trusted_device(self, user_id: str, device_token: str) -> bool:
        """Vérifie si un appareil est de confiance"""
        if not self.db or not device_token:
            return False

        try:
            user_oid = _safe_object_id(user_id)
            if not user_oid:
                return False

            device = self.db.trusted_devices.find_one({
                'user_id': user_oid,
                'token': device_token,
                'expires_at': {'$gt': datetime.utcnow()}
            })

            if device:
                # Mettre à jour last_used
                self.db.trusted_devices.update_one(
                    {'_id': device['_id']},
                    {'$set': {'last_used': datetime.utcnow()}}
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Error verifying trusted device: {e}")
            return False

    def get_trusted_devices(self, user_id: str) -> list:
        """Liste les appareils de confiance d'un utilisateur"""
        if not self.db:
            return []

        try:
            user_oid = _safe_object_id(user_id)
            if not user_oid:
                return []

            devices = list(self.db.trusted_devices.find({
                'user_id': user_oid,
                'expires_at': {'$gt': datetime.utcnow()}
            }).sort('last_used', -1))

            return [{
                'id': str(d['_id']),
                'browser': d.get('browser', 'Unknown'),
                'os': d.get('os', 'Unknown'),
                'device_type': d.get('device_type', 'unknown'),
                'ip_address': d.get('ip_address', ''),
                'created_at': d.get('created_at'),
                'last_used': d.get('last_used'),
                'is_current': False  # À définir par le caller
            } for d in devices]

        except Exception as e:
            logger.error(f"Error getting trusted devices: {e}")
            return []

    def remove_trusted_device(self, user_id: str, device_id: str) -> Dict[str, Any]:
        """Supprime un appareil de confiance"""
        if not self.db:
            return {'success': False, 'error': 'Database not available'}

        try:
            user_oid = _safe_object_id(user_id)
            device_oid = _safe_object_id(device_id)

            if not user_oid or not device_oid:
                return {'success': False, 'error': 'Invalid ID'}

            result = self.db.trusted_devices.delete_one({
                '_id': device_oid,
                'user_id': user_oid
            })

            if result.deleted_count > 0:
                return {'success': True, 'message': 'Device removed'}
            return {'success': False, 'error': 'Device not found'}

        except Exception as e:
            logger.error(f"Error removing trusted device: {e}")
            return {'success': False, 'error': str(e)}

    def remove_all_trusted_devices(self, user_id: str) -> Dict[str, Any]:
        """Supprime tous les appareils de confiance"""
        if not self.db:
            return {'success': False, 'error': 'Database not available'}

        try:
            user_oid = _safe_object_id(user_id)
            if not user_oid:
                return {'success': False, 'error': 'Invalid user ID'}

            result = self.db.trusted_devices.delete_many({'user_id': user_oid})

            return {
                'success': True,
                'message': f'{result.deleted_count} devices removed'
            }

        except Exception as e:
            logger.error(f"Error removing all trusted devices: {e}")
            return {'success': False, 'error': str(e)}

    # =====================================================
    # RÉGÉNÉRATION CODES DE SECOURS
    # =====================================================

    def regenerate_backup_codes(self, user_id: str, code: str) -> Dict[str, Any]:
        """Régénère les codes de secours après vérification"""
        if not self.db:
            return {'success': False, 'error': 'Database not available'}

        try:
            user_oid = _safe_object_id(user_id)
            if not user_oid:
                return {'success': False, 'error': 'Invalid user ID'}

            user = self.db.users.find_one({'_id': user_oid})
            if not user:
                return {'success': False, 'error': 'User not found'}

            if not user.get('two_factor_enabled'):
                return {'success': False, 'error': '2FA not enabled'}

            secret = user.get('two_factor_secret')

            # Vérifier le code
            if not self.verify_totp(secret, code):
                return {'success': False, 'error': 'Invalid verification code'}

            # Générer nouveaux codes
            backup_codes = self.generate_backup_codes()

            import hashlib
            hashed_backup_codes = [
                hashlib.sha256(c.replace('-', '').encode()).hexdigest()
                for c in backup_codes
            ]

            # Mettre à jour
            self.db.users.update_one(
                {'_id': user_oid},
                {'$set': {
                    'two_factor_backup_codes': hashed_backup_codes,
                    'two_factor_backup_codes_regenerated_at': datetime.utcnow()
                }}
            )

            self._log_2fa_event(user_id, 'backup_codes_regenerated')

            return {
                'success': True,
                'backup_codes': backup_codes,
                'message': 'Backup codes regenerated successfully'
            }

        except Exception as e:
            logger.error(f"Error regenerating backup codes: {e}")
            return {'success': False, 'error': str(e)}

    # =====================================================
    # STATUT 2FA
    # =====================================================

    def get_2fa_status(self, user_id: str) -> Dict[str, Any]:
        """Récupère le statut 2FA d'un utilisateur"""
        if not self.db:
            return {'enabled': False, 'error': 'Database not available'}

        try:
            user_oid = _safe_object_id(user_id)
            if not user_oid:
                return {'enabled': False, 'error': 'Invalid user ID'}

            user = self.db.users.find_one(
                {'_id': user_oid},
                {
                    'two_factor_enabled': 1,
                    'two_factor_enabled_at': 1,
                    'two_factor_backup_codes': 1
                }
            )

            if not user:
                return {'enabled': False, 'error': 'User not found'}

            backup_codes = user.get('two_factor_backup_codes', [])

            return {
                'enabled': user.get('two_factor_enabled', False),
                'enabled_at': user.get('two_factor_enabled_at'),
                'backup_codes_remaining': len(backup_codes),
                'trusted_devices_count': self.db.trusted_devices.count_documents({
                    'user_id': user_oid,
                    'expires_at': {'$gt': datetime.utcnow()}
                })
            }

        except Exception as e:
            logger.error(f"Error getting 2FA status: {e}")
            return {'enabled': False, 'error': str(e)}

    # =====================================================
    # VÉRIFICATION À LA CONNEXION
    # =====================================================

    def requires_2fa(self, user_id: str, device_token: Optional[str] = None) -> bool:
        """Vérifie si l'utilisateur doit passer par 2FA"""
        if not self.db:
            return False

        try:
            user_oid = _safe_object_id(user_id)
            if not user_oid:
                return False

            user = self.db.users.find_one(
                {'_id': user_oid},
                {'two_factor_enabled': 1}
            )

            if not user or not user.get('two_factor_enabled'):
                return False

            # Vérifier si l'appareil est de confiance
            if device_token and self.verify_trusted_device(user_id, device_token):
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking 2FA requirement: {e}")
            return False

    def verify_login_2fa(
        self,
        user_id: str,
        code: str,
        remember_device: bool = False,
        device_info: Optional[Dict] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Vérifie le code 2FA à la connexion"""
        if not self.db:
            return {'success': False, 'error': 'Database not available'}

        try:
            user_oid = _safe_object_id(user_id)
            if not user_oid:
                return {'success': False, 'error': 'Invalid user ID'}

            user = self.db.users.find_one({'_id': user_oid})
            if not user:
                return {'success': False, 'error': 'User not found'}

            secret = user.get('two_factor_secret')
            if not secret:
                return {'success': False, 'error': '2FA not configured'}

            # Vérifier le code (TOTP ou backup)
            is_backup_code = False
            if self.verify_totp(secret, code):
                pass  # Code TOTP valide
            elif self._verify_backup_code(user, code):
                is_backup_code = True
            else:
                self._log_2fa_event(user_id, '2fa_failed_attempt')
                return {'success': False, 'error': 'Invalid verification code'}

            result = {
                'success': True,
                'message': '2FA verification successful',
                'used_backup_code': is_backup_code
            }

            # Ajouter l'appareil de confiance si demandé
            if remember_device and device_info and ip_address:
                device_result = self.add_trusted_device(user_id, device_info, ip_address)
                if device_result.get('success'):
                    result['device_token'] = device_result['device_token']

            # Log succès
            self._log_2fa_event(user_id, '2fa_login_success')

            return result

        except Exception as e:
            logger.error(f"Error verifying login 2FA: {e}")
            return {'success': False, 'error': str(e)}

    # =====================================================
    # LOGGING & AUDIT
    # =====================================================

    def _log_2fa_event(self, user_id: str, event_type: str, details: Dict = None):
        """Log un événement 2FA pour l'audit"""
        if not self.db:
            return

        try:
            user_oid = _safe_object_id(user_id)

            log_entry = {
                'user_id': user_oid,
                'event_type': event_type,
                'timestamp': datetime.utcnow(),
                'details': details or {}
            }

            self.db.security_logs.insert_one(log_entry)

        except Exception as e:
            logger.error(f"Error logging 2FA event: {e}")

    def get_2fa_logs(self, user_id: str, limit: int = 20) -> list:
        """Récupère les logs 2FA d'un utilisateur"""
        if not self.db:
            return []

        try:
            user_oid = _safe_object_id(user_id)
            if not user_oid:
                return []

            logs = list(self.db.security_logs.find({
                'user_id': user_oid,
                'event_type': {'$regex': '^2fa_|^backup_code'}
            }).sort('timestamp', -1).limit(limit))

            return [{
                'event_type': log.get('event_type'),
                'timestamp': log.get('timestamp'),
                'details': log.get('details', {})
            } for log in logs]

        except Exception as e:
            logger.error(f"Error getting 2FA logs: {e}")
            return []


def get_two_factor_service() -> TwoFactorService:
    """Récupère une nouvelle instance du service 2FA"""
    return TwoFactorService()

# Instance pour compatibilité avec le code existant (utilise property pour DB fraîche)
two_factor_service = TwoFactorService()
