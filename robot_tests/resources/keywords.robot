*** Settings ***
Documentation    Keywords réutilisables pour les tests SarfX
...              Contient les actions communes: login, navigation, etc.

Library          SeleniumLibrary    timeout=${TIMEOUT}    implicit_wait=5s
Library          Collections
Library          String
Library          DateTime
Library          OperatingSystem

Resource         variables.robot

*** Keywords ***
# ============================================
# BROWSER SETUP
# ============================================
Open Browser To SarfX
    [Documentation]    Ouvre le navigateur avec les options configurées
    ${chrome_options}=    Evaluate    sys.modules['selenium.webdriver'].ChromeOptions()    sys
    Call Method    ${chrome_options}    add_argument    --no-sandbox
    Call Method    ${chrome_options}    add_argument    --disable-dev-shm-usage
    Call Method    ${chrome_options}    add_argument    --disable-gpu
    Call Method    ${chrome_options}    add_argument    --window-size=1920,1080
    Run Keyword If    ${HEADLESS}    Call Method    ${chrome_options}    add_argument    --headless
    Create Webdriver    Chrome    options=${chrome_options}
    Set Window Size    1920    1080

Close Browser Safely
    [Documentation]    Ferme le navigateur de manière sécurisée
    Run Keyword And Ignore Error    Close All Browsers

Take Screenshot On Failure
    [Documentation]    Capture d'écran automatique en cas d'échec
    ${time}=    Get Current Date    result_format=%Y%m%d_%H%M%S
    Capture Page Screenshot    failure_${time}.png

# ============================================
# LOGIN KEYWORDS
# ============================================
Go To Login Page
    [Documentation]    Navigue vers la page de connexion
    Go To    ${LOGIN_URL}
    Wait Until Page Contains Element    ${LOGIN_EMAIL_INPUT}    ${TIMEOUT}
    Title Should Contain    Login

Login With Credentials
    [Documentation]    Se connecte avec email et mot de passe
    [Arguments]    ${email}    ${password}
    Go To Login Page
    Input Text    ${LOGIN_EMAIL_INPUT}    ${email}
    Input Text    ${LOGIN_PASSWORD_INPUT}    ${password}
    Click Button    ${LOGIN_SUBMIT_BTN}
    Wait For Page Load

Login As Admin
    [Documentation]    Connexion avec le compte admin
    Login With Credentials    ${ADMIN_EMAIL}    ${ADMIN_PASSWORD}
    Wait Until Location Contains    /app    ${TIMEOUT}

Login As User
    [Documentation]    Connexion avec le compte utilisateur
    Login With Credentials    ${USER_EMAIL}    ${USER_PASSWORD}
    Wait Until Location Contains    /app    ${TIMEOUT}

Login As Bank Respo
    [Documentation]    Connexion avec le compte responsable banque
    Login With Credentials    ${BANK_RESPO_EMAIL}    ${BANK_RESPO_PASSWORD}
    Wait Until Location Contains    /app    ${TIMEOUT}

Login Via Demo Button Admin
    [Documentation]    Connexion via le bouton démo Admin
    Go To Login Page
    Wait Until Element Is Visible    ${DEMO_ADMIN_BTN}    ${SHORT_TIMEOUT}
    Click Element    ${DEMO_ADMIN_BTN}
    Wait For Page Load
    Click Button    ${LOGIN_SUBMIT_BTN}
    Wait Until Location Contains    /app    ${TIMEOUT}

Login Via Demo Button User
    [Documentation]    Connexion via le bouton démo User
    Go To Login Page
    Wait Until Element Is Visible    ${DEMO_USER_BTN}    ${SHORT_TIMEOUT}
    Click Element    ${DEMO_USER_BTN}
    Wait For Page Load
    Click Button    ${LOGIN_SUBMIT_BTN}
    Wait Until Location Contains    /app    ${TIMEOUT}

Logout
    [Documentation]    Déconnexion de l'utilisateur
    Click Element    ${NAV_LOGOUT}
    Wait Until Location Contains    /auth/login    ${TIMEOUT}

Verify Login Failed
    [Documentation]    Vérifie que la connexion a échoué
    Wait Until Element Is Visible    ${LOGIN_ERROR_MSG}    ${SHORT_TIMEOUT}
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
    Wait Until Element Is Visible    ${AMOUNT_INPUT}    ${TIMEOUT}

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

Navigate To Admin Dashboard
    [Documentation]    Navigue vers le dashboard admin
    Go To    ${ADMIN_URL}
    Wait For Page Load

Navigate To Admin Users
    [Documentation]    Navigue vers la gestion des utilisateurs admin
    Go To    ${ADMIN_USERS_URL}
    Wait For Page Load

Wait For Page Load
    [Documentation]    Attend que la page soit complètement chargée
    Wait For Condition    return document.readyState == "complete"    ${TIMEOUT}
    Sleep    0.5s

# ============================================
# CONVERTER KEYWORDS
# ============================================
Enter Conversion Amount
    [Documentation]    Entre un montant à convertir
    [Arguments]    ${amount}
    Clear Element Text    ${AMOUNT_INPUT}
    Input Text    ${AMOUNT_INPUT}    ${amount}

Select From Currency
    [Documentation]    Sélectionne la devise source
    [Arguments]    ${currency}
    Select From List By Value    ${FROM_CURRENCY}    ${currency}

Select To Currency
    [Documentation]    Sélectionne la devise cible
    [Arguments]    ${currency}
    Select From List By Value    ${TO_CURRENCY}    ${currency}

Click Convert Button
    [Documentation]    Clique sur le bouton convertir
    Click Element    ${CONVERT_BTN}
    Wait For Page Load

Perform Conversion
    [Documentation]    Effectue une conversion complète
    [Arguments]    ${amount}    ${from}    ${to}
    Enter Conversion Amount    ${amount}
    Select From Currency    ${from}
    Select To Currency    ${to}
    Click Convert Button

Get Conversion Result
    [Documentation]    Récupère le résultat de la conversion
    ${result}=    Get Text    ${RESULT_DISPLAY}
    RETURN    ${result}

Swap Currencies
    [Documentation]    Inverse les devises source et cible
    Click Element    ${SWAP_BTN}
    Wait For Page Load

# ============================================
# ADMIN KEYWORDS
# ============================================
Verify Admin Dashboard Loaded
    [Documentation]    Vérifie que le dashboard admin est chargé
    Wait Until Element Is Visible    ${ADMIN_KPI_CARDS}    ${TIMEOUT}
    Page Should Contain Element    ${ADMIN_KPI_CARDS}

Search Admin Users
    [Documentation]    Recherche un utilisateur dans l'admin
    [Arguments]    ${search_term}
    Input Text    ${ADMIN_SEARCH_INPUT}    ${search_term}
    Wait For Page Load

Count Admin Table Rows
    [Documentation]    Compte le nombre de lignes dans le tableau admin
    ${rows}=    Get Element Count    ${ADMIN_USER_ROW}
    RETURN    ${rows}

Export Data To CSV
    [Documentation]    Exporte les données en CSV
    Click Element    ${ADMIN_EXPORT_BTN}
    Sleep    2s

# ============================================
# VERIFICATION KEYWORDS
# ============================================
Page Should Be Accessible
    [Documentation]    Vérifie que la page est accessible (pas d'erreur 404/500)
    Page Should Not Contain    404
    Page Should Not Contain    500 Internal Server Error
    Page Should Not Contain    Page Not Found

Verify Toast Success
    [Documentation]    Vérifie qu'un toast de succès apparaît
    Wait Until Element Is Visible    ${TOAST_SUCCESS}    ${SHORT_TIMEOUT}

Verify Toast Error
    [Documentation]    Vérifie qu'un toast d'erreur apparaît
    Wait Until Element Is Visible    ${TOAST_ERROR}    ${SHORT_TIMEOUT}

Wait And Close Modal
    [Documentation]    Attend et ferme une modal
    Wait Until Element Is Visible    ${MODAL}    ${SHORT_TIMEOUT}
    Click Element    ${MODAL_CLOSE}
    Wait Until Element Is Not Visible    ${MODAL}    ${SHORT_TIMEOUT}

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
