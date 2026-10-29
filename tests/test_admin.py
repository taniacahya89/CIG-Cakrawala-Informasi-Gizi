"""Tests for administrator authorization and invitations."""

from app.extensions import db
from app.models.user import User, AdminInvitation
from app.utils.tokens import create_admin_invitation


def test_standard_user_blocked_from_admin(client, standard_user):
    """Test standard user receives 403 Forbidden on admin routes."""
    client.post('/auth/login', data={
        'email': 'testuser@example.com',
        'password': 'Password123!',
    })

    response = client.get('/admin/dashboard')
    assert response.status_code == 403


def test_anonymous_redirected_from_admin(client):
    """Test unauthenticated user is redirected to login."""
    response = client.get('/admin/dashboard')
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']


def test_admin_access_dashboard(client, admin_user):
    """Test administrator can access the admin dashboard."""
    client.post('/auth/login', data={
        'email': 'adminuser@example.com',
        'password': 'AdminPassword123!',
    })

    response = client.get('/admin/dashboard')
    assert response.status_code == 200
    assert 'Panel Manajemen CIG' in response.get_data(as_text=True)


def test_admin_invitation_flow(client, app, admin_user):
    """Test creating and accepting an admin invitation."""
    with app.app_context():
        admin = User.query.filter_by(email='adminuser@example.com').first()
        token = create_admin_invitation('invited_admin@example.com', admin)

    # Access acceptance page
    get_res = client.get(f'/admin/accept-invite/{token}')
    assert get_res.status_code == 200
    assert 'Bergabung Sebagai Administrator' in get_res.get_data(as_text=True)

    # Submit acceptance
    post_res = client.post(f'/admin/accept-invite/{token}', data={
        'full_name': 'New Admin Colleague',
        'password': 'AdminPass2026!',
        'password_confirm': 'AdminPass2026!',
        'age_range': '26-35',
        'city': 'Malang',
    }, follow_redirects=True)

    assert post_res.status_code == 200
    assert 'Akun administrator berhasil dibuat' in post_res.get_data(as_text=True)

    with app.app_context():
        new_admin = User.query.filter_by(email='invited_admin@example.com').first()
        assert new_admin is not None
        assert new_admin.role == 'admin'
        assert new_admin.is_admin is True



def test_invalid_admin_invite_token(client):
    """Test accessing admin invite with non-existent token."""
    response = client.get('/admin/accept-invite/invalid-invite-token-999', follow_redirects=True)
    assert response.status_code == 200
    assert 'Tautan undangan tidak valid' in response.get_data(as_text=True)


def test_admin_invite_creation_post(client, app, admin_user):
    """Test admin creating an invitation via POST."""
    client.post('/auth/login', data={
        'email': 'adminuser@example.com',
        'password': 'AdminPassword123!',
    })

    response = client.post('/admin/invite', data={
        'email': 'newcolleague@um.ac.id',
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Undangan administrator telah dikirim' in response.get_data(as_text=True)

    with app.app_context():
        invitation = AdminInvitation.query.filter_by(email='newcolleague@um.ac.id').first()
        assert invitation is not None
        assert invitation.accepted is False


def test_admin_users_list(client, admin_user, standard_user):
    """Test administrator viewing list of all registered users."""
    client.post('/auth/login', data={
        'email': 'adminuser@example.com',
        'password': 'AdminPassword123!',
    })

    response = client.get('/admin/users')
    assert response.status_code == 200
    assert 'Manajemen Pengguna' in response.get_data(as_text=True)
    assert 'adminuser@example.com' in response.get_data(as_text=True)
    assert 'testuser@example.com' in response.get_data(as_text=True)
