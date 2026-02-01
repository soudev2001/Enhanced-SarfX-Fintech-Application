"""
Classe de base pour les démos Playwright avec sous-titres et enregistrement vidéo
"""
import os
import json
import subprocess
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, Browser
from .config import (
    BASE_URL, LOGIN_URL, DEMO_ACCOUNTS, 
    OUTPUT_DIR, VIDEOS_DIR, SCREENSHOTS_DIR,
    VIDEO_CONFIG, DELAYS, SUBTITLES
)


class SubtitleTracker:
    """Génère les sous-titres au format SRT"""
    
    def __init__(self):
        self.subtitles = []
        self.start_time = None
        self.index = 1
    
    def start(self):
        self.start_time = datetime.now()
    
    def add(self, text: str, duration_ms: int = 3000):
        if not self.start_time:
            self.start()
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        start_time = self._format_time(elapsed)
        end_time = self._format_time(elapsed + (duration_ms / 1000))
        
        self.subtitles.append({
            'index': self.index,
            'start': start_time,
            'end': end_time,
            'text': text
        })
        self.index += 1
    
    def _format_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def save(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            for sub in self.subtitles:
                f.write(f"{sub['index']}\n")
                f.write(f"{sub['start']} --> {sub['end']}\n")
                f.write(f"{sub['text']}\n\n")


class DemoBase:
    """Classe de base pour toutes les démos Playwright"""
    
    def __init__(self, role: str, headless: bool = False):
        self.role = role
        self.account = DEMO_ACCOUNTS[role]
        self.headless = headless
        self.subtitles = SubtitleTracker()
        self.lang = 'fr'
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Créer les dossiers
        os.makedirs(VIDEOS_DIR, exist_ok=True)
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    
    def get_subtitle(self, key: str) -> str:
        return SUBTITLES.get(self.lang, SUBTITLES['fr']).get(key, key)
    
    def log(self, message: str):
        print(f"[{self.role.upper()}] {message}")
    
    def run(self) -> dict:
        """Exécute la démo et retourne les résultats"""
        result = {
            'role': self.role,
            'success': False,
            'video_path': None,
            'mp4_path': None,
            'srt_path': None,
            'screenshots': [],
            'error': None,
            'duration': 0
        }
        
        start_time = datetime.now()
        webm_path = os.path.join(VIDEOS_DIR, f"demo_{self.role}_{self.timestamp}.webm")
        mp4_path = os.path.join(VIDEOS_DIR, f"demo_{self.role}_{self.timestamp}.mp4")
        srt_path = os.path.join(VIDEOS_DIR, f"demo_{self.role}_{self.timestamp}.srt")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=self.headless,
                    args=['--start-maximized']
                )
                
                context = browser.new_context(
                    viewport={'width': VIDEO_CONFIG['width'], 'height': VIDEO_CONFIG['height']},
                    record_video_dir=VIDEOS_DIR,
                    record_video_size={
                        'width': VIDEO_CONFIG['width'],
                        'height': VIDEO_CONFIG['height']
                    },
                    locale='fr-FR'
                )
                
                page = context.new_page()
                self.subtitles.start()
                
                # Exécuter la démo spécifique au rôle
                self.execute_demo(page, result)
                
                # Fermer proprement
                context.close()
                browser.close()
                
                # Récupérer le chemin de la vidéo générée
                video_files = [f for f in os.listdir(VIDEOS_DIR) if f.endswith('.webm')]
                if video_files:
                    latest_video = max(video_files, key=lambda x: os.path.getctime(os.path.join(VIDEOS_DIR, x)))
                    original_path = os.path.join(VIDEOS_DIR, latest_video)
                    os.rename(original_path, webm_path)
                    result['video_path'] = webm_path
                
                # Convertir en MP4 avec FFmpeg
                if os.path.exists(webm_path):
                    self.convert_to_mp4(webm_path, mp4_path)
                    if os.path.exists(mp4_path):
                        result['mp4_path'] = mp4_path
                        # Supprimer le WebM
                        os.remove(webm_path)
                        result['video_path'] = mp4_path
                
                # Sauvegarder les sous-titres
                self.subtitles.save(srt_path)
                result['srt_path'] = srt_path
                
                result['success'] = True
                
        except Exception as e:
            result['error'] = str(e)
            self.log(f"Erreur: {e}")
        
        result['duration'] = (datetime.now() - start_time).total_seconds()
        return result
    
    def convert_to_mp4(self, webm_path: str, mp4_path: str):
        """Convertit WebM en MP4 avec FFmpeg"""
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', webm_path,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '22',
                '-c:a', 'aac',
                '-b:a', '128k',
                mp4_path
            ]
            subprocess.run(cmd, capture_output=True, timeout=120)
            self.log(f"Vidéo convertie en MP4: {mp4_path}")
        except Exception as e:
            self.log(f"Erreur conversion MP4: {e}")
    
    def take_screenshot(self, page: Page, name: str, result: dict):
        """Prend une capture d'écran"""
        filename = f"{self.role}_{name}_{self.timestamp}.png"
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        page.screenshot(path=filepath)
        result['screenshots'].append(filepath)
        self.log(f"Screenshot: {name}")
    
    def wait(self, ms: int = None, delay_type: str = 'medium'):
        """Attente avec délai configurable"""
        import time
        delay = ms if ms else DELAYS.get(delay_type, 1000)
        time.sleep(delay / 1000)
    
    def execute_demo(self, page: Page, result: dict):
        """À implémenter dans les sous-classes"""
        raise NotImplementedError("Chaque démo doit implémenter execute_demo()")
    
    def login_with_demo_button(self, page: Page, result: dict):
        """Connexion via le bouton démo rapide"""
        # Aller à la page de login
        page.goto(LOGIN_URL)
        self.wait(delay_type='page_load')
        self.subtitles.add(self.get_subtitle('login_start'))
        self.take_screenshot(page, 'login_page', result)
        
        # Cliquer sur le bouton démo correspondant au rôle
        demo_button_map = {
            'admin': 'Admin Demo',
            'bank': 'Bank Respo Demo',
            'user': 'User Demo'
        }
        button_text = demo_button_map.get(self.role, 'User Demo')
        
        self.wait(delay_type='short')
        self.subtitles.add(self.get_subtitle('login_demo_click'))
        
        # Chercher le bouton de démo par texte
        demo_section = page.locator('.demo-credentials, .demo-user').first
        if demo_section.is_visible():
            # Cliquer sur le bouton de démo
            page.locator(f"text={button_text}").click()
            self.wait(delay_type='medium')
        
        # Attendre la modal et cliquer sur "Utiliser ce compte"
        try:
            page.locator('button:has-text("Utiliser"), button:has-text("Se connecter")').first.click()
            self.wait(delay_type='page_load')
        except:
            # Fallback: remplir le formulaire manuellement
            page.fill('input[name="email"], input[type="email"]', self.account['email'])
            page.fill('input[name="password"], input[type="password"]', self.account['password'])
            page.click('button[type="submit"]')
            self.wait(delay_type='page_load')
        
        self.subtitles.add(self.get_subtitle('login_success'))
        self.take_screenshot(page, 'after_login', result)
    
    def navigate_to(self, page: Page, url: str, subtitle_key: str, result: dict):
        """Navigation vers une page avec sous-titre"""
        page.goto(f"{BASE_URL}{url}")
        self.wait(delay_type='page_load')
        self.subtitles.add(self.get_subtitle(subtitle_key))
        self.take_screenshot(page, subtitle_key, result)
    
    def click_sidebar_link(self, page: Page, link_text: str, subtitle_key: str, result: dict):
        """Clic sur un lien du sidebar"""
        try:
            # Sur mobile, ouvrir le sidebar d'abord
            toggle = page.locator('#sidebar-toggle')
            if toggle.is_visible():
                toggle.click()
                self.wait(delay_type='short')
            
            # Cliquer sur le lien
            page.locator(f'.wise-nav-item:has-text("{link_text}")').first.click()
            self.wait(delay_type='page_load')
            self.subtitles.add(self.get_subtitle(subtitle_key))
            self.take_screenshot(page, subtitle_key, result)
        except Exception as e:
            self.log(f"Navigation error: {e}")
    
    def logout(self, page: Page, result: dict):
        """Déconnexion"""
        self.subtitles.add(self.get_subtitle('logout'))
        page.goto(f"{BASE_URL}/auth/logout")
        self.wait(delay_type='medium')
        self.subtitles.add(self.get_subtitle('demo_complete'))
        self.take_screenshot(page, 'logout', result)
