"""
Service de gestion des démos Playwright
Gère l'exécution asynchrone, le stockage des vidéos et les logs
"""
import os
import threading
import json
from datetime import datetime
from typing import Optional, Dict, List

# État global des démos en cours
_demo_status: Dict[str, Dict] = {}
_demo_lock = threading.Lock()


def get_demo_dirs():
    """Retourne les chemins des dossiers de démo"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, 'robot_results', 'playwright')
    return {
        'base': base_dir,
        'output': output_dir,
        'videos': os.path.join(output_dir, 'videos'),
        'screenshots': os.path.join(output_dir, 'screenshots'),
        'logs': os.path.join(output_dir, 'logs')
    }


def init_demo_dirs():
    """Crée les dossiers nécessaires"""
    dirs = get_demo_dirs()
    for path in dirs.values():
        os.makedirs(path, exist_ok=True)


def get_demo_status(role: str) -> Dict:
    """Récupère le statut d'une démo"""
    with _demo_lock:
        return _demo_status.get(role, {
            'running': False,
            'success': None,
            'error': None,
            'video_path': None,
            'started_at': None,
            'completed_at': None
        })


def set_demo_status(role: str, status: Dict):
    """Met à jour le statut d'une démo"""
    with _demo_lock:
        _demo_status[role] = status


def run_demo_async(role: str, headless: bool = True) -> bool:
    """Lance une démo en arrière-plan"""
    # Vérifier si une démo est déjà en cours pour ce rôle
    current_status = get_demo_status(role)
    if current_status.get('running'):
        return False
    
    # Marquer comme en cours
    set_demo_status(role, {
        'running': True,
        'success': None,
        'error': None,
        'video_path': None,
        'started_at': datetime.now().isoformat(),
        'completed_at': None
    })
    
    def run_thread():
        try:
            # Importer le module approprié
            if role == 'admin':
                from playwright_demos.demo_admin import run_admin_demo
                result = run_admin_demo(headless=headless)
            elif role == 'bank':
                from playwright_demos.demo_bank import run_bank_demo
                result = run_bank_demo(headless=headless)
            elif role == 'user':
                from playwright_demos.demo_user import run_user_demo
                result = run_user_demo(headless=headless)
            else:
                raise ValueError(f"Rôle inconnu: {role}")
            
            # Mettre à jour le statut
            set_demo_status(role, {
                'running': False,
                'success': result.get('success', False),
                'error': result.get('error'),
                'video_path': result.get('video_path') or result.get('mp4_path'),
                'srt_path': result.get('srt_path'),
                'screenshots': result.get('screenshots', []),
                'duration': result.get('duration', 0),
                'started_at': get_demo_status(role).get('started_at'),
                'completed_at': datetime.now().isoformat()
            })
            
            # Sauvegarder le log
            save_demo_log(role, result)
            
        except Exception as e:
            set_demo_status(role, {
                'running': False,
                'success': False,
                'error': str(e),
                'video_path': None,
                'started_at': get_demo_status(role).get('started_at'),
                'completed_at': datetime.now().isoformat()
            })
    
    # Lancer dans un thread
    thread = threading.Thread(target=run_thread, daemon=True)
    thread.start()
    
    return True


def save_demo_log(role: str, result: Dict):
    """Sauvegarde le log de la démo"""
    dirs = get_demo_dirs()
    log_file = os.path.join(
        dirs['logs'], 
        f"demo_{role}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str)


def get_all_demo_statuses() -> Dict[str, Dict]:
    """Récupère le statut de toutes les démos"""
    return {
        'admin': get_demo_status('admin'),
        'bank': get_demo_status('bank'),
        'user': get_demo_status('user')
    }


def get_demo_videos() -> List[Dict]:
    """Liste toutes les vidéos de démo disponibles"""
    dirs = get_demo_dirs()
    videos = []
    
    if os.path.exists(dirs['videos']):
        for f in sorted(os.listdir(dirs['videos']), reverse=True):
            if f.endswith('.mp4'):
                filepath = os.path.join(dirs['videos'], f)
                # Extraire le rôle du nom de fichier (demo_admin_xxx.mp4)
                parts = f.replace('.mp4', '').split('_')
                role = parts[1] if len(parts) > 1 else 'unknown'
                
                videos.append({
                    'filename': f,
                    'role': role,
                    'size': os.path.getsize(filepath),
                    'created': datetime.fromtimestamp(os.path.getctime(filepath)).isoformat(),
                    'path': f'/admin/demo/video/{f}'
                })
    
    return videos


def get_demo_screenshots(role: Optional[str] = None) -> List[Dict]:
    """Liste les screenshots de démo"""
    dirs = get_demo_dirs()
    screenshots = []
    
    if os.path.exists(dirs['screenshots']):
        for f in sorted(os.listdir(dirs['screenshots']), reverse=True):
            if f.endswith('.png'):
                # Filtrer par rôle si spécifié
                if role and not f.startswith(role):
                    continue
                
                filepath = os.path.join(dirs['screenshots'], f)
                screenshots.append({
                    'filename': f,
                    'size': os.path.getsize(filepath),
                    'created': datetime.fromtimestamp(os.path.getctime(filepath)).isoformat(),
                    'path': f'/admin/demo/screenshot/{f}'
                })
    
    return screenshots[:50]  # Limiter à 50


def cleanup_old_demos(keep_count: int = 5):
    """Nettoie les anciennes démos en gardant les N plus récentes par rôle"""
    dirs = get_demo_dirs()
    
    for role in ['admin', 'bank', 'user']:
        # Nettoyer les vidéos
        if os.path.exists(dirs['videos']):
            videos = sorted(
                [f for f in os.listdir(dirs['videos']) if f.startswith(f'demo_{role}') and f.endswith('.mp4')],
                reverse=True
            )
            for old_video in videos[keep_count:]:
                os.remove(os.path.join(dirs['videos'], old_video))
                # Supprimer aussi le SRT associé
                srt_file = old_video.replace('.mp4', '.srt')
                srt_path = os.path.join(dirs['videos'], srt_file)
                if os.path.exists(srt_path):
                    os.remove(srt_path)


def check_playwright_installed() -> Dict:
    """Vérifie si Playwright est installé"""
    result = {
        'installed': False,
        'browsers_installed': False,
        'error': None
    }
    
    try:
        import playwright
        result['installed'] = True
        
        # Vérifier si les navigateurs sont installés
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
            result['browsers_installed'] = True
    except Exception as e:
        result['error'] = str(e)
    
    return result
