"""Custom Robot Framework library for Video Recording"""
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path


class VideoRecorder:
    """Library to record browser sessions as video"""

    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self):
        self.recording_process = None
        self.output_file = None

    def start_video_recording(self, output_dir, filename=None):
        """Start recording the screen with FFmpeg

        Args:
            output_dir: Directory where to save the video
            filename: Optional custom filename (default: demo_TIMESTAMP.mp4)
        """
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"demo_{timestamp}.mp4"

        if not filename.endswith('.mp4'):
            filename += '.mp4'

        self.output_file = output_path / filename

        try:
            # FFmpeg command for screen recording on Windows
            # Using gdigrab for Windows screen capture
            cmd = [
                'ffmpeg',
                '-f', 'gdigrab',           # Windows screen grabber
                '-framerate', '30',         # 30 fps
                '-i', 'desktop',            # Capture entire desktop
                '-c:v', 'libx264',          # H.264 codec
                '-preset', 'ultrafast',     # Fast encoding
                '-crf', '23',               # Quality (lower = better, 18-28 range)
                '-pix_fmt', 'yuv420p',      # Pixel format for compatibility
                '-y',                       # Overwrite output file
                str(self.output_file)
            ]

            # Start FFmpeg process in background
            self.recording_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            # Wait a moment for recording to start
            time.sleep(2)

            print(f"📹 Enregistrement vidéo démarré: {self.output_file}")
            return str(self.output_file)

        except FileNotFoundError:
            raise Exception(
                "FFmpeg n'est pas installé ou n'est pas dans le PATH. "
                "Installez-le avec: winget install ffmpeg ou choco install ffmpeg"
            )
        except Exception as e:
            raise Exception(f"Erreur lors du démarrage de l'enregistrement: {e}")

    def stop_video_recording(self):
        """Stop the video recording"""
        if self.recording_process is None:
            print("⚠️  Aucun enregistrement en cours")
            return None

        try:
            # Send quit command to FFmpeg (graceful shutdown)
            self.recording_process.terminate()

            # Wait for process to finish (max 10 seconds)
            self.recording_process.wait(timeout=10)

            print(f"✅ Enregistrement terminé: {self.output_file}")

            output = str(self.output_file)
            self.recording_process = None
            self.output_file = None

            return output

        except subprocess.TimeoutExpired:
            # Force kill if it doesn't stop gracefully
            self.recording_process.kill()
            print("⚠️  Enregistrement arrêté de force")

            output = str(self.output_file)
            self.recording_process = None
            self.output_file = None

            return output
        except Exception as e:
            print(f"⚠️  Erreur lors de l'arrêt: {e}")
            return None

    def is_recording(self):
        """Check if recording is in progress"""
        if self.recording_process is None:
            return False

        # Check if process is still running
        poll = self.recording_process.poll()
        return poll is None
