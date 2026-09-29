"""Helpers for normalizing, hashing, masking and encrypting identifiers."""
import hashlib
import hmac
import re
from urllib.parse import urlparse

from cryptography.fernet import Fernet
from django.conf import settings


# ---------- encryption (sensitive values stored at rest) ----------
def _fernet() -> Fernet:
    if not settings.FIELD_ENCRYPTION_KEY:
        raise RuntimeError("FIELD_ENCRYPTION_KEY is not set")
    return Fernet(settings.FIELD_ENCRYPTION_KEY.encode())


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()


# ---------- hashing (matching without storing searchable plaintext) ----------
def hmac_hash(value: str) -> str:
    return hmac.new(settings.HMAC_SECRET.encode(), value.encode(), hashlib.sha256).hexdigest()


def mask_value(value: str) -> str:
    """0712345678 -> +254 *** 678 style display; never reveals the full value."""
    value = value.strip()
    if value.startswith("+254") and len(value) >= 7:
        return f"+254 *** {value[-3:]}"
    return f"*** {value[-3:]}" if len(value) > 3 else "***"


# ---------- Kenyan phone numbers ----------
def normalize_msisdn(raw: str) -> str:
    """Accepts 0712345678, 712345678, 254712345678, +254 712 345 678 -> +254712345678."""
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("254") and len(digits) == 12:
        return "+" + digits
    if digits.startswith("0") and len(digits) == 10:
        return "+254" + digits[1:]
    if len(digits) == 9 and digits[0] in "17":
        return "+254" + digits
    raise ValueError("Enter a valid Kenyan phone number.")


def normalize_payment_value(id_type: str, raw: str) -> str:
    if id_type == "send_money":
        return normalize_msisdn(raw)
    digits = re.sub(r"\D", "", raw or "")
    if not digits:
        raise ValueError("Enter a valid number.")
    return digits


# ---------- social handles / links ----------
SOCIAL_HOSTS = {
    "tiktok": ("tiktok.com",),
    "instagram": ("instagram.com", "instagr.am"),
    "facebook": ("facebook.com", "fb.com"),
}


def parse_social(platform: str, raw: str) -> str:
    """Return a normalized lowercase handle from a handle or profile link.

    tiktok.com/@shop, https://www.instagram.com/shop/?igsh=x, @shop  ->  'shop'
    Short links (vm.tiktok.com/...) can't be resolved offline, so we ask for the full profile link.
    """
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("Enter a handle or profile link.")

    looks_like_url = "://" in raw or "/" in raw or re.match(r"^[\w.-]+\.(com|me|am)\b", raw)
    if looks_like_url:
        parsed = urlparse(raw if "://" in raw else "https://" + raw)
        host = (parsed.hostname or "").lower()
        if host.startswith("vm.") or host.startswith("vt.") or host in ("bit.ly", "t.co"):
            raise ValueError("That looks like a short link. Please paste the full profile link or the @handle.")
        allowed = SOCIAL_HOSTS.get(platform, ())
        if allowed and not any(host == h or host.endswith("." + h) for h in allowed):
            raise ValueError(f"That link doesn't look like a {platform} link.")
        segments = [s for s in parsed.path.split("/") if s]
        if platform == "tiktok":
            segments = [s for s in segments if s.startswith("@")]
        if not segments:
            raise ValueError("Couldn't find a profile in that link.")
        handle = segments[0]
    else:
        handle = raw

    handle = handle.lstrip("@").strip().lower()
    if not re.fullmatch(r"[a-z0-9._]{1,60}", handle):
        raise ValueError("That handle contains characters we don't recognize.")
    return handle
