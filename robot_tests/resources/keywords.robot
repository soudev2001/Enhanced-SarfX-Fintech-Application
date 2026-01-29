*** Settings ***
Documentation    Keywords réutilisables pour les tests SarfX
...              Contient les actions communes: login, navigation, etc.

Library          SeleniumLibrary    timeout=30s    implicit_wait=5s
Library          Collections
Library          String
Library          DateTime
Library          OperatingSystem
Library          Screenshot

Resource         variables.robot

*** Variables ***
${DEFAULT_TIMEOUT}    30s
${SCREENSHOT_DIR}     ${CURDIR}/../../robot_results/screenshots

*** Keywords ***
# ============================================
# BROWSER SETUP (FIXED for Selenium 4.40+)
# ============================================
Open Browser To SarfX
    [Documentation]    Ouvre le navigateur Chrome en mode headless avec options compatibles
    ${chrome_options}=    Evaluate    sys.modules['selenium.webdriver'].ChromeOptions()    sys
    Call Method    ${chrome_options}    add_argument    --no-sandbox
    Call Method    ${chrome_options}    add_argument    --disable-dev-shm-usage
    Call Method    ${chrome_options}    add_argument    --disable-gpu
    Call Method    ${chrome_options}    add_argument    --headless=new
    Call Method    ${chrome_options}    add_argument    --window-size=1920,1080
    Call Method    ${chrome_options}    add_argument    --disable-extensions
    Call Method    ${chrome_options}    add_argument    --disable-infobars
    Call Method    ${chrome_options}    add_argument    --remote-debugging-port=9222
    Create Webdriver    Chrome    options=${chrome_options}
    Set Window Size    1920    1080
    Set Selenium Timeout    30s

Open Browser With Video Recording
    [Documentation]    Ouvre le navigateur pour enregistrement vidéo (non-headless)
    ${chrome_options}=    Evaluate    sys.modules['selenium.webdriver'].ChromeOptions()    sys
    Call Method    ${chrome_options}    add_argument    --no-sandbox
    Call Method    ${chrome_options}    add_argument    --disable-dev-shm-usage
    Call Method    ${chrome_options}    add_argument    --disable-gpu
    Call Method    ${chrome_options}    add_argument    --window-size=1920,1080
    Call Method    ${chrome_options}    add_argument    --start-maximized
    Create Webdriver    Chrome    options=${chrome_options}
    Set Window Size    1920    1080
    Set Selenium Timeout    30s

Close Browser Safely
    [Documentation]    Ferme le navigateur de manière sécurisée
    Run Keyword And Ignore Error    Close All Browsers

Take Screenshot On Failure
    [Documentation]    Capture d'écran automatique en cas d'échec
    ${time}=    Get Current Date    result_format=%Y%m%d_%H%M%S
    Capture Page Screenshot    failure_${time}.png

Take Demo Screenshot
    [Documentation]    Capture d'écran avec nom descriptif pour la démo
    [Arguments]    ${step_name}
    ${time}=    Get Current Date    result_format=%Y%m%d_%H%M%S
    ${filename}=    Set Variable    demo_${step_name}_${time}.png
    Capture Page Screenshot    ${filename}
    Log    Screenshot captured: ${filename}
    RETURN    ${filename}

# ============================================
# LOGIN KEYWORDS
# ============================================
Go To Login Page
    [Documentation]    Navigue vers la page de connexion
    Go To    ${LOGIN_URL}
    Wait Until Page Contains Element    ${LOGIN_EMAIL_INPUT}    30s

Login With Credentials
    [Documentation]    Se connecte avec email et mot de passe
    [Arguments]    ${email}    ${password}
    Go To Login Page
    Wait Until Element Is Visible    ${LOGIN_EMAIL_INPUT}    30s
    Input Text    ${LOGIN_EMAIL_INPUT}    ${email}
    Input Text    ${LOGIN_PASSWORD_INPUT}    ${password}
    Click Button    ${LOGIN_SUBMIT_BTN}
    Wait For Page Load

Login As Admin
    [Documentation]    Connexion avec le compte admin
    Login With Credentials    ${ADMIN_EMAIL}    ${ADMIN_PASSWORD}
    Wait Until Location Contains    /app    30s

Login As User
    [Documentation]    Connexion avec le compte utilisateur
    Login With Credentials    ${USER_EMAIL}    ${USER_PASSWORD}
    Wait Until Location Contains    /app    30s

Login As Bank Respo
    [Documentation]    Connexion avec le compte responsable banque
    Login With Credentials    ${BANK_RESPO_EMAIL}    ${BANK_RESPO_PASSWORD}
    Wait Until Location Contains    /app    30s

Login Via Demo Button Admin
    [Documentation]    Connexion via le bouton démo Admin
    Go To Login Page
    ${status}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${DEMO_ADMIN_BTN}    10s
    Run Keyword If    ${status}    Click Element    ${DEMO_ADMIN_BTN}
    Run Keyword If    ${status}    Sleep    1s
    Run Keyword If    not ${status}    Input Text    ${LOGIN_EMAIL_INPUT}    ${ADMIN_EMAIL}
    Run Keyword If    not ${status}    Input Text    ${LOGIN_PASSWORD_INPUT}    ${ADMIN_PASSWORD}
    Click Button    ${LOGIN_SUBMIT_BTN}
    Wait Until Location Contains    /app    30s

Login Via Demo Button User
    [Documentation]    Connexion via le bouton démo User
    Go To Login Page
    ${status}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${DEMO_USER_BTN}    10s
    Run Keyword If    ${status}    Click Element    ${DEMO_USER_BTN}
    Run Keyword If    ${status}    Sleep    1s
    Run Keyword If    not ${status}    Input Text    ${LOGIN_EMAIL_INPUT}    ${USER_EMAIL}
    Run Keyword If    not ${status}    Input Text    ${LOGIN_PASSWORD_INPUT}    ${USER_PASSWORD}
    Click Button    ${LOGIN_SUBMIT_BTN}
    Wait Until Location Contains    /app    30s

Logout
    [Documentation]    Déconnexion de l'utilisateur
    ${status}=    Run Keyword And Return Status    Click Element    ${NAV_LOGOUT}
    Run Keyword If    not ${status}    Go To    ${BASE_URL}/auth/logout
    Sleep    1s

Verify Login Failed
    [Documentation]    Vérifie que la connexion a échoué
    Wait Until Element Is Visible    ${LOGIN_ERROR_MSG}    10s
    Element Should Be Visible    ${LOGIN_ERROR_MSG}

# ============================================
# NAVIGATION KEYWORDS
# ============================================
Navigate To Home
    [Documentation]    Navigue vers la page d'accueil de l'app
    Go To    ${APP_HOME_URL}
    Wait For Page Load

Navigate To Converter
    [Documentation]    Navigue vers le convertisseur
    Go To    ${CONVERTER_URL}
    Wait For Page Load
    Sleep    1s

Navigate To Wallets
    [Documentation]    Navigue vers les portefeuilles
    Go To    ${WALLETS_URL}
    Wait For Page Load

Navigate To Transactions
    [Documentation]    Navigue vers l'historique des transactions
    Go To    ${TRANSACTIONS_URL}
    Wait For Page Load

Navigate To Profile
    [Documentation]    Navigue vers le profil
    Go To    ${PROFILE_URL}
    Wait For Page Load

Navigate To Beneficiaries
    [Documentation]    Navigue vers les bénéficiaires
    Go To    ${BENEFICIARIES_URL}
    Wait For Page Load

Navigate To ATMs
    [Documentation]    Navigue vers la carte des ATMs
    Go To    ${ATM_URL}
    Wait For Page Load

Navigate To AI Assistant
    [Documentation]    Navigue vers l'assistant IA
    Go To    ${AI_URL}
    Wait For Page Load

Navigate To Admin Dashboard
    [Documentation]    Navigue vers le dashboard admin
    Go To    ${ADMIN_URL}
    Wait For Page Load

Navigate To Admin Users
    [Documentation]    Navigue vers la gestion des utilisateurs admin
    Go To    ${ADMIN_USERS_URL}
    Wait For Page Load

Navigate To Admin Wallets
    [Documentation]    Navigue vers la gestion des wallets admin
    Go To    ${ADMIN_WALLETS_URL}
    Wait For Page Load

Navigate To Admin Transactions
    [Documentation]    Navigue vers les transactions admin
    Go To    ${ADMIN_TRANSACTIONS_URL}
    Wait For Page Load

Navigate To Admin Banks
    [Documentation]    Navigue vers la gestion des banques
    Go To    ${ADMIN_BANKS_URL}
    Wait For Page Load

Wait For Page Load
    [Documentation]    Attend que la page soit complètement chargée
    Wait For Condition    return document.readyState == "complete"    30s
    Sleep    0.5s

Wait For Element And Click
    [Documentation]    Attend qu'un élément soit visible et clique dessus
    [Arguments]    ${locator}
    Wait Until Element Is Visible    ${locator}    30s
    Click Element    ${locator}

# ============================================
# CONVERTER KEYWORDS
# ============================================
Enter Conversion Amount
    [Documentation]    Entre un montant à convertir
    [Arguments]    ${amount}
    Wait Until Element Is Visible    ${AMOUNT_INPUT}    30s
    Clear Element Text    ${AMOUNT_INPUT}
    Input Text    ${AMOUNT_INPUT}    ${amount}

Select From Currency
    [Documentation]    Sélectionne la devise source
    [Arguments]    ${currency}
    Wait Until Element Is Visible    ${FROM_CURRENCY}    30s
    Select From List By Value    ${FROM_CURRENCY}    ${currency}

Select To Currency
    [Documentation]    Sélectionne la devise cible
    [Arguments]    ${currency}
    Wait Until Element Is Visible    ${TO_CURRENCY}    30s
    Select From List By Value    ${TO_CURRENCY}    ${currency}

Click Convert Button
    [Documentation]    Clique sur le bouton convertir
    Wait For Element And Click    ${CONVERT_BTN}
    Sleep    1s

Perform Conversion
    [Documentation]    Effectue une conversion complète
    [Arguments]    ${amount}    ${from}    ${to}
    Enter Conversion Amount    ${amount}
    Select From Currency    ${from}
    Select To Currency    ${to}
    Click Convert Button

Get Conversion Result
    [Documentation]    Récupère le résultat de la conversion
    Wait Until Element Is Visible    ${RESULT_DISPLAY}    30s
    ${result}=    Get Text    ${RESULT_DISPLAY}
    RETURN    ${result}

Swap Currencies
    [Documentation]    Inverse les devises source et cible
    Wait For Element And Click    ${SWAP_BTN}
    Sleep    1s

# ============================================
# ADMIN KEYWORDS
# ============================================
Verify Admin Dashboard Loaded
    [Documentation]    Vérifie que le dashboard admin est chargé
    Wait Until Element Is Visible    ${ADMIN_KPI_CARDS}    30s
    Page Should Contain Element    ${ADMIN_KPI_CARDS}

Search Admin Users
    [Documentation]    Recherche un utilisateur dans l'admin
    [Arguments]    ${search_term}
    Wait Until Element Is Visible    ${ADMIN_SEARCH_INPUT}    30s
    Input Text    ${ADMIN_SEARCH_INPUT}    ${search_term}
    Sleep    1s

Count Admin Table Rows
    [Documentation]    Compte le nombre de lignes dans le tableau admin
    ${rows}=    Get Element Count    ${ADMIN_USER_ROW}
    RETURN    ${rows}

Export Data To CSV
    [Documentation]    Exporte les données en CSV
    Wait For Element And Click    ${ADMIN_EXPORT_BTN}
    Sleep    2s

Click Admin Nav Item
    [Documentation]    Clique sur un item de navigation admin
    [Arguments]    ${nav_selector}
    Wait For Element And Click    ${nav_selector}
    Wait For Page Load

# ============================================
# WALLET KEYWORDS
# ============================================
Get Wallet Count
    [Documentation]    Compte le nombre de wallets affichés
    ${count}=    Get Element Count    ${WALLET_CARD}
    RETURN    ${count}

Verify Wallet Displayed
    [Documentation]    Vérifie qu'un wallet est affiché
    [Arguments]    ${currency}
    Page Should Contain    ${currency}

# ============================================
# VERIFICATION KEYWORDS
# ============================================
Page Should Be Accessible
    [Documentation]    Vérifie que la page est accessible (pas d'erreur 404/500)
    ${source}=    Get Source
    Should Not Contain    ${source}    404 Not Found
    Should Not Contain    ${source}    500 Internal Server Error

Verify Toast Success
    [Documentation]    Vérifie qu'un toast de succès apparaît
    ${status}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${TOAST_SUCCESS}    10s
    RETURN    ${status}

Verify Toast Error
    [Documentation]    Vérifie qu'un toast d'erreur apparaît
    ${status}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${TOAST_ERROR}    10s
    RETURN    ${status}

Wait And Close Modal
    [Documentation]    Attend et ferme une modal
    ${status}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${MODAL}    5s
    Run Keyword If    ${status}    Click Element    ${MODAL_CLOSE}
    Run Keyword If    ${status}    Sleep    1s

Element Should Be Visible With Retry
    [Documentation]    Vérifie qu'un élément est visible avec retry
    [Arguments]    ${locator}    ${retries}=3
    FOR    ${i}    IN RANGE    ${retries}
        ${status}=    Run Keyword And Return Status    Element Should Be Visible    ${locator}
        Return From Keyword If    ${status}
        Sleep    1s
    END
    Fail    Element ${locator} not visible after ${retries} retries

# ============================================
# MOBILE KEYWORDS
# ============================================
Set Mobile Viewport
    [Documentation]    Configure le viewport mobile (iPhone)
    Set Window Size    375    812

Set Desktop Viewport
    [Documentation]    Configure le viewport desktop
    Set Window Size    1920    1080

Set Tablet Viewport
    [Documentation]    Configure le viewport tablette
    Set Window Size    768    1024

# ============================================
# DEMO SCENARIO KEYWORDS
# ============================================
Demo Step With Screenshot
    [Documentation]    Exécute une étape de démo avec screenshot
    [Arguments]    ${step_name}    ${action_keyword}    @{args}
    Log    === DEMO STEP: ${step_name} ===    console=yes
    Run Keyword    ${action_keyword}    @{args}
    Sleep    1s
    ${screenshot}=    Take Demo Screenshot    ${step_name}
    RETURN    ${screenshot}

Log Demo Message
    [Documentation]    Log un message pour la démo
    [Arguments]    ${message}
    Log    \n========================================    console=yes
    Log    ${message}    console=yes
    Log    ========================================\n    console=yes

Verify Page Title Contains
    [Documentation]    Vérifie que le titre contient un texte
    [Arguments]    ${expected_text}
    ${title}=    Get Title
    Should Contain    ${title}    ${expected_text}    ignore_case=True
