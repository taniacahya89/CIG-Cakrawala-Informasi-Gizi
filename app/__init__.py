"""CIG Application Factory."""

from flask import Flask
from .config import config
from .extensions import db, migrate, login_manager, csrf, mail, limiter


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        import os
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    if config_name == 'production' and app.config.get('SECRET_KEY') == 'fallback-secret-key-change-me':
        raise RuntimeError('Set a strong SECRET_KEY in the production environment.')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    # Register user loader
    from .models import User, LearningModule, LearningProgress, QuizCategory, QuizQuestion, QuizBestScore, Recipe, RecipeFavorite, RecipeView, ScanHistory

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from .blueprints.main import main_bp
    from .blueprints.auth import auth_bp
    from .blueprints.user import user_bp
    from .blueprints.admin import admin_bp
    from .blueprints.content import content_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(content_bp)

    # Register error handlers
    register_error_handlers(app)

    # Context processors
    @app.context_processor
    def inject_app_info():
        return {
            'app_name': app.config.get('APP_NAME', 'CIG'),
            'app_short_name': app.config.get('APP_SHORT_NAME', 'CIG'),
        }

    return app


def register_error_handlers(app):
    """Register error handlers."""

    @app.errorhandler(404)
    def not_found(error):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(error):
        from flask import render_template
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(413)
    def upload_too_large(error):
        from flask import flash, redirect, request, url_for
        flash('File terlalu besar. Gambar maksimal 5 MB.', 'danger')
        return redirect(url_for('admin.content_index')) if request.path.startswith('/admin/') else ('File terlalu besar.', 413)

    @app.errorhandler(429)
    def too_many_requests(error):
        from flask import render_template
        return render_template('errors/429.html'), 429
