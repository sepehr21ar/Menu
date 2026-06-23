import bcrypt
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import SECRET_KEY

SESSION_COOKIE = "menu_session"

serializer = URLSafeTimedSerializer(SECRET_KEY)


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    password_bytes = password.encode("utf-8")
    hashed_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def sign_session(owner_id: int) -> str:
    return serializer.dumps({"owner_id": owner_id})


def verify_session(token: str, max_age: int = 60 * 60 * 24 * 7):
    try:
        data = serializer.loads(token, max_age=max_age)
        return data["owner_id"]
    except (BadSignature, SignatureExpired):
        return None
