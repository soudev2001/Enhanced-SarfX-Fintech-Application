#!/bin/bash

#############################################################
#  SarfX Robot Framework Tests - Runner Script
#############################################################
#
#  Ce script exécute les tests Robot Framework avec Selenium
#
#  Usage:
#    ./run_robot_tests.sh                    # Tous les tests
#    ./run_robot_tests.sh auth               # Tests auth seulement
#    ./run_robot_tests.sh converter          # Tests converter
#    ./run_robot_tests.sh admin              # Tests admin
#    ./run_robot_tests.sh api                # Tests API
#    ./run_robot_tests.sh --headed           # Mode avec navigateur visible
#    ./run_robot_tests.sh smoke              # Tests smoke seulement
#
#############################################################

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}      ${GREEN}🤖 SarfX Robot Framework Tests${NC}                         ${CYAN}║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${YELLOW}➤${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Variables
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROBOT_DIR="${SCRIPT_DIR}/robot_tests"
RESULTS_DIR="${SCRIPT_DIR}/robot_results"
TESTS_DIR="${ROBOT_DIR}/tests"

# Arguments
TEST_SUITE=""
INCLUDE_TAGS=""
EXCLUDE_TAGS=""
HEADED=""
EXTRA_ARGS=""

# Parse arguments
for arg in "$@"; do
    case $arg in
        auth)
            TEST_SUITE="${TESTS_DIR}/test_auth.robot"
            ;;
        converter)
            TEST_SUITE="${TESTS_DIR}/test_converter.robot"
            ;;
        admin)
            TEST_SUITE="${TESTS_DIR}/test_admin.robot"
            ;;
        api)
            TEST_SUITE="${TESTS_DIR}/test_api.robot"
            ;;
        smoke)
            INCLUDE_TAGS="--include smoke"
            ;;
        critical)
            INCLUDE_TAGS="--include critical"
            ;;
        mobile)
            INCLUDE_TAGS="--include mobile"
            ;;
        security)
            INCLUDE_TAGS="--include security"
            ;;
        --headed)
            EXTRA_ARGS="$EXTRA_ARGS --variable HEADLESS:False"
            ;;
        --include=*)
            INCLUDE_TAGS="--include ${arg#*=}"
            ;;
        --exclude=*)
            EXCLUDE_TAGS="--exclude ${arg#*=}"
            ;;
        *)
            EXTRA_ARGS="$EXTRA_ARGS $arg"
            ;;
    esac
done

# Default test suite
if [ -z "$TEST_SUITE" ]; then
    TEST_SUITE="${TESTS_DIR}"
fi

# Header
print_header

# Step 1: Check environment
print_step "Vérification de l'environnement..."

if ! command -v python3 &> /dev/null; then
    print_error "Python3 n'est pas installé"
    exit 1
fi

print_success "Python3 OK"

# Step 2: Create/activate venv
print_step "Configuration de l'environnement virtuel..."

VENV_DIR="${SCRIPT_DIR}/venv-robot"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

source "${VENV_DIR}/bin/activate"
print_success "Environnement activé: $VENV_DIR"

# Step 3: Install dependencies
print_step "Installation des dépendances Robot Framework..."

pip install -q -r requirements-robot.txt 2>/dev/null || {
    pip install robotframework robotframework-seleniumlibrary robotframework-requests selenium webdriver-manager
}

print_success "Dépendances installées"

# Step 4: Install ChromeDriver
print_step "Configuration de ChromeDriver..."

python3 << 'EOF'
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
try:
    driver_path = ChromeDriverManager().install()
    print(f"ChromeDriver: {driver_path}")
except Exception as e:
    print(f"Warning: {e}")
EOF

print_success "ChromeDriver configuré"

# Step 5: Create results directory
print_step "Préparation des dossiers de résultats..."

mkdir -p "${RESULTS_DIR}"
rm -rf "${RESULTS_DIR}"/*

print_success "Dossiers créés"

# Step 6: Check application
print_step "Vérification de l'application..."

APP_URL="https://sarfx.io"

if curl -s --head "${APP_URL}" | head -n 1 | grep -q "HTTP"; then
    print_success "Application accessible sur ${APP_URL}"
else
    print_error "⚠️  Application non accessible sur ${APP_URL}"
    echo ""
    read -p "Continuer quand même? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 7: Run tests
echo ""
print_step "Exécution des tests Robot Framework..."
echo ""

# Build command
CMD="robot \
    --outputdir ${RESULTS_DIR} \
    --loglevel DEBUG \
    --timestampoutputs \
    --reporttitle 'SarfX E2E Test Report' \
    --logtitle 'SarfX Test Log' \
    ${INCLUDE_TAGS} \
    ${EXCLUDE_TAGS} \
    ${EXTRA_ARGS} \
    ${TEST_SUITE}"

echo -e "${BLUE}Commande:${NC}"
echo "$CMD"
echo ""

# Run tests
$CMD && TEST_RESULT=0 || TEST_RESULT=$?

# Summary
echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"

if [ $TEST_RESULT -eq 0 ]; then
    print_success "Tous les tests ont réussi! 🎉"
else
    print_error "Certains tests ont échoué (code: $TEST_RESULT)"
fi

echo ""
echo -e "${YELLOW}📁 Résultats:${NC}"
echo "   📄 Rapport: ${RESULTS_DIR}/report.html"
echo "   📋 Log:     ${RESULTS_DIR}/log.html"
echo "   📊 Output:  ${RESULTS_DIR}/output.xml"

# Count screenshots
SCREENSHOT_COUNT=$(find "${RESULTS_DIR}" -type f -name "*.png" 2>/dev/null | wc -l)
echo ""
echo -e "${GREEN}📸 Screenshots capturés: ${SCREENSHOT_COUNT}${NC}"

# Open report hint
echo ""
echo -e "${YELLOW}💡 Pour voir le rapport:${NC}"
echo "   open ${RESULTS_DIR}/report.html"
echo "   # ou"
echo "   python3 -m http.server 8888 --directory ${RESULTS_DIR}"

echo ""
exit $TEST_RESULT
