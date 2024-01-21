# config.py
import os
import smtplib
from datetime import timedelta


class Config:
    DEBUG = True
    TESTING = False

    # Logging Configuration
    LOG_FILE = 'app.log'

    # Database Configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///appointments.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # Google Configuration
    GOOGLE_CLIENT_ID = '458784267516-25o1b1na4bba9c4m7l3cdbnrkolj7t4r.apps.googleusercontent.com'
    GOOGLE_CLIENT_SECRET = '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'

    # Email Configuration
    # os.environ.get('PASSWORD')
    MAIL_SERVER = 'smtp.example.com', 'smtp.gmail.com'
    MAIL_PORT = 587, 465
    MAIL_USE_TLS = True
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'your_username'
    MAIL_PASSWORD = 'your_password'
    MAIL_DEFAULT_SENDER = 'your_email@example.com'

    # Celery Configuration
    CELERY_BROKER_URL = 'pyamqp://guest@localhost//'
    CELERY_RESULT_BACKEND = 'rpc://'
    CELERY_CONFIG = {"broker_url": "redis://redis", "result_backend": "redis://redis"}

    # Session Configuration
    # os.urandom() generates a random string of 24 bytes, for secure secret key.
    #  This is for secure cookies, session protection, CSRF protection
    SECRET_KEY = os.urandom(24)
    # Enable secure cookies (Only set over HTTPS)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True  # Recommended for security
    SESSION_COOKIE_SAMESITE = 'Lax'  # Adjust as needed
    # if using flask-session
    SESSION_TYPE = 'filesystem'
    # Set session timeout to 30 minutes (adjust as needed)
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
