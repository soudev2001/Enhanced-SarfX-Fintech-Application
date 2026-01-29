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
# Login Page Selectors
# ============================================
${LOGIN_EMAIL_INPUT}     css:input[name="email"], css:#email
${LOGIN_PASSWORD_INPUT}  css:input[name="password"], css:#password
${LOGIN_SUBMIT_BTN}      css:button[type="submit"]
${LOGIN_ERROR_MSG}       css:.alert-danger, css:.error-message, css:.toast-error
${DEMO_ADMIN_BTN}        xpath://button[contains(text(),'Admin')] | css:[onclick*="admin@sarfx.io"]
${DEMO_USER_BTN}         xpath://button[contains(text(),'User')] | css:[onclick*="user@demo.com"]

# ============================================
# Registration Page Selectors
# ============================================
${REGISTER_NAME_INPUT}       css:input[name="name"], css:#name
${REGISTER_EMAIL_INPUT}      css:input[name="email"], css:#email
${REGISTER_PASSWORD_INPUT}   css:input[name="password"], css:#password
${REGISTER_CONFIRM_INPUT}    css:input[name="confirm_password"], css:#confirm_password
${REGISTER_SUBMIT_BTN}       css:button[type="submit"]

# ============================================
# App Navigation Selectors
# ============================================
${NAV_HOME}              css:a[href*="/app/"], css:.nav-home
${NAV_CONVERTER}         css:a[href*="/converter"]
${NAV_WALLETS}           css:a[href*="/wallets"]
${NAV_TRANSACTIONS}      css:a[href*="/transactions"]
${NAV_PROFILE}           css:a[href*="/profile"]
${NAV_LOGOUT}            css:a[href*="/logout"], css:.logout-btn

# ============================================
# Converter Page Selectors
# ============================================
${AMOUNT_INPUT}          css:#amount, css:input[name="amount"]
${FROM_CURRENCY}         css:#from-currency, css:select[name="from"]
${TO_CURRENCY}           css:#to-currency, css:select[name="to"]
${CONVERT_BTN}           css:#convert-btn, css:.convert-button
${RESULT_DISPLAY}        css:#result, css:.conversion-result
${SWAP_BTN}              css:#swap-btn, css:.swap-currencies
${RATE_DISPLAY}          css:.rate-display, css:#current-rate

# ============================================
# Admin Page Selectors
# ============================================
${ADMIN_SIDEBAR}         css:.admin-sidebar, css:#admin-nav
${ADMIN_KPI_CARDS}       css:.kpi-card, css:.stat-card
${ADMIN_USERS_TABLE}     css:.users-table, css:#users-list
${ADMIN_USER_ROW}        css:tr.user-row, css:.user-item
${ADMIN_SEARCH_INPUT}    css:#search, css:input[type="search"]
${ADMIN_EXPORT_BTN}      css:.export-btn, css:a[href*="export"]

# ============================================
# Common Selectors
# ============================================
${TOAST_SUCCESS}         css:.toast-success, css:.alert-success
${TOAST_ERROR}           css:.toast-error, css:.alert-danger
${LOADING_SPINNER}       css:.loading, css:.spinner
${MODAL}                 css:.modal.show, css:.modal:not(.hidden)
${MODAL_CLOSE}           css:.modal .close, css:[data-dismiss="modal"]
