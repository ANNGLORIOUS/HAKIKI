"""Validate and sanitize uploaded evidence.

- checks the real file type from its first bytes (not the file name)
- limits size
- re-encodes images, which removes EXIF data such as GPS location
- renames files to random names so original file names never leak
"""
import io
import uuid

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError
from rest_framework.exceptions import ValidationError

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_VIDEO_BYTES = 25 * 1024 * 1024
MAX_FILES = 6
Image.MAX_IMAGE_PIXELS = 40_000_000
NON_VIDEO_BRANDS = (b"heic", b"heix", b"hevc", b"mif1", b"msf1", b"avif")


def _kind(head):
    if head.startswith(b"\xff\xd8\xff"):
        return "image"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image"
    if head[4:8] == b"ftyp" and head[8:12] not in NON_VIDEO_BRANDS:
        return "video"
    return None


def process_upload(f, allow_video=True):
    """Return (ContentFile, 'image' | 'video') or raise a friendly ValidationError."""
    head = f.read(16)
    f.seek(0)
    kind = _kind(head)
    if kind is None or (kind == "video" and not allow_video):
        raise ValidationError({"files": "Only JPG, PNG, WebP images%s are allowed." % (" and MP4 videos" if allow_video else "")})

    if kind == "video":
        if f.size > MAX_VIDEO_BYTES:
            raise ValidationError({"files": "Videos must be 25 MB or smaller."})
        return ContentFile(f.read(), name="%s.mp4" % uuid.uuid4().hex), "video"

    if f.size > MAX_IMAGE_BYTES:
        raise ValidationError({"files": "Images must be 10 MB or smaller."})
    try:
        img = Image.open(f)
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ValidationError({"files": "One of the images could not be read."})

    img = ImageOps.exif_transpose(img)
    if max(img.size) > 2400:
        img.thumbnail((2400, 2400))
    out = io.BytesIO()
    if img.mode in ("RGBA", "LA", "P"):
        img.convert("RGBA").save(out, "PNG")
        ext = "png"
    else:
        img.convert("RGB").save(out, "JPEG", quality=85, optimize=True)
        ext = "jpg"
    return ContentFile(out.getvalue(), name="%s.%s" % (uuid.uuid4().hex, ext)), "image"
