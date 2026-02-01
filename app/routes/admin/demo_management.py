from flask import render_template, session, request, jsonify, Response
from app.routes.admin import admin_bp
from app.decorators import admin_required
from app.services.db_service import get_db, log_history
from datetime import datetime
import os


@admin_bp.route('/demo')
@admin_required
def demo_page():
    """Page de demonstration automatisee avec Robot Framework"""
    db = get_db()

    demo_results = []
    demo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'robot_results', 'demo')
    video_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'robot_results', 'videos')

    if os.path.exists(demo_dir):
        for f in sorted(os.listdir(demo_dir), reverse=True):
            if f.startswith('report-') and f.endswith('.html'):
                timestamp = f.replace('report-', '').replace('.html', '')
                demo_results.append({
                    'timestamp': timestamp,
                    'report_file': f,
                    'log_file': f.replace('report-', 'log-'),
                })

    latest_video = None
    if os.path.exists(video_dir):
        videos = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]
        if videos:
            latest_video = sorted(videos, reverse=True)[0]

    screenshot_count = 0
    if os.path.exists(demo_dir):
        screenshot_count = len([f for f in os.listdir(demo_dir) if f.endswith('.png')])

    return render_template('admin/demo.html',
                         demo_results=demo_results[:10],
                         latest_video=latest_video,
                         screenshot_count=screenshot_count)


@admin_bp.route('/demo/run', methods=['POST'])
@admin_required
def run_demo():
    """Lance la demonstration Robot Framework en arriere-plan"""
    import subprocess
    import threading
    import shutil

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    script_path = os.path.join(base_dir, 'run_demo_robot.sh')

    if not os.path.exists(script_path):
        return jsonify({
            'success': False,
            'message': 'Script run_demo_robot.sh non trouve. La demo doit etre executee localement.'
        }), 400

    robot_installed = shutil.which('robot') is not None
    if not robot_installed:
        try:
            result = subprocess.run(['python', '-c', 'import robot'], capture_output=True)
            robot_installed = result.returncode == 0
        except:
            pass

    if not robot_installed:
        return jsonify({
            'success': False,
            'message': 'Robot Framework non installe. Installez avec: pip install robotframework robotframework-seleniumlibrary'
        }), 400

    chrome_path = shutil.which('google-chrome') or shutil.which('chromium') or shutil.which('chromium-browser')
    if not chrome_path:
        return jsonify({
            'success': False,
            'message': 'Chrome/Chromium non trouve. La demo necessite un navigateur Chrome.'
        }), 400

    demo_dir = os.path.join(base_dir, 'robot_results', 'demo')
    os.makedirs(demo_dir, exist_ok=True)

    def run_demo_thread():
        try:
            subprocess.run(
                ['bash', script_path, '--headless'],
                cwd=base_dir,
                timeout=600,
                capture_output=True
            )
        except subprocess.TimeoutExpired:
            print("Demo timeout after 10 minutes")
        except Exception as e:
            print(f"Demo error: {e}")

    thread = threading.Thread(target=run_demo_thread, daemon=True)
    thread.start()

    log_history("DEMO_STARTED", "Demonstration Robot Framework lancee", user=session.get('email'))

    return jsonify({
        'success': True,
        'message': 'Demonstration lancee en arriere-plan'
    })


@admin_bp.route('/demo/status')
@admin_required
def demo_status():
    """Verifie le statut de la derniere demo"""
    import subprocess

    try:
        result = subprocess.run(['pgrep', '-f', 'robot'], capture_output=True, text=True)
        is_running = result.returncode == 0
    except:
        is_running = False

    demo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'robot_results', 'demo')

    latest_report = None
    screenshot_count = 0

    if os.path.exists(demo_dir):
        reports = [f for f in os.listdir(demo_dir) if f.startswith('report-') and f.endswith('.html')]
        if reports:
            latest_report = sorted(reports, reverse=True)[0]
        screenshot_count = len([f for f in os.listdir(demo_dir) if f.endswith('.png')])

    return jsonify({
        'running': is_running,
        'latest_report': latest_report,
        'screenshot_count': screenshot_count
    })


@admin_bp.route('/demo/screenshots')
@admin_required
def demo_screenshots():
    """Liste les screenshots de la demo"""
    demo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'robot_results', 'demo')

    screenshots = []
    if os.path.exists(demo_dir):
        for f in sorted(os.listdir(demo_dir)):
            if f.endswith('.png'):
                screenshots.append({
                    'name': f,
                    'path': f'/admin/demo/screenshot/{f}'
                })

    return jsonify(screenshots)


@admin_bp.route('/demo/screenshot/<filename>')
@admin_required
def get_demo_screenshot(filename):
    """Retourne un screenshot de la demo"""
    from flask import send_from_directory

    demo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'robot_results', 'demo')

    if not filename.endswith('.png') or '..' in filename:
        return "Invalid file", 400

    return send_from_directory(demo_dir, filename)


@admin_bp.route('/demo/video')
@admin_required
def get_demo_video():
    """Retourne la derniere video de demo"""
    from flask import send_from_directory

    video_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'robot_results', 'videos')

    if os.path.exists(os.path.join(video_dir, 'demo_latest.mp4')):
        return send_from_directory(video_dir, 'demo_latest.mp4')

    return "No video available", 404


@admin_bp.route('/demo/report')
@admin_required
def get_demo_report():
    """Retourne le dernier rapport HTML"""
    from flask import send_from_directory

    demo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'robot_results', 'demo')

    if os.path.exists(demo_dir):
        reports = [f for f in os.listdir(demo_dir) if f.startswith('report') and f.endswith('.html')]
        if reports:
            latest = sorted(reports, reverse=True)[0]
            return send_from_directory(demo_dir, latest)

    return "No report available", 404


# ==================== PLAYWRIGHT DEMO ROUTES ====================

@admin_bp.route('/demo/playwright/run/<role>', methods=['POST'])
@admin_required
def run_playwright_demo(role):
    """Lance une demo Playwright pour un role specifique"""
    from app.services.demo_service import run_demo_async, check_playwright_installed, init_demo_dirs

    if role not in ['admin', 'bank', 'user']:
        return jsonify({'success': False, 'message': 'Role invalide'}), 400

    pw_check = check_playwright_installed()
    if not pw_check['installed']:
        return jsonify({
            'success': False,
            'message': 'Playwright non installe. Executez: pip install playwright && playwright install chromium'
        }), 400

    if not pw_check['browsers_installed']:
        return jsonify({
            'success': False,
            'message': 'Navigateurs Playwright non installes. Executez: playwright install chromium'
        }), 400

    init_demo_dirs()

    headless = request.json.get('headless', True) if request.is_json else True
    started = run_demo_async(role, headless=headless)

    if not started:
        return jsonify({
            'success': False,
            'message': f'Une demo {role} est deja en cours'
        }), 409

    log_history("PLAYWRIGHT_DEMO_STARTED", f"Demo Playwright {role} lancee", user=session.get('email'))

    return jsonify({
        'success': True,
        'message': f'Demo {role} lancee en arriere-plan',
        'role': role
    })


@admin_bp.route('/demo/playwright/status')
@admin_required
def get_playwright_demo_status():
    """Recupere le statut de toutes les demos Playwright"""
    from app.services.demo_service import get_all_demo_statuses

    return jsonify(get_all_demo_statuses())


@admin_bp.route('/demo/playwright/status/<role>')
@admin_required
def get_playwright_demo_status_role(role):
    """Recupere le statut d'une demo specifique"""
    from app.services.demo_service import get_demo_status

    if role not in ['admin', 'bank', 'user']:
        return jsonify({'error': 'Role invalide'}), 400

    return jsonify(get_demo_status(role))


@admin_bp.route('/demo/playwright/videos')
@admin_required
def get_playwright_videos():
    """Liste toutes les videos de demo Playwright"""
    from app.services.demo_service import get_demo_videos

    return jsonify(get_demo_videos())


@admin_bp.route('/demo/video/<filename>')
@admin_required
def serve_demo_video(filename):
    """Sert une video de demo"""
    from flask import send_from_directory

    if '..' in filename or not (filename.endswith('.mp4') or filename.endswith('.webm')):
        return "Invalid file", 400

    video_dirs = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'robot_results', 'playwright', 'videos'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'robot_results', 'videos')
    ]

    for video_dir in video_dirs:
        filepath = os.path.join(video_dir, filename)
        if os.path.exists(filepath):
            return send_from_directory(video_dir, filename)

    return "Video not found", 404


@admin_bp.route('/demo/playwright/screenshots')
@admin_required
def get_playwright_screenshots():
    """Liste les screenshots des demos Playwright"""
    from app.services.demo_service import get_demo_screenshots

    role = request.args.get('role')
    return jsonify(get_demo_screenshots(role))


@admin_bp.route('/demo/playwright/screenshot/<filename>')
@admin_required
def serve_playwright_screenshot(filename):
    """Sert un screenshot de demo Playwright"""
    from flask import send_from_directory

    if '..' in filename or not filename.endswith('.png'):
        return "Invalid file", 400

    screenshot_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'robot_results', 'playwright', 'screenshots'
    )

    if os.path.exists(os.path.join(screenshot_dir, filename)):
        return send_from_directory(screenshot_dir, filename)

    return "Screenshot not found", 404


@admin_bp.route('/demo/playwright/check')
@admin_required
def check_playwright():
    """Verifie l'installation de Playwright"""
    from app.services.demo_service import check_playwright_installed

    return jsonify(check_playwright_installed())


@admin_bp.route('/demo/download-script')
@admin_required
def download_demo_script():
    """Telecharge le script de demo Playwright standalone pour execution locale"""

    base_url = request.host_url.rstrip('/')

    script_content = f'''#!/usr/bin/env python3
"""
SarfX Demo Robot - Script standalone pour execution locale
Genere depuis {base_url}

Usage:
    python sarfx_demo.py --role admin --visible
    python sarfx_demo.py --role bank --visible
    python sarfx_demo.py --role user --visible
    python sarfx_demo.py --role admin --headless

Prerequis:
    pip install playwright
    playwright install chromium
"""
import argparse
import time
import os
from datetime import datetime

# Configuration
BASE_URL = "{base_url}"
DEMO_ACCOUNTS = {{
    'admin': {{'email': 'admin@sarfx.io', 'password': 'Admin123!'}},
    'bank': {{'email': 'bank@sarfx.io', 'password': 'Bank123!'}},
    'user': {{'email': 'user@sarfx.io', 'password': 'User123!'}}
}}

SCENARIOS = {{
    'admin': [
        ('/', 'Accueil SarfX'),
        ('/login', 'Connexion'),
        ('/app', 'Dashboard App'),
        ('/admin', 'Dashboard Admin'),
        ('/admin/users', 'Gestion Utilisateurs'),
        ('/admin/banks', 'Gestion Banques'),
        ('/admin/atms', 'Gestion ATMs'),
        ('/app/transactions', 'Historique Transactions'),
    ],
    'bank': [
        ('/', 'Accueil SarfX'),
        ('/login', 'Connexion'),
        ('/app', 'Dashboard App'),
        ('/app/bank/settings', 'Configuration Banque'),
        ('/app/bank/atms', 'ATMs de la Banque'),
        ('/app/converter', 'Convertisseur'),
        ('/app/wallets', 'Wallets'),
    ],
    'user': [
        ('/', 'Accueil SarfX'),
        ('/login', 'Connexion'),
        ('/app', 'Dashboard App'),
        ('/app/wallets', 'Mes Wallets'),
        ('/app/converter', 'Convertisseur'),
        ('/app/atms', 'Trouver ATMs'),
        ('/app/beneficiaries', 'Beneficiaires'),
        ('/app/transactions', 'Historique'),
        ('/app/ai-forecast', 'IA Predictions'),
        ('/app/faq', 'FAQ'),
    ]
}}


def run_demo(role: str, headless: bool = False):
    """Execute la demo pour un role donne"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright non installe. Executez:")
        print("   pip install playwright")
        print("   playwright install chromium")
        return

    account = DEMO_ACCOUNTS.get(role)
    scenario = SCENARIOS.get(role)

    if not account or not scenario:
        print(f"Role invalide: {{role}}")
        return

    print(f"Demarrage de la demo {{role.upper()}}...")
    print(f"   Mode: {{'headless' if headless else 'visible'}}")
    print(f"   URL: {{BASE_URL}}")
    print()

    output_dir = os.path.join(os.getcwd(), 'sarfx_demo_output')
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    video_path = os.path.join(output_dir, f'demo_{{role}}_{{timestamp}}')

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=300
        )

        context = browser.new_context(
            viewport={{'width': 1920, 'height': 1080}},
            record_video_dir=video_path,
            record_video_size={{'width': 1920, 'height': 1080}}
        )

        page = context.new_page()

        try:
            print(f"Connexion en tant que {{account['email']}}...")
            page.goto(f"{{BASE_URL}}/login")
            time.sleep(1)

            page.fill('input[name="email"], input[type="email"]', account['email'])
            page.fill('input[name="password"], input[type="password"]', account['password'])
            page.click('button[type="submit"]')
            time.sleep(2)

            print("Connecte!")
            print()

            for path, description in scenario:
                if path == '/login':
                    continue

                print(f"{{description}}...")
                url = f"{{BASE_URL}}{{path}}"
                page.goto(url)
                time.sleep(2)

                screenshot_path = os.path.join(output_dir, f'{{role}}_{{path.replace("/", "_")}}.png')
                page.screenshot(path=screenshot_path)

                page.evaluate('window.scrollTo(0, document.body.scrollHeight / 2)')
                time.sleep(1)

            print()
            print("Demo terminee!")

        finally:
            context.close()
            browser.close()

    for f in os.listdir(video_path):
        if f.endswith('.webm'):
            final_video = os.path.join(output_dir, f'demo_{{role}}_{{timestamp}}.webm')
            os.rename(os.path.join(video_path, f), final_video)
            print(f"Video: {{final_video}}")
            break

    print(f"Screenshots: {{output_dir}}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SarfX Demo Robot')
    parser.add_argument('--role', choices=['admin', 'bank', 'user'], required=True,
                        help='Role a demontrer')
    parser.add_argument('--visible', action='store_true',
                        help='Mode visible (ouvre le navigateur)')
    parser.add_argument('--headless', action='store_true',
                        help='Mode headless (invisible)')

    args = parser.parse_args()

    headless = args.headless or not args.visible
    run_demo(args.role, headless=headless)
'''

    response = Response(
        script_content,
        mimetype='text/x-python',
        headers={'Content-Disposition': 'attachment;filename=sarfx_demo.py'}
    )
    return response
