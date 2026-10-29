"""Token generation and validation utilities for CIG."""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from flask import current_app
from app.extensions import db
from app.models.user import PasswordResetToken, AdminInvitation


def generate_token():
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(48)


def hash_token(token):
    """Create a SHA-256 hash of a token for storage."""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def create_password_reset_token(user):
    """Create a password reset token for a user.

    Invalidates any existing tokens for the user.
    Returns the raw token (not the hash).
    """
    # Invalidate existing tokens
    PasswordResetToken.query.filter_by(user_id=user.id, used=False).update({'used': True})

    token = generate_token()
    expiry_seconds = current_app.config.get('PASSWORD_RESET_TOKEN_EXPIRY', 3600)

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token(token),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=expiry_seconds),
    )
    db.session.add(reset_token)
    db.session.commit()

    return token


def verify_password_reset_token(token):
    """Verify a password reset token and return the associated user.

    Returns the User if valid, None otherwise.
    """
    token_record = PasswordResetToken.query.filter_by(
        token_hash=hash_token(token),
        used=False,
    ).first()

    if token_record is None or not token_record.is_valid:
        return None

    return token_record.user


def consume_password_reset_token(token):
    """Mark a password reset token as used.

    Returns True if the token was valid and consumed, False otherwise.
    """
    token_record = PasswordResetToken.query.filter_by(
        token_hash=hash_token(token),
        used=False,
    ).first()

    if token_record is None or not token_record.is_valid:
        return False

    token_record.used = True
    db.session.commit()
    return True


def create_admin_invitation(email, invited_by_user):
    """Create an admin invitation token.

    Returns the raw token (not the hash).
    """
    token = generate_token()
    expiry_seconds = current_app.config.get('ADMIN_INVITE_TOKEN_EXPIRY', 86400)

    invitation = AdminInvitation(
        email=email,
        token_hash=hash_token(token),
        invited_by_id=invited_by_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=expiry_seconds),
    )
    db.session.add(invitation)
    db.session.commit()

    return token


def verify_admin_invitation(token):
    """Verify an admin invitation token.

    Returns the AdminInvitation if valid, None otherwise.
    """
    invitation = AdminInvitation.query.filter_by(
        token_hash=hash_token(token),
        accepted=False,
    ).first()

    if invitation is None or not invitation.is_valid:
        return None

    return invitation


def accept_admin_invitation(token):
    """Mark an admin invitation as accepted.

    Returns True if the token was valid and accepted, False otherwise.
    """
    invitation = AdminInvitation.query.filter_by(
        token_hash=hash_token(token),
        accepted=False,
    ).first()

    if invitation is None or not invitation.is_valid:
        return False

    invitation.accepted = True
    db.session.commit()
    return True
