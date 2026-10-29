"""User model for CIG."""

from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(UserMixin, db.Model):
    """User model with role-based access control."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    age_range = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    password_reset_tokens = db.relationship('PasswordResetToken', backref='user', lazy='dynamic',
                                            cascade='all, delete-orphan')
    sent_invitations = db.relationship('AdminInvitation', backref='invited_by', lazy='dynamic',
                                       cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check the user's password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        """Check if user has admin role."""
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.email}>'


class PasswordResetToken(db.Model):
    """Token for password reset requests."""

    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token_hash = db.Column(db.String(512), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)

    @property
    def is_expired(self):
        """Check if the token has expired."""
        if self.expires_at is None:
            return True
        now = datetime.now(timezone.utc)
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now > expires

    @property
    def is_valid(self):
        """Check if the token is still valid (not expired and not used)."""
        return not self.used and not self.is_expired

    def __repr__(self):
        return f'<PasswordResetToken user_id={self.user_id}>'


class AdminInvitation(db.Model):
    """Invitation for administrator accounts."""

    __tablename__ = 'admin_invitations'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    token_hash = db.Column(db.String(512), nullable=False, unique=True)
    invited_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    accepted = db.Column(db.Boolean, default=False, nullable=False)

    @property
    def is_expired(self):
        """Check if the invitation has expired."""
        if self.expires_at is None:
            return True
        now = datetime.now(timezone.utc)
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now > expires

    @property
    def is_valid(self):
        """Check if the invitation is still valid (not expired and not accepted)."""
        return not self.accepted and not self.is_expired

    def __repr__(self):
        return f'<AdminInvitation email={self.email}>'
