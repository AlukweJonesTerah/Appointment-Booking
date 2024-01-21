# app_factory.py

from flask import Flask
from auth_blueprint.auth_blueprint import auth_bp
import logging
from flask_login import LoginManager
from celery_worker.celery_worker_app import make_celery


def configure_logging(app, config=None):
    # Configure the logging level and format
    if config:
        logging.basicConfig(level=logging.INFO)
        app.logger.setLevel(logging.INFO)
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        app.config['DEBUG'] = True

        # Add a file handler to log to a file
        file_handler = logging.FileHandler('app.log')
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        # Configure a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create a formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add the handlers to the app logger
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)


login_manager = LoginManager()


def create_app(config=None):
    app = Flask(__name__, static_folder='static')
    # Register Blueprints
    if config:
        app.config.from_object(config)

    app.register_blueprint(auth_bp, url_prefix='/auth')

    configure_logging(app, config=config)

    # SQLAlcheny extension initialization
    # db.init_app(app)

    # Migrations initialization
    # migrate.init_app(app, db)

    # Login Configuration
    login_manager.login_view = 'login'
    login_manager.init_app(app)

    # Session Configuration
    # Session(app)
    # Celery
    celery = make_celery(app)
    celery.set_default()

    # Mail
    # mail.init_app(app)

    # app.register_blueprint(main)

    return app, celery, logging
