"""Tests for database models."""

from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models.user import User, PasswordResetToken, AdminInvitation
from app.utils.tokens import hash_token, generate_token


def test_user_password_hashing(app):
    """Test password hashing and verification."""
    with app.app_context():
        user = User(
            full_name='Budi Santoso',
            email='budi@example.com',
            age_range='18-25',
            city='Malang',
        )
        user.set_password('SecretPass123!')
        assert user.password_hash is not None
        assert user.password_hash != 'SecretPass123!'
        assert user.check_password('SecretPass123!') is True
        assert user.check_password('WrongPass') is False


def test_user_roles(app):
    """Test user role checking."""
    with app.app_context():
        user = User(full_name='User', email='u@example.com', role='user', age_range='18-25', city='Malang')
        admin = User(full_name='Admin', email='a@example.com', role='admin', age_range='26-35', city='Malang')

        assert user.is_admin is False
        assert admin.is_admin is True


def test_password_reset_token_validity(app):
    """Test token validity and expiration."""
    with app.app_context():
        user = User(full_name='User', email='token@example.com', age_range='18-25', city='Malang')
        user.set_password('Pass123!')
        db.session.add(user)
        db.session.commit()

        # Valid token
        raw_token = generate_token()
        token = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db.session.add(token)
        db.session.commit()

        assert token.is_valid is True
        assert token.is_expired is False

        # Expired token
        token.expires_at = datetime.now(timezone.utc) - timedelta(minutes=10)
        assert token.is_valid is False
        assert token.is_expired is True

        # Used token
        token.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        token.used = True
        assert token.is_valid is False


def test_admin_invitation_validity(app):
    """Test admin invitation validity and expiration."""
    with app.app_context():
        admin = User(full_name='Admin', email='adm@example.com', role='admin', age_range='26-35', city='Malang')
        admin.set_password('Pass123!')
        db.session.add(admin)
        db.session.commit()

        raw_token = generate_token()
        invitation = AdminInvitation(
            email='newadmin@example.com',
            token_hash=hash_token(raw_token),
            invited_by_id=admin.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        db.session.add(invitation)
        db.session.commit()

        assert invitation.is_valid is True
        assert invitation.is_expired is False

        # Accept
        invitation.accepted = True
        assert invitation.is_valid is False
