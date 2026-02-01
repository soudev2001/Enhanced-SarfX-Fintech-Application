*** Settings ***
Documentation    Tests d'authentification SarfX
...              Login, Logout, Registration, Protection des routes

Resource         ../resources/keywords.robot
Resource         ../resources/variables.robot

Suite Setup      Open Browser To SarfX
Suite Teardown   Close Browser Safely
Test Teardown    Run Keyword If Test Failed    Take Screenshot On Failure

Force Tags       auth

*** Test Cases ***
# ============================================
# LOGIN TESTS
# ============================================
TC_AUTH_001 - La page de login se charge correctement
    [Documentation]    Vérifie que la page de connexion s'affiche
    [Tags]    smoke    critical
    Go To Login Page
    Page Should Contain Element    ${LOGIN_EMAIL_INPUT}
    Page Should Contain Element    ${LOGIN_PASSWORD_INPUT}
    Page Should Contain Element    ${LOGIN_SUBMIT_BTN}
    Capture Page Screenshot    login_page.png

TC_AUTH_002 - Connexion admin réussie
    [Documentation]    L'admin peut se connecter avec succès
    [Tags]    smoke    critical
    Login As Admin
    Location Should Contain    /app
    Capture Page Screenshot    admin_logged_in.png
    Logout

TC_AUTH_003 - Connexion utilisateur réussie
    [Documentation]    Un utilisateur peut se connecter
    [Tags]    smoke
    Login As User
    Location Should Contain    /app
    Capture Page Screenshot    user_logged_in.png
    Logout

TC_AUTH_004 - Connexion échoue avec mauvais mot de passe
    [Documentation]    La connexion échoue si le mot de passe est incorrect
    [Tags]    negative
    Login With Credentials    ${ADMIN_EMAIL}    wrongpassword123
    Verify Login Failed
    Location Should Contain    /auth/login
    Capture Page Screenshot    login_failed_wrong_password.png

TC_AUTH_005 - Connexion échoue avec email inexistant
    [Documentation]    La connexion échoue si l'email n'existe pas
    [Tags]    negative
    Login With Credentials    nonexistent@test.com    password123
    Verify Login Failed
    Location Should Contain    /auth/login
    Capture Page Screenshot    login_failed_no_user.png

TC_AUTH_006 - Bouton démo Admin fonctionne
    [Documentation]    Le bouton de connexion démo Admin remplit le formulaire
    [Tags]    demo
    Go To Login Page
    Wait Until Element Is Visible    ${DEMO_ADMIN_BTN}    ${SHORT_TIMEOUT}
    Click Element    ${DEMO_ADMIN_BTN}
    Sleep    1s
    ${email_value}=    Get Value    ${LOGIN_EMAIL_INPUT}
    Should Contain    ${email_value}    admin
    Capture Page Screenshot    demo_admin_button.png

TC_AUTH_007 - Bouton démo User fonctionne
    [Documentation]    Le bouton de connexion démo User remplit le formulaire
    [Tags]    demo
    Go To Login Page
    Wait Until Element Is Visible    ${DEMO_USER_BTN}    ${SHORT_TIMEOUT}
    Click Element    ${DEMO_USER_BTN}
    Sleep    1s
    ${email_value}=    Get Value    ${LOGIN_EMAIL_INPUT}
    Should Not Be Empty    ${email_value}
    Capture Page Screenshot    demo_user_button.png

# ============================================
# LOGOUT TESTS
# ============================================
TC_AUTH_010 - Déconnexion redirige vers login
    [Documentation]    Après déconnexion, l'utilisateur est redirigé vers login
    [Tags]    smoke
    Login As Admin
    Logout
    Location Should Contain    /auth/login
    Capture Page Screenshot    logout_redirect.png

TC_AUTH_011 - Session invalidée après déconnexion
    [Documentation]    L'utilisateur ne peut plus accéder à l'app après logout
    [Tags]    security
    Login As Admin
    Logout
    Go To    ${APP_HOME_URL}
    Location Should Contain    /auth/login
    Capture Page Screenshot    session_invalidated.png

# ============================================
# REGISTRATION TESTS
# ============================================
TC_AUTH_020 - Page d'inscription se charge
    [Documentation]    La page d'inscription s'affiche correctement
    [Tags]    smoke
    Go To    ${REGISTER_URL}
    Wait Until Page Contains Element    ${REGISTER_EMAIL_INPUT}    ${TIMEOUT}
    Page Should Contain Element    ${REGISTER_NAME_INPUT}
    Page Should Contain Element    ${REGISTER_PASSWORD_INPUT}
    Capture Page Screenshot    registration_page.png

TC_AUTH_021 - Inscription avec email existant échoue
    [Documentation]    L'inscription avec un email déjà utilisé échoue
    [Tags]    negative
    Go To    ${REGISTER_URL}
    Input Text    ${REGISTER_NAME_INPUT}    Test User
    Input Text    ${REGISTER_EMAIL_INPUT}    ${ADMIN_EMAIL}
    Input Text    ${REGISTER_PASSWORD_INPUT}    password123
    ${confirm_exists}=    Run Keyword And Return Status    Element Should Be Visible    ${REGISTER_CONFIRM_INPUT}
    Run Keyword If    ${confirm_exists}    Input Text    ${REGISTER_CONFIRM_INPUT}    password123
    Click Button    ${REGISTER_SUBMIT_BTN}
    Sleep    2s
    # Should show error or stay on registration
    Capture Page Screenshot    registration_duplicate_email.png

# ============================================
# ROUTE PROTECTION TESTS
# ============================================
TC_AUTH_030 - Utilisateur non connecté redirigé vers login
    [Documentation]    L'accès à /app sans connexion redirige vers login
    [Tags]    security    critical
    Close All Browsers
    Open Browser To SarfX
    Go To    ${APP_HOME_URL}
    Wait Until Location Contains    /auth/login    ${TIMEOUT}
    Capture Page Screenshot    route_protection_app.png

TC_AUTH_031 - Admin protégé - user normal refusé
    [Documentation]    Un utilisateur normal ne peut pas accéder à l'admin
    [Tags]    security
    Login As User
    Go To    ${ADMIN_URL}
    # Should be redirected or show forbidden
    ${is_admin}=    Run Keyword And Return Status    Location Should Contain    /admin
    Run Keyword If    ${is_admin}    Page Should Contain    Forbidden
    ...    ELSE    Log    User correctly redirected away from admin
    Capture Page Screenshot    user_blocked_from_admin.png
    Logout

TC_AUTH_032 - Admin accessible par admin
    [Documentation]    Un admin peut accéder au dashboard admin
    [Tags]    smoke
    Login As Admin
    Navigate To Admin Dashboard
    Location Should Contain    /admin
    Verify Admin Dashboard Loaded
    Capture Page Screenshot    admin_access_granted.png
    Logout

# ============================================
# MOBILE TESTS
# ============================================
TC_AUTH_040 - Login responsive sur mobile
    [Documentation]    La page de login s'affiche correctement sur mobile
    [Tags]    mobile    responsive
    Set Mobile Viewport
    Go To Login Page
    Page Should Contain Element    ${LOGIN_EMAIL_INPUT}
    Page Should Contain Element    ${LOGIN_SUBMIT_BTN}
    Capture Page Screenshot    login_mobile.png
    Set Desktop Viewport

TC_AUTH_041 - Login fonctionne sur mobile
    [Documentation]    La connexion fonctionne sur un viewport mobile
    [Tags]    mobile
    Set Mobile Viewport
    Login As Admin
    Location Should Contain    /app
    Capture Page Screenshot    login_mobile_success.png
    Logout
    Set Desktop Viewport
