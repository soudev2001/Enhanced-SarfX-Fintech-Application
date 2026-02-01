#!/usr/bin/env python3
"""Script pour merger automatiquement la dernière vidéo avec ses sous-titres"""
import subprocess
import sys
from pathlib import Path


def find_latest_video(video_dir):
    """Trouve la vidéo la plus récente"""
    video_path = Path(video_dir)
    videos = list(video_path.glob("demo_*.mp4"))

    if not videos:
        return None

    # Trier par date de modification
    latest = max(videos, key=lambda p: p.stat().st_mtime)
    return latest


def find_latest_srt(video_dir):
    """Trouve le fichier SRT le plus récent"""
    video_path = Path(video_dir)
    srts = list(video_path.glob("demo_*.srt"))

    if not srts:
        return None

    # Trier par date de modification
    latest = max(srts, key=lambda p: p.stat().st_mtime)
    return latest


def merge_video_subtitles(video_file, srt_file, output_file=None):
    """Fusionne une vidéo avec ses sous-titres"""

    if output_file is None:
        output_file = video_file.parent / f"{video_file.stem}_with_subtitles.mp4"

    print(f"📹 Vidéo: {video_file}")
    print(f"📝 Sous-titres: {srt_file}")
    print(f"💾 Output: {output_file}")
    print()
    print("🎬 Fusion en cours...")

    # Commande FFmpeg pour merger vidéo + sous-titres
    cmd = [
        'ffmpeg',
        '-i', str(video_file),
        '-vf', f"subtitles={srt_file}:force_style='FontName=Arial,FontSize=24,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,BackColour=&H80000000&,BorderStyle=3,Outline=2,Shadow=1'",
        '-c:a', 'copy',
        '-y',
        str(output_file)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"\n✅ Fusion réussie!")
            print(f"📹 Fichier créé: {output_file}")
            return True
        else:
            print(f"\n❌ Erreur lors de la fusion:")
            print(result.stderr)
            return False

    except FileNotFoundError:
        print("\n❌ FFmpeg non trouvé. Installez-le avec:")
        print("   winget install ffmpeg")
        return False
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return False


def auto_merge_latest():
    """Fusionne automatiquement la dernière vidéo avec le dernier SRT"""
    video_dir = Path(__file__).parent / "robot_results" / "video_demo" / "videos"

    if not video_dir.exists():
        print(f"❌ Dossier vidéo non trouvé: {video_dir}")
        return False

    print("🔍 Recherche des fichiers...")

    # Trouver la dernière vidéo
    video_file = find_latest_video(video_dir)
    if not video_file:
        print("❌ Aucune vidéo trouvée dans:", video_dir)
        return False

    # Trouver le dernier SRT
    srt_file = find_latest_srt(video_dir)
    if not srt_file:
        print("❌ Aucun fichier de sous-titres trouvé dans:", video_dir)
        return False

    print(f"✅ Vidéo trouvée: {video_file.name}")
    print(f"✅ Sous-titres trouvés: {srt_file.name}")
    print()

    # Fusionner
    return merge_video_subtitles(video_file, srt_file)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Mode manuel: merge_video.py video.mp4 subtitles.srt
        video_file = Path(sys.argv[1])
        srt_file = Path(sys.argv[2]) if len(sys.argv) > 2 else video_file.with_suffix('.srt')

        if not video_file.exists():
            print(f"❌ Vidéo non trouvée: {video_file}")
            sys.exit(1)

        if not srt_file.exists():
            print(f"❌ Sous-titres non trouvés: {srt_file}")
            sys.exit(1)

        success = merge_video_subtitles(video_file, srt_file)
        sys.exit(0 if success else 1)
    else:
        # Mode automatique: merge la dernière vidéo
        success = auto_merge_latest()
        sys.exit(0 if success else 1)
