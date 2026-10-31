"""CIG YOLOv8 segmentation and *visual mask-area* summary.

This is NOT a nutrition, mass, volume, or calorie estimator. The denominator
is the union of the four model-detected semantic areas in image pixels.
"""
from functools import lru_cache
from io import BytesIO
from pathlib import Path
import json
import math
import re

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

CATEGORY_ORDER = ('karbohidrat', 'protein', 'sayur', 'buah')
CATEGORY_LABELS = {
    'karbohidrat': 'Karbohidrat',
    'protein': 'Protein',
    'sayur': 'Sayuran',
    'buah': 'Buah-buahan',
}
CATEGORY_COLORS = {
    'karbohidrat': (235, 156, 45),
    'protein': (198, 40, 40),
    'sayur': (27, 94, 32),
    'buah': (112, 68, 179),
}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 12_000_000
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


class ScanInputError(ValueError):
    """Invalid photo supplied by the visitor."""


class ModelSetupError(RuntimeError):
    """Model missing, incompatible, or class mapping unknown."""


def prepare_photo(data: bytes) -> Image.Image:
    """Decode an uploaded JPEG/PNG/WebP safely and orient it correctly."""
    if not data:
        raise ScanInputError('Pilih foto makanan terlebih dahulu.')
    if len(data) > MAX_UPLOAD_BYTES:
        raise ScanInputError('Ukuran foto maksimal 5 MB.')
    try:
        with Image.open(BytesIO(data)) as candidate:
            if candidate.format not in ('JPEG', 'PNG', 'WEBP'):
                raise ScanInputError('Gunakan foto berformat JPG, PNG, atau WebP.')
            if candidate.width * candidate.height > MAX_IMAGE_PIXELS:
                raise ScanInputError('Resolusi foto terlalu besar (maksimal 12 megapiksel).')
            candidate.load()
            image = ImageOps.exif_transpose(candidate).convert('RGB')
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ScanInputError('File bukan foto yang valid atau foto rusak.') from exc
    return image


def _normalize_name(value):
    return re.sub(r'[^a-z0-9]+', '', str(value).casefold())


def _guess_category(name):
    value = _normalize_name(name)
    aliases = {
        'karbohidrat': ('karbo', 'carbo', 'starch', 'karbohidrat'),
        'protein': ('protein', 'proteins'),
        'sayur': ('sayur', 'vegetab', 'veggie'),
        'buah': ('buah', 'fruit'),
    }
    matches = [category for category, terms in aliases.items() if any(t in value for t in terms)]
    if len(matches) == 1:
        return matches[0]
    return None


def resolve_class_map(names, override=''):
    """Map actual checkpoint class IDs to CIG classes; never guess numeric order.

    Override syntax: SCAN_CLASS_MAP='{"0":"karbohidrat","1":"protein",
    "2":"sayur","3":"buah"}'. Use actual IDs printed by YOLO.
    """
    if isinstance(names, (list, tuple)):
        names = dict(enumerate(names))
    if not isinstance(names, dict):
        raise ModelSetupError('Checkpoint tidak memiliki daftar nama kelas YOLO yang valid.')
    try:
        mapping = {int(k): _guess_category(v) for k, v in names.items()}
    except (ValueError, TypeError) as exc:
        raise ModelSetupError('ID kelas YOLO tidak valid.') from exc
    if override:
        try:
            explicit = json.loads(override)
            if not isinstance(explicit, dict):
                raise ValueError('JSON map must be an object')
            mapping = {int(k): str(v).strip().casefold() for k, v in explicit.items()}
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            raise ModelSetupError('SCAN_CLASS_MAP harus berupa JSON object dengan ID kelas numerik.') from exc
    if set(mapping) != {int(k) for k in names} or set(mapping.values()) != set(CATEGORY_ORDER) or len(mapping) != 4:
        safe_names = {str(k): str(v) for k, v in names.items()}
        raise ModelSetupError(
            f'Empat kelas model tidak dikenali secara unik: {safe_names}. '
            'Atur SCAN_CLASS_MAP sesuai ID hasil print(model.names).'
        )
    return mapping


@lru_cache(maxsize=2)
def _get_model(model_path: str):
    checkpoint = Path(model_path)
    if not checkpoint.is_file():
        raise ModelSetupError('Model best.pt belum ditemukan dalam folder models/yolo/.')
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise ModelSetupError('Ultralytics belum terpasang di .venv. Instal dengan pip install ultralytics.') from exc
    try:
        model = YOLO(str(checkpoint))
    except Exception as exc:
        raise ModelSetupError('Model YOLO gagal dimuat. Periksa file best.pt dan versi Ultralytics.') from exc
    if getattr(model, 'task', None) != 'segment':
        raise ModelSetupError('Model best.pt harus merupakan YOLO instance segmentation, bukan detection.')
    return model


def _largest_remainder_percentages(counts):
    total = sum(counts.values())
    if not total:
        return {k: 0.0 for k in CATEGORY_ORDER}
    raw_units = {k: counts[k] * 1000 / total for k in CATEGORY_ORDER}
    units = {k: math.floor(raw_units[k]) for k in CATEGORY_ORDER}
    remaining = 1000 - sum(units.values())
    sorted_remainder = sorted(CATEGORY_ORDER, key=lambda k: raw_units[k] - units[k], reverse=True)
    for k in sorted_remainder[:remaining]:
        units[k] += 1
    return {k: units[k] / 10 for k in CATEGORY_ORDER}


def summarize_masks(image: Image.Image, masks, classes, confidence, class_map):
    """Return RGB overlay and class proportions of uniquely assigned pixels.

    Higher-confidence instances take precedence at overlap pixels so each
    detected pixel contributes to exactly one class; percentages sum to 100.
    """
    width, height = image.size
    pixels = np.zeros((height, width), dtype=np.uint8)
    if masks is not None:
        if not (len(masks) == len(classes) == len(confidence)):
            raise ModelSetupError('Hasil segmentasi tidak konsisten antara mask dan kelas.')
        # Lower-confidence first; higher-confidence masks win overlaps.
        for i in sorted(range(len(classes)), key=lambda ix: float(confidence[ix])):
            class_id = int(classes[i])
            if class_id not in class_map:
                raise ModelSetupError('Deteksi mengandung ID kelas yang belum dipetakan.')
            binary = np.asarray(masks[i]) > 0.5
            if binary.shape != (height, width):
                binary_image = Image.fromarray(binary.astype('uint8') * 255)
                binary = np.asarray(binary_image.resize((width, height), Image.Resampling.NEAREST)) > 0
            category_index = CATEGORY_ORDER.index(class_map[class_id]) + 1
            pixels[binary] = category_index
    counts = {name: int(np.count_nonzero(pixels == ix)) for ix, name in enumerate(CATEGORY_ORDER, 1)}
    overlay_array = np.array(image.convert('RGB'), dtype=np.uint8, copy=True)
    for ix, name in enumerate(CATEGORY_ORDER, 1):
        selected = pixels == ix
        if selected.any():
            rgb = np.array(CATEGORY_COLORS[name], dtype=np.float64)
            overlay_array[selected] = np.clip(overlay_array[selected].astype(float) * 0.55 + rgb * 0.45, 0, 255).astype(np.uint8)
    return Image.fromarray(overlay_array, 'RGB'), _largest_remainder_percentages(counts), sum(counts.values())


def analyze_photo(image: Image.Image, model_path: str, class_override='', device='cpu', imgsz=640):
    """Run REAL checkpoint inference; no mock values or guessed measurements."""
    model = _get_model(str(Path(model_path).resolve()))
    class_map = resolve_class_map(model.names, class_override)
    try:
        results = model.predict(
            source=image, imgsz=int(imgsz), conf=0.25,
            device=device, retina_masks=True, verbose=False, save=False,
        )
    except Exception as exc:
        raise RuntimeError('Proses segmentasi YOLO gagal. Periksa model, driver, dan log server.') from exc
    if not results:
        raise RuntimeError('YOLO tidak mengembalikan hasil inferensi.')
    result = results[0]
    if result.masks is None or result.boxes is None:
        masks, classes, confs = None, [], []
    else:
        masks = result.masks.data.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy()
        confs = result.boxes.conf.cpu().numpy()
    return summarize_masks(image, masks, classes, confs, class_map)


def as_webp_bytes(image: Image.Image, *, quality=82):
    buffer = BytesIO()
    image.save(buffer, format='WEBP', quality=quality, method=4)
    return buffer.getvalue()
