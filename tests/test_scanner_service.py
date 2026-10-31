"""Model-independent scanner tests (do not need best.pt or Ultralytics)."""
from io import BytesIO
import numpy as np
import pytest
from PIL import Image
from app.services.food_scanner import (
    ModelSetupError, ScanInputError, CATEGORY_ORDER, analyze_photo, as_webp_bytes,
    prepare_photo, resolve_class_map, summarize_masks,
)


def _photo():
    return Image.new('RGB', (10, 10), 'white')


def test_resolve_class_names_not_numeric_guesses():
    names = {3: 'Vegetables', 2: 'fruits', 0: 'Carbohydrates', 1: 'Protein'}
    assert resolve_class_map(names) == {0:'karbohidrat',1:'protein',2:'buah',3:'sayur'}


def test_resolve_class_map_rejects_unrecognized_class():
    with pytest.raises(ModelSetupError):
        resolve_class_map({0:'class0',1:'class1',2:'class2',3:'class3'})
    mapping = resolve_class_map({0:'class0',1:'class1',2:'class2',3:'class3'},
                                '{"0":"buah","1":"protein","2":"sayur","3":"karbohidrat"}')
    assert mapping[0] == 'buah'


def test_mask_pixel_overlap_is_not_counted_twice():
    # Instance 1 covers 50 pixels; instance 2 has higher confidence and
    # overlaps by 25, replacing those pixels with class protein.
    masks = np.zeros((2,10,10), dtype=np.uint8)
    masks[0,0:5,:] = 1
    masks[1,0:5,5:10] = 1
    masks[1,5:10,0:5] = 1
    overlay, percent, pixel_count = summarize_masks(
        _photo(), masks, [0,1], [0.4,0.9], {0:'karbohidrat',1:'protein'}
    )
    assert overlay.size == (10, 10)
    assert pixel_count == 75
    assert percent == {'karbohidrat':33.3,'protein':66.7,'sayur':0.0,'buah':0.0}
    assert sum(percent.values()) == 100.0


def test_mask_resizes_using_nearest_neighbor():
    small = np.array([[[1,0],[0,0]]],dtype=np.uint8)
    _, values, count = summarize_masks(_photo(), small, [2], [0.7], {2:'sayur'})
    assert count > 0
    assert values['sayur'] == 100.0


def test_zero_detections_returns_no_fabricated_percentages():
    _, values, count = summarize_masks(_photo(), None, [], [], {})
    assert count == 0
    assert values == dict.fromkeys(CATEGORY_ORDER, 0.0)


def test_photo_validation_and_webp_roundtrip():
    buf = BytesIO()
    _photo().save(buf,format='PNG')
    parsed = prepare_photo(buf.getvalue())
    assert parsed.size == (10,10)
    assert Image.open(BytesIO(as_webp_bytes(parsed))).format == 'WEBP'
    with pytest.raises(ScanInputError):
        prepare_photo(b'not an actual image')


def test_reject_oversized_image_file():
    with pytest.raises(ScanInputError, match='5 MB'):
        prepare_photo(b'x' * (5 * 1024 * 1024 + 1))
