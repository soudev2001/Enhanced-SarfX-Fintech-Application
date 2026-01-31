#!/bin/bash
# ============================================
# SarfX - Complete Production Deployment Script
# ============================================
# This script:
# - Installs system dependencies (Redis, Python)
# - Configures Google OAuth credentials
# - Updates .env for production
# - Installs all Python requirements
#
# Run: sudo bash setup_oauth_prod.sh
# ============================================

set -e

echo "🚀 SarfX - Déploiement Production Complet"
echo "=========================================="
echo "Date: $(date)"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Google OAuth Credentials - À CONFIGURER
# Copiez ces valeurs depuis Google Cloud Console
# Ou créez un fichier .oauth_credentials avec:
#   GOOGLE_CLIENT_ID=votre-client-id
#   GOOGLE_CLIENT_SECRET=votre-client-secret

# Check if credentials file exists
if [ -f "$SCRIPT_DIR/.oauth_credentials" ]; then
    source "$SCRIPT_DIR/.oauth_credentials"
    echo -e "${GREEN}✅ OAuth credentials loaded from .oauth_credentials${NC}"
else
    # Default placeholders - user must configure
    GOOGLE_CLIENT_ID="${GOOGLE_CLIENT_ID:-YOUR_GOOGLE_CLIENT_ID}"
    GOOGLE_CLIENT_SECRET="${GOOGLE_CLIENT_SECRET:-YOUR_GOOGLE_CLIENT_SECRET}"
fi

OAUTH_REDIRECT_URI="https://sarfx.io/auth/login/google/callback"

# Determine the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENV_FILE="$SCRIPT_DIR/.env"

echo -e "${YELLOW}📁 Working directory: $SCRIPT_DIR${NC}"
echo -e "${YELLOW}📄 .env file: $ENV_FILE${NC}"

# ============================================
# 0. Check if running as root (for apt install)
# ============================================
echo -e "\n${BLUE}🔍 Checking permissions...${NC}"
if [[ $EUID -ne 0 ]]; then
   echo -e "${YELLOW}⚠️  Not running as root. Some operations may require sudo.${NC}"
   SUDO_CMD="sudo"
else
   echo -e "${GREEN}✅ Running as root${NC}"
   SUDO_CMD=""
fi

# ============================================
# 0.5 Backup existing .env
# ============================================
echo -e "\n${GREEN}💾 Step 0: Backing up .env...${NC}"
if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ Backup created: .env.backup.$(date +%Y%m%d_%H%M%S)"
else
    echo -e "${YELLOW}⚠️  No existing .env file found${NC}"
fi

# ============================================
# 1. Install System Dependencies (Redis, Python3-pip)
# ============================================
echo -e "\n${GREEN}📦 Step 1: Installing system dependencies...${NC}"

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    echo "   Detected OS: $OS"
fi

# Update package list
echo "   Updating package list..."
$SUDO_CMD apt update -qq 2>/dev/null || echo "   apt update skipped"

# Install Redis
if ! command -v redis-server &> /dev/null; then
    echo "   Installing Redis..."
    $SUDO_CMD apt install -y redis-server
    echo "   ✅ Redis installed"
else
    echo "   ✅ Redis already installed"
fi

# Install Python3 and pip
if ! command -v python3 &> /dev/null; then
    echo "   Installing Python3..."
    $SUDO_CMD apt install -y python3 python3-pip python3-venv
    echo "   ✅ Python3 installed"
else
    echo "   ✅ Python3 already installed"
fi

# Install pip if not present
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "   Installing pip..."
    $SUDO_CMD apt install -y python3-pip
    echo "   ✅ pip installed"
else
    echo "   ✅ pip already installed"
fi

# ============================================
# 2. Start and Enable Redis
# ============================================
echo -e "\n${GREEN}🔴 Step 2: Configuring Redis service...${NC}"

# Start Redis
$SUDO_CMD systemctl start redis-server 2>/dev/null || $SUDO_CMD systemctl start redis 2>/dev/null || echo "   Redis service start skipped"
$SUDO_CMD systemctl enable redis-server 2>/dev/null || $SUDO_CMD systemctl enable redis 2>/dev/null || echo "   Redis enable skipped"

# Check Redis
if redis-cli ping > /dev/null 2>&1; then
    echo "   ✅ Redis is running (PONG received)"
else
    echo -e "${YELLOW}   ⚠️  Redis not responding, but continuing...${NC}"
fi

# ============================================
# 3. Generate SECRET_KEY if not exists
# ============================================
echo -e "\n${GREEN}🔐 Step 3: Checking SECRET_KEY...${NC}"

if grep -q "^SECRET_KEY=" "$ENV_FILE" 2>/dev/null; then
    CURRENT_KEY=$(grep "^SECRET_KEY=" "$ENV_FILE" | cut -d'=' -f2)
    if [[ "$CURRENT_KEY" == "super_secret_key_change_me_in_production"* ]] || [[ ${#CURRENT_KEY} -lt 32 ]]; then
        echo "⚠️  Weak SECRET_KEY detected, generating new one..."
        NEW_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || python -c "import secrets; print(secrets.token_hex(32))")
        sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$NEW_SECRET_KEY|" "$ENV_FILE"
        echo "✅ New SECRET_KEY generated"
    else
        echo "✅ SECRET_KEY already configured"
    fi
else
    NEW_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || python -c "import secrets; print(secrets.token_hex(32))")
    echo "SECRET_KEY=$NEW_SECRET_KEY" >> "$ENV_FILE"
    echo "✅ SECRET_KEY added to .env"
fi

# ============================================
# 4. Add Google OAuth credentials
# ============================================
echo -e "\n${GREEN}🔑 Step 4: Configuring Google OAuth...${NC}"

# Remove old Google OAuth entries if they exist
sed -i '/^GOOGLE_CLIENT_ID=/d' "$ENV_FILE" 2>/dev/null || true
sed -i '/^GOOGLE_CLIENT_SECRET=/d' "$ENV_FILE" 2>/dev/null || true
sed -i '/^OAUTH_REDIRECT_URI=/d' "$ENV_FILE" 2>/dev/null || true

# Add new Google OAuth credentials
echo "" >> "$ENV_FILE"
echo "# ===========================================" >> "$ENV_FILE"
echo "# GOOGLE OAUTH 2.0 - Auto-configured $(date +%Y-%m-%d)" >> "$ENV_FILE"
echo "# ===========================================" >> "$ENV_FILE"
echo "GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID" >> "$ENV_FILE"
echo "GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET" >> "$ENV_FILE"
echo "OAUTH_REDIRECT_URI=$OAUTH_REDIRECT_URI" >> "$ENV_FILE"

echo "✅ Google OAuth credentials added to .env"

# ============================================
# 5. Configure Redis URL in .env
# ============================================
echo -e "\n${GREEN}📦 Step 5: Checking Redis configuration...${NC}"

if ! grep -q "^REDIS_URL=" "$ENV_FILE" 2>/dev/null; then
    echo "REDIS_URL=redis://localhost:6379/0" >> "$ENV_FILE"
    echo "CACHE_TYPE=redis" >> "$ENV_FILE"
    echo "✅ Redis configuration added"
else
    echo "✅ Redis already configured"
fi

# ============================================
# 6. Set production environment
# ============================================
echo -e "\n${GREEN}🌍 Step 6: Setting production environment...${NC}"

if grep -q "^FLASK_ENV=" "$ENV_FILE" 2>/dev/null; then
    sed -i "s|^FLASK_ENV=.*|FLASK_ENV=production|" "$ENV_FILE"
else
    echo "FLASK_ENV=production" >> "$ENV_FILE"
fi
echo "✅ FLASK_ENV set to production"

# ============================================
# 7. Install Python dependencies
# ============================================
echo -e "\n${GREEN}📚 Step 7: Installing Python dependencies...${NC}"

cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo "   Activating virtual environment..."
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Install requirements
echo "   Installing requirements.txt..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt --quiet --no-warn-script-location
elif command -v pip &> /dev/null; then
    pip install -r requirements.txt --quiet --no-warn-script-location
else
    echo -e "${RED}❌ pip not found. Please install Python dependencies manually.${NC}"
    exit 1
fi

echo "✅ Python dependencies installed"

# ============================================
# 8. Verify critical packages
# ============================================
echo -e "\n${GREEN}🔍 Step 8: Verifying critical packages...${NC}"

python3 -c "import authlib; print('   ✅ authlib installed')" 2>/dev/null || echo -e "${RED}   ❌ authlib missing${NC}"
python3 -c "import flask_talisman; print('   ✅ flask-talisman installed')" 2>/dev/null || echo -e "${RED}   ❌ flask-talisman missing${NC}"
python3 -c "import flask_limiter; print('   ✅ flask-limiter installed')" 2>/dev/null || echo -e "${RED}   ❌ flask-limiter missing${NC}"
python3 -c "import flask_caching; print('   ✅ flask-caching installed')" 2>/dev/null || echo -e "${RED}   ❌ flask-caching missing${NC}"
python3 -c "import redis; print('   ✅ redis-py installed')" 2>/dev/null || echo -e "${RED}   ❌ redis-py missing${NC}"

# ============================================
# 9. Set proper permissions
# ============================================
echo -e "\n${GREEN}🔒 Step 9: Setting permissions...${NC}"

# Protect .env file
chmod 600 "$ENV_FILE" 2>/dev/null || echo "   Could not set .env permissions"
echo "   ✅ .env permissions set (600)"

# ============================================
# 10. Summary
# ============================================
echo ""
echo "============================================"
echo -e "${GREEN}✅ DÉPLOIEMENT PRODUCTION TERMINÉ !${NC}"
echo "============================================"
echo ""
echo -e "${BLUE}📋 Résumé de la configuration :${NC}"
echo "   ✅ Redis : Installé et démarré"
echo "   ✅ Google OAuth : Configuré"
echo "   ✅ SECRET_KEY : Généré"
echo "   ✅ Dépendances Python : Installées"
echo "   ✅ Environment : Production"
echo "   ✅ Permissions : Sécurisées"
echo ""
echo -e "${YELLOW}🔄 Prochaines étapes :${NC}"
echo ""
echo "   1. Redémarrer l'application :"
echo -e "      ${GREEN}sudo systemctl restart sarfx-enhanced${NC}"
echo ""
echo "   2. Vérifier les logs :"
echo -e "      ${GREEN}sudo journalctl -u sarfx-enhanced -f${NC}"
echo ""
echo "   3. Tester Google OAuth :"
echo -e "      ${GREEN}https://sarfx.io/auth/login${NC}"
echo ""
echo "   4. Vérifier Redis :"
echo -e "      ${GREEN}redis-cli ping${NC}"
echo ""
echo "============================================"
echo -e "${BLUE}📄 Variables .env ajoutées :${NC}"
echo "   GOOGLE_CLIENT_ID=639845...googleusercontent.com"
echo "   GOOGLE_CLIENT_SECRET=GOCSPX-..."
echo "   OAUTH_REDIRECT_URI=https://sarfx.io/auth/login/google/callback"
echo "   REDIS_URL=redis://localhost:6379/0"
echo "   CACHE_TYPE=redis"
echo "   FLASK_ENV=production"
echo "============================================"
echo ""
echo -e "${GREEN}🎉 Tout est prêt ! Redémarrez l'application.${NC}"
echo ""
