*** Settings ***
Documentation    Démonstration COMPLÈTE SarfX avec VIDEO, SCREENSHOTS et SOUS-TITRES
...              Mode navigateur VISIBLE pour capture vidéo professionnelle
...              Couvre: Admin, Utilisateur, Responsable Banque
...              Génère fichier .srt pour sous-titrage vidéo

Library          SeleniumLibrary    timeout=30s    implicit_wait=5s
Library          Collections
Library          String
Library          DateTime
Library          OperatingSystem
Library          ../resources/VideoRecorder.py
Library          ../resources/SubtitlesGenerator.py

Resource         ../resources/keywords.robot
Resource         ../resources/variables.robot

Suite Setup      Setup Video Demo Environment
Suite Teardown   Cleanup Video Demo Environment
Test Teardown    Run Keyword If Test Failed    Take Screenshot On Failure

Force Tags       video-demo    full-scenario    with-subtitles

*** Variables ***
${DEMO_OUTPUT_DIR}       ${CURDIR}/../../robot_results/video_demo
${VIDEO_DIR}             ${CURDIR}/../../robot_results/video_demo/videos
${SCREENSHOT_DIR}        ${CURDIR}/../../robot_results/video_demo/screenshots
${USE_VIDEO}             1
${VIDEO_FILE}            ${EMPTY}
${SUBTITLE_FILE}         ${EMPTY}

*** Keywords ***
Setup Video Demo Environment
    [Documentation]    Initialise l'environnement pour la démo vidéo complète
    Log To Console    ${\n}========================================
    Log To Console    🎬 INITIALISATION DEMO VIDEO COMPLETE
    Log To Console    ========================================

    # Créer les répertoires
    Create Directory    ${DEMO_OUTPUT_DIR}
    Create Directory    ${VIDEO_DIR}
    Create Directory    ${SCREENSHOT_DIR}

    Set Screenshot Directory    ${SCREENSHOT_DIR}

    # Initialiser les sous-titres
    Start Subtitles
    Add Subtitle    🎬 Démonstration SarfX - Application Fintech    5
    Add Subtitle    📱 Plateforme de change et services bancaires    4

    # Démarrer l'enregistrement vidéo si activé
    ${video_enabled}=    Convert To Integer    ${USE_VIDEO}
    Run Keyword If    ${video_enabled} == 1    Start Screen Recording

    # Ouvrir le navigateur en mode VISIBLE (non-headless)
    Open Browser With Video Recording
    Go To    ${BASE_URL}

    Log To Console    ✅ Environnement vidéo prêt
    Log To Console    ========================================${\n}

Cleanup Video Demo Environment
    [Documentation]    Nettoie l'environnement et sauvegarde tout
    Log To Console    ${\n}========================================
    Log To Console    🧹 NETTOYAGE ET FINALISATION
    Log To Console    ========================================

    # Sous-titre final
    Add Subtitle    ✅ Fin de la démonstration - Merci !    5
    Add Subtitle    📧 Contact: info@sarfx.io    4

    # Sauvegarder les sous-titres
    ${timestamp}=    Get Current Date    result_format=%Y%m%d_%H%M%S
    ${srt_file}=    Save Subtitles    ${VIDEO_DIR}/demo_${timestamp}.srt
    Set Suite Variable    ${SUBTITLE_FILE}    ${srt_file}

    # Fermer le navigateur
    Close Browser Safely

    # Arrêter l'enregistrement vidéo
    ${video_enabled}=    Convert To Integer    ${USE_VIDEO}
    Run Keyword If    ${video_enabled} == 1    Stop Screen Recording

    # Afficher résumé
    ${sub_count}=    Get Subtitle Count
    Log To Console    📹 Vidéo: ${VIDEO_FILE}
    Log To Console    📝 Sous-titres: ${srt_file} (${sub_count} entrées)
    Log To Console    📸 Screenshots: ${SCREENSHOT_DIR}
    Log To Console    ✅ Demo terminée
    Log To Console    ========================================${\n}

Start Screen Recording
    [Documentation]    Démarre l'enregistrement vidéo de l'écran
    TRY
        ${video_file}=    Start Video Recording    ${VIDEO_DIR}
        Set Suite Variable    ${VIDEO_FILE}    ${video_file}
        Sleep    2s    # Attendre que l'enregistrement démarre
        Log To Console    📹 Enregistrement vidéo: ${video_file}
    EXCEPT
        Log To Console    ⚠️  Impossible de démarrer la vidéo (FFmpeg manquant?)
        Set Suite Variable    ${VIDEO_FILE}    ${EMPTY}
    END

Stop Screen Recording
    [Documentation]    Arrête l'enregistrement vidéo
    TRY
        ${saved_file}=    Stop Video Recording
        Log To Console    ✅ Vidéo enregistrée: ${saved_file}
    EXCEPT
        Log To Console    ⚠️  Erreur lors de l'arrêt de la vidéo
    END

Take High Quality Screenshot With Subtitle
    [Documentation]    Prend un screenshot HD avec sous-titre synchronisé
    [Arguments]    ${step_name}    ${subtitle_text}=${EMPTY}    ${wait_time}=1s

    Sleep    ${wait_time}
    ${timestamp}=    Get Current Date    result_format=%Y%m%d_%H%M%S
    ${filename}=    Set Variable    ${step_name}_${timestamp}
    Capture Page Screenshot    ${filename}.png

    # Ajouter sous-titre si fourni
    Run Keyword If    '${subtitle_text}' != '${EMPTY}'    Add Subtitle    ${subtitle_text}    3

    Log To Console    📸 Screenshot: ${filename}.png
    RETURN    ${filename}

Wait And Screenshot With Subtitle
    [Documentation]    Attend, prend screenshot et ajoute sous-titre
    [Arguments]    ${step_name}    ${subtitle_text}    ${wait_time}=2s
    Sleep    ${wait_time}
    Take High Quality Screenshot With Subtitle    ${step_name}    ${subtitle_text}

*** Test Cases ***
# ============================================
# DÉMO COMPLÈTE AVEC TOUS LES UTILISATEURS
# ============================================

DEMO_001 - Landing Page
    [Documentation]    Page d'accueil SarfX
    [Tags]    landing    intro
    Log To Console    ${\n}🏠 LANDING PAGE${\n}

    Add Subtitle    🌐 Page d'accueil SarfX    3
    Wait Until Page Contains Element    css:body    timeout=10s
    Take High Quality Screenshot With Subtitle    01_landing_page    📱 Interface moderne et intuitive    3s
    Page Should Contain    SarfX

    Log To Console    ✅ Landing page chargée${\n}

# ============================================
# PARTIE 1: ADMINISTRATEUR
# ============================================

DEMO_002 - Connexion Administrateur
    [Documentation]    Login admin et accès dashboard
    [Tags]    admin    auth
    Log To Console    ${\n}👤 CONNEXION ADMINISTRATEUR${\n}

    Add Subtitle    👤 Connexion Administrateur    3
    Go To Login Page
    Take High Quality Screenshot With Subtitle    02_login_page    🔐 Page de connexion    2s

    Add Subtitle    ✉️ Email: admin@sarfx.io    2
    Input Text    ${LOGIN_EMAIL_INPUT}    ${ADMIN_EMAIL}
    Sleep    1s
    Take High Quality Screenshot With Subtitle    03_admin_email

    Add Subtitle    🔑 Saisie du mot de passe    2
    Input Text    ${LOGIN_PASSWORD_INPUT}    ${ADMIN_PASSWORD}
    Sleep    1s
    Take High Quality Screenshot With Subtitle    04_admin_password

    Click Button    ${LOGIN_SUBMIT_BTN}
    Sleep    2s
    Add Subtitle    ✅ Accès Dashboard Administrateur    4
    Take High Quality Screenshot With Subtitle    05_admin_dashboard    📊 Tableau de bord admin

    Page Should Contain    Dashboard
    Log To Console    ✅ Admin connecté${\n}

DEMO_003 - Gestion Utilisateurs
    [Documentation]    Administration des utilisateurs
    [Tags]    admin    users
    Log To Console    ${\n}👥 GESTION UTILISATEURS${\n}

    Add Subtitle    👥 Gestion des utilisateurs    3
    Click Link    ${ADMIN_USERS_LINK}
    Wait And Screenshot With Subtitle    06_admin_users    📋 Liste des utilisateurs    3s

    Page Should Contain    Users
    Log To Console    ✅ Module utilisateurs affiché${\n}

DEMO_004 - Gestion Wallets Admin
    [Documentation]    Administration des portefeuilles
    [Tags]    admin    wallets
    Log To Console    ${\n}💰 GESTION WALLETS${\n}

    Add Subtitle    💰 Gestion des portefeuilles    3
    Click Link    ${ADMIN_WALLETS_LINK}
    Wait And Screenshot With Subtitle    07_admin_wallets    💵 Tous les portefeuilles    3s

    Page Should Contain    Wallets
    Log To Console    ✅ Module wallets affiché${\n}

DEMO_005 - Transactions Admin
    [Documentation]    Historique toutes transactions
    [Tags]    admin    transactions
    Log To Console    ${\n}💳 TRANSACTIONS ADMIN${\n}

    Add Subtitle    💳 Historique des transactions    3
    Click Link    ${ADMIN_TRANSACTIONS_LINK}
    Wait And Screenshot With Subtitle    08_admin_transactions    📜 Toutes les transactions    3s

    Log To Console    ✅ Transactions affichées${\n}

DEMO_006 - Gestion Banques
    [Documentation]    Administration des banques
    [Tags]    admin    banks
    Log To Console    ${\n}🏦 GESTION BANQUES${\n}

    Add Subtitle    🏦 Gestion des banques partenaires    3
    Click Link    ${ADMIN_BANKS_LINK}
    Wait And Screenshot With Subtitle    09_admin_banks    🏢 Banques partenaires    3s

    Page Should Contain    Bank
    Log To Console    ✅ Module banques affiché${\n}

DEMO_007 - Déconnexion Admin
    [Documentation]    Logout administrateur
    [Tags]    admin    auth
    Log To Console    ${\n}🚪 DÉCONNEXION ADMIN${\n}

    Add Subtitle    🚪 Déconnexion administrateur    2
    Click Link    ${LOGOUT_LINK}
    Sleep    2s
    Take High Quality Screenshot With Subtitle    10_admin_logout

    Log To Console    ✅ Admin déconnecté${\n}

# ============================================
# PARTIE 2: UTILISATEUR STANDARD
# ============================================

DEMO_008 - Connexion Utilisateur
    [Documentation]    Login utilisateur standard
    [Tags]    user    auth
    Log To Console    ${\n}👤 CONNEXION UTILISATEUR${\n}

    Add Subtitle    👤 Connexion Utilisateur Standard    3
    Go To Login Page
    Take High Quality Screenshot With Subtitle    11_user_login_page    🔐 Interface utilisateur    2s

    Add Subtitle    📧 Email: user@demo.com    2
    Login With Credentials    ${USER_EMAIL}    ${USER_PASSWORD}
    Sleep    2s
    Add Subtitle    ✅ Accès Espace Utilisateur    4
    Take High Quality Screenshot With Subtitle    12_user_dashboard    🏠 Dashboard utilisateur

    Log To Console    ✅ Utilisateur connecté${\n}

DEMO_009 - Convertisseur de Devises
    [Documentation]    Conversion USD → MAD
    [Tags]    user    converter
    Log To Console    ${\n}💱 CONVERTISSEUR${\n}

    Add Subtitle    💱 Convertisseur de devises    3
    Go To    ${BASE_URL}/app/converter
    Wait And Screenshot With Subtitle    13_converter_page    💰 Taux de change en temps réel    2s

    Add Subtitle    📝 Montant: 100 USD    2
    Input Text    id:amount    100
    Sleep    1s
    Take High Quality Screenshot With Subtitle    14_amount_entered

    Add Subtitle    💵 USD → MAD    2
    Select From List By Label    id:from_currency    USD
    Sleep    1s
    Select From List By Label    id:to_currency    MAD
    Sleep    1s
    Take High Quality Screenshot With Subtitle    15_currencies_selected    🔄 Sélection des devises

    Add Subtitle    ⚡ Calcul en cours...    2
    Click Button    css:button[type="submit"]
    Sleep    2s
    Add Subtitle    ✅ Résultat: ~980 MAD    3
    Take High Quality Screenshot With Subtitle    16_conversion_result    💸 Résultat de la conversion

    Log To Console    ✅ Conversion effectuée${\n}

DEMO_010 - Portefeuilles Utilisateur
    [Documentation]    Mes portefeuilles
    [Tags]    user    wallets
    Log To Console    ${\n}💰 MES PORTEFEUILLES${\n}

    Add Subtitle    💰 Mes Portefeuilles    3
    Click Link    ${USER_WALLETS_LINK}
    Wait And Screenshot With Subtitle    17_user_wallets    💵 Soldes disponibles    3s

    Log To Console    ✅ Portefeuilles affichés${\n}

DEMO_011 - Historique Transactions
    [Documentation]    Mes transactions
    [Tags]    user    transactions
    Log To Console    ${\n}📜 MES TRANSACTIONS${\n}

    Add Subtitle    📜 Historique de mes transactions    3
    Click Link    ${USER_TRANSACTIONS_LINK}
    Wait And Screenshot With Subtitle    18_user_transactions    💳 Opérations récentes    3s

    Log To Console    ✅ Historique affiché${\n}

DEMO_012 - Carte des ATMs
    [Documentation]    Localisation distributeurs
    [Tags]    user    atms
    Log To Console    ${\n}🏧 CARTE DES ATMs${\n}

    Add Subtitle    🏧 Localisation des distributeurs    3
    Go To    ${BASE_URL}/app/atms
    Sleep    3s    # Attendre chargement carte
    Add Subtitle    📍 Carte interactive des ATMs    4
    Take High Quality Screenshot With Subtitle    19_atm_map    🗺️ Trouvez l'ATM le plus proche

    Log To Console    ✅ Carte affichée${\n}

DEMO_013 - Profil Utilisateur
    [Documentation]    Mes informations
    [Tags]    user    profile
    Log To Console    ${\n}⚙️ MON PROFIL${\n}

    Add Subtitle    ⚙️ Profil Utilisateur    3
    Go To    ${BASE_URL}/app/profile
    Wait And Screenshot With Subtitle    20_user_profile    👤 Informations personnelles    2s

    Log To Console    ✅ Profil affiché${\n}

DEMO_014 - Déconnexion Utilisateur
    [Documentation]    Logout utilisateur
    [Tags]    user    auth
    Log To Console    ${\n}🚪 DÉCONNEXION USER${\n}

    Add Subtitle    🚪 Déconnexion utilisateur    2
    Click Link    ${LOGOUT_LINK}
    Sleep    2s
    Take High Quality Screenshot With Subtitle    21_user_logout

    Log To Console    ✅ Utilisateur déconnecté${\n}

# ============================================
# PARTIE 3: RESPONSABLE BANQUE
# ============================================

DEMO_015 - Connexion Banque
    [Documentation]    Login responsable banque
    [Tags]    bank    auth
    Log To Console    ${\n}🏦 CONNEXION BANQUE${\n}

    Add Subtitle    🏦 Connexion Responsable Banque    3
    Go To Login Page
    Take High Quality Screenshot With Subtitle    22_bank_login_page    🏢 Interface banque    2s

    Add Subtitle    📧 Email: bank.respo@boa.ma    2
    Login With Credentials    ${BANK_RESPO_EMAIL}    ${BANK_RESPO_PASSWORD}
    Sleep    2s
    Add Subtitle    ✅ Accès Espace Banque    4
    Take High Quality Screenshot With Subtitle    23_bank_dashboard    📊 Dashboard bancaire

    Page Should Contain Element    css:body
    Log To Console    ✅ Responsable banque connecté${\n}

DEMO_016 - Dashboard Banque
    [Documentation]    Vue d'ensemble banque
    [Tags]    bank
    Log To Console    ${\n}📊 DASHBOARD BANQUE${\n}

    Add Subtitle    📊 Tableau de bord bancaire    3
    Wait And Screenshot With Subtitle    24_bank_overview    📈 Statistiques et KPIs    3s

    Log To Console    ✅ Dashboard exploré${\n}

DEMO_017 - Déconnexion Banque
    [Documentation]    Logout banque
    [Tags]    bank    auth
    Log To Console    ${\n}🚪 DÉCONNEXION BANQUE${\n}

    Add Subtitle    🚪 Déconnexion responsable banque    2
    Click Link    ${LOGOUT_LINK}
    Sleep    2s
    Take High Quality Screenshot With Subtitle    25_bank_logout

    Log To Console    ✅ Banque déconnectée${\n}

# ============================================
# RÉCAPITULATIF FINAL
# ============================================

DEMO_018 - Récapitulatif Final
    [Documentation]    Vue finale et résumé
    [Tags]    final    recap
    Log To Console    ${\n}🎬 RÉCAPITULATIF${\n}

    Add Subtitle    🎬 Récapitulatif de la Démonstration    4
    Go To    ${BASE_URL}
    Sleep    2s

    Add Subtitle    ✅ Administrateur: Gestion complète    3
    Sleep    2s
    Add Subtitle    ✅ Utilisateur: Conversion & Opérations    3
    Sleep    2s
    Add Subtitle    ✅ Banque: Suivi et statistiques    3
    Sleep    2s

    Add Subtitle    📱 Application SarfX - Fintech    4
    Take High Quality Screenshot With Subtitle    26_final_recap    🌟 Merci de votre attention !    3s

    Log To Console    ========================================
    Log To Console    ✅ DÉMO COMPLÈTE TERMINÉE
    Log To Console    📹 Vidéo: ${VIDEO_FILE}
    Log To Console    📝 Sous-titres: ${SUBTITLE_FILE}
    Log To Console    📸 Screenshots: ${SCREENSHOT_DIR}
    Log To Console    ========================================${\n}
