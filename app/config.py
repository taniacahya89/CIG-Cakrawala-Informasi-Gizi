"""CIG Application Configuration."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-secret-key-change-me')
    _raw_db_url = os.environ.get('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@localhost:5432/cig_db')
    if _raw_db_url.startswith('postgresql://'):
        _raw_db_url = _raw_db_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    SQLALCHEMY_DATABASE_URI = _raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Limit the entire multipart request; each image is checked at 5 MB separately.
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Session security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 604800  # 7 days in seconds

    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

    # Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 1025))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', '0') == '1'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', '0') == '1'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@cig.local')

    # Rate limiting
    RATELIMIT_STORAGE_URI = 'memory://'
    RATELIMIT_DEFAULT = '200/hour'

    # Token expiry (in seconds)
    PASSWORD_RESET_TOKEN_EXPIRY = 3600  # 1 hour
    ADMIN_INVITE_TOKEN_EXPIRY = 86400  # 24 hours

    # Application
    APP_NAME = 'Cakrawala Informasi Gizi'
    APP_SHORT_NAME = 'CIG'

    # Scanner: use checkpoint stored outside SQLAlchemy app/models.
    SCAN_MODEL_PATH = os.environ.get(
        'SCAN_MODEL_PATH', str(Path(__file__).resolve().parent.parent / 'models' / 'yolo' / 'best.pt')
    )
    SCAN_CLASS_MAP = os.environ.get('SCAN_CLASS_MAP', '')
    SCAN_DEVICE = os.environ.get('SCAN_DEVICE', 'cpu')
    SCAN_IMGSZ = int(os.environ.get('SCAN_IMGSZ', '640'))


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'sqlite:///:memory:')
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    SERVER_NAME = 'localhost'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
