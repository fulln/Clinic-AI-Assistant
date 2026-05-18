import os
import uuid
from datetime import datetime, timedelta

import bcrypt
import jwt as _jwt


class Password:
    """Value object wrapping bcrypt operations."""

    @staticmethod
    def hash(plain: str) -> str:
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()

    @staticmethod
    def verify(plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())


class Token:
    """Value object wrapping JWT operations."""

    ALGORITHM = "HS256"

    @classmethod
    def _secret(cls) -> str:
        return os.environ["JWT_SECRET_KEY"]

    @classmethod
    def create_access(cls, user_id: uuid.UUID, role: str) -> tuple[str, str]:
        """Returns (encoded_token, jti)."""
        jti = str(uuid.uuid4())
        expire_minutes = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        payload = {
            "sub": str(user_id),
            "role": role,
            "jti": jti,
            "exp": datetime.utcnow() + timedelta(minutes=expire_minutes),
            "type": "access",
        }
        return _jwt.encode(payload, cls._secret(), algorithm=cls.ALGORITHM), jti

    @classmethod
    def create_refresh(cls, user_id: uuid.UUID, device_id: str) -> str:
        expire_days = int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        payload = {
            "sub": str(user_id),
            "device": device_id,
            "exp": datetime.utcnow() + timedelta(days=expire_days),
            "type": "refresh",
        }
        return _jwt.encode(payload, cls._secret(), algorithm=cls.ALGORITHM)

    @classmethod
    def decode(cls, token: str) -> dict:
        return _jwt.decode(token, cls._secret(), algorithms=[cls.ALGORITHM])
