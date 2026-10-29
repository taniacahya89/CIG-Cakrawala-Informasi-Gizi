"""Pytest fixtures for CIG."""

import pytest
from app import create_app
from app.extensions import db
from app.models.user import User


@pytest.fixture
def app():
    """Create test application."""
    test_app = create_app('testing')

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def standard_user(app):
    """Create a standard user for testing."""
    with app.app_context():
        user = User(
            full_name='Test User',
            email='testuser@example.com',
            role='user',
            age_range='18-25',
            city='Malang',
        )
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def admin_user(app):
    """Create an administrator user for testing."""
    with app.app_context():
        admin = User(
            full_name='Admin User',
            email='adminuser@example.com',
            role='admin',
            age_range='26-35',
            city='Malang',
        )
        admin.set_password('AdminPassword123!')
        db.session.add(admin)
        db.session.commit()
        return admin
