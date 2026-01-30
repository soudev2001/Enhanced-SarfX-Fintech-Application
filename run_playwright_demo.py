#!/usr/bin/env python3
"""
Script pour lancer les démos Playwright depuis la ligne de commande
Usage:
    python run_playwright_demo.py admin
    python run_playwright_demo.py bank
    python run_playwright_demo.py user
    python run_playwright_demo.py all
"""
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description='Lancer les démos Playwright SarfX')
    parser.add_argument('role', choices=['admin', 'bank', 'user', 'all'], 
                        help='Rôle à démontrer (admin, bank, user, all)')
    parser.add_argument('--headless', action='store_true', default=True,
                        help='Mode headless (par défaut)')
    parser.add_argument('--visible', action='store_true',
                        help='Mode visible (ouvre le navigateur)')
    parser.add_argument('--url', default=None,
                        help='URL de base (par défaut: https://sarfx.io)')
    
    args = parser.parse_args()
    
    headless = not args.visible
    
    # Configurer l'URL si spécifiée
    if args.url:
        import os
        os.environ['SARFX_URL'] = args.url
    
    print(f"🎬 Lancement de la démo {args.role}...")
    print(f"   Mode: {'headless' if headless else 'visible'}")
    print(f"   URL: {args.url or 'https://sarfx.io'}")
    print()
    
    if args.role == 'all':
        # Lancer les 3 démos séquentiellement
        from playwright_demos.demo_admin import run_admin_demo
        from playwright_demos.demo_bank import run_bank_demo
        from playwright_demos.demo_user import run_user_demo
        
        results = {}
        
        print("=" * 50)
        print("👑 ADMIN DEMO")
        print("=" * 50)
        results['admin'] = run_admin_demo(headless=headless)
        print_result(results['admin'])
        
        print("\n" + "=" * 50)
        print("🏦 BANK DEMO")
        print("=" * 50)
        results['bank'] = run_bank_demo(headless=headless)
        print_result(results['bank'])
        
        print("\n" + "=" * 50)
        print("👤 USER DEMO")
        print("=" * 50)
        results['user'] = run_user_demo(headless=headless)
        print_result(results['user'])
        
        # Résumé
        print("\n" + "=" * 50)
        print("📊 RÉSUMÉ")
        print("=" * 50)
        for role, result in results.items():
            status = "✅" if result['success'] else "❌"
            duration = f"{result['duration']:.1f}s" if result.get('duration') else "N/A"
            print(f"  {status} {role.upper()}: {duration}")
        
    else:
        # Lancer une seule démo
        if args.role == 'admin':
            from playwright_demos.demo_admin import run_admin_demo
            result = run_admin_demo(headless=headless)
        elif args.role == 'bank':
            from playwright_demos.demo_bank import run_bank_demo
            result = run_bank_demo(headless=headless)
        elif args.role == 'user':
            from playwright_demos.demo_user import run_user_demo
            result = run_user_demo(headless=headless)
        
        print_result(result)


def print_result(result):
    """Affiche le résultat d'une démo"""
    if result['success']:
        print(f"\n✅ Démo terminée avec succès!")
        print(f"   Durée: {result['duration']:.1f} secondes")
        if result.get('video_path'):
            print(f"   Vidéo: {result['video_path']}")
        if result.get('srt_path'):
            print(f"   Sous-titres: {result['srt_path']}")
        if result.get('screenshots'):
            print(f"   Screenshots: {len(result['screenshots'])} captures")
    else:
        print(f"\n❌ Erreur lors de la démo")
        if result.get('error'):
            print(f"   Erreur: {result['error']}")


if __name__ == '__main__':
    main()
