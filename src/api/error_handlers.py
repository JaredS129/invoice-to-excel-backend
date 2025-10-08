"""Global error handlers for Flask API."""
from flask import jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app):
    """
    Register global error handlers for the Flask application.

    Args:
        app: Flask application instance
    """

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        return jsonify({
            'success': False,
            'error': {
                'code': 'BAD_REQUEST',
                'message': str(error.description) if hasattr(error, 'description') else 'Bad request'
            }
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Endpoint not found'
            }
        }), 404

    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle 413 Request Entity Too Large errors."""
        return jsonify({
            'success': False,
            'error': {
                'code': 'REQUEST_TOO_LARGE',
                'message': 'Request size exceeds maximum allowed (100MB)'
            }
        }), 413

    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error."""
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred during processing'
            }
        }), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle any unexpected errors."""
        # Handle custom API errors
        if isinstance(error, APIError):
            return jsonify(error.to_dict()), error.status_code

        # Log the error for debugging
        app.logger.error(f'Unexpected error: {str(error)}', exc_info=True)

        # If it's an HTTP exception, use its status code
        if isinstance(error, HTTPException):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'HTTP_ERROR',
                    'message': error.description
                }
            }), error.code

        # Generic 500 error for unexpected exceptions
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500


class APIError(Exception):
    """Custom API error with status code and error code."""

    def __init__(self, message, status_code=400, error_code=None):
        """
        Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code (default: 400)
            error_code: Machine-readable error code (default: generic)
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or 'API_ERROR'

    def to_dict(self):
        """Convert error to dictionary for JSON response."""
        return {
            'success': False,
            'error': {
                'code': self.error_code,
                'message': self.message
            }
        }
