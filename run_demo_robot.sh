#!/bin/bash
# ============================================
# SarfX Robot Framework Demo Runner
# Avec enregistrement vidéo et screenshots
# ============================================

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Répertoires
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv-robot"
RESULTS_DIR="${SCRIPT_DIR}/robot_results"
DEMO_DIR="${RESULTS_DIR}/demo"
VIDEO_DIR="${RESULTS_DIR}/videos"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Configuration
RECORD_VIDEO=${RECORD_VIDEO:-true}
HEADLESS=${HEADLESS:-false}
DISPLAY_NUM=${DISPLAY_NUM:-99}

echo -e "${MAGENTA}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║      🎬 SarfX Robot Framework Demo                           ║"
echo "║      Avec Vidéo + Screenshots                                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================
# Fonctions utilitaires
# ============================================

check_dependencies() {
    echo -e "${CYAN}➤ Vérification des dépendances...${NC}"
    
    # Python
    if command -v python3 &> /dev/null; then
        echo -e "${GREEN}✓ Python3 OK${NC}"
    else
        echo -e "${RED}✗ Python3 non trouvé${NC}"
        exit 1
    fi
    
    # Chrome/Chromium
    if command -v google-chrome &> /dev/null || command -v chromium-browser &> /dev/null || command -v chromium &> /dev/null; then
        echo -e "${GREEN}✓ Chrome/Chromium OK${NC}"
    else
        echo -e "${YELLOW}⚠ Chrome non trouvé - installation...${NC}"
        apt-get update && apt-get install -y chromium-browser || true
    fi
    
    # Xvfb pour virtual display
    if command -v Xvfb &> /dev/null; then
        echo -e "${GREEN}✓ Xvfb OK${NC}"
    else
        echo -e "${YELLOW}⚠ Xvfb non trouvé - installation...${NC}"
        apt-get update && apt-get install -y xvfb || true
    fi
    
    # FFmpeg pour l'enregistrement vidéo
    if command -v ffmpeg &> /dev/null; then
        echo -e "${GREEN}✓ FFmpeg OK${NC}"
        FFMPEG_AVAILABLE=true
    else
        echo -e "${YELLOW}⚠ FFmpeg non trouvé - installation...${NC}"
        apt-get update && apt-get install -y ffmpeg || FFMPEG_AVAILABLE=false
    fi
}

setup_virtual_display() {
    if [ "$HEADLESS" = "true" ] || [ -z "$DISPLAY" ]; then
        echo -e "${CYAN}➤ Configuration du display virtuel...${NC}"
        
        # Arrêter tout Xvfb existant
        pkill -9 Xvfb 2>/dev/null || true
        sleep 1
        
        # Démarrer Xvfb
        Xvfb :${DISPLAY_NUM} -screen 0 1920x1080x24 &
        export DISPLAY=:${DISPLAY_NUM}
        sleep 2
        
        echo -e "${GREEN}✓ Display virtuel :${DISPLAY_NUM} démarré${NC}"
    fi
}

setup_venv() {
    echo -e "${CYAN}➤ Configuration de l'environnement virtuel...${NC}"
    
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
    fi
    
    source "${VENV_DIR}/bin/activate"
    echo -e "${GREEN}✓ Environnement activé: ${VENV_DIR}${NC}"
    
    echo -e "${CYAN}➤ Installation des dépendances...${NC}"
    pip install --quiet --upgrade pip
    pip install --quiet robotframework robotframework-seleniumlibrary robotframework-requests selenium webdriver-manager
    echo -e "${GREEN}✓ Dépendances installées${NC}"
}

setup_chromedriver() {
    echo -e "${CYAN}➤ Configuration de ChromeDriver...${NC}"
    
    # Utiliser webdriver-manager pour obtenir le bon chromedriver
    python3 -c "
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import os

try:
    driver_path = ChromeDriverManager().install()
    print(f'ChromeDriver: {driver_path}')
except Exception as e:
    # Fallback pour chromium
    try:
        driver_path = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
        print(f'ChromeDriver (Chromium): {driver_path}')
    except:
        print('Warning: Could not auto-install chromedriver')
"
    echo -e "${GREEN}✓ ChromeDriver configuré${NC}"
}

create_directories() {
    echo -e "${CYAN}➤ Création des répertoires...${NC}"
    mkdir -p "${RESULTS_DIR}"
    mkdir -p "${DEMO_DIR}"
    mkdir -p "${VIDEO_DIR}"
    echo -e "${GREEN}✓ Répertoires créés${NC}"
}

start_video_recording() {
    if [ "$RECORD_VIDEO" = "true" ] && [ "$FFMPEG_AVAILABLE" = "true" ]; then
        echo -e "${CYAN}➤ Démarrage de l'enregistrement vidéo...${NC}"
        
        VIDEO_FILE="${VIDEO_DIR}/demo_${TIMESTAMP}.mp4"
        
        # Enregistrement avec ffmpeg
        ffmpeg -y -f x11grab -video_size 1920x1080 -framerate 15 \
               -i :${DISPLAY_NUM} -c:v libx264 -preset ultrafast \
               -pix_fmt yuv420p "${VIDEO_FILE}" &
        FFMPEG_PID=$!
        
        echo -e "${GREEN}✓ Enregistrement démarré: ${VIDEO_FILE}${NC}"
        echo -e "${GREEN}  PID: ${FFMPEG_PID}${NC}"
    fi
}

stop_video_recording() {
    if [ -n "$FFMPEG_PID" ]; then
        echo -e "${CYAN}➤ Arrêt de l'enregistrement vidéo...${NC}"
        kill -INT $FFMPEG_PID 2>/dev/null || true
        sleep 2
        kill -9 $FFMPEG_PID 2>/dev/null || true
        echo -e "${GREEN}✓ Vidéo sauvegardée: ${VIDEO_FILE}${NC}"
    fi
}

check_app() {
    echo -e "${CYAN}➤ Vérification de l'application...${NC}"
    
    APP_URL=${APP_URL:-"https://sarfx.io"}
    
    if curl -s -o /dev/null -w "%{http_code}" "$APP_URL" | grep -q "200\|301\|302"; then
        echo -e "${GREEN}✓ Application accessible sur ${APP_URL}${NC}"
    else
        echo -e "${YELLOW}⚠ Application non accessible sur ${APP_URL}${NC}"
        echo -e "${YELLOW}  Les tests vont quand même s'exécuter${NC}"
    fi
}

run_demo_tests() {
    echo ""
    echo -e "${MAGENTA}➤ Exécution de la démonstration Robot Framework...${NC}"
    echo ""
    
    # Variables pour Robot
    ROBOT_VARS=""
    if [ "$HEADLESS" = "false" ]; then
        ROBOT_VARS="--variable HEADLESS:False"
    fi
    
    # Commande Robot
    ROBOT_CMD="robot \
        --outputdir ${DEMO_DIR} \
        --output output-${TIMESTAMP}.xml \
        --log log-${TIMESTAMP}.html \
        --report report-${TIMESTAMP}.html \
        --loglevel DEBUG \
        --timestampoutputs \
        ${ROBOT_VARS} \
        ${SCRIPT_DIR}/robot_tests/tests/test_full_demo.robot"
    
    echo -e "${BLUE}Commande:${NC}"
    echo "$ROBOT_CMD"
    echo ""
    
    # Exécuter Robot
    set +e
    $ROBOT_CMD
    ROBOT_EXIT_CODE=$?
    set -e
    
    return $ROBOT_EXIT_CODE
}

generate_html_report() {
    echo -e "${CYAN}➤ Génération du rapport HTML enrichi...${NC}"
    
    # Créer un index HTML avec toutes les captures et la vidéo
    cat > "${DEMO_DIR}/index.html" << 'HTMLEOF'
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SarfX Demo Report</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        header { 
            text-align: center; 
            padding: 40px 0; 
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            margin-bottom: 30px;
        }
        h1 { 
            font-size: 2.5rem; 
            background: linear-gradient(90deg, #00d4ff, #0099ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .subtitle { color: #888; font-size: 1.1rem; }
        .stats { 
            display: flex; 
            justify-content: center; 
            gap: 30px; 
            margin-top: 20px; 
        }
        .stat { 
            background: rgba(255,255,255,0.1); 
            padding: 15px 30px; 
            border-radius: 10px;
            text-align: center;
        }
        .stat-value { font-size: 2rem; font-weight: bold; color: #00d4ff; }
        .stat-label { font-size: 0.9rem; color: #888; }
        
        .section { 
            background: rgba(255,255,255,0.05); 
            border-radius: 15px; 
            padding: 30px; 
            margin-bottom: 30px;
        }
        .section h2 { 
            font-size: 1.5rem; 
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(255,255,255,0.1);
        }
        
        .video-container { 
            text-align: center; 
            margin: 20px 0;
        }
        video { 
            max-width: 100%; 
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }
        
        .screenshots { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); 
            gap: 20px;
        }
        .screenshot { 
            background: rgba(255,255,255,0.05); 
            border-radius: 10px; 
            overflow: hidden;
            transition: transform 0.3s;
        }
        .screenshot:hover { transform: scale(1.02); }
        .screenshot img { 
            width: 100%; 
            height: 200px; 
            object-fit: cover;
            cursor: pointer;
        }
        .screenshot-info { padding: 15px; }
        .screenshot-name { font-weight: 600; margin-bottom: 5px; }
        .screenshot-time { font-size: 0.85rem; color: #888; }
        
        .links { 
            display: flex; 
            gap: 15px; 
            justify-content: center;
            flex-wrap: wrap;
        }
        .link-btn { 
            display: inline-block;
            padding: 12px 30px;
            background: linear-gradient(90deg, #00d4ff, #0099ff);
            color: #fff;
            text-decoration: none;
            border-radius: 25px;
            font-weight: 600;
            transition: all 0.3s;
        }
        .link-btn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0,212,255,0.4);
        }
        
        /* Modal for full-size images */
        .modal { 
            display: none; 
            position: fixed; 
            top: 0; left: 0; 
            width: 100%; height: 100%; 
            background: rgba(0,0,0,0.9); 
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .modal.active { display: flex; }
        .modal img { max-width: 95%; max-height: 95%; border-radius: 10px; }
        .modal-close { 
            position: absolute; 
            top: 20px; right: 30px; 
            font-size: 40px; 
            color: #fff; 
            cursor: pointer;
        }
        
        footer { 
            text-align: center; 
            padding: 30px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎬 SarfX Demo Report</h1>
            <p class="subtitle">Robot Framework Automated Demo</p>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value" id="screenshot-count">-</div>
                    <div class="stat-label">Screenshots</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="test-count">-</div>
                    <div class="stat-label">Tests Exécutés</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="duration">-</div>
                    <div class="stat-label">Durée</div>
                </div>
            </div>
        </header>
        
        <section class="section">
            <h2>📹 Vidéo de la Démonstration</h2>
            <div class="video-container">
                <video id="demo-video" controls>
                    <source src="../videos/demo_latest.mp4" type="video/mp4">
                    Vidéo non disponible
                </video>
            </div>
        </section>
        
        <section class="section">
            <h2>📸 Captures d'Écran</h2>
            <div class="screenshots" id="screenshots-grid">
                <!-- Screenshots will be loaded dynamically -->
                <p>Chargement des captures...</p>
            </div>
        </section>
        
        <section class="section">
            <h2>📊 Rapports Détaillés</h2>
            <div class="links">
                <a href="report.html" class="link-btn">📋 Rapport Robot</a>
                <a href="log.html" class="link-btn">📜 Log Détaillé</a>
                <a href="output.xml" class="link-btn">📄 Output XML</a>
            </div>
        </section>
        
        <footer>
            <p>Généré par SarfX Robot Framework Demo Runner</p>
            <p id="generation-date"></p>
        </footer>
    </div>
    
    <div class="modal" id="image-modal">
        <span class="modal-close">&times;</span>
        <img src="" alt="Full size">
    </div>
    
    <script>
        // Date de génération
        document.getElementById('generation-date').textContent = new Date().toLocaleString('fr-FR');
        
        // Charger les screenshots
        const screenshotsGrid = document.getElementById('screenshots-grid');
        
        // Liste des screenshots (à générer dynamiquement)
        const screenshots = [];
        
        // Chercher les fichiers PNG dans le dossier
        fetch('.')
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const links = doc.querySelectorAll('a');
                const pngFiles = [];
                
                links.forEach(link => {
                    const href = link.getAttribute('href');
                    if (href && href.endsWith('.png')) {
                        pngFiles.push(href);
                    }
                });
                
                document.getElementById('screenshot-count').textContent = pngFiles.length;
                
                if (pngFiles.length === 0) {
                    screenshotsGrid.innerHTML = '<p>Aucune capture disponible</p>';
                    return;
                }
                
                screenshotsGrid.innerHTML = '';
                pngFiles.sort().forEach(file => {
                    const div = document.createElement('div');
                    div.className = 'screenshot';
                    div.innerHTML = `
                        <img src="${file}" alt="${file}" onclick="openModal('${file}')">
                        <div class="screenshot-info">
                            <div class="screenshot-name">${file.replace('.png', '').replace(/_/g, ' ')}</div>
                        </div>
                    `;
                    screenshotsGrid.appendChild(div);
                });
            })
            .catch(() => {
                screenshotsGrid.innerHTML = '<p>Erreur de chargement</p>';
            });
        
        // Modal
        function openModal(src) {
            const modal = document.getElementById('image-modal');
            modal.querySelector('img').src = src;
            modal.classList.add('active');
        }
        
        document.querySelector('.modal-close').onclick = function() {
            document.getElementById('image-modal').classList.remove('active');
        };
        
        document.getElementById('image-modal').onclick = function(e) {
            if (e.target === this) this.classList.remove('active');
        };
    </script>
</body>
</html>
HTMLEOF

    echo -e "${GREEN}✓ Rapport HTML créé: ${DEMO_DIR}/index.html${NC}"
}

show_results() {
    echo ""
    echo -e "${MAGENTA}══════════════════════════════════════════════════════════════${NC}"
    
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ Démonstration terminée avec succès!${NC}"
    else
        echo -e "${YELLOW}⚠ Démonstration terminée avec des erreurs (code: $1)${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}📁 Résultats:${NC}"
    echo -e "   📄 Index:      ${DEMO_DIR}/index.html"
    echo -e "   📋 Rapport:    ${DEMO_DIR}/report.html"
    echo -e "   📜 Log:        ${DEMO_DIR}/log.html"
    echo -e "   📊 Output:     ${DEMO_DIR}/output.xml"
    
    # Compter les screenshots
    SCREENSHOT_COUNT=$(ls -1 ${DEMO_DIR}/*.png 2>/dev/null | wc -l)
    echo -e "   📸 Screenshots: ${SCREENSHOT_COUNT}"
    
    if [ -f "$VIDEO_FILE" ]; then
        echo -e "   📹 Vidéo:      ${VIDEO_FILE}"
        # Créer un lien symbolique pour la dernière vidéo
        ln -sf "${VIDEO_FILE}" "${VIDEO_DIR}/demo_latest.mp4"
    fi
    
    echo ""
    echo -e "${CYAN}💡 Pour voir les résultats:${NC}"
    echo -e "   python3 -m http.server 8888 --directory ${DEMO_DIR}"
    echo -e "   # Puis ouvrir: http://localhost:8888/index.html"
    echo ""
}

cleanup() {
    echo -e "${CYAN}➤ Nettoyage...${NC}"
    stop_video_recording
    pkill -9 Xvfb 2>/dev/null || true
}

# ============================================
# MAIN
# ============================================

main() {
    trap cleanup EXIT
    
    check_dependencies
    setup_venv
    setup_chromedriver
    create_directories
    
    if [ "$RECORD_VIDEO" = "true" ]; then
        setup_virtual_display
        start_video_recording
    fi
    
    check_app
    
    run_demo_tests
    RESULT=$?
    
    stop_video_recording
    generate_html_report
    show_results $RESULT
    
    exit $RESULT
}

# Gestion des options
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-video)
            RECORD_VIDEO=false
            shift
            ;;
        --headless)
            HEADLESS=true
            shift
            ;;
        --display)
            DISPLAY_NUM="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --no-video    Désactiver l'enregistrement vidéo"
            echo "  --headless    Exécuter en mode headless"
            echo "  --display N   Utiliser le display :N (défaut: 99)"
            echo "  --help        Afficher cette aide"
            exit 0
            ;;
        *)
            echo "Option inconnue: $1"
            exit 1
            ;;
    esac
done

main
