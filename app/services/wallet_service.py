"""
Service layer for wallet management.
Handles all business logic related to user wallets, balances, and transactions.
"""
from datetime import datetime
import uuid
import requests
from flask import current_app
from app.services.db_service import get_db

# Liste centralisée des devises valides
VALID_CURRENCIES = ['USD', 'EUR', 'MAD', 'GBP', 'CHF', 'CAD', 'AED', 'SAR']

# Taux de fallback pour les conversions
FALLBACK_RATES = {
    'EUR_USD': 1.0850, 'USD_EUR': 0.9217,
    'EUR_MAD': 10.8245, 'MAD_EUR': 0.0924,
    'USD_MAD': 10.0523, 'MAD_USD': 0.0995,
    'GBP_MAD': 12.6721, 'MAD_GBP': 0.0789,
    'CHF_MAD': 11.2345, 'MAD_CHF': 0.0890,
    'CAD_MAD': 7.4521, 'MAD_CAD': 0.1342,
    'AED_MAD': 2.7341, 'MAD_AED': 0.3658,
    'SAR_MAD': 2.6734, 'MAD_SAR': 0.3741,
    'GBP_USD': 1.2650, 'USD_GBP': 0.7905,
    'GBP_EUR': 1.1662, 'EUR_GBP': 0.8575,
}

# Commission SarfX sur les swaps (0.5%)
SWAP_FEE_PERCENTAGE = 0.005


def get_wallet_by_user_id(user_id):
    """
    Retrieves a user's wallet by their user ID.
    If a wallet doesn't exist, it creates one.
    """
    db = get_db()
    if db is None:
        current_app.logger.error("Database connection is not available.")
        return None, "Database connection failed."

    user_id_str = str(user_id)
    wallet = db.wallets.find_one({"user_id": user_id_str})

    if not wallet:
        return _create_wallet(user_id_str, db)

    return wallet, None


def create_wallet(user_id, email=None):
    """
    Public function to create a wallet for a new user.
    Called from auth_routes when a new user registers.
    
    Args:
        user_id: The user's ID (string)
        email: The user's email (optional, for logging)
    
    Returns:
        tuple: (wallet, error_message)
    """
    db = get_db()
    if db is None:
        return None, "Database connection failed"
    
    return _create_wallet(user_id, db)


def _create_wallet(user_id, db):
    """
    Creates a new wallet for a user with default currencies.
    This is an internal function called by get_wallet_by_user_id.
    """
    try:
        wallet = {
            "wallet_id": str(uuid.uuid4()),
            "user_id": user_id,
            "balances": {
                "USD": 0.0,
                "EUR": 0.0,
                "MAD": 0.0,
            },
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        db.wallets.insert_one(wallet)
        current_app.logger.info(f"Created a new wallet for user_id: {user_id}")
        return wallet, None
    except Exception as e:
        current_app.logger.error(f"Failed to create wallet for user_id {user_id}: {e}")
        return None, "Wallet creation failed."


def add_currency_to_wallet(user_id, currency):
    """
    Adds a new currency to a user's wallet with a zero balance.
    """
    if currency not in VALID_CURRENCIES:
        return False, f"Invalid currency: {currency}."

    db = get_db()
    if db is None:
        return False, "Database connection failed."

    wallet, error = get_wallet_by_user_id(user_id)
    if error:
        return False, error

    if currency in wallet.get('balances', {}):
        return False, f"Currency {currency} already exists in the wallet."

    try:
        db.wallets.update_one(
            {"user_id": str(user_id)},
            {
                "$set": {
                    f"balances.{currency}": 0.0,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return True, f"Currency {currency} added successfully."
    except Exception as e:
        current_app.logger.error(f"Failed to add currency {currency} for user {user_id}: {e}")
        return False, "An unexpected error occurred."


def remove_currency_from_wallet(user_id, currency):
    """
    Removes a currency from a user's wallet, only if the balance is zero.
    """
    if currency not in VALID_CURRENCIES:
        return False, f"Invalid currency: {currency}."

    db = get_db()
    if db is None:
        return False, "Database connection failed."

    wallet, error = get_wallet_by_user_id(user_id)
    if error:
        return False, error

    balances = wallet.get('balances', {})
    if currency not in balances:
        return False, f"Currency {currency} not found in the wallet."

    if balances[currency] != 0:
        return False, "Cannot remove currency with a non-zero balance."

    try:
        db.wallets.update_one(
            {"user_id": str(user_id)},
            {
                "$unset": {f"balances.{currency}": ""},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return True, f"Currency {currency} removed successfully."
    except Exception as e:
        current_app.logger.error(f"Failed to remove currency {currency} for user {user_id}: {e}")
        return False, "An unexpected error occurred."


def get_user_transactions(user_id, currency=None, limit=50):
    """
    Retrieves transaction history for a user.
    Can be filtered by a specific currency.
    """
    db = get_db()
    if db is None:
        current_app.logger.error("Database connection is not available.")
        return [], "Database connection failed."

    user_id_str = str(user_id)
    query = {"$or": [{"sender_id": user_id_str}, {"recipient_id": user_id_str}]}

    if currency:
        query["currency"] = currency

    try:
        transactions = list(db.transactions.find(query).sort("created_at", -1).limit(limit))
        return transactions, None
    except Exception as e:
        current_app.logger.error(f"Failed to retrieve transactions for user {user_id_str}: {e}")
        return [], "Failed to retrieve transactions."


def get_total_balance_in_usd(user_id):
    """
    Calculates the total wallet balance in a target currency (USD).
    """
    from app.services.exchange_service import get_all_rates

    wallet, error = get_wallet_by_user_id(user_id)
    if error:
        return {"total_usd": 0, "wallets": []}, error

    primary_currency = wallet.get('primary_currency', 'USD')

    rates_data = get_all_rates('USD')
    if not rates_data.get('success'):
        return {"total_usd": 0, "wallets": []}, "Could not fetch exchange rates."

    rates = rates_data['rates']
    total_usd = 0
    wallet_details = []

    balances = wallet.get('balances', {})
    for currency, balance in balances.items():
        balance = float(balance or 0)
        # The rate from get_all_rates('USD') is how many of that currency you get for 1 USD
        rate_from_usd = rates.get(currency, 1.0)
        usd_value = balance / rate_from_usd if rate_from_usd != 0 else 0

        total_usd += usd_value
        wallet_details.append({
            "currency": currency,
            "balance": balance,
            "usd_value": usd_value,
            "is_primary": currency == primary_currency
        })

    # Sort wallets by USD value
    wallet_details.sort(key=lambda x: x['usd_value'], reverse=True)

    return {
        "total_usd": round(total_usd, 2),
        "wallets": wallet_details
    }, None


def set_primary_currency(user_id, currency):
    """
    Sets a currency as the primary currency for a user's wallet.
    """
    if currency not in VALID_CURRENCIES:
        return False, f"Invalid currency: {currency}."

    db = get_db()
    if db is None:
        return False, "Database connection failed."

    wallet, error = get_wallet_by_user_id(user_id)
    if error:
        return False, error

    if currency not in wallet.get('balances', {}):
        return False, f"Currency {currency} does not exist in the wallet."

    try:
        db.wallets.update_one(
            {"user_id": str(user_id)},
            {
                "$set": {
                    "primary_currency": currency,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return True, f"{currency} has been set as your primary currency."
    except Exception as e:
        current_app.logger.error(f"Failed to set primary currency for user {user_id}: {e}")
        return False, "An unexpected error occurred."


# ============================================================
# SWAP / EXCHANGE FUNCTIONS
# ============================================================

def get_swap_rate(from_currency, to_currency):
    """
    Gets the exchange rate for swapping between currencies.
    Tries the AI backend first, then falls back to static rates.
    """
    from app.config import Config

    if from_currency == to_currency:
        return 1.0, 'same_currency'

    # Try AI Backend first
    try:
        ai_url = getattr(Config, 'AI_BACKEND_URL', 'http://localhost:8087')
        timeout = getattr(Config, 'AI_BACKEND_TIMEOUT', 5)

        response = requests.get(
            f"{ai_url}/smart-rate/{from_currency}/{to_currency}",
            timeout=timeout
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('sarfx_offer', {}).get('rate'):
                return data['sarfx_offer']['rate'], 'ai_backend'
    except requests.RequestException as e:
        current_app.logger.warning(f"AI Backend unavailable for swap rate: {e}")
    except Exception as e:
        current_app.logger.warning(f"Error fetching AI rate: {e}")

    # Fallback to static rates
    key = f"{from_currency}_{to_currency}"
    if key in FALLBACK_RATES:
        return FALLBACK_RATES[key], 'fallback'

    # Try inverse rate
    inverse_key = f"{to_currency}_{from_currency}"
    if inverse_key in FALLBACK_RATES:
        return 1.0 / FALLBACK_RATES[inverse_key], 'fallback_inverse'

    return None, 'rate_not_found'


def calculate_swap_preview(from_currency, to_currency, amount):
    """
    Calculates a preview of a swap operation without executing it.
    Returns the expected outcome including fees.
    """
    if from_currency not in VALID_CURRENCIES or to_currency not in VALID_CURRENCIES:
        return None, "Invalid currency."

    if amount <= 0:
        return None, "Amount must be positive."

    rate, source = get_swap_rate(from_currency, to_currency)
    if rate is None:
        return None, f"Exchange rate not available for {from_currency}/{to_currency}."

    # Calculate fee
    fee_amount = amount * SWAP_FEE_PERCENTAGE
    net_amount = amount - fee_amount

    # Calculate received amount
    received_amount = net_amount * rate

    return {
        'from_currency': from_currency,
        'to_currency': to_currency,
        'amount': amount,
        'rate': rate,
        'rate_source': source,
        'fee_percentage': SWAP_FEE_PERCENTAGE * 100,
        'fee_amount': round(fee_amount, 4),
        'net_amount': round(net_amount, 4),
        'received_amount': round(received_amount, 4),
        'effective_rate': round(received_amount / amount, 6) if amount > 0 else 0
    }, None


def execute_swap(user_id, from_currency, to_currency, amount):
    """
    Executes a swap between two currencies in the user's wallet.
    Deducts from one currency and adds to another.
    """
    if from_currency not in VALID_CURRENCIES or to_currency not in VALID_CURRENCIES:
        return None, "Invalid currency."

    if from_currency == to_currency:
        return None, "Cannot swap same currency."

    if amount <= 0:
        return None, "Amount must be positive."

    db = get_db()
    if db is None:
        return None, "Database connection failed."

    # Get user's wallet
    wallet, error = get_wallet_by_user_id(user_id)
    if error:
        return None, error

    balances = wallet.get('balances', {})

    # Check if user has both currencies
    if from_currency not in balances:
        return None, f"You don't have a {from_currency} wallet."

    if to_currency not in balances:
        return None, f"You don't have a {to_currency} wallet. Please add it first."

    # Check sufficient balance
    current_balance = float(balances.get(from_currency, 0))
    if current_balance < amount:
        return None, f"Insufficient {from_currency} balance. Available: {current_balance:.2f}"

    # Calculate swap
    preview, preview_error = calculate_swap_preview(from_currency, to_currency, amount)
    if preview_error:
        return None, preview_error

    # Execute the swap atomically
    try:
        new_from_balance = current_balance - amount
        new_to_balance = float(balances.get(to_currency, 0)) + preview['received_amount']

        # Update wallet
        result = db.wallets.update_one(
            {"user_id": str(user_id)},
            {
                "$set": {
                    f"balances.{from_currency}": round(new_from_balance, 4),
                    f"balances.{to_currency}": round(new_to_balance, 4),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            return None, "Failed to update wallet."

        # Create transaction record
        transaction = {
            "transaction_id": f"SWAP-{str(uuid.uuid4())[:8].upper()}",
            "user_id": str(user_id),
            "sender_id": str(user_id),
            "recipient_id": str(user_id),
            "type": "swap",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "amount": amount,
            "rate": preview['rate'],
            "fee": preview['fee_amount'],
            "final_amount": preview['received_amount'],
            "status": "completed",
            "rate_source": preview['rate_source'],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        db.transactions.insert_one(transaction)

        current_app.logger.info(
            f"Swap executed: {amount} {from_currency} → {preview['received_amount']} {to_currency} "
            f"for user {user_id}"
        )

        return {
            "success": True,
            "transaction_id": transaction['transaction_id'],
            "from_currency": from_currency,
            "to_currency": to_currency,
            "amount_sent": amount,
            "amount_received": preview['received_amount'],
            "rate": preview['rate'],
            "fee": preview['fee_amount'],
            "new_balance_from": round(new_from_balance, 4),
            "new_balance_to": round(new_to_balance, 4)
        }, None

    except Exception as e:
        current_app.logger.error(f"Swap execution failed for user {user_id}: {e}")
        return None, "Swap execution failed. Please try again."


def get_wallet_swap_rates(user_id):
    """
    Gets all available swap rates for currencies in the user's wallet.
    """
    wallet, error = get_wallet_by_user_id(user_id)
    if error:
        return None, error

    balances = wallet.get('balances', {})
    currencies = list(balances.keys())

    swap_rates = []
    for from_curr in currencies:
        for to_curr in currencies:
            if from_curr != to_curr:
                rate, source = get_swap_rate(from_curr, to_curr)
                if rate:
                    swap_rates.append({
                        'from': from_curr,
                        'to': to_curr,
                        'rate': rate,
                        'source': source,
                        'fee_percentage': SWAP_FEE_PERCENTAGE * 100
                    })

    return swap_rates, None


def deposit_to_wallet(user_id, currency, amount, source="manual", reference=None):
    """
    Deposits funds to a user's wallet.
    Used by admin or payment systems.

    Args:
        user_id: User identifier
        currency: Currency code (USD, EUR, etc.)
        amount: Amount to deposit
        source: Source of deposit (manual, card, bank, etc.)
        reference: Payment reference/transaction ID
    """
    if currency not in VALID_CURRENCIES:
        return False, f"Invalid currency: {currency}."

    if amount <= 0:
        return False, "Amount must be positive."

    db = get_db()
    if db is None:
        return False, "Database connection failed."

    wallet, error = get_wallet_by_user_id(user_id)
    if error:
        return False, error

    balances = wallet.get('balances', {})
    if currency not in balances:
        return False, f"Currency {currency} not in wallet. Add it first."

    try:
        current_balance = float(balances.get(currency, 0))
        new_balance = current_balance + amount

        db.wallets.update_one(
            {"user_id": str(user_id)},
            {
                "$set": {
                    f"balances.{currency}": round(new_balance, 4),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Record transaction
        transaction = {
            "transaction_id": f"DEP-{str(uuid.uuid4())[:8].upper()}",
            "user_id": str(user_id),
            "recipient_id": str(user_id),
            "type": "deposit",
            "currency": currency,
            "amount": amount,
            "status": "completed",
            "source": source,
            "reference": reference,
            "created_at": datetime.utcnow()
        }
        db.transactions.insert_one(transaction)

        return True, f"Deposited {amount} {currency} successfully."

    except Exception as e:
        current_app.logger.error(f"Deposit failed for user {user_id}: {e}")
        return False, "Deposit failed."


def withdraw_from_wallet(user_id, currency, amount, destination="manual"):
    """
    Withdraws funds from a user's wallet.
    """
    if currency not in VALID_CURRENCIES:
        return False, f"Invalid currency: {currency}."

    if amount <= 0:
        return False, "Amount must be positive."

    db = get_db()
    if db is None:
        return False, "Database connection failed."

    wallet, error = get_wallet_by_user_id(user_id)
    if error:
        return False, error

    balances = wallet.get('balances', {})
    current_balance = float(balances.get(currency, 0))

    if current_balance < amount:
        return False, f"Insufficient balance. Available: {current_balance:.2f} {currency}"

    try:
        new_balance = current_balance - amount

        db.wallets.update_one(
            {"user_id": str(user_id)},
            {
                "$set": {
                    f"balances.{currency}": round(new_balance, 4),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Record transaction
        transaction = {
            "transaction_id": f"WDR-{str(uuid.uuid4())[:8].upper()}",
            "user_id": str(user_id),
            "sender_id": str(user_id),
            "type": "withdrawal",
            "currency": currency,
            "amount": amount,
            "status": "completed",
            "destination": destination,
            "created_at": datetime.utcnow()
        }
        db.transactions.insert_one(transaction)

        return True, f"Withdrawn {amount} {currency} successfully."

    except Exception as e:
        current_app.logger.error(f"Withdrawal failed for user {user_id}: {e}")
        return False, "Withdrawal failed."


# ============================================================
# ADMIN / HISTORY FUNCTIONS
# ============================================================

def get_wallet_history(wallet_id, limit=100):
    """
    Gets the adjustment history for a specific wallet.
    Used by admin to track balance changes.
    """
    db = get_db()
    if db is None:
        return []

    try:
        history = list(
            db.wallet_adjustments
            .find({"wallet_id": wallet_id})
            .sort("created_at", -1)
            .limit(limit)
        )

        # Convert ObjectId to string for JSON serialization
        for item in history:
            item['_id'] = str(item['_id'])

        return history
    except Exception as e:
        current_app.logger.error(f"Failed to get wallet history: {e}")
        return []


def get_all_wallets_summary():
    """
    Gets a summary of all wallets for admin dashboard.
    """
    db = get_db()
    if db is None:
        return []

    try:
        wallets = list(db.wallets.find())

        summary = []
        for wallet in wallets:
            # Get user info
            user_id = wallet.get('user_id')
            user = None
            if user_id:
                try:
                    from bson import ObjectId
                    if isinstance(user_id, str) and len(user_id) == 24:
                        user = db.users.find_one({"_id": ObjectId(user_id)})
                    else:
                        user = db.users.find_one({"_id": user_id})
                except Exception:
                    pass

            # Calculate total balance in USD
            total_usd = 0
            balances = wallet.get('balances', {})

            summary.append({
                'wallet_id': wallet.get('wallet_id'),
                'user_id': user_id,
                'user_email': user.get('email', 'Unknown') if user else 'Unknown',
                'balances': balances,
                'currency_count': len(balances),
                'is_active': wallet.get('is_active', True),
                'created_at': wallet.get('created_at'),
                'updated_at': wallet.get('updated_at')
            })

        return summary
    except Exception as e:
        current_app.logger.error(f"Failed to get wallets summary: {e}")
        return []


def admin_adjust_balance(wallet_id, currency, amount, admin_id, reason=""):
    """
    Admin function to adjust a wallet balance.
    Records the adjustment in wallet_adjustments collection.
    """
    if currency not in VALID_CURRENCIES:
        return False, f"Invalid currency: {currency}."

    db = get_db()
    if db is None:
        return False, "Database connection failed."

    wallet = db.wallets.find_one({"wallet_id": wallet_id})
    if not wallet:
        return False, "Wallet not found."

    try:
        old_balance = float(wallet.get('balances', {}).get(currency, 0))
        new_balance = old_balance + amount

        # Don't allow negative balances
        if new_balance < 0:
            return False, f"Adjustment would result in negative balance ({new_balance:.2f})"

        # Record adjustment
        adjustment = {
            "wallet_id": wallet_id,
            "user_id": wallet['user_id'],
            "currency": currency,
            "old_balance": old_balance,
            "new_balance": new_balance,
            "difference": amount,
            "admin_id": str(admin_id),
            "reason": reason,
            "created_at": datetime.utcnow()
        }
        db.wallet_adjustments.insert_one(adjustment)

        # Update wallet
        db.wallets.update_one(
            {"wallet_id": wallet_id},
            {
                "$set": {
                    f"balances.{currency}": round(new_balance, 4),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        current_app.logger.info(
            f"Admin {admin_id} adjusted wallet {wallet_id}: {amount:+.2f} {currency}"
        )

        return True, f"Balance adjusted: {old_balance:.2f} → {new_balance:.2f} {currency}"

    except Exception as e:
        current_app.logger.error(f"Admin balance adjustment failed: {e}")
        return False, "Adjustment failed."


def get_wallet_stats():
    """
    Gets global wallet statistics for admin dashboard.
    """
    db = get_db()
    if db is None:
        return {}

    try:
        total_wallets = db.wallets.count_documents({})
        active_wallets = db.wallets.count_documents({"is_active": True})

        # Aggregate total balances per currency
        pipeline = [
            {"$project": {"balances": {"$objectToArray": "$balances"}}},
            {"$unwind": "$balances"},
            {"$group": {
                "_id": "$balances.k",
                "total": {"$sum": "$balances.v"}
            }}
        ]

        currency_totals = {}
        for item in db.wallets.aggregate(pipeline):
            currency_totals[item['_id']] = round(item['total'], 2)

        return {
            'total_wallets': total_wallets,
            'active_wallets': active_wallets,
            'inactive_wallets': total_wallets - active_wallets,
            'currency_totals': currency_totals,
            'currencies_in_use': len(currency_totals)
        }
    except Exception as e:
        current_app.logger.error(f"Failed to get wallet stats: {e}")
        return {}
