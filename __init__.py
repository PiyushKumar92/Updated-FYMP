# Suppress warnings first
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="face_recognition_models")
warnings.filterwarnings("ignore", message=".*pkg_resources is deprecated.*")

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_moment import Moment
from flask_wtf.csrf import CSRFProtect
from celery import Celery
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
bcrypt = Bcrypt()
moment = Moment()
csrf = CSRFProtect()


def make_celery(app):
    # Validate Celery configuration
    broker_url = app.config.get("CELERY_BROKER_URL")
    result_backend = app.config.get("CELERY_RESULT_BACKEND")
    
    if not broker_url or not result_backend:
        raise ValueError("Celery configuration missing: CELERY_BROKER_URL and CELERY_RESULT_BACKEND are required")
    
    celery = Celery(
        app.import_name,
        backend=result_backend,
        broker=broker_url,
    )
    celery.conf.update(app.config)
    return celery


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    login.login_view = "main.login"
    login.login_message = "Please log in to access this page"
    bcrypt.init_app(app)
    moment.init_app(app)
    csrf.init_app(app)
    
    # Track user activity
    @app.before_request
    def track_user_activity():
        from flask_login import current_user
        from app.models import get_ist_now
        
        if current_user.is_authenticated:
            # Update last activity every 5 minutes to avoid too many DB writes
            current_time = get_ist_now()
            if not hasattr(current_user, '_last_activity_update') or \
               (current_time - current_user._last_activity_update).seconds > 300:
                current_user.last_seen = current_time
                current_user.is_online = True
                current_user._last_activity_update = current_time
                try:
                    db.session.commit()
                except:
                    db.session.rollback()
    
    # Add security headers with relaxed CSP for development
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Relaxed CSP for development - allows inline scripts and external CDNs
        response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: https:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; style-src 'self' 'unsafe-inline' https:; font-src 'self' https:; img-src 'self' data: blob: https:; connect-src 'self' https:;"
        return response

    from app.routes import bp as main_bp
    from app.admin import admin_bp
    from app.error_handlers import register_error_handlers

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Context processors for global data
    @app.context_processor
    def inject_global_data():
        from flask_login import current_user
        from app.models import Announcement, Notification, get_ist_now
        from datetime import datetime
        
        # Auto-deactivate expired announcements
        try:
            current_time = get_ist_now()
            expired_announcements = Announcement.query.filter(
                Announcement.is_active == True,
                Announcement.expires_at.isnot(None),
                Announcement.expires_at <= current_time
            ).all()
            
            for announcement in expired_announcements:
                announcement.is_active = False
            
            if expired_announcements:
                db.session.commit()
        except:
            db.session.rollback()
        
        # Get active announcements for logged-in users only
        active_announcements = []
        if current_user.is_authenticated:
            try:
                from app.models import AnnouncementRead
                
                # Get all active announcements
                current_time = get_ist_now()
                all_active = Announcement.query.filter(
                    Announcement.is_active == True,
                    db.or_(
                        Announcement.expires_at.is_(None),
                        Announcement.expires_at > current_time
                    )
                ).order_by(Announcement.created_at.desc()).all()
                
                # Filter out announcements already read by current user
                read_announcement_ids = db.session.query(AnnouncementRead.announcement_id).filter_by(user_id=current_user.id).all()
                read_ids = [r[0] for r in read_announcement_ids]
                
                active_announcements = [a for a in all_active if a.id not in read_ids]
            except Exception:
                # If table doesn't exist, show all announcements
                try:
                    current_time = get_ist_now()
                    active_announcements = Announcement.query.filter(
                        Announcement.is_active == True,
                        db.or_(
                            Announcement.expires_at.is_(None),
                            Announcement.expires_at > current_time
                        )
                    ).order_by(Announcement.created_at.desc()).all()
                except Exception:
                    active_announcements = []
        
        # Get unread notifications count for authenticated users
        unread_count = 0
        if current_user.is_authenticated:
            unread_count = current_user.unread_notifications_count
        
        return {
            'active_announcements': active_announcements,
            'unread_notifications_count': unread_count
        }

    return app


@login.user_loader
def load_user(user_id):
    from app.models import User
    
    try:
        return User.query.get(int(user_id))
    except (ValueError, TypeError):
        return None


from app import models
