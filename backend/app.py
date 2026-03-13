"""
app.py
------
Application entry point.

Responsibilities:
  - Create and configure the Flask app
  - Register blueprints (route groups)
  - Enable CORS for frontend communication
  - Start the development server when run directly
"""

import os
from flask import Flask
from flask_cors import CORS

from config import config
from utils.logger import setup_logger
from controllers.scan_controller import scan_bp
from controllers.report_controller import report_bp

# Make sure the reports directory exists at startup
os.makedirs(config.REPORTS_DIR, exist_ok=True)


def create_app() -> Flask:
    """
    Application factory function.
    Returns a fully configured Flask application instance.
    Using a factory makes the app easier to test and extend.
    """
    app = Flask(__name__)
    app.secret_key = config.SECRET_KEY

    # Allow requests from any origin (adjust in production to specific domains)
    CORS(app, resources={r"/api/*": {"origins": [
        "https://ai-vul-scanner.vercel.app",
        "http://localhost:5173"
    ]}})

    # Configure centralised logging
    setup_logger()

    # Register route blueprints
    # Each blueprint groups related endpoints under a shared URL prefix
    app.register_blueprint(scan_bp,   url_prefix="/api")
    app.register_blueprint(report_bp, url_prefix="/api")

    # Simple health-check endpoint — useful for load-balancers / monitoring
    @app.get("/health")
    def health():
        return {"status": "ok", "service": "vuln-scanner"}, 200

    return app


# ------------------------------------------------------------------ #
# Development server entry point
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    flask_app = create_app()
    flask_app.run(host="0.0.0.0", port=port, debug=False)
