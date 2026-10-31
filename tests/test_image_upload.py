"""Regression coverage for admin image media and original-account safety."""
from io import BytesIO

from PIL import Image
from app.extensions import db
from app.models.content import LearningModule


def _png():
    payload = BytesIO()
    Image.new('RGB', (64, 48), '#bf2424').save(payload, 'PNG')
    payload.seek(0)
    return payload


def _login_admin(client):
    response = client.post('/auth/login', data={
        'email': 'adminuser@example.com',
        'password': 'AdminPassword123!',
    })
    assert response.status_code == 302


def test_new_content_image_upload_and_replace(client, app, admin_user, tmp_path):
    app.static_folder = str(tmp_path)
    _login_admin(client)
    response = client.post('/admin/content/module/new', data={
        'title': 'Gizi Seimbang', 'category': 'Edukasi Gizi',
        'content': 'Isi artikel', 'sort_order': '1',
        'image': (_png(), 'cover.png'),
    }, content_type='multipart/form-data')
    assert response.status_code == 302
    with app.app_context():
        row = LearningModule.query.filter_by(title='Gizi Seimbang').first()
        assert row is not None and row.image_path
        record_id = row.id
        original = row.image_path
    assert (tmp_path / original).exists()

    response = client.post(f'/admin/content/module/{record_id}/upload-image', data={
        'image': (_png(), 'updated.png'),
    }, content_type='multipart/form-data')
    assert response.status_code == 302
    with app.app_context():
        updated = db.session.get(LearningModule, record_id)
        assert updated.image_path != original
        current = updated.image_path
    assert (tmp_path / current).exists()
    assert not (tmp_path / original).exists()

    response = client.post(f'/admin/content/module/{record_id}/remove-image')
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(LearningModule, record_id).image_path is None
    assert not (tmp_path / current).exists()


def test_invalid_image_does_not_overwrite_existing(client, app, admin_user, tmp_path):
    app.static_folder = str(tmp_path)
    _login_admin(client)
    with app.app_context():
        row = LearningModule(slug='imgtest', title='Image Test', content='Isi', category='Gizi')
        db.session.add(row)
        db.session.commit()
        record_id = row.id
    response = client.post(f'/admin/content/module/{record_id}/upload-image', data={
        'image': (BytesIO(b'not-a-real-image'), 'bad.png'),
    }, content_type='multipart/form-data', follow_redirects=True)
    assert response.status_code == 200
    assert b'Gagal mengunggah gambar' in response.data
    with app.app_context():
        assert db.session.get(LearningModule, record_id).image_path is None


def test_non_admin_cannot_upload(client, app, standard_user):
    client.post('/auth/login', data={'email':'testuser@example.com','password':'Password123!'})
    response = client.post('/admin/content/module/1/upload-image', data={
        'image': (_png(), 'test.png'),
    }, content_type='multipart/form-data')
    assert response.status_code == 403
