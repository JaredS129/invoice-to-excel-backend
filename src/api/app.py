"""Flask application factory for invoice processing API."""
import os
from flask import Flask
from flask_cors import CORS


def create_app(config=None):
    """
    Create and configure Flask application.

    Args:
        config: Optional configuration dictionary

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    # Default configuration
    app.config.update({
        'MAX_CONTENT_LENGTH': 100 * 1024 * 1024,  # 100MB max request size
        'JSON_SORT_KEYS': False,
    })

    # Apply custom configuration if provided
    if config:
        app.config.update(config)

    # Enable CORS for all routes
    CORS(app)

    # Register error handlers
    from src.api.error_handlers import register_error_handlers
    register_error_handlers(app)

    # Register routes
    from src.api.routes import api_bp
    app.register_blueprint(api_bp)

    return app


if __name__ == '__main__':
    """Entry point for running the application."""
    app = create_app()

    # Check environment for production vs development
    flask_env = os.environ.get('FLASK_ENV', 'production')

    if flask_env == 'development':
        # Development mode with Flask debug server
        app.run(
            debug=True,
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000))
        )
    else:
        # Production mode with Waitress WSGI server
        from waitress import serve
        port = int(os.environ.get('PORT', 5000))
        print(f'Serving on http://0.0.0.0:{port}')
        serve(
            app,
            host='0.0.0.0',
            port=port,
            threads=5
        )
