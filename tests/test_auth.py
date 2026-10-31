"""Tests for authentication and user management."""

from app.extensions import db
from app.models.user import User
from app.utils.tokens import create_password_reset_token


def test_homepage_loads(client):
    """Test that homepage loads successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert 'Kenali' in response.get_data(as_text=True)
    assert 'Isi Piringku' in response.get_data(as_text=True)
    assert 'Cakrawala Informasi Gizi' in response.get_data(as_text=True)


def test_user_registration(client, app):
    """Test user registration flow."""
    response = client.post('/auth/register', data={
        'full_name': 'Ahmad Fauzi',
        'email': 'ahmad@example.com',
        'password': 'Password123!',
        'password_confirm': 'Password123!',
        'age_range': '18-25',
        'city': 'Malang',
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Pendaftaran berhasil' in response.get_data(as_text=True)

    with app.app_context():
        user = User.query.filter_by(email='ahmad@example.com').first()
        assert user is not None
        assert user.full_name == 'Ahmad Fauzi'
        assert user.role == 'user'
        assert user.check_password('Password123!') is True


def test_registration_duplicate_email(client, standard_user):
    """Test duplicate email rejection."""
    response = client.post('/auth/register', data={
        'full_name': 'Duplicate User',
        'email': 'testuser@example.com',
        'password': 'Password123!',
        'password_confirm': 'Password123!',
        'age_range': '18-25',
        'city': 'Malang',
    })

    assert response.status_code == 200
    assert 'Email sudah terdaftar' in response.get_data(as_text=True)


def test_login_and_logout(client, standard_user):
    """Test login and logout flow."""
    # Valid login
    response = client.post('/auth/login', data={
        'email': 'testuser@example.com',
        'password': 'Password123!',
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Dashboard' in response.get_data(as_text=True)

    # GET /auth/logout is rejected (Method Not Allowed)
    get_logout = client.get('/auth/logout')
    assert get_logout.status_code == 405

    # POST /auth/logout succeeds
    logout_response = client.post('/auth/logout', follow_redirects=True)
    assert logout_response.status_code == 200
    assert 'Anda telah berhasil keluar' in logout_response.get_data(as_text=True)


def test_login_invalid_credentials(client, standard_user):
    """Test login failure with wrong password."""
    response = client.post('/auth/login', data={
        'email': 'testuser@example.com',
        'password': 'WrongPassword!',
    })

    assert response.status_code == 200
    assert 'Email atau kata sandi salah' in response.get_data(as_text=True)


def test_password_reset_flow(client, app, standard_user):
    """Test complete password reset request and consumption."""
    with app.app_context():
        user = User.query.filter_by(email='testuser@example.com').first()
        token = create_password_reset_token(user)

    # Access reset form
    get_res = client.get(f'/auth/reset-password/{token}')
    assert get_res.status_code == 200
    assert 'Buat Kata Sandi Baru' in get_res.get_data(as_text=True)

    # Submit new password
    post_res = client.post(f'/auth/reset-password/{token}', data={
        'password': 'BrandNewPassword123!',
        'password_confirm': 'BrandNewPassword123!',
    }, follow_redirects=True)

    assert post_res.status_code == 200
    assert 'Kata sandi berhasil diubah' in post_res.get_data(as_text=True)

    # Login with new password
    login_res = client.post('/auth/login', data={
        'email': 'testuser@example.com',
        'password': 'BrandNewPassword123!',
    }, follow_redirects=True)
    assert login_res.status_code == 200
    assert 'Dashboard' in login_res.get_data(as_text=True)


def test_profile_update(client, app, standard_user):
    """Test updating user profile with identity verification for email change."""
    # Login first
    client.post('/auth/login', data={
        'email': 'testuser@example.com',
        'password': 'Password123!',
    })

    # Changing email without password verification is rejected
    unverified_res = client.post('/user/profile/update', data={
        'full_name': 'Updated Name',
        'email': 'updated@example.com',
        'age_range': '26-35',
        'city': 'Surabaya',
        'password_verification': '',
    }, follow_redirects=True)
    assert 'Verifikasi kata sandi saat ini diperlukan' in unverified_res.get_data(as_text=True)

    # Update profile with correct password verification succeeds
    response = client.post('/user/profile/update', data={
        'full_name': 'Updated Name',
        'email': 'updated@example.com',
        'age_range': '26-35',
        'city': 'Surabaya',
        'password_verification': 'Password123!',
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Profil berhasil diperbarui' in response.get_data(as_text=True)

    with app.app_context():
        user = User.query.filter_by(email='updated@example.com').first()
        assert user is not None
        assert user.full_name == 'Updated Name'
        assert user.city == 'Surabaya'



def test_forgot_password_request(client, app, standard_user):
    """Test requesting a password reset email."""
    response = client.post('/auth/forgot-password', data={
        'email': 'testuser@example.com',
    }, follow_redirects=True)
    assert response.status_code == 200


def test_invalid_reset_token(client):
    """Test accessing reset password with non-existent token."""
    response = client.get('/auth/reset-password/invalid-token-12345', follow_redirects=True)
    assert response.status_code == 200
    assert 'Tautan reset tidak valid' in response.get_data(as_text=True)


def test_password_change_with_verification(client, app, standard_user):
    """Test changing password from profile with verification."""
    client.post('/auth/login', data={
        'email': 'testuser@example.com',
        'password': 'Password123!',
    })

    # Wrong current password
    fail_res = client.post('/user/profile/change-password', data={
        'current_password': 'WrongOldPassword',
        'new_password': 'NewPassword123!',
        'new_password_confirm': 'NewPassword123!',
    }, follow_redirects=True)
    assert fail_res.status_code == 200
    assert 'Kata sandi saat ini salah' in fail_res.get_data(as_text=True)

    # Correct current password
    success_res = client.post('/user/profile/change-password', data={
        'current_password': 'Password123!',
        'new_password': 'NewPassword123!',
        'new_password_confirm': 'NewPassword123!',
    }, follow_redirects=True)
    assert success_res.status_code == 200
    assert 'Kata sandi berhasil diubah' in success_res.get_data(as_text=True)


def test_scanner_page(client):
    """Pastikan halaman AI Scanner menampilkan formulir upload."""
    response = client.get('/scan-makanan')
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Scan Makanan' in html
    assert 'name="food_image"' in html
    assert 'Tahap Pengembangan Berikutnya' not in html

