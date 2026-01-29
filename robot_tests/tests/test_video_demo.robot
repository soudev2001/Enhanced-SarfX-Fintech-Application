*** Settings ***
Documentation    Démonstration SarfX avec VIDEO et SCREENSHOTS
...              Mode navigateur VISIBLE pour capture vidéo
...              Screenshots haute résolution à chaque étape

Library          SeleniumLibrary    timeout=30s    implicit_wait=5s
Library          Collections
Library          String
Library          DateTime
Library          OperatingSystem
Library          ../resources/VideoRecorder.py

Resource         ../resources/keywords.robot
Resource         ../resources/variables.robot

Suite Setup      Setup Video Demo Environment
Suite Teardown   Cleanup Video Demo Environment
Test Teardown    Run Keyword If Test Failed    Take Screenshot On Failure

Force Tags       video-demo    full-scenario

*** Variables ***
${DEMO_OUTPUT_DIR}       ${CURDIR}/../../robot_results/video_demo
${VIDEO_DIR}             ${CURDIR}/../../robot_results/video_demo/videos
${SCREENSHOT_DIR}        ${CURDIR}/../../robot_results/video_demo/screenshots
${USE_VIDEO}             1
${VIDEO_FILE}            ${EMPTY}

*** Keywords ***
Setup Video Demo Environment
    [Documentation]    Initialise l'environnement pour la démo vidéo
    Log To Console    ${\n}========================================
    Log To Console    🎬 INITIALISATION DEMO VIDEO
    Log To Console    ========================================

    # Créer les répertoires
    Create Directory    ${DEMO_OUTPUT_DIR}
    Create Directory    ${VIDEO_DIR}
    Create Directory    ${SCREENSHOT_DIR}

    Set Screenshot Directory    ${SCREENSHOT_DIR}

    # Démarrer l'enregistrement vidéo si activé
    ${video_enabled}=    Convert To Integer    ${USE_VIDEO}
    Run Keyword If    ${video_enabled} == 1    Start Screen Recording

    # Ouvrir le navigateur en mode VISIBLE (non-headless)
    Open Browser With Video Recording
    Go To    ${BASE_URL}

    Log To Console    ✅ Environnement vidéo prêt
    Log To Console    ========================================${\n}

Cleanup Video Demo Environment
    [Documentation]    Nettoie l'environnement et arrête la vidéo
    Log To Console    ${\n}========================================
    Log To Console    🧹 NETTOYAGE ET FINALISATION
    Log To Console    ========================================

    # Fermer le navigateur
    Close Browser Safely

    # Arrêter l'enregistrement vidéo
    ${video_enabled}=    Convert To Integer    ${USE_VIDEO}
    Run Keyword If    ${video_enabled} == 1    Stop Screen Recording

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

Take High Quality Screenshot
    [Documentation]    Prend un screenshot haute qualité avec nom descriptif
    [Arguments]    ${step_name}
    ${timestamp}=    Get Current Date    result_format=%Y%m%d_%H%M%S
    ${filename}=    Set Variable    ${step_name}_${timestamp}
    Capture Page Screenshot    ${filename}.png
    Sleep    1s    # Pause pour la vidéo
    Log To Console    📸 Screenshot: ${filename}.png
    RETURN    ${filename}

Wait And Screenshot
    [Documentation]    Attend puis prend un screenshot (pour vidéo fluide)
    [Arguments]    ${step_name}    ${wait_time}=2s
    Sleep    ${wait_time}
    Take High Quality Screenshot    ${step_name}

*** Test Cases ***
# ============================================
# DÉMO COMPLÈTE AVEC VIDÉO
# ============================================

DEMO_001 - Landing Page
    [Documentation]    Affiche la landing page SarfX
    [Tags]    landing
    Log To Console    ${\n}🏠 LANDING PAGE${\n}

    Wait Until Page Contains Element    css:body    timeout=10s
    Wait And Screenshot    01_landing_page    3s
    Page Should Contain    SarfX

    Log To Console    ✅ Landing page chargée${\n}

DEMO_002 - Login Admin
    [Documentation]    Connexion administrateur
    [Tags]    admin    auth
    Log To Console    👤 CONNEXION ADMIN${\n}

    Go To Login Page
    Wait And Screenshot    02_login_page

    Input Text    ${LOGIN_EMAIL_INPUT}    ${ADMIN_EMAIL}
    Sleep    1s
    Take High Quality Screenshot    03_email_entered

    Input Text    ${LOGIN_PASSWORD_INPUT}    ${ADMIN_PASSWORD}
    Sleep    1s
    Take High Quality Screenshot    04_password_entered

    Click Button    ${LOGIN_SUBMIT_BTN}
    Sleep    2s
    Take High Quality Screenshot    05_dashboard_admin

    Page Should Contain    Dashboard
    Log To Console    ✅ Admin connecté${\n}

DEMO_003 - Navigation Dashboard Admin
    [Documentation]    Exploration du dashboard administrateur
    [Tags]    admin
    Log To Console    📊 DASHBOARD ADMIN${\n}

    Wait And Screenshot    06_admin_home

    # Gestion Utilisateurs
    Click Link    ${ADMIN_USERS_LINK}
    Wait And Screenshot    07_users_management    3s

    # Gestion Wallets
    Click Link    ${ADMIN_WALLETS_LINK}
    Wait And Screenshot    08_wallets_management    3s

    # Gestion Transactions
    Click Link    ${ADMIN_TRANSACTIONS_LINK}
    Wait And Screenshot    09_transactions_admin    3s

    # Gestion Banques
    Click Link    ${ADMIN_BANKS_LINK}
    Wait And Screenshot    10_banks_management    3s

    Log To Console    ✅ Dashboard exploré${\n}

DEMO_004 - Logout et Login User
    [Documentation]    Déconnexion admin et connexion utilisateur
    [Tags]    auth
    Log To Console    🚪 CHANGEMENT DE SESSION${\n}

    Click Link    ${LOGOUT_LINK}
    Wait And Screenshot    11_logout_admin    2s

    Go To Login Page
    Login With Credentials    ${USER_EMAIL}    ${USER_PASSWORD}
    Wait And Screenshot    12_user_dashboard    3s

    Log To Console    ✅ Utilisateur connecté${\n}

DEMO_005 - Convertisseur de Devises
    [Documentation]    Test du convertisseur
    [Tags]    converter
    Log To Console    💱 CONVERTISSEUR${\n}

    Go To    ${BASE_URL}/app/converter
    Wait And Screenshot    13_converter_page    2s

    Input Text    id:amount    100
    Sleep    1s
    Take High Quality Screenshot    14_amount_entered

    Select From List By Label    id:from_currency    USD
    Sleep    1s
    Select From List By Label    id:to_currency    MAD
    Sleep    1s
    Take High Quality Screenshot    15_currencies_selected

    Click Button    css:button[type="submit"]
    Sleep    2s
    Take High Quality Screenshot    16_conversion_result

    Log To Console    ✅ Conversion effectuée${\n}

DEMO_006 - Wallets Utilisateur
    [Documentation]    Consultation des portefeuilles
    [Tags]    wallets
    Log To Console    💰 PORTEFEUILLES${\n}

    Click Link    ${USER_WALLETS_LINK}
    Wait And Screenshot    17_user_wallets    3s

    Log To Console    ✅ Portefeuilles affichés${\n}

DEMO_007 - Transactions Utilisateur
    [Documentation]    Historique des transactions
    [Tags]    transactions
    Log To Console    📜 TRANSACTIONS${\n}

    Click Link    ${USER_TRANSACTIONS_LINK}
    Wait And Screenshot    18_user_transactions    3s

    Log To Console    ✅ Historique affiché${\n}

DEMO_008 - Carte ATMs
    [Documentation]    Localisation des distributeurs
    [Tags]    atms
    Log To Console    🏧 CARTE DES ATMs${\n}

    Go To    ${BASE_URL}/app/atms
    Sleep    3s    # Attendre le chargement de la carte
    Take High Quality Screenshot    19_atm_map

    Log To Console    ✅ Carte affichée${\n}

DEMO_009 - Profil Utilisateur
    [Documentation]    Consultation du profil
    [Tags]    profile
    Log To Console    ⚙️ PROFIL${\n}

    Go To    ${BASE_URL}/app/profile
    Wait And Screenshot    20_user_profile    2s

    Log To Console    ✅ Profil affiché${\n}

DEMO_010 - Fin de Demo
    [Documentation]    Écran final de la démonstration
    [Tags]    final
    Log To Console    ${\n}🎬 FIN DE LA DÉMONSTRATION${\n}

    Go To    ${BASE_URL}
    Wait And Screenshot    21_demo_end    3s

    Log To Console    ========================================
    Log To Console    ✅ DÉMO TERMINÉE AVEC SUCCÈS
    Log To Console    📹 Vidéo: ${VIDEO_FILE}
    Log To Console    📸 Screenshots: ${SCREENSHOT_DIR}
    Log To Console    ========================================${\n}
