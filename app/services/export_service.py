"""
Service d'export de rapports pour SarfX
Gère l'export des données en PDF et CSV
"""
import io
import csv
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


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


class ExportService:
    """Service d'export de rapports"""

    def __init__(self, db=None):
        self._db = db

    @property
    def db(self):
        """Obtient une connexion DB fraîche à chaque accès pour éviter MongoClient after close"""
        if self._db is not None:
            return self._db
        return _get_db()

    # =====================================================
    # EXPORT CSV
    # =====================================================

    def export_transactions_csv(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        currency: Optional[str] = None,
        limit: int = 10000
    ) -> io.StringIO:
        """
        Exporte les transactions au format CSV

        Args:
            user_id: Filtrer par utilisateur (None = toutes)
            start_date: Date de début
            end_date: Date de fin
            status: Filtrer par statut (pending, completed, cancelled)
            currency: Filtrer par devise
            limit: Nombre max de transactions

        Returns:
            StringIO contenant le CSV
        """
        if self.db is None:
            return self._create_empty_csv(['Erreur: Base de données indisponible'])

        # Construction du filtre
        query = {}

        if user_id:
            query['user_id'] = user_id

        if start_date or end_date:
            query['created_at'] = {}
            if start_date:
                query['created_at']['$gte'] = start_date
            if end_date:
                query['created_at']['$lte'] = end_date

        if status:
            query['status'] = status

        if currency:
            query['$or'] = [
                {'from_currency': currency},
                {'to_currency': currency}
            ]

        # Récupération des transactions
        transactions = list(
            self.db.transactions.find(query)
            .sort('created_at', -1)
            .limit(limit)
        )

        # Création du CSV
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # En-têtes
        headers = [
            'ID Transaction',
            'Date',
            'Utilisateur',
            'Type',
            'Devise Source',
            'Montant Source',
            'Devise Destination',
            'Montant Destination',
            'Taux',
            'Frais',
            'Statut',
            'Bénéficiaire',
            'Référence'
        ]
        writer.writerow(headers)

        # Données
        for tx in transactions:
            row = [
                str(tx.get('_id', '')),
                tx.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if tx.get('created_at') else '',
                tx.get('user_email', tx.get('user_id', '')),
                tx.get('type', 'exchange'),
                tx.get('from_currency', ''),
                f"{tx.get('amount', 0):.2f}",
                tx.get('to_currency', ''),
                f"{tx.get('final_amount', 0):.2f}",
                f"{tx.get('rate', 0):.4f}",
                f"{tx.get('fee', 0):.2f}",
                tx.get('status', 'pending'),
                tx.get('recipient_name', ''),
                tx.get('reference', tx.get('transaction_id', ''))
            ]
            writer.writerow(row)

        output.seek(0)
        return output

    def export_users_csv(
        self,
        role: Optional[str] = None,
        kyc_status: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 10000
    ) -> io.StringIO:
        """
        Exporte les utilisateurs au format CSV
        """
        if self.db is None:
            return self._create_empty_csv(['Erreur: Base de données indisponible'])

        query = {}

        if role:
            query['role'] = role

        if kyc_status:
            query['kyc_status'] = kyc_status

        if is_active is not None:
            query['is_active'] = is_active

        users = list(
            self.db.users.find(query, {'password': 0})
            .sort('created_at', -1)
            .limit(limit)
        )

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        headers = [
            'ID',
            'Email',
            'Nom',
            'Rôle',
            'Statut KYC',
            'Niveau KYC',
            'Actif',
            'Vérifié',
            'Date inscription',
            'Dernière connexion',
            'Code Banque'
        ]
        writer.writerow(headers)

        for user in users:
            row = [
                str(user.get('_id', '')),
                user.get('email', ''),
                user.get('name', ''),
                user.get('role', 'user'),
                user.get('kyc_status', 'none'),
                user.get('kyc_level', 'none'),
                'Oui' if user.get('is_active', True) else 'Non',
                'Oui' if user.get('is_verified', False) else 'Non',
                user.get('created_at', '').strftime('%Y-%m-%d %H:%M') if user.get('created_at') else '',
                user.get('last_login', '').strftime('%Y-%m-%d %H:%M') if user.get('last_login') else '',
                user.get('bank_code', '')
            ]
            writer.writerow(row)

        output.seek(0)
        return output

    def export_wallets_csv(self, user_id: Optional[str] = None) -> io.StringIO:
        """
        Exporte les wallets au format CSV
        """
        if self.db is None:
            return self._create_empty_csv(['Erreur: Base de données indisponible'])

        query = {}
        if user_id:
            query['user_id'] = user_id

        wallets = list(self.db.wallets.find(query))

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        headers = [
            'ID Wallet',
            'ID Utilisateur',
            'EUR',
            'USD',
            'MAD',
            'GBP',
            'Date création',
            'Dernière mise à jour'
        ]
        writer.writerow(headers)

        for wallet in wallets:
            balances = wallet.get('balances', {})
            row = [
                str(wallet.get('_id', wallet.get('wallet_id', ''))),
                wallet.get('user_id', ''),
                f"{balances.get('EUR', 0):.2f}",
                f"{balances.get('USD', 0):.2f}",
                f"{balances.get('MAD', 0):.2f}",
                f"{balances.get('GBP', 0):.2f}",
                wallet.get('created_at', '').strftime('%Y-%m-%d %H:%M') if wallet.get('created_at') else '',
                wallet.get('updated_at', '').strftime('%Y-%m-%d %H:%M') if wallet.get('updated_at') else ''
            ]
            writer.writerow(row)

        output.seek(0)
        return output

    def export_beneficiaries_csv(self, user_id: Optional[str] = None) -> io.StringIO:
        """
        Exporte les bénéficiaires au format CSV
        """
        if self.db is None:
            return self._create_empty_csv(['Erreur: Base de données indisponible'])

        query = {}
        if user_id:
            query['user_id'] = user_id

        beneficiaries = list(self.db.beneficiaries.find(query))

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        headers = [
            'ID',
            'Utilisateur',
            'Nom',
            'Banque',
            'IBAN',
            'Ville',
            'Pays',
            'Nb Transferts',
            'Favori',
            'Date création'
        ]
        writer.writerow(headers)

        for ben in beneficiaries:
            row = [
                str(ben.get('_id', '')),
                ben.get('user_id', ''),
                ben.get('name', ''),
                ben.get('bank_name', ''),
                ben.get('iban', '')[:8] + '****' if ben.get('iban') else '',  # Masquer IBAN
                ben.get('city', ''),
                ben.get('country', ''),
                ben.get('transfer_count', 0),
                'Oui' if ben.get('is_favorite') else 'Non',
                ben.get('created_at', '').strftime('%Y-%m-%d') if ben.get('created_at') else ''
            ]
            writer.writerow(row)

        output.seek(0)
        return output

    # =====================================================
    # EXPORT PDF (HTML to PDF)
    # =====================================================

    def generate_transaction_report_html(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> str:
        """
        Génère un rapport HTML des transactions (pour conversion PDF)
        """
        if self.db is None:
            return self._error_html("Base de données indisponible")

        query = {}
        if user_id:
            query['user_id'] = user_id
        if start_date:
            query['created_at'] = {'$gte': start_date}
        if end_date:
            if 'created_at' not in query:
                query['created_at'] = {}
            query['created_at']['$lte'] = end_date

        transactions = list(
            self.db.transactions.find(query)
            .sort('created_at', -1)
            .limit(limit)
        )

        # Calculer les statistiques
        total_amount = sum(tx.get('amount', 0) for tx in transactions)
        total_fees = sum(tx.get('fee', 0) for tx in transactions)
        completed = len([tx for tx in transactions if tx.get('status') == 'completed'])

        # Générer le HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Rapport des Transactions - SarfX</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 12px;
            line-height: 1.5;
            color: #333;
            padding: 40px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #6366f1;
        }}
        .logo {{
            font-size: 28px;
            font-weight: 700;
            color: #6366f1;
        }}
        .logo span {{ color: #e05a03; }}
        .report-info {{
            text-align: right;
            color: #666;
        }}
        .report-title {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #1e293b;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #f8fafc;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: 700;
            color: #6366f1;
        }}
        .stat-label {{
            font-size: 11px;
            color: #64748b;
            text-transform: uppercase;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 10px 8px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background: #f1f5f9;
            font-weight: 600;
            color: #475569;
            font-size: 11px;
            text-transform: uppercase;
        }}
        tr:hover {{ background: #f8fafc; }}
        .status {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .status-completed {{ background: #dcfce7; color: #166534; }}
        .status-pending {{ background: #fef3c7; color: #92400e; }}
        .status-cancelled {{ background: #fee2e2; color: #991b1b; }}
        .amount {{ font-weight: 600; color: #1e293b; }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            text-align: center;
            color: #94a3b8;
            font-size: 10px;
        }}
        @media print {{
            body {{ padding: 20px; }}
            .stat-card {{ break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">Sarf<span>X</span></div>
        <div class="report-info">
            <strong>Rapport des Transactions</strong><br>
            Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}<br>
            {f"Du {start_date.strftime('%d/%m/%Y')}" if start_date else ""}
            {f"au {end_date.strftime('%d/%m/%Y')}" if end_date else ""}
        </div>
    </div>

    <h2 class="report-title">Résumé des Transactions</h2>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{len(transactions)}</div>
            <div class="stat-label">Transactions</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{total_amount:,.2f} €</div>
            <div class="stat-label">Volume Total</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{total_fees:,.2f} €</div>
            <div class="stat-label">Frais Collectés</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{(completed/len(transactions)*100) if transactions else 0:.1f}%</div>
            <div class="stat-label">Taux de Succès</div>
        </div>
    </div>

    <h3 style="margin-bottom: 15px;">Détail des Transactions</h3>

    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th>Référence</th>
                <th>Type</th>
                <th>De</th>
                <th>Vers</th>
                <th>Taux</th>
                <th>Frais</th>
                <th>Statut</th>
            </tr>
        </thead>
        <tbody>
"""

        for tx in transactions:
            status_class = f"status-{tx.get('status', 'pending')}"
            html += f"""
            <tr>
                <td>{tx.get('created_at', '').strftime('%d/%m/%Y %H:%M') if tx.get('created_at') else '-'}</td>
                <td>{tx.get('reference', tx.get('transaction_id', '-'))[:12]}...</td>
                <td>{tx.get('type', 'exchange').capitalize()}</td>
                <td class="amount">{tx.get('amount', 0):,.2f} {tx.get('from_currency', '')}</td>
                <td class="amount">{tx.get('final_amount', 0):,.2f} {tx.get('to_currency', '')}</td>
                <td>{tx.get('rate', 0):.4f}</td>
                <td>{tx.get('fee', 0):.2f} €</td>
                <td><span class="status {status_class}">{tx.get('status', 'pending')}</span></td>
            </tr>
"""

        html += f"""
        </tbody>
    </table>

    <div class="footer">
        <p>SarfX - Plateforme d'échange de devises</p>
        <p>Ce document est généré automatiquement et ne constitue pas une facture officielle.</p>
    </div>
</body>
</html>
"""
        return html

    def generate_wallet_statement_html(self, user_id: str, period_days: int = 30) -> str:
        """
        Génère un relevé de compte HTML pour un utilisateur
        """
        if self.db is None:
            return self._error_html("Base de données indisponible")

        user = self.db.users.find_one({'_id': _safe_object_id(user_id)})
        wallet = self.db.wallets.find_one({'user_id': user_id})

        if not user or not wallet:
            return self._error_html("Utilisateur ou wallet non trouvé")

        start_date = datetime.utcnow() - timedelta(days=period_days)

        # Récupérer les transactions de la période
        transactions = list(self.db.transactions.find({
            'user_id': user_id,
            'created_at': {'$gte': start_date}
        }).sort('created_at', -1))

        balances = wallet.get('balances', {})

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Relevé de Compte - SarfX</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 12px;
            line-height: 1.5;
            color: #333;
            padding: 40px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #6366f1;
        }}
        .logo {{ font-size: 28px; font-weight: 700; color: #6366f1; }}
        .logo span {{ color: #e05a03; }}
        .account-info {{
            background: #f8fafc;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
        }}
        .account-info h3 {{
            margin-bottom: 15px;
            color: #1e293b;
        }}
        .balance-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
        }}
        .balance-item {{
            text-align: center;
            padding: 15px;
            background: white;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }}
        .balance-currency {{
            font-size: 14px;
            font-weight: 600;
            color: #6366f1;
        }}
        .balance-amount {{
            font-size: 20px;
            font-weight: 700;
            color: #1e293b;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 10px 8px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background: #f1f5f9;
            font-weight: 600;
            color: #475569;
            font-size: 11px;
        }}
        .credit {{ color: #16a34a; }}
        .debit {{ color: #dc2626; }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            color: #94a3b8;
            font-size: 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">Sarf<span>X</span></div>
        <div style="text-align: right;">
            <strong>Relevé de Compte</strong><br>
            Période: {period_days} derniers jours<br>
            {datetime.now().strftime('%d/%m/%Y')}
        </div>
    </div>

    <div class="account-info">
        <h3>Informations du Compte</h3>
        <p><strong>Titulaire:</strong> {user.get('name', user.get('email', 'N/A'))}</p>
        <p><strong>Email:</strong> {user.get('email', 'N/A')}</p>
        <p><strong>Statut KYC:</strong> {user.get('kyc_status', 'Non vérifié').capitalize()}</p>

        <h3 style="margin-top: 20px;">Soldes Actuels</h3>
        <div class="balance-grid">
            <div class="balance-item">
                <div class="balance-currency">EUR</div>
                <div class="balance-amount">{balances.get('EUR', 0):,.2f}</div>
            </div>
            <div class="balance-item">
                <div class="balance-currency">USD</div>
                <div class="balance-amount">{balances.get('USD', 0):,.2f}</div>
            </div>
            <div class="balance-item">
                <div class="balance-currency">MAD</div>
                <div class="balance-amount">{balances.get('MAD', 0):,.2f}</div>
            </div>
            <div class="balance-item">
                <div class="balance-currency">GBP</div>
                <div class="balance-amount">{balances.get('GBP', 0):,.2f}</div>
            </div>
        </div>
    </div>

    <h3>Historique des Mouvements</h3>
    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th>Description</th>
                <th>Débit</th>
                <th>Crédit</th>
            </tr>
        </thead>
        <tbody>
"""

        for tx in transactions:
            is_debit = tx.get('type') in ['send', 'exchange', 'withdraw']
            debit = f"{tx.get('amount', 0):,.2f} {tx.get('from_currency', '')}" if is_debit else "-"
            credit = f"{tx.get('final_amount', 0):,.2f} {tx.get('to_currency', '')}" if not is_debit else "-"

            html += f"""
            <tr>
                <td>{tx.get('created_at', '').strftime('%d/%m/%Y %H:%M') if tx.get('created_at') else '-'}</td>
                <td>{tx.get('type', '').capitalize()} - {tx.get('from_currency', '')} → {tx.get('to_currency', '')}</td>
                <td class="debit">{debit}</td>
                <td class="credit">{credit}</td>
            </tr>
"""

        html += """
        </tbody>
    </table>

    <div class="footer">
        <p>Document généré automatiquement par SarfX</p>
        <p>Pour toute question, contactez support@sarfx.io</p>
    </div>
</body>
</html>
"""
        return html

    # =====================================================
    # HELPERS
    # =====================================================

    def _create_empty_csv(self, message: List[str]) -> io.StringIO:
        """Crée un CSV vide avec un message"""
        output = io.StringIO()
        writer = csv.writer(output)
        for msg in message:
            writer.writerow([msg])
        output.seek(0)
        return output

    def _error_html(self, message: str) -> str:
        """Génère une page HTML d'erreur"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Erreur - SarfX</title>
    <style>
        body {{ font-family: sans-serif; padding: 50px; text-align: center; }}
        .error {{ color: #dc2626; font-size: 18px; }}
    </style>
</head>
<body>
    <h1>Erreur</h1>
    <p class="error">{message}</p>
</body>
</html>
"""


def get_export_service() -> ExportService:
    """Retourne une nouvelle instance du service d'export pour éviter les connexions périmées"""
    return ExportService()
