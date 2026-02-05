from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from datetime import datetime
import uuid
from app.services.db_service import get_db
from app.services.wallet_service import get_user_transactions, get_total_balance_in_usd
from app.decorators import login_required, role_required, get_current_user, get_user_wallet

app_bp = Blueprint('app', __name__)


# ==================== OFFLINE PAGE ====================

@app_bp.route('/offline')
def offline():
    """Page affichée quand l'utilisateur est hors ligne"""
    return render_template('offline.html')





def get_suppliers():
    """Récupère tous les fournisseurs actifs"""
    db = get_db()
    if db is None:
        return []
    suppliers = list(db.suppliers.find({"is_active": True}))
    # Convert ObjectId to string for JSON serialization
    for s in suppliers:
        s['_id'] = str(s['_id'])
    return suppliers

def get_settings():
    """Récupère les paramètres de l'application"""
    db = get_db()
    if db is None:
        return {}
    settings = db.settings.find_one({"type": "app"})
    return settings or {}


@app_bp.route('/')
@login_required
def home():
    """Page d'accueil de l'application"""
    user = get_current_user()
    wallet = get_user_wallet(session['user_id'])

    transactions, trans_error = get_user_transactions(session['user_id'], limit=3)
    if trans_error:
        flash(trans_error, 'error')
        transactions = []

    # Calculer le solde total de tous les wallets
    total_balance, balance_error = get_total_balance_in_usd(session['user_id'])
    if balance_error:
        flash(balance_error, 'error')
        total_balance = {"total_usd": 0, "wallets": []}

    db = get_db()
    suppliers_count = db.suppliers.count_documents({"is_active": True}) if db is not None else 0

    # Récupérer les banques partenaires actives
    banks = []
    bank_count = 6
    atm_count = 250
    if db is not None:
        if 'banks' in db.list_collection_names():
            banks = list(db.banks.find({"is_active": True}).limit(10))
            count = db.banks.count_documents({"is_active": True})
            if count > 0:
                bank_count = count
        if 'atm_locations' in db.list_collection_names():
            atm_count = db.atm_locations.count_documents({})

    return render_template('app_home.html',
        active_tab='home',
        user=user,
        wallet=wallet,
        total_balance=total_balance,
        transactions=transactions,
        suppliers_count=suppliers_count,
        banks=banks,
        bank_count=bank_count,
        atm_count=atm_count
    )


@app_bp.route('/converter', methods=['GET', 'POST'])
@login_required
def converter():
    """Page du convertisseur"""
    user = get_current_user()
    suppliers = get_suppliers()

    # Gérer la sauvegarde des données de conversion en session (POST depuis home page)
    if request.method == 'POST':
        session['converter_amount'] = request.form.get('amount', '1000')
        session['converter_from_currency'] = request.form.get('from_currency', 'EUR')
        session['converter_to_currency'] = request.form.get('to_currency', 'MAD')
        session.modified = True
        return redirect(url_for('app.converter'))

    # Récupérer les valeurs depuis la session ou utiliser les valeurs par défaut
    initial_amount = session.pop('converter_amount', '1000')
    initial_from = session.pop('converter_from_currency', 'USD')
    initial_to = session.pop('converter_to_currency', 'MAD')

    # S'il n'y a pas de fournisseurs, en créer quelques-uns par défaut
    if not suppliers:
        db = get_db()
        if db is not None:
            default_suppliers = [
                {
                    "name": "Binance P2P",
                    "type": "crypto",
                    "rate": 10.12,
                    "fee": 0,
                    "logo": "https://cryptologos.cc/logos/binance-coin-bnb-logo.png?v=026",
                    "is_active": True
                },
                {
                    "name": "Banque Populaire",
                    "type": "bank",
                    "rate": 9.85,
                    "fee": 20,
                    "logo": "https://upload.wikimedia.org/wikipedia/fr/2/22/Logo_Banque_Populaire.png",
                    "is_active": True
                },
                {
                    "name": "Western Union",
                    "type": "transfer",
                    "rate": 9.95,
                    "fee": 15,
                    "logo": "https://www.westernunion.com/content/dam/wu/jm/logos/wu_logo.svg",
                    "is_active": True
                }
            ]
            db.suppliers.insert_many(default_suppliers)
            suppliers = get_suppliers()

    # Récupérer le wallet pour afficher les soldes
    wallet = get_user_wallet(session['user_id'])

    return render_template('app_converter.html',
        active_tab='converter',
        user=user,
        suppliers=suppliers,
        wallet=wallet,
        initial_amount=initial_amount,
        initial_from=initial_from,
        initial_to=initial_to
    )


@app_bp.route('/ai')
@login_required
def ai_forecast():
    """Page des prévisions IA"""
    user = get_current_user()
    settings = get_settings()

    return render_template('app_ai.html',
        active_tab='ai',
        user=user,
        ai_backend_url=settings.get('ai_backend_url', 'https://sarfx-backend-ai-618432953337.europe-west1.run.app')
    )


@app_bp.route('/rate-history')
@login_required
def rate_history():
    """Page de l'historique des taux avec graphiques"""
    user = get_current_user()
    return render_template('app_rate_history.html',
        active_tab='rate_history',
        user=user
    )


@app_bp.route('/rate-alerts')
@login_required
def rate_alerts():
    """Page de gestion des alertes de taux"""
    user = get_current_user()
    return render_template('app_rate_alerts.html',
        active_tab='rate_alerts',
        user=user
    )


@app_bp.route('/profile')
@login_required
def profile():
    """Page du profil utilisateur"""
    user = get_current_user()
    wallet = get_user_wallet(session['user_id'])
    transactions, error = get_user_transactions(session['user_id'], limit=5)
    if error:
        flash(error, 'error')
        transactions = []

    # Récupérer les cartes bancaires de l'utilisateur
    cards = []
    db = get_db()
    if db is not None:
        try:
            cards = list(db.user_cards.find({"user_id": str(session['user_id'])}).sort("created_at", -1))
        except Exception as e:
            print(f"Error fetching cards: {e}")

    return render_template('app_profile.html',
        active_tab='profile',
        user=user,
        wallet=wallet,
        transactions=transactions,
        cards=cards
    )


@app_bp.route('/settings')
@login_required
def settings():
    """Page des réglages"""
    user = get_current_user()
    app_settings = get_settings()

    # Récupérer les préférences utilisateur depuis la DB
    db = get_db()
    if db is not None and user:
        from bson import ObjectId
        try:
            user_prefs = db.users.find_one(
                {"_id": ObjectId(session['user_id'])},
                {"accent_color": 1, "theme": 1, "notification_preferences": 1}
            )
            if user_prefs:
                user['accent_color'] = user_prefs.get('accent_color', 'orange')
                user['theme'] = user_prefs.get('theme', 'light')
                user['notification_preferences'] = user_prefs.get('notification_preferences', {})
        except Exception:
            pass

    return render_template('app_settings.html',
        active_tab='settings',
        user=user,
        settings=app_settings
    )


@app_bp.route('/transactions')
@login_required
def transactions():
    """Page de l'historique des transactions avec pagination"""
    user = get_current_user()
    db = get_db()

    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 15

    # Get total count and stats
    total = 0
    stats = {'completed': 0, 'pending': 0, 'failed': 0}
    all_transactions = []

    if db is not None:
        try:
            user_id = str(session['user_id'])

            # Count total transactions
            total = db.transactions.count_documents({"user_id": user_id})

            # Get stats by status
            stats['completed'] = db.transactions.count_documents({"user_id": user_id, "status": "completed"})
            stats['pending'] = db.transactions.count_documents({"user_id": user_id, "status": "pending"})
            stats['failed'] = db.transactions.count_documents({"user_id": user_id, "status": "failed"})

            # Get paginated transactions
            skip = (page - 1) * per_page
            all_transactions = list(db.transactions.find(
                {"user_id": user_id}
            ).sort("created_at", -1).skip(skip).limit(per_page))

        except Exception as e:
            print(f"Erreur lors de la récupération des transactions: {e}")

    # Calculate pagination info
    pages = (total + per_page - 1) // per_page if total > 0 else 1
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': pages
    }

    return render_template('app_transactions.html',
        active_tab='transactions',
        user=user,
        transactions=all_transactions,
        pagination=pagination,
        stats=stats
    )


@app_bp.route('/beneficiaries')
@login_required
def beneficiaries():
    """Page des bénéficiaires et leur historique avec pagination"""
    try:
        user = get_current_user()
        if not user:
            return redirect(url_for('auth.login'))

        db = get_db()

        # Pagination pour l'historique de chaque bénéficiaire
        history_page = request.args.get('history_page', 1, type=int)
        history_per_page = 10
        selected_beneficiary = request.args.get('beneficiary_id', None)

        # Récupérer les bénéficiaires de l'utilisateur
        user_beneficiaries = []
        total_transfers = 0

        if db is not None:
            try:
                user_beneficiaries = list(db.beneficiaries.find({"user_id": str(session['user_id'])}))

                # Pour chaque bénéficiaire, récupérer son historique de transactions complet
                for benef in user_beneficiaries:
                    benef['_id'] = str(benef['_id'])

                    # Compter le total des transferts pour ce bénéficiaire
                    benef['transfer_count'] = db.transactions.count_documents({
                        "user_id": str(session['user_id']),
                        "beneficiary_id": benef['_id']
                    })
                    total_transfers += benef['transfer_count']

                    # Calculer le montant total envoyé
                    pipeline = [
                        {"$match": {
                            "user_id": str(session['user_id']),
                            "beneficiary_id": benef['_id']
                        }},
                        {"$group": {
                            "_id": None,
                            "total": {"$sum": "$amount"}
                        }}
                    ]
                    result = list(db.transactions.aggregate(pipeline))
                    benef['total_sent'] = result[0]['total'] if result else 0

                    # Récupérer les transactions avec pagination si c'est le bénéficiaire sélectionné
                    if selected_beneficiary == benef['_id']:
                        skip = (history_page - 1) * history_per_page
                        benef['transactions'] = list(db.transactions.find({
                            "user_id": str(session['user_id']),
                            "beneficiary_id": benef['_id']
                        }).sort("created_at", -1).skip(skip).limit(history_per_page))

                        # Info pagination
                        benef['pagination'] = {
                            'page': history_page,
                            'per_page': history_per_page,
                            'total': benef['transfer_count'],
                            'pages': (benef['transfer_count'] + history_per_page - 1) // history_per_page if benef['transfer_count'] > 0 else 1
                        }
                    else:
                        # Juste les 5 dernières par défaut
                        benef['transactions'] = list(db.transactions.find({
                            "user_id": str(session['user_id']),
                            "beneficiary_id": benef['_id']
                        }).sort("created_at", -1).limit(5))

            except Exception as e:
                print(f"Erreur lors de la récupération des bénéficiaires: {e}")
                user_beneficiaries = []

        return render_template('app_beneficiaries.html',
            active_tab='beneficiaries',
            user=user,
            beneficiaries=user_beneficiaries,
            total_transfers=total_transfers,
            selected_beneficiary=selected_beneficiary
        )
    except Exception as e:
        print(f"Erreur dans la route beneficiaries: {e}")
        from flask import flash
        flash('Erreur lors du chargement des bénéficiaires', 'error')
        return redirect(url_for('app.home'))


@app_bp.route('/beneficiaries/<beneficiary_id>/send', methods=['GET', 'POST'])
@login_required
def send_to_beneficiary(beneficiary_id):
    """Page et traitement de l'envoi d'argent à un bénéficiaire."""
    from app.services.wallet_service import get_wallet_by_user_id, withdraw_from_wallet, VALID_CURRENCIES
    from bson import ObjectId

    user = get_current_user()
    db = get_db()

    # Récupérer le bénéficiaire
    beneficiary = None
    if db is not None:
        try:
            beneficiary = db.beneficiaries.find_one({
                "_id": ObjectId(beneficiary_id),
                "user_id": str(session['user_id'])
            })
        except Exception:
            pass

    if not beneficiary:
        flash("Bénéficiaire non trouvé.", "error")
        return redirect(url_for('app.beneficiaries'))

    # Récupérer le wallet de l'utilisateur
    wallet, error = get_wallet_by_user_id(session['user_id'])
    if error:
        flash(error, 'error')
        return redirect(url_for('app.beneficiaries'))

    if request.method == 'POST':
        currency = request.form.get('currency', '').upper()
        amount = request.form.get('amount', 0, type=float)
        note = request.form.get('note', '')

        # Validation
        if not currency or currency not in VALID_CURRENCIES:
            flash('Devise invalide.', 'error')
            return redirect(url_for('app.send_to_beneficiary', beneficiary_id=beneficiary_id))

        if amount <= 0:
            flash('Le montant doit être supérieur à 0.', 'error')
            return redirect(url_for('app.send_to_beneficiary', beneficiary_id=beneficiary_id))

        # Vérifier le solde disponible
        balances = wallet.get('balances', {})
        current_balance = float(balances.get(currency, 0))

        if current_balance < amount:
            flash(f'Solde insuffisant! Disponible: {current_balance:.2f} {currency}. Vous essayez d\'envoyer {amount:.2f} {currency}.', 'error')
            return redirect(url_for('app.send_to_beneficiary', beneficiary_id=beneficiary_id))

        # Effectuer le retrait (débit)
        success, message = withdraw_from_wallet(
            user_id=session['user_id'],
            currency=currency,
            amount=amount,
            destination=f"beneficiary:{beneficiary_id}"
        )

        if not success:
            flash(f'Erreur: {message}', 'error')
            return redirect(url_for('app.send_to_beneficiary', beneficiary_id=beneficiary_id))

        # Enregistrer la transaction de transfert
        try:
            transfer_record = {
                "transaction_id": f"TRF-{str(uuid.uuid4())[:8].upper()}",
                "user_id": str(session['user_id']),
                "beneficiary_id": beneficiary_id,
                "beneficiary_name": beneficiary.get('name', 'Inconnu'),
                "beneficiary_bank": beneficiary.get('bank', ''),
                "beneficiary_iban": beneficiary.get('iban', ''),
                "type": "transfer",
                "currency": currency,
                "amount": amount,
                "note": note,
                "status": "completed",
                "created_at": datetime.utcnow()
            }
            db.transactions.insert_one(transfer_record)
        except Exception as e:
            print(f"Erreur enregistrement transaction: {e}")

        flash(f'✅ Transfert réussi! {amount:.2f} {currency} envoyé à {beneficiary.get("name", "Bénéficiaire")}.', 'success')
        return redirect(url_for('app.beneficiaries'))

    # GET - Afficher le formulaire
    return render_template('app_send_beneficiary.html',
        active_tab='beneficiaries',
        user=user,
        beneficiary=beneficiary,
        wallet=wallet,
        currencies=VALID_CURRENCIES
    )


@app_bp.route('/bank-settings')
@login_required
def bank_settings():
    """Page de configuration API pour les responsables banque"""
    user = get_current_user()

    # Vérifier que l'utilisateur est bank_respo
    if user.get('role') != 'bank_respo':
        return redirect(url_for('app.home'))

    db = get_db()
    bank = None
    if db is not None:
        # Récupérer la banque associée à ce responsable
        bank_code = user.get('bank_code')
        if bank_code:
            bank = db.banks.find_one({"code": bank_code})

    return render_template('app_bank_settings.html',
        active_tab='bank_settings',
        user=user,
        bank=bank
    )


@app_bp.route('/wallets')
@login_required
def wallets():
    """Displays the multi-currency wallets page."""
    user = get_current_user()
    from app.services.wallet_service import get_total_balance_in_usd, get_user_transactions

    total_balance, balance_error = get_total_balance_in_usd(session['user_id'])
    if balance_error:
        flash(balance_error, 'error')

    transactions, trans_error = get_user_transactions(session['user_id'], limit=10)
    if trans_error:
        flash(trans_error, 'error')

    return render_template('app_wallets.html',
        active_tab='wallets',
        user=user,
        total_balance=total_balance,
        transactions=transactions
    )


@app_bp.route('/wallets/add-currency', methods=['POST'])
@login_required
def add_wallet_currency():
    """Adds a new currency to the user's wallet."""
    from app.services.wallet_service import add_currency_to_wallet

    currency = request.form.get('currency')
    if not currency:
        flash('No currency specified.', 'error')
        return redirect(url_for('app.wallets'))

    success, message = add_currency_to_wallet(session['user_id'], currency)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('app.wallets'))


@app_bp.route('/wallets/remove-currency', methods=['POST'])
@login_required
def remove_wallet_currency():
    """Removes a currency from the user's wallet if the balance is zero."""
    from app.services.wallet_service import remove_currency_from_wallet

    currency = request.form.get('currency')
    if not currency:
        flash('No currency specified.', 'error')
        return redirect(url_for('app.wallets'))

    success, message = remove_currency_from_wallet(session['user_id'], currency)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('app.wallets'))


@app_bp.route('/wallets/set-primary-currency', methods=['POST'])
@login_required
def set_primary_currency():
    """Sets a currency as the primary currency for the user."""
    from app.services.wallet_service import set_primary_currency as set_primary_currency_service

    currency = request.form.get('currency')
    if not currency:
        flash('No currency specified.', 'error')
        return redirect(url_for('app.wallets'))

    success, message = set_primary_currency_service(session['user_id'], currency)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('app.wallets'))


@app_bp.route('/wallets/swap', methods=['GET', 'POST'])
@login_required
def wallet_swap():
    """Page and handler for currency swap within wallet."""
    from app.services.wallet_service import (
        get_wallet_by_user_id, calculate_swap_preview, execute_swap,
        get_wallet_swap_rates, VALID_CURRENCIES
    )
    from flask import jsonify

    user = get_current_user()
    wallet, error = get_wallet_by_user_id(session['user_id'])

    if error:
        flash(error, 'error')
        return redirect(url_for('app.wallets'))

    if request.method == 'POST':
        from_currency = request.form.get('from_currency', '').upper()
        to_currency = request.form.get('to_currency', '').upper()
        amount = float(request.form.get('amount', 0))

        if not from_currency or not to_currency or amount <= 0:
            flash('Veuillez remplir tous les champs correctement.', 'error')
            return redirect(url_for('app.wallet_swap'))

        result, swap_error = execute_swap(session['user_id'], from_currency, to_currency, amount)

        if swap_error:
            flash(swap_error, 'error')
        else:
            flash(
                f"Swap réussi! {amount} {from_currency} → {result['amount_received']:.2f} {to_currency}",
                'success'
            )
            return redirect(url_for('app.wallets'))

    # Get swap rates for display
    swap_rates, _ = get_wallet_swap_rates(session['user_id'])

    return render_template('app_wallet_swap.html',
        active_tab='wallets',
        user=user,
        wallet=wallet,
        swap_rates=swap_rates or [],
        currencies=VALID_CURRENCIES
    )


@app_bp.route('/wallets/transactions/<currency>')
@login_required
def wallet_transactions(currency):
    """API endpoint to get transactions for a specific currency."""
    from app.services.wallet_service import get_user_transactions
    from flask import jsonify

    transactions, error = get_user_transactions(session['user_id'], currency=currency, limit=50)

    if error:
        return jsonify({"error": error}), 500

    # Convert ObjectId and datetime objects for JSON serialization
    for tx in transactions:
        tx['_id'] = str(tx['_id'])
        tx['created_at'] = tx['created_at'].isoformat() if 'created_at' in tx else None
        tx['updated_at'] = tx['updated_at'].isoformat() if 'updated_at' in tx else None


    return jsonify(transactions=transactions)


@app_bp.route('/wallets/recharge', methods=['GET', 'POST'])
@login_required
def wallet_recharge():
    """Page de recharge du portefeuille par carte bancaire (simulée)."""
    from app.services.wallet_service import get_wallet_by_user_id, deposit_to_wallet, VALID_CURRENCIES

    user = get_current_user()
    wallet, error = get_wallet_by_user_id(session['user_id'])

    if error:
        flash(error, 'error')
        return redirect(url_for('app.wallets'))

    if request.method == 'POST':
        currency = request.form.get('currency', '').upper()
        amount = request.form.get('amount', 0, type=float)
        card_number = request.form.get('card_number', '').replace(' ', '')
        card_expiry = request.form.get('card_expiry', '')
        card_cvv = request.form.get('card_cvv', '')
        card_name = request.form.get('card_name', '')

        # Validation
        if not currency or currency not in VALID_CURRENCIES:
            flash('Devise invalide.', 'error')
            return redirect(url_for('app.wallet_recharge'))

        if amount <= 0 or amount > 10000:
            flash('Le montant doit être entre 0.01 et 10,000.', 'error')
            return redirect(url_for('app.wallet_recharge'))

        if len(card_number) < 16:
            flash('Numéro de carte invalide.', 'error')
            return redirect(url_for('app.wallet_recharge'))

        # Simulation de paiement (toujours succès pour la démo)
        payment_reference = f"CARD-{card_number[-4:]}-{int(amount*100)}"

        success, message = deposit_to_wallet(
            user_id=session['user_id'],
            currency=currency,
            amount=amount,
            source='card',
            reference=payment_reference
        )

        if not success:
            flash(f'Erreur lors du crédit: {message}', 'error')
        else:
            flash(f'✅ Recharge réussie! {amount:.2f} {currency} ajoutés à votre portefeuille.', 'success')
            return redirect(url_for('app.wallets'))

        return redirect(url_for('app.wallet_recharge'))

    return render_template('app_wallet_recharge.html',
        active_tab='wallets',
        user=user,
        wallet=wallet,
        currencies=VALID_CURRENCIES
    )


@app_bp.route('/atms')
@login_required
def atms():
    """Page de recherche des DABs partenaires"""
    user = get_current_user()
    db = get_db()

    banks = []
    cities = set()
    atm_count = 0

    if db is not None:
        # Récupérer les banques partenaires avec leurs ATMs
        if 'banks' in db.list_collection_names():
            banks = list(db.banks.find({"is_active": True}))
            for bank in banks:
                bank['_id'] = str(bank['_id'])
                cities.add(bank.get('city', 'Unknown'))
                atm_count += bank.get('atm_count', 0)

    return render_template('app_atms.html',
        active_tab='atms',
        user=user,
        banks=banks,
        cities=sorted(list(cities)),
        atm_count=atm_count
    )


@app_bp.route('/faq')
@login_required
def faq():
    """Page des questions fréquentes"""
    user = get_current_user()

    return render_template('app_faq.html',
        active_tab='faq',
        user=user
    )


# ==================== ROUTES POUR LES RÔLES ADMINISTRATIFS ====================

@app_bp.route('/admin-sr-bank')
@role_required('admin', 'admin_sr_bank')
def admin_sr_bank():
    """Dashboard pour les administrateurs senior de banque"""
    user = get_current_user()
    db = get_db()

    # Statistiques bancaires
    stats = {
        'total_banks': 0,
        'total_atms': 0,
        'total_users': 0,
        'total_transactions': 0,
        'total_volume': 0
    }

    if db is not None:
        stats['total_banks'] = db.banks.count_documents({})
        stats['total_atms'] = db.atms.count_documents({}) if 'atms' in db.list_collection_names() else 0
        stats['total_users'] = db.users.count_documents({'role': {'$in': ['user', 'bank_user']}})
        stats['total_transactions'] = db.transactions.count_documents({})

        # Calculer le volume total
        transactions = db.transactions.find({'status': 'completed'})
        for tx in transactions:
            stats['total_volume'] += float(tx.get('amount', 0))

    return render_template('admin/sr_bank_dashboard_2026.html',
        user=user,
        stats=stats
    )


@app_bp.route('/admin-associate-bank')
@role_required('admin', 'admin_sr_bank', 'admin_associate_bank', 'bank_respo')
def admin_associate_bank():
    """Dashboard pour les administrateurs associés de banque avec contrôle API"""
    user = get_current_user()
    db = get_db()

    # Récupérer la banque associée à l'utilisateur
    user_bank = None
    bank_stats = {
        'atm_count': 0,
        'user_count': 0,
        'transaction_count': 0,
        'api_calls': 0
    }

    if db is not None and user.get('bank_code'):
        user_bank = db.banks.find_one({'code': user['bank_code']})
        if user_bank:
            user_bank['_id'] = str(user_bank['_id'])
            bank_stats['atm_count'] = db.atms.count_documents({'bank_code': user['bank_code']}) if 'atms' in db.list_collection_names() else 0
            bank_stats['user_count'] = db.users.count_documents({'bank_code': user['bank_code']})
            bank_stats['transaction_count'] = db.transactions.count_documents({'bank_code': user['bank_code']})
            # En production, récupérer depuis une collection api_logs
            bank_stats['api_calls'] = 0

    return render_template('admin/associate_bank_dashboard_2026.html',
        user=user,
        bank=user_bank,
        stats=bank_stats
    )


@app_bp.route('/admin-associate-bank/api-control')
@role_required('admin', 'admin_sr_bank', 'admin_associate_bank', 'bank_respo')
def admin_api_control():
    """Page de contrôle API pour les administrateurs associés de banque"""
    user = get_current_user()
    db = get_db()

    # Récupérer les informations API de la banque
    api_info = {
        'api_key': None,
        'api_secret': None,
        'webhook_url': None,
        'is_active': False,
        'rate_limit': 1000,
        'last_sync': None
    }

    if db is not None and user.get('bank_code'):
        bank = db.banks.find_one({'code': user['bank_code']})
        if bank:
            api_info.update({
                'api_key': bank.get('api_key'),
                'api_secret': bank.get('api_secret'),
                'webhook_url': bank.get('webhook_url'),
                'is_active': bank.get('api_active', False),
                'rate_limit': bank.get('api_rate_limit', 1000),
                'last_sync': bank.get('last_api_sync')
            })

    return render_template('admin/api_control_2026.html',
        user=user,
        api_info=api_info
    )


@app_bp.route('/admin-associate-bank/atm-management')
@role_required('admin', 'admin_sr_bank', 'admin_associate_bank', 'bank_respo')
def admin_atm_management():
    """Gestion des ATMs pour les administrateurs de banque"""
    user = get_current_user()
    db = get_db()

    atms = []
    if db is not None and user.get('bank_code'):
        if 'atms' in db.list_collection_names():
            atms = list(db.atms.find({'bank_code': user['bank_code']}))
            for atm in atms:
                atm['_id'] = str(atm['_id'])

    return render_template('admin/atm_management_2026.html',
        user=user,
        atms=atms
    )


@app_bp.route('/associate-bank', methods=['GET', 'POST'])
@login_required
def associate_bank():
    """Associer un user banque à une banque et donner accès à l'API banque"""
    user = get_current_user()
    db = get_db()
    banks = list(db.banks.find({"is_active": True})) if db is not None else []
    if request.method == 'POST':
        bank_code = request.form.get('bank_code')
        if bank_code:
            db.users.update_one({"_id": user['_id']}, {"$set": {"bank_code": bank_code, "role": "bank_user"}})
            flash("Association à la banque réussie !", "success")
            return redirect(url_for('app.bank_settings'))
        else:
            flash("Veuillez sélectionner une banque.", "error")
    return render_template('app_associate_bank.html', user=user, banks=banks)


# ==================== PAGES DE DÉTAILS ====================

@app_bp.route('/banks')
@login_required
def banks_list():
    """Page listant toutes les banques partenaires (accessible à tous)"""
    user = get_current_user()
    db = get_db()

    banks = []
    bank_stats = {}

    if db is not None:
        # Récupérer toutes les banques actives
        banks = list(db.banks.find({"is_active": True}).sort("name", 1))

        # Pour chaque banque, récupérer le nombre d'ATMs
        for bank in banks:
            bank['_id'] = str(bank['_id'])
            bank_code = bank.get('code', bank.get('bank_code', ''))
            if bank_code and 'atm_locations' in db.list_collection_names():
                atm_count = db.atm_locations.count_documents({"bank_code": bank_code})
                bank['atm_count'] = atm_count
            else:
                bank['atm_count'] = 0

    return render_template('app_banks.html',
        active_tab='banks',
        user=user,
        banks=banks
    )


@app_bp.route('/banks/<bank_id>')
@login_required
def bank_detail(bank_id):
    """Page de détails d'une banque"""
    import logging
    from bson import ObjectId
    from bson.errors import InvalidId
    logger = logging.getLogger(__name__)

    user = get_current_user()
    db = get_db()

    if db is None:
        logger.error("DB is None in bank_detail")
        flash("Erreur de connexion à la base de données", "error")
        return redirect(url_for('app.banks_list'))

    # Récupérer la banque - essayer par ID, puis par code
    bank = None
    try:
        bank = db.banks.find_one({"_id": ObjectId(bank_id)})
        logger.info(f"Bank search by ID {bank_id}: {'found' if bank else 'not found'}")
    except Exception as e:
        logger.warning(f"Bank search by ID failed: {e}")

    # Si pas trouvé par ID, chercher par code ou bank_code
    if not bank:
        bank = db.banks.find_one({"code": bank_id})
        logger.info(f"Bank search by code {bank_id}: {'found' if bank else 'not found'}")
    if not bank:
        bank = db.banks.find_one({"bank_code": bank_id})
        logger.info(f"Bank search by bank_code {bank_id}: {'found' if bank else 'not found'}")

    if not bank:
        logger.error(f"Bank not found for ID: {bank_id}")
        flash("Banque non trouvée", "error")
        return redirect(url_for('app.banks_list'))

    logger.info(f"Bank found: {bank.get('name')}")
    bank['_id'] = str(bank['_id'])

    # Mapping entre codes banques et bank_codes ATM
    BANK_CODE_MAPPING = {
        'AWB': 'attijariwafa',
        'ATTIJARIWAFA': 'attijariwafa',
        'BOA': 'boa',
        'CIH': 'cih',
        'BP': 'banque_populaire',
        'BMCE': 'bmci',
        'BMCI': 'bmci',
        'SG': 'sg',
    }

    bank_code = bank.get('code', bank.get('bank_code', ''))
    # Convertir le code banque en bank_code ATM
    atm_bank_code = BANK_CODE_MAPPING.get(bank_code.upper(), bank_code.lower()) if bank_code else ''

    # Récupérer les ATMs de cette banque
    atms = []
    atm_count = 0
    if atm_bank_code and 'atm_locations' in db.list_collection_names():
        atms = list(db.atm_locations.find({"bank_code": atm_bank_code}).limit(20))
        atm_count = db.atm_locations.count_documents({"bank_code": atm_bank_code})
        logger.info(f"ATMs found for bank_code '{atm_bank_code}': {atm_count}")
        for atm in atms:
            atm['_id'] = str(atm['_id'])

    # Statistiques
    stats = {
        'atm_count': atm_count,
        'cities': len(set(atm.get('city', '') for atm in atms if atm.get('city'))),
    }

    return render_template('app_bank_detail.html',
        active_tab='banks',
        user=user,
        bank=bank,
        atms=atms,
        stats=stats
    )


@app_bp.route('/transactions/<transaction_id>')
@login_required
def transaction_detail(transaction_id):
    """Page de détails d'une transaction"""
    from bson import ObjectId
    from bson.errors import InvalidId
    user = get_current_user()
    db = get_db()

    if db is None:
        flash("Erreur de connexion à la base de données", "error")
        return redirect(url_for('app.transactions'))

    # Récupérer la transaction
    try:
        transaction = db.transactions.find_one({
            "_id": ObjectId(transaction_id),
            "user_id": str(session['user_id'])
        })
    except:
        transaction = None

    if not transaction:
        flash("Transaction non trouvée", "error")
        return redirect(url_for('app.transactions'))

    transaction['_id'] = str(transaction['_id'])

    # Récupérer les infos du bénéficiaire si présent
    beneficiary = None
    if transaction.get('beneficiary_id'):
        try:
            beneficiary = db.beneficiaries.find_one({"_id": ObjectId(transaction['beneficiary_id'])})
            if beneficiary:
                beneficiary['_id'] = str(beneficiary['_id'])
        except:
            pass

    # Récupérer l'historique des statuts si disponible
    status_history = transaction.get('status_history', [])

    return render_template('app_transaction_detail.html',
        active_tab='transactions',
        user=user,
        transaction=transaction,
        beneficiary=beneficiary,
        status_history=status_history
    )
