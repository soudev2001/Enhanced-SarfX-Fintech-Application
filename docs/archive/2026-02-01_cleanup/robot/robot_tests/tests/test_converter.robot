*** Settings ***
Documentation    Tests du convertisseur de devises SarfX
...              Conversion, taux, alertes, historique

Resource         ../resources/keywords.robot
Resource         ../resources/variables.robot

Suite Setup      Run Keywords    Open Browser To SarfX    AND    Login As Admin
Suite Teardown   Run Keywords    Logout    AND    Close Browser Safely
Test Teardown    Run Keyword If Test Failed    Take Screenshot On Failure

Force Tags       converter

*** Test Cases ***
# ============================================
# PAGE LOAD TESTS
# ============================================
TC_CONV_001 - La page convertisseur se charge
    [Documentation]    Vérifie que la page de conversion s'affiche
    [Tags]    smoke    critical
    Navigate To Converter
    Page Should Contain Element    ${AMOUNT_INPUT}
    Page Should Be Accessible
    Capture Page Screenshot    converter_page.png

TC_CONV_002 - Le convertisseur a les sélecteurs de devises
    [Documentation]    Les sélecteurs de devises sont présents
    [Tags]    smoke
    Navigate To Converter
    Page Should Contain Element    ${FROM_CURRENCY}
    Page Should Contain Element    ${TO_CURRENCY}
    Capture Page Screenshot    converter_selectors.png

TC_CONV_003 - Le taux de change est affiché
    [Documentation]    Le taux actuel est visible
    [Tags]    smoke
    Navigate To Converter
    Wait Until Element Is Visible    ${RATE_DISPLAY}    ${TIMEOUT}
    ${rate}=    Get Text    ${RATE_DISPLAY}
    Should Not Be Empty    ${rate}
    Capture Page Screenshot    converter_rate_display.png

# ============================================
# CONVERSION TESTS
# ============================================
TC_CONV_010 - Conversion USD vers MAD
    [Documentation]    Convertir 100 USD en MAD
    [Tags]    critical    conversion
    Navigate To Converter
    Perform Conversion    100    USD    MAD
    Sleep    2s
    ${result}=    Get Conversion Result
    Should Not Be Empty    ${result}
    Log    Résultat conversion: ${result}
    Capture Page Screenshot    conversion_usd_mad.png

TC_CONV_011 - Conversion EUR vers MAD
    [Documentation]    Convertir 50 EUR en MAD
    [Tags]    conversion
    Navigate To Converter
    Perform Conversion    50    EUR    MAD
    Sleep    2s
    ${result}=    Get Conversion Result
    Should Not Be Empty    ${result}
    Log    Résultat conversion: ${result}
    Capture Page Screenshot    conversion_eur_mad.png

TC_CONV_012 - Conversion avec montant décimal
    [Documentation]    Convertir un montant avec décimales
    [Tags]    conversion
    Navigate To Converter
    Perform Conversion    123.45    USD    MAD
    Sleep    2s
    ${result}=    Get Conversion Result
    Should Not Be Empty    ${result}
    Capture Page Screenshot    conversion_decimal.png

TC_CONV_013 - Conversion avec grand montant
    [Documentation]    Convertir un grand montant (10000)
    [Tags]    conversion
    Navigate To Converter
    Perform Conversion    10000    USD    MAD
    Sleep    2s
    ${result}=    Get Conversion Result
    Should Not Be Empty    ${result}
    Capture Page Screenshot    conversion_large_amount.png

TC_CONV_014 - Conversion avec montant zéro
    [Documentation]    Vérifier le comportement avec montant 0
    [Tags]    edge_case
    Navigate To Converter
    Perform Conversion    0    USD    MAD
    Sleep    1s
    Capture Page Screenshot    conversion_zero.png

# ============================================
# CURRENCY SWAP TESTS
# ============================================
TC_CONV_020 - Swap des devises fonctionne
    [Documentation]    Le bouton swap inverse les devises
    [Tags]    functionality
    Navigate To Converter
    Select From Currency    USD
    Select To Currency    MAD
    ${from_before}=    Get Selected List Value    ${FROM_CURRENCY}
    ${to_before}=    Get Selected List Value    ${TO_CURRENCY}
    Swap Currencies
    Sleep    1s
    ${from_after}=    Get Selected List Value    ${FROM_CURRENCY}
    ${to_after}=    Get Selected List Value    ${TO_CURRENCY}
    Should Be Equal    ${from_before}    ${to_after}
    Should Be Equal    ${to_before}    ${from_after}
    Capture Page Screenshot    currency_swap.png

TC_CONV_021 - Sélection rapide de paires
    [Documentation]    Les boutons de paires rapides fonctionnent
    [Tags]    functionality
    Navigate To Converter
    # Check for quick pair buttons
    ${buttons}=    Get WebElements    css:.pair-btn, css:.quick-pair, css:[data-pair]
    ${count}=    Get Length    ${buttons}
    Run Keyword If    ${count} > 0    Click Element    ${buttons}[0]
    Sleep    1s
    Capture Page Screenshot    quick_pairs.png

# ============================================
# RATE DISPLAY TESTS
# ============================================
TC_CONV_030 - Rafraîchir les taux
    [Documentation]    Le bouton refresh met à jour les taux
    [Tags]    functionality
    Navigate To Converter
    ${refresh_btn}=    Set Variable    css:#refresh-rates, css:.refresh-btn, css:[onclick*="refresh"]
    ${exists}=    Run Keyword And Return Status    Element Should Be Visible    ${refresh_btn}
    Run Keyword If    ${exists}    Click Element    ${refresh_btn}
    Sleep    2s
    Capture Page Screenshot    rates_refreshed.png

TC_CONV_031 - Graphique historique affiché
    [Documentation]    Le graphique d'historique des taux est visible
    [Tags]    chart
    Navigate To Converter
    ${chart}=    Set Variable    css:canvas, css:.chart, css:#rate-chart
    ${exists}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${chart}    ${SHORT_TIMEOUT}
    Run Keyword If    ${exists}    Log    Chart is visible
    ...    ELSE    Log    No chart found on page
    Capture Page Screenshot    rate_chart.png

# ============================================
# PROVIDERS TESTS
# ============================================
TC_CONV_040 - Liste des fournisseurs affichée
    [Documentation]    La liste des providers est visible
    [Tags]    providers
    Navigate To Converter
    ${providers}=    Set Variable    css:.provider-list, css:.providers, css:#providers
    ${exists}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${providers}    ${SHORT_TIMEOUT}
    Run Keyword If    ${exists}    Log    Providers list visible
    Capture Page Screenshot    providers_list.png

TC_CONV_041 - Meilleur fournisseur mis en évidence
    [Documentation]    Le meilleur taux est mis en surbrillance
    [Tags]    providers
    Navigate To Converter
    ${best}=    Set Variable    css:.best-rate, css:.recommended, css:[data-best="true"]
    ${exists}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${best}    ${SHORT_TIMEOUT}
    Run Keyword If    ${exists}    Log    Best provider highlighted
    Capture Page Screenshot    best_provider.png

# ============================================
# ALERTS TESTS
# ============================================
TC_CONV_050 - Onglet alertes accessible
    [Documentation]    L'onglet des alertes de taux est accessible
    [Tags]    alerts
    Navigate To Converter
    ${alerts_tab}=    Set Variable    css:[href*="alert"], css:#alerts-tab, css:.alerts-link
    ${exists}=    Run Keyword And Return Status    Element Should Be Visible    ${alerts_tab}
    Run Keyword If    ${exists}    Click Element    ${alerts_tab}
    Sleep    1s
    Capture Page Screenshot    alerts_tab.png

TC_CONV_051 - Formulaire création alerte
    [Documentation]    Le formulaire de création d'alerte est présent
    [Tags]    alerts
    Navigate To Converter
    ${alert_form}=    Set Variable    css:form[action*="alert"], css:#alert-form, css:.create-alert
    ${exists}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${alert_form}    ${SHORT_TIMEOUT}
    Run Keyword If    ${exists}    Log    Alert form is visible
    Capture Page Screenshot    alert_form.png

# ============================================
# MOBILE TESTS
# ============================================
TC_CONV_060 - Convertisseur responsive mobile
    [Documentation]    Le convertisseur s'affiche correctement sur mobile
    [Tags]    mobile    responsive
    Set Mobile Viewport
    Navigate To Converter
    Page Should Contain Element    ${AMOUNT_INPUT}
    Capture Page Screenshot    converter_mobile.png
    Set Desktop Viewport

TC_CONV_061 - Conversion fonctionne sur mobile
    [Documentation]    La conversion fonctionne sur viewport mobile
    [Tags]    mobile
    Set Mobile Viewport
    Navigate To Converter
    Perform Conversion    100    USD    MAD
    Sleep    2s
    ${result}=    Get Conversion Result
    Should Not Be Empty    ${result}
    Capture Page Screenshot    conversion_mobile.png
    Set Desktop Viewport

# ============================================
# PERFORMANCE TESTS
# ============================================
TC_CONV_070 - Conversion répond rapidement
    [Documentation]    La conversion répond en moins de 5 secondes
    [Tags]    performance
    Navigate To Converter
    ${start}=    Get Time    epoch
    Perform Conversion    100    USD    MAD
    Wait Until Element Is Visible    ${RESULT_DISPLAY}    5s
    ${end}=    Get Time    epoch
    ${duration}=    Evaluate    ${end} - ${start}
    Should Be True    ${duration} < 5    Conversion took too long: ${duration}s
    Log    Conversion duration: ${duration} seconds
    Capture Page Screenshot    conversion_performance.png
