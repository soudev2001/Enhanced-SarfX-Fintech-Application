"""Générateur de sous-titres SRT pour vidéos Robot Framework"""
from datetime import datetime, timedelta
from pathlib import Path


class SubtitlesGenerator:
    """Library to generate SRT subtitles for demo videos"""

    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self):
        self.subtitles = []
        self.start_time = None
        self.counter = 1

    def start_subtitles(self):
        """Initialize subtitle generation"""
        self.subtitles = []
        self.start_time = datetime.now()
        self.counter = 1
        print("📝 Sous-titres initialisés")

    def add_subtitle(self, text, duration=3):
        """Add a subtitle entry

        Args:
            text: Subtitle text to display
            duration: Duration in seconds (default: 3)
        """
        if self.start_time is None:
            self.start_subtitles()

        # Calculate timestamps
        elapsed = (datetime.now() - self.start_time).total_seconds()
        start = timedelta(seconds=elapsed)
        end = timedelta(seconds=elapsed + duration)

        # Format: HH:MM:SS,mmm
        start_str = self._format_time(start)
        end_str = self._format_time(end)

        # SRT format
        subtitle = f"{self.counter}\n{start_str} --> {end_str}\n{text}\n\n"
        self.subtitles.append(subtitle)
        self.counter += 1

        print(f"📝 Sous-titre #{self.counter-1}: {text[:50]}...")

    def save_subtitles(self, output_file):
        """Save subtitles to SRT file

        Args:
            output_file: Path to output .srt file
        """
        if not self.subtitles:
            print("⚠️  Aucun sous-titre à sauvegarder")
            return None

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure .srt extension
        if not output_path.suffix == '.srt':
            output_path = output_path.with_suffix('.srt')

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(self.subtitles)

        print(f"✅ {len(self.subtitles)} sous-titres sauvegardés: {output_path}")
        return str(output_path)

    def _format_time(self, td):
        """Format timedelta to SRT time format (HH:MM:SS,mmm)"""
        hours, remainder = divmod(td.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int((seconds % 1) * 1000)

        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d},{milliseconds:03d}"

    def get_subtitle_count(self):
        """Return the number of subtitles created"""
        return len(self.subtitles)
