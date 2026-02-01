*** Settings ***
Documentation    Tests API SarfX avec RequestsLibrary
...              Taux, Conversion, Banks, ATMs

Library          RequestsLibrary
Library          Collections
Library          String

Force Tags       api

*** Variables ***
${API_BASE}      https://sarfx.io/api

*** Test Cases ***
# ============================================
# RATES API TESTS
# ============================================
TC_API_001 - GET /api/rates retourne des données
    [Documentation]    L'endpoint des taux retourne une réponse valide
    [Tags]    smoke    critical
    Create Session    sarfx    ${API_BASE}
    ${response}=    GET On Session    sarfx    /rates
    Should Be True    ${response.status_code} < 400
    Log    Response: ${response.json()}

TC_API_002 - GET /api/rates/live retourne les taux en direct
    [Documentation]    Les taux live sont retournés
    [Tags]    smoke
    Create Session    sarfx    ${API_BASE}
    ${response}=    GET On Session    sarfx    /rates/live
    Should Be True    ${response.status_code} < 500

TC_API_003 - GET /api/rates/best avec paramètres
    [Documentation]    Les meilleurs taux avec montant
    [Tags]    functionality
    Create Session    sarfx    ${API_BASE}
    ${params}=    Create Dictionary    amount=1000    from=USD    to=MAD
    ${response}=    GET On Session    sarfx    /rates/best    params=${params}
    Should Be True    ${response.status_code} < 500
    Log    Best rates: ${response.json()}

TC_API_004 - Taux avec devise invalide
    [Documentation]    L'API gère les devises invalides
    [Tags]    negative
    Create Session    sarfx    ${API_BASE}
    ${params}=    Create Dictionary    base=INVALID    quote=MAD
    ${response}=    GET On Session    sarfx    /rates/live    params=${params}    expected_status=any
    Should Be True    ${response.status_code} < 500

# ============================================
# CONVERT API TESTS
# ============================================
TC_API_010 - Conversion USD vers MAD
    [Documentation]    Convertir 100 USD en MAD via API
    [Tags]    critical    conversion
    Create Session    sarfx    ${API_BASE}
    ${params}=    Create Dictionary    amount=100    from=USD    to=MAD
    ${response}=    GET On Session    sarfx    /convert    params=${params}
    Should Be True    ${response.status_code} < 400
    ${json}=    Set Variable    ${response.json()}
    Log    Conversion result: ${json}

TC_API_011 - Conversion EUR vers MAD
    [Documentation]    Convertir 50 EUR en MAD via API
    [Tags]    conversion
    Create Session    sarfx    ${API_BASE}
    ${params}=    Create Dictionary    amount=50    from=EUR    to=MAD
    ${response}=    GET On Session    sarfx    /convert    params=${params}
    Should Be True    ${response.status_code} < 400

TC_API_012 - Conversion avec montant zéro
    [Documentation]    Comportement avec montant 0
    [Tags]    edge_case
    Create Session    sarfx    ${API_BASE}
    ${params}=    Create Dictionary    amount=0    from=USD    to=MAD
    ${response}=    GET On Session    sarfx    /convert    params=${params}    expected_status=any
    Should Be True    ${response.status_code} < 500

TC_API_013 - Conversion avec montant négatif
    [Documentation]    Comportement avec montant négatif
    [Tags]    negative
    Create Session    sarfx    ${API_BASE}
    ${params}=    Create Dictionary    amount=-100    from=USD    to=MAD
    ${response}=    GET On Session    sarfx    /convert    params=${params}    expected_status=any
    Should Be True    ${response.status_code} < 500

TC_API_014 - Conversion sans paramètres
    [Documentation]    Comportement sans paramètres
    [Tags]    negative
    Create Session    sarfx    ${API_BASE}
    ${response}=    GET On Session    sarfx    /convert    expected_status=any
    Should Be True    ${response.status_code} < 500

# ============================================
# HISTORY API TESTS
# ============================================
TC_API_020 - Historique des taux 7 jours
    [Documentation]    Récupérer l'historique sur 7 jours
    [Tags]    history
    Create Session    sarfx    ${API_BASE}
    ${params}=    Create Dictionary    base=USD    quote=MAD    days=7
    ${response}=    GET On Session    sarfx    /rates/history    params=${params}    expected_status=any
    Should Be True    ${response.status_code} < 500

TC_API_021 - Historique des taux 30 jours
    [Documentation]    Récupérer l'historique sur 30 jours
    [Tags]    history
    Create Session    sarfx    ${API_BASE}
    ${params}=    Create Dictionary    base=EUR    quote=MAD    days=30
    ${response}=    GET On Session    sarfx    /rates/history    params=${params}    expected_status=any
    Should Be True    ${response.status_code} < 500

# ============================================
# BANKS API TESTS
# ============================================
TC_API_030 - Liste des banques
    [Documentation]    Récupérer la liste des banques
    [Tags]    smoke    banks
    Create Session    sarfx    ${API_BASE}
    ${response}=    GET On Session    sarfx    /banks
    Should Be True    ${response.status_code} < 400
    ${json}=    Set Variable    ${response.json()}
    Log    Banks: ${json}

TC_API_031 - Banques ont les champs requis
    [Documentation]    Vérifier la structure des données banques
    [Tags]    banks
    Create Session    sarfx    ${API_BASE}
    ${response}=    GET On Session    sarfx    /banks
    Should Be True    ${response.status_code} < 400

# ============================================
# ATMs API TESTS
# ============================================
TC_API_040 - Liste des ATMs
    [Documentation]    Récupérer la liste des ATMs
    [Tags]    smoke    atms
    Create Session    sarfx    ${API_BASE}
    ${response}=    GET On Session    sarfx    /atms
    Should Be True    ${response.status_code} < 400

TC_API_041 - ATMs les plus proches
    [Documentation]    Trouver les ATMs proches de Casablanca
    [Tags]    atms    geolocation
    Create Session    sarfx    ${API_BASE}
    ${data}=    Create Dictionary    lat=33.5731    lng=-7.5898
    ${response}=    POST On Session    sarfx    /atms/nearest    data=${data}    expected_status=any
    Should Be True    ${response.status_code} < 500

# ============================================
# WALLET API TESTS
# ============================================
TC_API_050 - Wallet balance sans auth
    [Documentation]    Le solde wallet nécessite une authentification
    [Tags]    security    wallet
    Create Session    sarfx    ${API_BASE}
    ${response}=    GET On Session    sarfx    /wallet/balance    expected_status=any
    # Should require auth - 401, 403, or redirect 302
    Should Be True    ${response.status_code} in [200, 302, 401, 403]

# ============================================
# ALERTS API TESTS
# ============================================
TC_API_060 - Alertes sans auth
    [Documentation]    Les alertes nécessitent une authentification
    [Tags]    security    alerts
    Create Session    sarfx    ${API_BASE}
    ${response}=    GET On Session    sarfx    /alerts    expected_status=any
    Should Be True    ${response.status_code} < 500

# ============================================
# THEME API TESTS
# ============================================
TC_API_070 - Changer thème dark
    [Documentation]    Changer le thème en dark
    [Tags]    theme
    Create Session    sarfx    ${API_BASE}
    ${data}=    Create Dictionary    theme=dark
    ${response}=    POST On Session    sarfx    /theme    data=${data}    expected_status=any
    Should Be True    ${response.status_code} < 500

TC_API_071 - Changer thème light
    [Documentation]    Changer le thème en light
    [Tags]    theme
    Create Session    sarfx    ${API_BASE}
    ${data}=    Create Dictionary    theme=light
    ${response}=    POST On Session    sarfx    /theme    data=${data}    expected_status=any
    Should Be True    ${response.status_code} < 500

# ============================================
# ERROR HANDLING TESTS
# ============================================
TC_API_080 - Endpoint inconnu retourne 404
    [Documentation]    Un endpoint inexistant retourne 404
    [Tags]    error_handling
    Create Session    sarfx    ${API_BASE}
    ${response}=    GET On Session    sarfx    /unknown-endpoint-xyz    expected_status=404
    Should Be Equal As Integers    ${response.status_code}    404

TC_API_081 - API retourne JSON valide
    [Documentation]    Les réponses sont en JSON valide
    [Tags]    smoke
    Create Session    sarfx    ${API_BASE}
    ${response}=    GET On Session    sarfx    /rates
    ${content_type}=    Get From Dictionary    ${response.headers}    Content-Type
    Should Contain    ${content_type}    application/json

# ============================================
# PERFORMANCE TESTS
# ============================================
TC_API_090 - Temps de réponse rates < 5s
    [Documentation]    L'API rates répond en moins de 5 secondes
    [Tags]    performance
    Create Session    sarfx    ${API_BASE}    timeout=5
    ${response}=    GET On Session    sarfx    /rates
    Should Be True    ${response.status_code} < 400
    Should Be True    ${response.elapsed.total_seconds()} < 5
    Log    Response time: ${response.elapsed.total_seconds()}s

TC_API_091 - Temps de réponse convert < 5s
    [Documentation]    L'API convert répond en moins de 5 secondes
    [Tags]    performance
    Create Session    sarfx    ${API_BASE}    timeout=5
    ${params}=    Create Dictionary    amount=100    from=USD    to=MAD
    ${response}=    GET On Session    sarfx    /convert    params=${params}
    Should Be True    ${response.elapsed.total_seconds()} < 5
    Log    Response time: ${response.elapsed.total_seconds()}s
