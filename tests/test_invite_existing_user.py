"""An existing account may only be upgraded when its owner is logged in."""
from app.extensions import db
from app.models.user import User
from app.utils.tokens import create_admin_invitation


def test_existing_account_invite_requires_own_login(client, app, standard_user, admin_user):
    with app.app_context():
        admin = User.query.filter_by(email='adminuser@example.com').first()
        token = create_admin_invitation('testuser@example.com', admin)

    response = client.get(f'/admin/accept-invite/{token}')
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']

    response = client.post(f'/admin/accept-invite/{token}')
    assert response.status_code == 302
    with app.app_context():
        assert User.query.filter_by(email='testuser@example.com').first().role == 'user'

    client.post('/auth/login', data={'email':'testuser@example.com','password':'Password123!'})
    response = client.post(f'/admin/accept-invite/{token}')
    assert response.status_code == 302
    with app.app_context():
        assert User.query.filter_by(email='testuser@example.com').first().role == 'admin'
