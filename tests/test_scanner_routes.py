"""End-to-end Flask route checks with inference stubbed; no best.pt required.

Use service tests separately for actual mask-area arithmetic.
"""
from io import BytesIO
from PIL import Image
from app.extensions import db
from app.models.content import ScanHistory


def _image_file():
    buffer = BytesIO()
    Image.new('RGB', (20, 20), color='yellow').save(buffer, 'PNG')
    buffer.seek(0)
    return buffer


def _stub_inference(monkeypatch):
    def fake_analyze(img, *args):
        return img.copy(), {'karbohidrat':50.0,'protein':50.0,'sayur':0.0,'buah':0.0}, 400
    monkeypatch.setattr('app.blueprints.main.routes.analyze_photo', fake_analyze)


def test_guest_scan_does_not_save_history(client, app, monkeypatch):
    _stub_inference(monkeypatch)
    resp = client.post('/scan-makanan', data={'food_image': (_image_file(), 'foto.png')},
                       content_type='multipart/form-data')
    assert resp.status_code == 200
    assert b'Hasil Segmentasi' in resp.data
    assert b'data:image/webp;base64' in resp.data
    with app.app_context():
        assert ScanHistory.query.count() == 0


def test_logged_in_scan_saved_private_and_owner_can_delete(client, app, standard_user, monkeypatch, tmp_path):
    app.instance_path = str(tmp_path)
    _stub_inference(monkeypatch)
    login = client.post('/auth/login', data={'email':'testuser@example.com','password':'Password123!'},
                        follow_redirects=False)
    assert login.status_code in (302,303)
    resp = client.post('/scan-makanan', data={'food_image': (_image_file(), 'foto.png')},
                       content_type='multipart/form-data')
    assert resp.status_code == 200
    with app.app_context():
        record = ScanHistory.query.one()
        scan_id = record.id
    media = client.get(f'/scan-makanan/riwayat/{scan_id}/overlay')
    assert media.status_code == 200
    assert media.mimetype == 'image/webp'
    assert media.headers['Cache-Control'] == 'private, no-store'
    deleted = client.post(f'/scan-makanan/riwayat/{scan_id}/hapus', follow_redirects=False)
    assert deleted.status_code in (302, 303)
    with app.app_context():
        assert ScanHistory.query.count() == 0
    assert client.get(f'/scan-makanan/riwayat/{scan_id}/overlay').status_code == 404


def test_bad_upload_returns_message(client):
    resp = client.post('/scan-makanan', data={'food_image': (BytesIO(b'hello'), 'x.png')},
                       content_type='multipart/form-data', follow_redirects=True)
    assert resp.status_code == 200
    assert 'Foto'.encode() in resp.data or 'foto'.encode() in resp.data


def test_other_user_cannot_access_scan(client, app, standard_user, monkeypatch, tmp_path):
    app.instance_path = str(tmp_path)
    _stub_inference(monkeypatch)
    with app.app_context():
        db.session.add(ScanHistory(user_id=standard_user.id,
            image_path='user_1/none_original.webp', overlay_path='user_1/none_overlay.webp',
            area_percentages={'buah':100.0}))
        db.session.commit()
        scan_id = ScanHistory.query.first().id
    # Guest must login, cannot access a private scan.
    assert client.get(f'/scan-makanan/riwayat/{scan_id}/original').status_code in (302, 401)
    assert client.post(f'/scan-makanan/riwayat/{scan_id}/hapus').status_code in (302, 401)
