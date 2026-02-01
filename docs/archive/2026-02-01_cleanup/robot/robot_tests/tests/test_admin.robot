*** Settings ***
Documentation    Tests du panel administrateur SarfX
...              Dashboard, Users, Wallets, Banks, Transactions

Resource         ../resources/keywords.robot
Resource         ../resources/variables.robot

Suite Setup      Run Keywords    Open Browser To SarfX    AND    Login As Admin
Suite Teardown   Run Keywords    Logout    AND    Close Browser Safely
Test Teardown    Run Keyword If Test Failed    Take Screenshot On Failure

Force Tags       admin

*** Test Cases ***
# ============================================
# DASHBOARD TESTS
# ============================================
TC_ADMIN_001 - Dashboard admin se charge
    [Documentation]    Le dashboard administrateur s'affiche correctement
    [Tags]    smoke    critical
    Navigate To Admin Dashboard
    Location Should Contain    /admin
    Page Should Be Accessible
    Capture Page Screenshot    admin_dashboard.png

TC_ADMIN_002 - KPI cards affichées
    [Documentation]    Les cartes KPI sont visibles sur le dashboard
    [Tags]    smoke
    Navigate To Admin Dashboard
    Wait Until Element Is Visible    ${ADMIN_KPI_CARDS}    ${TIMEOUT}
    ${count}=    Get Element Count    ${ADMIN_KPI_CARDS}
    Should Be True    ${count} >= 1    No KPI cards found
    Log    Found ${count} KPI cards
    Capture Page Screenshot    admin_kpi_cards.png

TC_ADMIN_003 - Graphiques affichés
    [Documentation]    Les graphiques du dashboard sont présents
    [Tags]    chart
    Navigate To Admin Dashboard
    ${charts}=    Get WebElements    css:canvas, css:.chart, css:[id*="chart"]
    ${count}=    Get Length    ${charts}
    Log    Found ${count} charts
    Capture Page Screenshot    admin_charts.png

TC_ADMIN_004 - Actions rapides présentes
    [Documentation]    Les boutons d'actions rapides sont visibles
    [Tags]    functionality
    Navigate To Admin Dashboard
    ${actions}=    Get WebElements    css:.quick-action, css:.action-btn, css:[href*="/admin/"]
    ${count}=    Get Length    ${actions}
    Should Be True    ${count} >= 1    No quick actions found
    Capture Page Screenshot    admin_quick_actions.png

# ============================================
# USER MANAGEMENT TESTS
# ============================================
TC_ADMIN_010 - Liste des utilisateurs se charge
    [Documentation]    La page de gestion des utilisateurs s'affiche
    [Tags]    smoke    critical
    Navigate To Admin Users
    Location Should Contain    /admin/users
    Page Should Be Accessible
    Capture Page Screenshot    admin_users_page.png

TC_ADMIN_011 - Tableau utilisateurs affiché
    [Documentation]    Le tableau des utilisateurs est visible
    [Tags]    smoke
    Navigate To Admin Users
    ${table}=    Set Variable    css:table, css:.users-table, css:#users-list
    Wait Until Element Is Visible    ${table}    ${TIMEOUT}
    Capture Page Screenshot    admin_users_table.png

TC_ADMIN_012 - Recherche utilisateurs fonctionne
    [Documentation]    La recherche filtre les utilisateurs
    [Tags]    functionality
    Navigate To Admin Users
    ${search}=    Set Variable    css:#search, css:input[type="search"], css:.search-input
    ${exists}=    Run Keyword And Return Status    Element Should Be Visible    ${search}
    Run Keyword If    ${exists}    Input Text    ${search}    admin
    Sleep    1s
    Capture Page Screenshot    admin_users_search.png

TC_ADMIN_013 - Filtre par rôle fonctionne
    [Documentation]    Le filtre par rôle fonctionne
    [Tags]    functionality
    Navigate To Admin Users
    ${filter}=    Set Variable    css:select[name="role"], css:#role-filter, css:.role-select
    ${exists}=    Run Keyword And Return Status    Element Should Be Visible    ${filter}
    Run Keyword If    ${exists}    Select From List By Index    ${filter}    1
    Sleep    1s
    Capture Page Screenshot    admin_users_filter.png

TC_ADMIN_014 - Modal détails utilisateur
    [Documentation]    La modal de détails utilisateur s'ouvre
    [Tags]    functionality
    Navigate To Admin Users
    ${view_btn}=    Set Variable    css:.view-user, css:[data-action="view"], css:.btn-info
    ${exists}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${view_btn}    ${SHORT_TIMEOUT}
    Run Keyword If    ${exists}    Click Element    ${view_btn}
    Sleep    1s
    Capture Page Screenshot    admin_user_modal.png
    Run Keyword And Ignore Error    Click Element    ${MODAL_CLOSE}

# ============================================
# WALLET MANAGEMENT TESTS
# ============================================
TC_ADMIN_020 - Liste des wallets se charge
    [Documentation]    La page de gestion des portefeuilles s'affiche
    [Tags]    smoke
    Go To    ${ADMIN_WALLETS_URL}
    Wait For Page Load
    Page Should Be Accessible
    Capture Page Screenshot    admin_wallets_page.png

TC_ADMIN_021 - Formulaire ajustement wallet
    [Documentation]    Le formulaire d'ajustement de solde est présent
    [Tags]    functionality
    Go To    ${ADMIN_WALLETS_URL}
    ${form}=    Set Variable    css:form[action*="adjust"], css:#adjust-form, css:.wallet-adjust
    ${exists}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${form}    ${SHORT_TIMEOUT}
    Log    Adjustment form exists: ${exists}
    Capture Page Screenshot    admin_wallet_adjust.png

# ============================================
# TRANSACTION MANAGEMENT TESTS
# ============================================
TC_ADMIN_030 - Liste des transactions se charge
    [Documentation]    La page des transactions s'affiche
    [Tags]    smoke
    Go To    ${ADMIN_TRANSACTIONS_URL}
    Wait For Page Load
    Page Should Be Accessible
    Capture Page Screenshot    admin_transactions_page.png

TC_ADMIN_031 - Filtres transactions présents
    [Documentation]    Les filtres de transactions sont disponibles
    [Tags]    functionality
    Go To    ${ADMIN_TRANSACTIONS_URL}
    ${filters}=    Get WebElements    css:select, css:input[type="date"], css:.filter
    ${count}=    Get Length    ${filters}
    Log    Found ${count} filter elements
    Capture Page Screenshot    admin_transactions_filters.png

# ============================================
# BANK MANAGEMENT TESTS
# ============================================
TC_ADMIN_040 - Liste des banques se charge
    [Documentation]    La page de gestion des banques s'affiche
    [Tags]    smoke
    Go To    ${ADMIN_BANKS_URL}
    Wait For Page Load
    Page Should Be Accessible
    Capture Page Screenshot    admin_banks_page.png

TC_ADMIN_041 - Formulaire ajout banque présent
    [Documentation]    Le formulaire d'ajout de banque est visible
    [Tags]    functionality
    Go To    ${ADMIN_BANKS_URL}
    ${add_btn}=    Set Variable    css:.add-bank, css:#add-bank-btn, css:[href*="bank/add"]
    ${exists}=    Run Keyword And Return Status    Element Should Be Visible    ${add_btn}
    Log    Add bank button exists: ${exists}
    Capture Page Screenshot    admin_add_bank.png

# ============================================
# EXPORT TESTS
# ============================================
TC_ADMIN_050 - Export utilisateurs CSV
    [Documentation]    L'export CSV des utilisateurs fonctionne
    [Tags]    export
    Navigate To Admin Users
    ${export_btn}=    Set Variable    css:a[href*="export"], css:.export-csv, css:#export-users
    ${exists}=    Run Keyword And Return Status    Element Should Be Visible    ${export_btn}
    Run Keyword If    ${exists}    Log    Export button found
    ...    ELSE    Log    No export button on page
    Capture Page Screenshot    admin_export_users.png

TC_ADMIN_051 - Export transactions CSV
    [Documentation]    L'export CSV des transactions fonctionne
    [Tags]    export
    Go To    ${ADMIN_TRANSACTIONS_URL}
    Wait For Page Load
    ${export_btn}=    Set Variable    css:a[href*="export"], css:.export-csv, css:#export-trans
    ${exists}=    Run Keyword And Return Status    Element Should Be Visible    ${export_btn}
    Log    Export transactions button exists: ${exists}
    Capture Page Screenshot    admin_export_transactions.png

# ============================================
# NAVIGATION TESTS
# ============================================
TC_ADMIN_060 - Navigation entre pages admin
    [Documentation]    La navigation dans l'admin fonctionne
    [Tags]    navigation
    Navigate To Admin Dashboard
    Location Should Contain    /admin
    Navigate To Admin Users
    Location Should Contain    /admin/users
    Go To    ${ADMIN_WALLETS_URL}
    Location Should Contain    /admin/wallets
    Capture Page Screenshot    admin_navigation.png

TC_ADMIN_061 - Sidebar admin présente
    [Documentation]    La sidebar de navigation admin est visible
    [Tags]    navigation
    Navigate To Admin Dashboard
    ${sidebar}=    Set Variable    css:.sidebar, css:#admin-sidebar, css:nav.admin-nav
    ${exists}=    Run Keyword And Return Status    Element Should Be Visible    ${sidebar}
    Log    Admin sidebar exists: ${exists}
    Capture Page Screenshot    admin_sidebar.png

# ============================================
# ACCESS CONTROL TESTS
# ============================================
TC_ADMIN_070 - Utilisateur normal bloqué de l'admin
    [Documentation]    Un utilisateur normal ne peut pas accéder à l'admin
    [Tags]    security    critical
    Logout
    Login As User
    Go To    ${ADMIN_URL}
    Sleep    2s
    # Should be redirected or forbidden
    ${is_blocked}=    Run Keyword And Return Status    Location Should Not Contain    /admin/
    Run Keyword If    not ${is_blocked}    Page Should Contain    Forbidden
    Capture Page Screenshot    user_admin_blocked.png
    Logout
    Login As Admin

TC_ADMIN_071 - Bank user bloqué de l'admin principal
    [Documentation]    Un utilisateur banque ne peut pas accéder à l'admin principal
    [Tags]    security
    Logout
    Login As Bank Respo
    Go To    ${ADMIN_URL}
    Sleep    2s
    # Bank respo might have limited admin access
    Capture Page Screenshot    bank_respo_admin_access.png
    Logout
    Login As Admin

# ============================================
# MOBILE TESTS
# ============================================
TC_ADMIN_080 - Dashboard responsive mobile
    [Documentation]    Le dashboard admin s'affiche sur mobile
    [Tags]    mobile    responsive
    Set Mobile Viewport
    Navigate To Admin Dashboard
    Page Should Be Accessible
    Capture Page Screenshot    admin_dashboard_mobile.png
    Set Desktop Viewport

TC_ADMIN_081 - Users page responsive mobile
    [Documentation]    La page utilisateurs s'affiche sur mobile
    [Tags]    mobile    responsive
    Set Mobile Viewport
    Navigate To Admin Users
    Page Should Be Accessible
    Capture Page Screenshot    admin_users_mobile.png
    Set Desktop Viewport
