import argparse
from app import create_app

app = create_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run SarfX Flask application')
    parser.add_argument('--port', '-p', type=int, default=5050, help='Port to run the server on (default: 5050 for dev)')
    parser.add_argument('--host', '-H', type=str, default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--no-debug', action='store_true', help='Disable debug mode')
    args = parser.parse_args()

    # Debug mode is on for development; turn off in production
    app.run(host=args.host, port=args.port, debug=not args.no_debug)