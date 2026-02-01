# Archive nettoyage - 2026-02-01

Objectif: conserver le cœur applicatif et déplacer les éléments de démo/artefacts/scripts ponctuels dans une archive traçable.

## Dossiers déplacés
- demo_outputs/
  - sarfx_demo_output/
  - robot_results/
- demos/
  - playwright_demos/
- robot/
  - robot_tests/
- documentation/
  - documentation/

## Fichiers déplacés
### docs/
- architecture.md
- ATM_MODULE_README.md
- CHECKLIST.md
- CORRECTIONS_CONVERTER_IA.md
- DEMARRAGE_VIDEO.md
- FIX_BACKEND_GUIDE.md
- FIX_SUMMARY.md
- IMPLEMENTATION_COMPLETE.md
- IMPLEMENTATION_SUMMARY.md
- NOUVELLES_FONCTIONNALITES.md
- ROBOT_ROUTES_MAPPING.md
- VIDEO_DEMO_GUIDE.md
- VISUAL_GUIDE.md
- WALLETS_DEMO_GUIDE.md
- WALLETS_DONE.md
- WALLETS_IMPROVEMENTS.md
- WALLETS_INDEX.md
- WALLETS_README.md
- WALLETS_SUMMARY.md
- WALLETS_VISUAL_SUMMARY.md

### legacy/
- HOMEPAGE V2.txt
- HOMEPAGE.txt
- graph TD.mmd
- realapp.html

### demos/
- sarfx_demo.py
- run_demo_robot.sh
- run_demo_windows.bat
- run_playwright_demo.py
- run_video_demo_windows.bat
- install_playwright.sh
- install_ffmpeg_windows.bat
- merge_video.py
- merge_video_subtitles.bat
- test_video_recording.bat
- test_chrome.py

### robot/
- requirements-robot.txt
- run_robot_tests.sh

### utilities/
- fix_502.sh
- fix_admin_verified.py
- fix_ai_backend.sh
- migrate_roles.py
- reset_structure.sh
- update_all.sh

## Raison
- Réduire le bruit et conserver uniquement le code/flux principaux.
- Garder les éléments de démo et scripts ponctuels accessibles mais hors du chemin principal.
