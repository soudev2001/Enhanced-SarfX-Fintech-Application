#!/bin/bash

#############################################################
#  SarfX E2E Tests - Runner Script
#############################################################
#
#  Ce script exécute les tests E2E Playwright avec:
#  - Enregistrement vidéo
#  - Screenshots sur échec
#  - Rapport HTML
#
#  Usage:
#    ./run_tests.sh                    # Tous les tests
#    ./run_tests.sh auth               # Tests d'authentification
#    ./run_tests.sh converter          # Tests du convertisseur
#    ./run_tests.sh admin              # Tests admin
#    ./run_tests.sh api                # Tests API
#    ./run_tests.sh --headed           # Mode visible (avec navigateur)
#    ./run_tests.sh --debug            # Mode debug
#
#############################################################

set -e

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction d'affichage
print_header() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}          ${GREEN}SarfX E2E Tests - Playwright Runner${NC}               ${BLUE}║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
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
RESULTS_DIR="${SCRIPT_DIR}/tests/results"
VIDEOS_DIR="${RESULTS_DIR}/videos"
SCREENSHOTS_DIR="${RESULTS_DIR}/screenshots"
TRACES_DIR="${RESULTS_DIR}/traces"

# Arguments
TEST_MARKER=""
HEADED=""
DEBUG=""
VERBOSE="-v"
EXTRA_ARGS=""

# Parse arguments
for arg in "$@"; do
    case $arg in
        auth|converter|admin|api|e2e)
            TEST_MARKER="-m $arg"
            ;;
        --headed)
            HEADED="--headed"
            ;;
        --debug)
            DEBUG="--slowmo 500"
            HEADED="--headed"
            ;;
        -vv)
            VERBOSE="-vv"
            ;;
        -q)
            VERBOSE=""
            ;;
        *)
            EXTRA_ARGS="$EXTRA_ARGS $arg"
            ;;
    esac
done

# Header
print_header

# Étape 1: Vérifier l'environnement
print_step "Vérification de l'environnement..."

# Check Python
if ! command -v python &> /dev/null; then
    print_error "Python n'est pas installé"
    exit 1
fi

# Check if venv exists, create if not
if [ ! -d "${SCRIPT_DIR}/venv" ]; then
    print_step "Création de l'environnement virtuel..."
    python -m venv venv
fi

print_success "Environnement Python OK"

# Étape 2: Activer venv et installer dépendances
print_step "Activation de l'environnement virtuel..."

# Activer selon l'OS
if [ -f "${SCRIPT_DIR}/venv/bin/activate" ]; then
    source "${SCRIPT_DIR}/venv/bin/activate"
else
    source "${SCRIPT_DIR}/venv/Scripts/activate"
fi

print_success "Environnement activé"

# Étape 3: Installer les dépendances de test
print_step "Installation des dépendances de test..."

pip install -q -r requirements-test.txt 2>/dev/null || {
    print_error "Échec de l'installation des dépendances"
    exit 1
}

print_success "Dépendances installées"

# Étape 4: Installer les navigateurs Playwright
print_step "Installation des navigateurs Playwright..."

python -m playwright install chromium 2>/dev/null || {
    print_step "Installation avec sudo..."
    python -m playwright install chromium --with-deps 2>/dev/null || true
}

print_success "Navigateurs installés"

# Étape 5: Créer les dossiers de résultats
print_step "Préparation des dossiers de résultats..."

mkdir -p "${VIDEOS_DIR}"
mkdir -p "${SCREENSHOTS_DIR}"
mkdir -p "${TRACES_DIR}"

print_success "Dossiers créés"

# Étape 6: Vérifier que l'application tourne
print_step "Vérification de l'application..."

APP_URL="http://localhost:5000"

if curl -s --head "${APP_URL}" | head -n 1 | grep -q "HTTP"; then
    print_success "Application accessible sur ${APP_URL}"
else
    print_error "⚠️  Application non accessible sur ${APP_URL}"
    echo ""
    echo -e "${YELLOW}Pour démarrer l'application:${NC}"
    echo "    python run.py"
    echo ""
    echo -e "${YELLOW}Ou continuer sans serveur (les tests échoueront):${NC}"
    read -p "Continuer quand même? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Étape 7: Exécuter les tests
echo ""
print_step "Exécution des tests Playwright..."
echo ""

# Build command
CMD="python -m pytest tests/e2e/ ${VERBOSE} ${TEST_MARKER} ${HEADED} --html=${RESULTS_DIR}/report.html --self-contained-html ${EXTRA_ARGS}"

# Add slow motion if debug
if [ -n "$DEBUG" ]; then
    export PWDEBUG=1
fi

echo -e "${BLUE}Commande:${NC} $CMD"
echo ""

# Run tests
$CMD && TEST_RESULT=0 || TEST_RESULT=$?

# Résumé
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"

if [ $TEST_RESULT -eq 0 ]; then
    print_success "Tous les tests ont réussi! 🎉"
else
    print_error "Certains tests ont échoué"
fi

echo ""
echo -e "${YELLOW}📁 Résultats:${NC}"
echo "   📄 Rapport HTML: ${RESULTS_DIR}/report.html"
echo "   📹 Vidéos:       ${VIDEOS_DIR}/"
echo "   📸 Screenshots:  ${SCREENSHOTS_DIR}/"
echo "   🔍 Traces:       ${TRACES_DIR}/"

# Compter les fichiers
VIDEO_COUNT=$(find "${VIDEOS_DIR}" -type f -name "*.webm" 2>/dev/null | wc -l)
SCREENSHOT_COUNT=$(find "${SCREENSHOTS_DIR}" -type f -name "*.png" 2>/dev/null | wc -l)

echo ""
echo -e "${GREEN}📊 Statistiques:${NC}"
echo "   📹 Vidéos enregistrées: ${VIDEO_COUNT}"
echo "   📸 Screenshots: ${SCREENSHOT_COUNT}"

# Ouvrir le rapport si disponible
if [ -f "${RESULTS_DIR}/report.html" ]; then
    echo ""
    echo -e "${YELLOW}💡 Pour voir le rapport:${NC}"
    echo "   open ${RESULTS_DIR}/report.html"
    echo "   # ou"
    echo "   python -m http.server 8000 --directory ${RESULTS_DIR}"
fi

echo ""
exit $TEST_RESULT
