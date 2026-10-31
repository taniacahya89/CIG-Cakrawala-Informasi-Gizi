"""Validated, size-bounded image uploads for CIG managed content.

Only local files inside app/static/uploads/<type>/ are managed here.
The database is updated separately so callers can commit before deleting old media.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from uuid import uuid4
import warnings

from flask import current_app, url_for
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_PIXELS = 20_000_000
TARGET_MAX_WIDTH = 1200
TARGET_MAX_HEIGHT = 1200
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_FORMATS = {'JPEG', 'PNG', 'WEBP'}
UPLOAD_FOLDERS = {
    'module': 'uploads/modules',
    'quiz': 'uploads/quizzes',
    'recipe': 'uploads/recipes',
}


def _root():
    return Path(current_app.static_folder).resolve()


def _destination(kind):
    if kind not in UPLOAD_FOLDERS:
        raise ValueError('Jenis konten tidak didukung.')
    folder = (_root() / UPLOAD_FOLDERS[kind]).resolve()
    if not folder.is_relative_to(_root()):
        raise ValueError('Lokasi gambar tidak aman.')
    return folder


def _validate_and_load(file):
    """Read at most 5 MB and load an actual image (never trust filename alone)."""
    if file is None or not getattr(file, 'filename', ''):
        raise ValueError('Pilih gambar terlebih dahulu.')
    if Path(file.filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError('Gunakan file JPG, PNG, atau WebP.')

    try:
        file.stream.seek(0)
        payload = file.stream.read(MAX_FILE_SIZE + 1)
    except (OSError, ValueError) as exc:
        raise ValueError('Gambar tidak dapat dibaca.') from exc
    if not payload:
        raise ValueError('File gambar kosong.')
    if len(payload) > MAX_FILE_SIZE:
        raise ValueError('Ukuran gambar maksimal 5 MB.')

    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(payload)) as im:
                if im.format not in ALLOWED_FORMATS:
                    raise ValueError('Format gambar harus JPG, PNG, atau WebP.')
                if im.width * im.height > MAX_PIXELS:
                    raise ValueError('Resolusi gambar terlalu besar.')
                im.load()
                result = ImageOps.exif_transpose(im)
                # Preserve transparency against a white background.
                if result.mode in ('RGBA', 'LA') or (result.mode == 'P' and 'transparency' in result.info):
                    rgba = result.convert('RGBA')
                    bg = Image.new('RGBA', rgba.size, 'white')
                    bg.alpha_composite(rgba)
                    result = bg.convert('RGB')
                else:
                    result = result.convert('RGB')
                result.thumbnail((TARGET_MAX_WIDTH, TARGET_MAX_HEIGHT), Image.Resampling.LANCZOS)
                return result
    except ValueError:
        raise
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError('File bukan gambar valid atau resolusinya terlalu besar.') from exc


def process_and_save_image(file, kind, existing_filename=None):
    """Save a NEW unique file; leave the existing image untouched until DB commit.

    Return (success, relative_path_or_safe_error, original_name), preserving the
    application's previous API. existing_filename is accepted for compatibility.
    """
    path = None
    try:
        image = _validate_and_load(file)
        folder = _destination(kind)
        folder.mkdir(parents=True, exist_ok=True)
        filename = uuid4().hex + '.webp'
        path = folder / filename
        image.save(path, 'WEBP', quality=85, method=5)
        relative_path = f'{UPLOAD_FOLDERS[kind]}/{filename}'
        return True, relative_path, file.filename
    except ValueError as exc:
        return False, str(exc), None
    except (OSError, Image.DecompressionBombError) as exc:
        current_app.logger.exception('Image upload failed')
        if path is not None:
            path.unlink(missing_ok=True)
        return False, 'Penyimpanan gambar gagal. Periksa ruang disk dan izin folder.', None


def delete_image_file(image_path):
    """Delete only valid generated images inside approved upload folders."""
    if not isinstance(image_path, str):
        return False
    try:
        relative = Path(image_path.replace('\\', '/'))
        if relative.is_absolute() or '..' in relative.parts:
            return False
        parts = relative.parts
        if len(parts) != 3 or '/'.join(parts[:2]) not in UPLOAD_FOLDERS.values():
            return False
        # Uploaded names are always 32-character UUIDs plus .webp
        if len(relative.stem) != 32 or any(c not in '0123456789abcdef' for c in relative.stem) or relative.suffix != '.webp':
            return False
        candidate = (_root() / relative).resolve()
        if not candidate.is_relative_to(_root()):
            return False
        candidate.unlink(missing_ok=True)
        return True
    except OSError:
        current_app.logger.warning('Could not remove old image file')
        return False


def get_image_url(image_path):
    """Return static URL for an existing relative image path."""
    return url_for('static', filename=image_path) if image_path else None
