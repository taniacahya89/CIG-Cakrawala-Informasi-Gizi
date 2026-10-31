"""Homepage and CIG food segmentation scanner."""
import base64
from pathlib import Path
from uuid import uuid4

from flask import (abort, current_app, flash, redirect, render_template, request,
                   send_file, url_for)
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.extensions import db, limiter
from app.models.content import LearningModule, ScanHistory
from app.services.food_scanner import (
    CATEGORY_COLORS, CATEGORY_LABELS, CATEGORY_ORDER, MAX_UPLOAD_BYTES,
    ModelSetupError, ScanInputError, analyze_photo, as_webp_bytes, prepare_photo,
)
from . import main_bp


@main_bp.route('/')
def index():
    """Homepage."""
    return render_template('main/index.html')


def _suggested_modules():
    terms = ('piring', 'gizi seimbang', 'sayur', 'buah', 'makan')
    matches = (LearningModule.query.filter(
        LearningModule.is_published.is_(True),
        or_(*(LearningModule.title.ilike(f'%{term}%') for term in terms))
    ).order_by(LearningModule.sort_order, LearningModule.id).limit(3).all())
    return matches or (LearningModule.query.filter_by(is_published=True)
                       .order_by(LearningModule.sort_order, LearningModule.id)
                       .limit(3).all())


def _scan_directory(user_id):
    """Private disk location; never put uploaded personal scans under static/."""
    return Path(current_app.instance_path) / 'scan_history' / f'user_{user_id}'


def _store_user_scan(original_bytes, overlay_bytes, percentages):
    """Persist both images and their DB record only after real inference succeeds."""
    folder = _scan_directory(current_user.id)
    folder.mkdir(parents=True, exist_ok=True)
    filename = uuid4().hex
    original = folder / f'{filename}_original.webp'
    overlay = folder / f'{filename}_overlay.webp'
    try:
        original.write_bytes(original_bytes)
        overlay.write_bytes(overlay_bytes)
        record = ScanHistory(
            user_id=current_user.id,
            image_path=f'user_{current_user.id}/{original.name}',
            overlay_path=f'user_{current_user.id}/{overlay.name}',
            area_percentages=percentages,
        )
        db.session.add(record)
        db.session.commit()
        return record
    except Exception:
        db.session.rollback()
        original.unlink(missing_ok=True)
        overlay.unlink(missing_ok=True)
        raise


def _private_scan_path(relative_path, user_id):
    """Restrict file reads/deletes to this user's private scan folder."""
    if not relative_path:
        return None
    root = _scan_directory(user_id).resolve()
    candidate = (Path(current_app.instance_path) / 'scan_history' / relative_path).resolve()
    if not candidate.is_relative_to(root) or candidate.suffix.lower() != '.webp':
        abort(404)
    return candidate


@main_bp.route('/scan-makanan', methods=['GET', 'POST'])
@limiter.limit('10 per hour', methods=['POST'])
def scan_makanan():
    """Upload/capture food photos and analyze with the user's real checkpoint.

    Guests: images and results stay in memory for this request only.
    Logged-in users: save real scan results to existing ScanHistory model.
    """
    result_data = None
    if request.method == 'POST':
        uploaded = request.files.get('food_image')
        if uploaded is None or not uploaded.filename:
            flash('Pilih foto makanan melalui galeri atau kamera.', 'danger')
        else:
            try:
                photo_bytes = uploaded.stream.read(MAX_UPLOAD_BYTES + 1)
                photo = prepare_photo(photo_bytes)
                overlay, percentages, pixel_count = analyze_photo(
                    photo,
                    current_app.config['SCAN_MODEL_PATH'],
                    current_app.config.get('SCAN_CLASS_MAP', ''),
                    current_app.config.get('SCAN_DEVICE', 'cpu'),
                    current_app.config.get('SCAN_IMGSZ', 640),
                )
                original_bytes = as_webp_bytes(photo)
                overlay_bytes = as_webp_bytes(overlay)
                record = None
                if current_user.is_authenticated:
                    record = _store_user_scan(original_bytes, overlay_bytes, percentages)
                    original_url = url_for('main.scan_media', scan_id=record.id, kind='original')
                    overlay_url = url_for('main.scan_media', scan_id=record.id, kind='overlay')
                else:
                    original_url = 'data:image/webp;base64,' + base64.b64encode(original_bytes).decode('ascii')
                    overlay_url = 'data:image/webp;base64,' + base64.b64encode(overlay_bytes).decode('ascii')
                result_data = {
                    'percentages': percentages,
                    'pixels': pixel_count,
                    'original_url': original_url,
                    'overlay_url': overlay_url,
                    'saved': record is not None,
                    'record_id': record.id if record else None,
                }
            except ScanInputError as exc:
                flash(str(exc), 'danger')
            except ModelSetupError as exc:
                current_app.logger.error('Scan model configuration: %s', exc)
                flash('Scanner belum siap: ' + str(exc), 'danger')
            except Exception:
                current_app.logger.exception('Food scan failed')
                flash('Pemindaian gagal. Lihat log PowerShell untuk detail teknis.', 'danger')

    colors = {k: '#%02x%02x%02x' % CATEGORY_COLORS[k] for k in CATEGORY_ORDER}
    return render_template('main/scan.html', scan=result_data, colors=colors,
                           labels=CATEGORY_LABELS, categories=CATEGORY_ORDER,
                           suggested_modules=_suggested_modules() if result_data else [])


@main_bp.get('/scan-makanan/riwayat/<int:scan_id>/<kind>')
@login_required
def scan_media(scan_id, kind):
    """Serve private scan photos only to their owner, not as public static assets."""
    record = ScanHistory.query.filter_by(id=scan_id, user_id=current_user.id).first_or_404()
    if kind not in ('original', 'overlay'):
        abort(404)
    path = _private_scan_path(record.image_path if kind == 'original' else record.overlay_path,
                              current_user.id)
    if path is None or not path.is_file():
        abort(404)
    response = send_file(path, mimetype='image/webp', conditional=False)
    response.headers['Cache-Control'] = 'private, no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@main_bp.post('/scan-makanan/riwayat/<int:scan_id>/hapus')
@login_required
def scan_delete(scan_id):
    """Authenticated, CSRF-protected deletion of a user's own scan."""
    record = ScanHistory.query.filter_by(id=scan_id, user_id=current_user.id).first_or_404()
    files = [_private_scan_path(p, current_user.id) for p in (record.image_path, record.overlay_path)]
    db.session.delete(record)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Could not delete scan row %s', scan_id)
        flash('Riwayat gagal dihapus. Silakan coba lagi.', 'danger')
        return redirect(url_for('user.meal_tracker'))
    for path in files:
        if path:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                current_app.logger.warning('Unable to delete old scan file for scan ID %s', scan_id)
    flash('Riwayat pemindaian berhasil dihapus.', 'success')
    return redirect(url_for('user.meal_tracker'))
