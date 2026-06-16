import base64
import hashlib
import hmac
import os
import secrets


SECRET_KEY = os.environ.get("MENU_MAKER_SECRET", "dev-change-me-menu-maker")
SESSION_COOKIE = "menu_maker_session"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"{base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_b64, digest_b64 = stored_hash.split("$", 1)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return hmac.compare_digest(digest, expected)


def sign_session(owner_id: int) -> str:
    payload = str(owner_id).encode()
    signature = hmac.new(SECRET_KEY.encode(), payload, hashlib.sha256).digest()
    return (
        base64.urlsafe_b64encode(payload).decode()
        + "."
        + base64.urlsafe_b64encode(signature).decode()
    )


def read_session(value: str | None) -> int | None:
    if not value or "." not in value:
        return None
    payload_b64, signature_b64 = value.split(".", 1)
    try:
        payload = base64.urlsafe_b64decode(payload_b64.encode())
        signature = base64.urlsafe_b64decode(signature_b64.encode())
    except ValueError:
        return None
    expected = hmac.new(SECRET_KEY.encode(), payload, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        return int(payload.decode())
    except ValueError:
        return None
