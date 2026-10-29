"""Image upload and processing utilities for CIG content."""

import os
import uuid
from datetime import datetime
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from flask import current_app, flash


# Maximum file size: 5 MB
MAX_FILE_SIZE = 5 * 1024 * 1024

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/png',
    'image/webp',
}

# Allowed extensions
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}

# Target image dimensions (width, height) - None means no resize
# Using 1200px width for good quality while keeping file size reasonable
TARGET_MAX_WIDTH = 1200
TARGET_MAX_HEIGHT = 1200

# Upload subfolders
UPLOAD_FOLDERS = {
    'module': 'uploads/modules',
    'quiz': 'uploads/quizzes',
    'recipe': 'uploads/recipes',
}


def get_upload_folder(kind):
    """Get the upload folder path for a content type."""
    folder = UPLOAD_FOLDERS.get(kind, 'uploads')
    return os.path.join(current_app.static_folder, folder)


def ensure_upload_folder(kind):
    """Ensure the upload folder exists."""
    folder = get_upload_folder(kind)
    os.makedirs(folder, exist_ok=True)
    return folder


def allowed_file(filename):
    """Check if the file extension is allowed."""
    if not filename:
        return False
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def allowed_mime_type(file_content):
    """Check if the file content matches an allowed MIME type."""
    # Reset file pointer if needed
    if hasattr(file_content, 'seek'):
        file_content.seek(0)
    
    # Check for JPEG
    if file_content[:2] == b'\xff\xd8':
        return 'image/jpeg'
    # Check for PNG
    if file_content[:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'
    # Check for WebP
    if file_content[:4] == b'RIFF' and file_content[8:12] == b'WEBP':
        return 'image/webp'
    
    return None


def validate_image_file(file):
    """
    Validate an uploaded image file.
    
    Returns:
        tuple: (is_valid, error_message, mime_type)
    """
    # Check if file exists
    if not file:
        return False, 'Tidak ada file yang dipilih.', None
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        return False, f'File terlalu besar. Maksimal ukuran adalah 5 MB.', None
    
    if file_size == 0:
        return False, 'File kosong.', None
    
    # Read first bytes to check MIME type
    header = file.read(12)
    file.seek(0)  # Reset to beginning
    
    detected_mime = None
    # Check for JPEG
    if header[:2] == b'\xff\xd8':
        detected_mime = 'image/jpeg'
    # Check for PNG
    elif header[:8] == b'\x89PNG\r\n\x1a\n':
        detected_mime = 'image/png'
    # Check for WebP
    elif header[:4] == b'RIFF' and header[8:12] == b'WEBP':
        detected_mime = 'image/webp'
    
    if not detected_mime:
        return False, 'Format file tidak didukung. Gunakan JPEG, PNG, atau WebP.', None
    
    if detected_mime not in ALLOWED_MIME_TYPES:
        return False, 'Format file tidak diizinkan.', None
    
    # Validate image content using Pillow
    try:
        img = Image.open(file)
        # Verify it's a valid image by loading it
        img.load()
        file.seek(0)  # Reset for further processing
        return True, None, detected_mime
    except UnidentifiedImageError:
        return False, 'File bukan gambar yang valid.', None
    except Exception as e:
        return False, f'Gambar tidak dapat dibaca: {str(e)}', None


def process_and_save_image(file, kind, existing_filename=None):
    """
    Process and save an uploaded image.
    
    Args:
        file: FileStorage object from Flask
        kind: Content type ('module', 'quiz', 'recipe')
        existing_filename: Optional filename to replace (for cleanup)
    
    Returns:
        tuple: (success, relative_path_or_error_message, original_filename)
    """
    # Validate file first
    is_valid, error_msg, mime_type = validate_image_file(file)
    if not is_valid:
        return False, error_msg, None
    
    # Ensure upload folder exists
    upload_folder = ensure_upload_folder(kind)
    
    # Generate unique filename using UUID
    file_ext = '.webp'  # Convert to WebP for optimization
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    
    # Clean up old file if replacing
    if existing_filename:
        old_path = os.path.join(upload_folder, existing_filename)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass  # Ignore cleanup errors
    
    # Process the image
    try:
        img = Image.open(file)
        
        # Handle EXIF orientation
        img = _fix_exif_orientation(img)
        
        # Convert to RGB if needed (for PNG with transparency)
        if img.mode in ('RGBA', 'P'):
            # Create white background for transparency
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Resize if needed while preserving aspect ratio
        img = _resize_image(img, TARGET_MAX_WIDTH, TARGET_MAX_HEIGHT)
        
        # Save as optimized WebP
        output_path = os.path.join(upload_folder, unique_filename)
        img.save(
            output_path,
            'WEBP',
            quality=85,
            optimize=True,
        )
        
        # Generate relative path for database storage
        relative_path = os.path.join(UPLOAD_FOLDERS[kind], unique_filename).replace(os.sep, '/')
        
        return True, relative_path, file.filename
    
    except Exception as e:
        return False, f'Gagal memproses gambar: {str(e)}', None


def _fix_exif_orientation(img):
    """Fix image orientation based on EXIF data."""
    try:
        exif = img.getexif()
        if exif:
            orientation = exif.get(0x0112)  # Orientation tag
            if orientation == 3:
                img = img.rotate(180, expand=True)
            elif orientation == 6:
                img = img.rotate(270, expand=True)
            elif orientation == 8:
                img = img.rotate(90, expand=True)
            # Remove EXIF orientation to prevent re-rotation
            exif[0x0112] = 1
            img.info['exif'] = exif.tobytes()
    except (AttributeError, KeyError, IndexError):
        # No EXIF data or other issue, just return original
        pass
    return img


def _resize_image(img, max_width, max_height):
    """Resize image while preserving aspect ratio."""
    if img.width <= max_width and img.height <= max_height:
        return img
    
    # Calculate new dimensions
    ratio = min(max_width / img.width, max_height / img.height)
    new_width = int(img.width * ratio)
    new_height = int(img.height * ratio)
    
    # Use LANCZOS for high-quality downsampling
    return img.resize((new_width, new_height), Image.LANCZOS)


def delete_image_file(image_path):
    """
    Delete an image file from the filesystem.
    
    Args:
        image_path: Relative path from static folder (e.g., 'uploads/modules/abc123.webp')
    
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    if not image_path:
        return False
    
    try:
        # Resolve full path
        full_path = os.path.join(current_app.static_folder, image_path)
        
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
    except OSError:
        pass
    
    return False


def get_image_url(image_path):
    """
    Get a proper URL for an image path.
    
    Args:
        image_path: Relative path from static folder
    
    Returns:
        Flask URL or None if path is empty
    """
    if not image_path:
        return None
    
    from flask import url_for
    return url_for('static', filename=image_path)