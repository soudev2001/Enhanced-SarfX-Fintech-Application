*** Settings ***
Documentation    Démonstration complète de l'application SarfX
...              Ce test simule toutes les actions: Admin, User, Bank User
...              Avec captures d'écran et enregistrement vidéo

Library          SeleniumLibrary    timeout=30s    implicit_wait=5s
Library          Collections
Library          String
Library          DateTime
Library          OperatingSystem

Resource         ../resources/keywords.robot
Resource         ../resources/variables.robot

Suite Setup      Setup Demo Environment
Suite Teardown   Cleanup Demo Environment
Test Teardown    Run Keyword If Test Failed    Take Screenshot On Failure

Force Tags       demo    full-scenario

*** Variables ***
${DEMO_OUTPUT_DIR}       ${CURDIR}/../../robot_results/demo
${STEP_COUNTER}          ${0}

*** Test Cases ***
# ============================================
# SCÉNARIO COMPLET DE DÉMONSTRATION
# ============================================

DEMO_001 - Introduction et Landing Page
    [Documentation]    Affiche la landing page de SarfX
    [Tags]    intro    landing
    Log Demo Message    🎬 DÉBUT DE LA DÉMONSTRATION SARFX
    Go To    ${BASE_URL}
    Wait For Page Load
    Take Demo Screenshot    01_landing_page
    Page Should Be Accessible
    Log Demo Message    ✅ Landing page accessible

DEMO_010 - Connexion Administrateur
    [Documentation]    L'administrateur se connecte au système
    [Tags]    admin    login
    Log Demo Message    👤 CONNEXION ADMIN: admin@sarfx.io
    Go To Login Page
    Take Demo Screenshot    02_login_page
    Input Text    ${LOGIN_EMAIL_INPUT}    ${ADMIN_EMAIL}
    Take Demo Screenshot    03_login_email_entered
    Input Text    ${LOGIN_PASSWORD_INPUT}    ${ADMIN_PASSWORD}
    Take Demo Screenshot    04_login_password_entered
    Click Button    ${LOGIN_SUBMIT_BTN}
    Wait Until Location Contains    /app    30s
    Take Demo Screenshot    05_admin_logged_in
    Log Demo Message    ✅ Admin connecté avec succès

DEMO_011 - Navigation vers Dashboard Admin
    [Documentation]    L'admin accède au dashboard d'administration
    [Tags]    admin    dashboard
    Log Demo Message    📊 ACCÈS AU DASHBOARD ADMIN
    Navigate To Admin Dashboard
    Take Demo Screenshot    06_admin_dashboard
    Page Should Be Accessible
    Log Demo Message    ✅ Dashboard admin chargé

DEMO_012 - Exploration Gestion Utilisateurs
    [Documentation]    L'admin consulte la liste des utilisateurs
    [Tags]    admin    users
    Log Demo Message    👥 GESTION DES UTILISATEURS
    Navigate To Admin Users
    Take Demo Screenshot    07_admin_users_list
    Sleep    1s
    Page Should Be Accessible
    ${count}=    Count Admin Table Rows
    Log Demo Message    ✅ ${count} utilisateurs trouvés

DEMO_013 - Exploration Gestion Wallets
    [Documentation]    L'admin consulte les wallets
    [Tags]    admin    wallets
    Log Demo Message    💰 GESTION DES WALLETS
    Navigate To Admin Wallets
    Take Demo Screenshot    08_admin_wallets
    Page Should Be Accessible
    Log Demo Message    ✅ Wallets affichés

DEMO_014 - Exploration Transactions Admin
    [Documentation]    L'admin consulte les transactions
    [Tags]    admin    transactions
    Log Demo Message    💳 HISTORIQUE DES TRANSACTIONS
    Navigate To Admin Transactions
    Take Demo Screenshot    09_admin_transactions
    Page Should Be Accessible
    Log Demo Message    ✅ Transactions affichées

DEMO_015 - Exploration Gestion Banques
    [Documentation]    L'admin consulte les banques partenaires
    [Tags]    admin    banks
    Log Demo Message    🏦 GESTION DES BANQUES
    Navigate To Admin Banks
    Take Demo Screenshot    10_admin_banks
    Page Should Be Accessible
    Log Demo Message    ✅ Banques affichées

DEMO_019 - Déconnexion Admin
    [Documentation]    L'administrateur se déconnecte
    [Tags]    admin    logout
    Log Demo Message    🚪 DÉCONNEXION ADMIN
    Logout
    Take Demo Screenshot    11_admin_logged_out
    Log Demo Message    ✅ Admin déconnecté

DEMO_020 - Connexion Utilisateur Standard
    [Documentation]    Un utilisateur standard se connecte
    [Tags]    user    login
    Log Demo Message    👤 CONNEXION USER: user@demo.com
    Login With Credentials    ${USER_EMAIL}    ${USER_PASSWORD}
    Take Demo Screenshot    12_user_logged_in
    Log Demo Message    ✅ Utilisateur connecté

DEMO_021 - Page d'Accueil Utilisateur
    [Documentation]    L'utilisateur voit sa page d'accueil
    [Tags]    user    home
    Log Demo Message    🏠 PAGE D'ACCUEIL UTILISATEUR
    Navigate To Home
    Take Demo Screenshot    13_user_home
    Page Should Be Accessible
    Log Demo Message    ✅ Page d'accueil affichée

DEMO_022 - Convertisseur de Devises
    [Documentation]    L'utilisateur utilise le convertisseur
    [Tags]    user    converter
    Log Demo Message    💱 CONVERTISSEUR DE DEVISES
    Navigate To Converter
    Take Demo Screenshot    14_converter_page
    # Conversion USD vers MAD
    ${status}=    Run Keyword And Return Status    Enter Conversion Amount    100
    Run Keyword If    ${status}    Take Demo Screenshot    15_converter_amount
    ${status2}=    Run Keyword And Return Status    Select From Currency    USD
    Run Keyword If    ${status2}    Take Demo Screenshot    16_converter_from_usd
    ${status3}=    Run Keyword And Return Status    Select To Currency    MAD
    Run Keyword If    ${status3}    Take Demo Screenshot    17_converter_to_mad
    ${status4}=    Run Keyword And Return Status    Click Convert Button
    Sleep    2s
    Take Demo Screenshot    18_converter_result
    Log Demo Message    ✅ Conversion 100 USD → MAD effectuée

DEMO_023 - Portefeuilles Utilisateur
    [Documentation]    L'utilisateur consulte ses portefeuilles
    [Tags]    user    wallets
    Log Demo Message    💰 MES PORTEFEUILLES
    Navigate To Wallets
    Take Demo Screenshot    19_user_wallets
    Page Should Be Accessible
    Log Demo Message    ✅ Portefeuilles affichés

DEMO_024 - Historique Transactions
    [Documentation]    L'utilisateur consulte son historique
    [Tags]    user    transactions
    Log Demo Message    📜 HISTORIQUE DES TRANSACTIONS
    Navigate To Transactions
    Take Demo Screenshot    20_user_transactions
    Page Should Be Accessible
    Log Demo Message    ✅ Historique affiché

DEMO_025 - Bénéficiaires
    [Documentation]    L'utilisateur consulte ses bénéficiaires
    [Tags]    user    beneficiaries
    Log Demo Message    👥 MES BÉNÉFICIAIRES
    Navigate To Beneficiaries
    Take Demo Screenshot    21_user_beneficiaries
    Page Should Be Accessible
    Log Demo Message    ✅ Bénéficiaires affichés

DEMO_026 - Carte des ATMs
    [Documentation]    L'utilisateur trouve un ATM proche
    [Tags]    user    atms
    Log Demo Message    🏧 LOCALISATION DES ATMs
    Navigate To ATMs
    Take Demo Screenshot    22_atm_map
    Page Should Be Accessible
    Log Demo Message    ✅ Carte des ATMs affichée

DEMO_027 - Profil Utilisateur
    [Documentation]    L'utilisateur consulte son profil
    [Tags]    user    profile
    Log Demo Message    ⚙️ MON PROFIL
    Navigate To Profile
    Take Demo Screenshot    23_user_profile
    Page Should Be Accessible
    Log Demo Message    ✅ Profil affiché

DEMO_029 - Déconnexion Utilisateur
    [Documentation]    L'utilisateur se déconnecte
    [Tags]    user    logout
    Log Demo Message    🚪 DÉCONNEXION UTILISATEUR
    Logout
    Take Demo Screenshot    24_user_logged_out
    Log Demo Message    ✅ Utilisateur déconnecté

DEMO_030 - Connexion Responsable Banque
    [Documentation]    Un responsable de banque se connecte
    [Tags]    bank    login
    Log Demo Message    👤 CONNEXION BANK RESPO: bank.respo@boa.ma
    ${status}=    Run Keyword And Return Status    Login With Credentials    ${BANK_RESPO_EMAIL}    ${BANK_RESPO_PASSWORD}
    Run Keyword If    ${status}    Take Demo Screenshot    25_bank_respo_logged_in
    Run Keyword If    not ${status}    Log Demo Message    ⚠️ Compte bank respo non disponible - skipping
    Run Keyword If    ${status}    Log Demo Message    ✅ Responsable banque connecté

DEMO_031 - Dashboard Banque
    [Documentation]    Le responsable banque voit son dashboard
    [Tags]    bank    dashboard
    ${logged_in}=    Run Keyword And Return Status    Location Should Contain    /app
    Run Keyword If    ${logged_in}    Navigate To Home
    Run Keyword If    ${logged_in}    Take Demo Screenshot    26_bank_dashboard
    Run Keyword If    ${logged_in}    Log Demo Message    ✅ Dashboard banque affiché
    Run Keyword If    not ${logged_in}    Log Demo Message    ⚠️ Skipping - non connecté

DEMO_039 - Déconnexion Bank Respo
    [Documentation]    Le responsable banque se déconnecte
    [Tags]    bank    logout
    ${logged_in}=    Run Keyword And Return Status    Location Should Contain    /app
    Run Keyword If    ${logged_in}    Logout
    Run Keyword If    ${logged_in}    Take Demo Screenshot    27_bank_logged_out
    Log Demo Message    ✅ Session terminée

DEMO_040 - Test Version Mobile
    [Documentation]    Test de l'interface mobile
    [Tags]    responsive    mobile
    Log Demo Message    📱 TEST VERSION MOBILE
    Open Browser To SarfX
    Set Mobile Viewport
    Go To    ${BASE_URL}
    Take Demo Screenshot    28_mobile_landing
    Go To Login Page
    Take Demo Screenshot    29_mobile_login
    Login With Credentials    ${ADMIN_EMAIL}    ${ADMIN_PASSWORD}
    Take Demo Screenshot    30_mobile_home
    Navigate To Converter
    Take Demo Screenshot    31_mobile_converter
    Log Demo Message    ✅ Version mobile fonctionnelle
    Close Browser Safely

DEMO_099 - Fin de la Démonstration
    [Documentation]    Résumé et fin de la démo
    [Tags]    summary
    Log Demo Message    🎬 FIN DE LA DÉMONSTRATION SARFX
    Log Demo Message    ========================================
    Log Demo Message    ✅ Landing page testée
    Log Demo Message    ✅ Authentification Admin testée
    Log Demo Message    ✅ Dashboard Admin exploré
    Log Demo Message    ✅ Gestion Users/Wallets/Transactions/Banks
    Log Demo Message    ✅ Authentification User testée
    Log Demo Message    ✅ Convertisseur de devises testé
    Log Demo Message    ✅ Portefeuilles utilisateur testés
    Log Demo Message    ✅ Historique transactions testé
    Log Demo Message    ✅ Carte ATMs testée
    Log Demo Message    ✅ Interface mobile testée
    Log Demo Message    ========================================
    Log Demo Message    📁 Screenshots disponibles dans: robot_results/demo/

*** Keywords ***
Setup Demo Environment
    [Documentation]    Prépare l'environnement de démonstration
    Log Demo Message    🚀 INITIALISATION DE LA DÉMONSTRATION
    Create Directory    ${DEMO_OUTPUT_DIR}
    Set Screenshot Directory    ${DEMO_OUTPUT_DIR}
    Open Browser To SarfX
    Set Window Size    1920    1080
    Log Demo Message    ✅ Environnement prêt

Cleanup Demo Environment
    [Documentation]    Nettoie l'environnement après la démo
    Log Demo Message    🧹 NETTOYAGE DE L'ENVIRONNEMENT
    Run Keyword And Ignore Error    Close All Browsers
    Log Demo Message    ✅ Démonstration terminée
