"""PostgreSQL Live Integration Tests.

These tests connect directly to the active PostgreSQL database (`cig_db`).
They verify:
1. Active PostgreSQL engine connectivity and schema integrity.
2. Alembic migration version table and applied version.
3. CRUD operations on isolated test records (cleaned up after each test).
4. Deactivation status of insecure demo accounts.
Existing application tables and user data are never dropped or altered.
"""

import os
import pytest
from sqlalchemy import text
from app import create_app
from app.extensions import db
from app.models.user import User, AdminInvitation, PasswordResetToken


@pytest.fixture(scope='module')
def pg_app():
    """Create app instance using active development PostgreSQL database."""
    # Ensure FLASK_ENV uses development config pointing to PostgreSQL
    app = create_app('development')
    with app.app_context():
        # Verify engine connects to postgresql
        engine_url = str(db.engine.url)
        assert 'postgresql' in engine_url, f"Expected PostgreSQL URL, got: {engine_url}"
        yield app


def test_postgresql_connection(pg_app):
    """Verify live PostgreSQL connectivity and database name."""
    with pg_app.app_context():
        result = db.session.execute(text("SELECT current_database(), version();")).fetchone()
        db_name, version = result[0], result[1]
        assert db_name == 'cig_db'
        assert 'PostgreSQL' in version


def test_postgresql_schema_tables_exist(pg_app):
    """Verify that all required tables exist in the public PostgreSQL schema."""
    with pg_app.app_context():
        query = text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in db.session.execute(query).fetchall()]

        assert 'users' in tables
        assert 'password_reset_tokens' in tables
        assert 'admin_invitations' in tables
        assert 'alembic_version' in tables


def test_alembic_migration_head(pg_app):
    """Verify that Alembic has recorded the applied migration version in PostgreSQL."""
    with pg_app.app_context():
        version = db.session.execute(text("SELECT version_num FROM alembic_version;")).scalar()
        assert version is not None
        assert len(version) > 0


def test_demo_accounts_deactivated_in_postgres(pg_app):
    """Verify that disclosed demo accounts are deactivated in PostgreSQL."""
    with pg_app.app_context():
        demo_users = User.query.filter(User.email.in_(['admin@cig.local', 'tania@cig.local'])).all()
        for u in demo_users:
            assert u.is_active is False, f"Account {u.email} must be deactivated"


def test_postgresql_isolated_crud(pg_app):
    """Verify CRUD operations with isolated test data on live PostgreSQL.

    Existing tables and user data are preserved. The test record is deleted
    at the end of the test.
    """
    test_email = 'pg_integration_test_user@cig.local'

    with pg_app.app_context():
        # Clean up any leftover test record
        existing = User.query.filter_by(email=test_email).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        # 1. Create
        test_user = User(
            full_name='Postgres Test User',
            email=test_email,
            role='user',
            age_range='18-25',
            city='Malang',
        )
        test_user.set_password('PgSecurePass2026!')
        db.session.add(test_user)
        db.session.commit()

        user_id = test_user.id
        assert user_id is not None

        # 2. Read from PostgreSQL
        loaded_user = db.session.get(User, user_id)
        assert loaded_user is not None
        assert loaded_user.email == test_email
        assert loaded_user.check_password('PgSecurePass2026!') is True
        assert loaded_user.check_password('WrongPass') is False

        # 3. Update in PostgreSQL
        loaded_user.city = 'Kota Batu'
        db.session.commit()

        updated_user = db.session.get(User, user_id)
        assert updated_user.city == 'Kota Batu'

        # 4. Clean up (delete only this test user)
        db.session.delete(updated_user)
        db.session.commit()

        # Verify deletion
        assert db.session.get(User, user_id) is None
