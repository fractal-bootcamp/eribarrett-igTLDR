import os
import logging
from flask import Flask, current_app
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import get_config
from controllers import instagram_monitor
from app.routes import api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    config = get_config()
    
    # Load configuration
    app.config.from_object(config)
    
    # Configure CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Configure rate limiting
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=[config.RATELIMIT_DEFAULT],
        storage_uri=config.RATELIMIT_STORAGE_URL
    )
    
    # Register blueprints
    app.register_blueprint(api, url_prefix='/api')
    
    # Start the Instagram monitor when first request is received
    # Using Flask 2.x compatible approach
    @app.route('/start-monitor', methods=['GET'])
    @limiter.exempt
    def start_monitor_route():
        if not instagram_monitor.is_running():
            instagram_monitor.start()
            logger.info("Instagram monitor started via route")
        return {'status': 'monitor started'}, 200
    
    # Manually start monitor during app init in non-testing environments
    if not app.config['TESTING']:
        with app.app_context():
            instagram_monitor.start()
            logger.info("Instagram monitor started during app initialization")
    
    # Shutdown the Instagram monitor when the app is stopping
    @app.teardown_appcontext
    def stop_monitor(exception=None):
        instagram_monitor.stop()
    
    # Health check route
    @app.route('/health', methods=['GET'])
    @limiter.exempt
    def health_check():
        return {'status': 'ok'}, 200
    
    return app

app = create_app() 