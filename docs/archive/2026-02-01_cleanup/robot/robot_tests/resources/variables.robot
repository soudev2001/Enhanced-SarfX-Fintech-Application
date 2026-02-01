*** Settings ***
Documentation    Variables globales pour les tests SarfX
...              Contient URLs, credentials et sélecteurs

*** Variables ***
# ============================================
# URLs
# ============================================
${BASE_URL}              https://sarfx.io
${LOGIN_URL}             ${BASE_URL}/auth/login
${REGISTER_URL}          ${BASE_URL}/auth/register
${APP_HOME_URL}          ${BASE_URL}/app/
${CONVERTER_URL}         ${BASE_URL}/app/converter
${WALLETS_URL}           ${BASE_URL}/app/wallets
${TRANSACTIONS_URL}      ${BASE_URL}/app/transactions
${BENEFICIARIES_URL}     ${BASE_URL}/app/beneficiaries
${PROFILE_URL}           ${BASE_URL}/app/profile
${ADMIN_URL}             ${BASE_URL}/admin/
${ADMIN_USERS_URL}       ${BASE_URL}/admin/users
${ADMIN_WALLETS_URL}     ${BASE_URL}/admin/wallets
${ADMIN_BANKS_URL}       ${BASE_URL}/admin/banks
${ADMIN_TRANSACTIONS_URL}    ${BASE_URL}/admin/transactions
${ATM_URL}               ${BASE_URL}/app/atms
${RATE_HISTORY_URL}      ${BASE_URL}/app/rate-history
${AI_URL}                ${BASE_URL}/app/ai

# ============================================
# Test Accounts
# ============================================
${ADMIN_EMAIL}           admin@sarfx.io
${ADMIN_PASSWORD}        admin123

${USER_EMAIL}            user@demo.com
${USER_PASSWORD}         user123

${BANK_RESPO_EMAIL}      bank.respo@boa.ma
${BANK_RESPO_PASSWORD}   bank123

${BANK_USER_EMAIL}       bank.user@boa.ma
${BANK_USER_PASSWORD}    bank123

# Demo test user (created for tests)
${TEST_USER_EMAIL}       test.demo@sarfx.io
${TEST_USER_PASSWORD}    Test@123456
${TEST_USER_NAME}        Demo Test User

# ============================================
# Timeouts
# ============================================
${TIMEOUT}               30s
${SHORT_TIMEOUT}         10s
${LONG_TIMEOUT}          60s

# ============================================
# Browser Settings
# ============================================
${BROWSER}               chrome
${HEADLESS}              ${TRUE}

# ============================================
# Login Page Selectors (FIXED - no duplicate css: prefix)
# ============================================
${LOGIN_EMAIL_INPUT}     css:input[name="email"]
${LOGIN_PASSWORD_INPUT}  css:input[name="password"]
${LOGIN_SUBMIT_BTN}      css:button[type="submit"]
${LOGIN_ERROR_MSG}       css:.alert-danger, .error-message, .toast-error
${DEMO_ADMIN_BTN}        xpath://button[contains(text(),'Admin')]
${DEMO_USER_BTN}         xpath://button[contains(text(),'User')]
${LOGIN_REGISTER_LINK}   css:a[href*="register"]

# ============================================
# Registration Page Selectors (FIXED)
# ============================================
${REGISTER_NAME_INPUT}       css:input[name="name"]
${REGISTER_EMAIL_INPUT}      css:input[name="email"]
${REGISTER_PASSWORD_INPUT}   css:input[name="password"]
${REGISTER_CONFIRM_INPUT}    css:input[name="confirm_password"]
${REGISTER_SUBMIT_BTN}       css:button[type="submit"]

# ============================================
# App Navigation Selectors (FIXED)
# ============================================
${NAV_HOME}              css:a[href="/app/"], a[href="/app"]
${NAV_CONVERTER}         css:a[href*="converter"]
${NAV_WALLETS}           css:a[href*="wallets"]
${NAV_TRANSACTIONS}      css:a[href*="transactions"]
${NAV_PROFILE}           css:a[href*="profile"]
${NAV_LOGOUT}            css:a[href*="logout"]
${NAV_BENEFICIARIES}     css:a[href*="beneficiaries"]
${NAV_ATMS}              css:a[href*="atms"]
${NAV_AI}                css:a[href*="ai"]
${NAV_ADMIN}             css:a[href*="admin"]
${USER_MENU}             css:.user-menu, .dropdown-toggle, .nav-user

# Links alternatives (for compatibility)
${LOGOUT_LINK}           ${NAV_LOGOUT}
${USER_WALLETS_LINK}     ${NAV_WALLETS}
${USER_TRANSACTIONS_LINK}    ${NAV_TRANSACTIONS}
${USER_PROFILE_LINK}     ${NAV_PROFILE}
${ADMIN_USERS_LINK}      css:a[href*="/admin/users"]
${ADMIN_WALLETS_LINK}    css:a[href*="/admin/wallets"]
${ADMIN_TRANSACTIONS_LINK}   css:a[href*="/admin/transactions"]
${ADMIN_BANKS_LINK}      css:a[href*="/admin/banks"]

# ============================================
# Converter Page Selectors (FIXED)
# ============================================
${AMOUNT_INPUT}          css:#amount
${FROM_CURRENCY}         css:#from-currency
${TO_CURRENCY}           css:#to-currency
${CONVERT_BTN}           css:#convert-btn, .convert-button, button[type="submit"]
${RESULT_DISPLAY}        css:#result, .conversion-result, .result-amount
${SWAP_BTN}              css:#swap-btn, .swap-btn, .swap-currencies
${RATE_DISPLAY}          css:.rate-display, .current-rate, #current-rate
${RATE_CARD}             css:.rate-card, .exchange-rate
${PROVIDER_LIST}         css:.provider-list, .providers, #providers

# ============================================
# Wallet Page Selectors
# ============================================
${WALLET_CARD}           css:.wallet-card, .currency-wallet
${WALLET_BALANCE}        css:.wallet-balance, .balance-amount
${WALLET_CURRENCY}       css:.wallet-currency, .currency-code
${ADD_WALLET_BTN}        css:#add-wallet, .add-wallet-btn
${WALLET_ACTIONS}        css:.wallet-actions, .wallet-menu

# ============================================
# Transaction Page Selectors
# ============================================
${TX_TABLE}              css:.transactions-table, #transactions-list, table
${TX_ROW}                css:.transaction-row, tr
${TX_FILTER_DATE}        css:#date-filter, input[type="date"]
${TX_FILTER_TYPE}        css:#type-filter, select[name="type"]
${TX_SEARCH}             css:#tx-search, input[type="search"]

# ============================================
# Admin Page Selectors (FIXED)
# ============================================
${ADMIN_SIDEBAR}         css:.sidebar, .admin-sidebar, #sidebar
${ADMIN_KPI_CARDS}       css:.stat-card, .kpi-card, .info-card
${ADMIN_USERS_TABLE}     css:table, .users-table, #users-table
${ADMIN_USER_ROW}        css:tbody tr, .user-row
${ADMIN_SEARCH_INPUT}    css:input[name="search"], #search, input[type="search"]
${ADMIN_EXPORT_BTN}      css:a[href*="export"], .export-btn
${ADMIN_NAV_USERS}       css:a[href*="users"]
${ADMIN_NAV_WALLETS}     css:a[href*="wallets"]
${ADMIN_NAV_TX}          css:a[href*="transactions"]
${ADMIN_NAV_BANKS}       css:a[href*="banks"]
${ADMIN_NAV_ATMS}        css:a[href*="atms"]
${ADMIN_NAV_SOURCES}     css:a[href*="sources"]
${ADMIN_NAV_API}         css:a[href*="api"]

# ============================================
# Profile Page Selectors
# ============================================
${PROFILE_NAME}          css:#name, input[name="name"]
${PROFILE_EMAIL}         css:#email, input[name="email"]
${PROFILE_PHONE}         css:#phone, input[name="phone"]
${PROFILE_SAVE_BTN}      css:button[type="submit"], .save-btn
${PROFILE_AVATAR}        css:.avatar, .profile-image

# ============================================
# Common Selectors (FIXED)
# ============================================
${TOAST_SUCCESS}         css:.toast-success, .alert-success, .success-message
${TOAST_ERROR}           css:.toast-error, .alert-danger, .error-message
${LOADING_SPINNER}       css:.loading, .spinner, .loader
${MODAL}                 css:.modal.show, .modal[style*="display: block"]
${MODAL_CLOSE}           css:.modal .close, .btn-close, [data-bs-dismiss="modal"]
${PAGE_TITLE}            css:h1, .page-title, .header-title
${CARD}                  css:.card, .panel
${TABLE}                 css:table, .data-table
${BUTTON_PRIMARY}        css:.btn-primary, button[type="submit"]
${BUTTON_SECONDARY}      css:.btn-secondary, .btn-outline
${ALERT}                 css:.alert, .notification
