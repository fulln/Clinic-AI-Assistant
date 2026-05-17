import uuid
from datetime import timedelta

from src.domains.auth.value_objects import Password, Token
from src.infrastructure.cache import redis_client


class AuthDomainService:
    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return Password.verify(plain, hashed)

    @staticmethod
    def create_access_token(user_id: uuid.UUID, role: str) -> tuple[str, str]:
        """Returns (token, jti)."""
        return Token.create_access(user_id, role)

    @staticmethod
    def create_refresh_token(user_id: uuid.UUID, device_id: str) -> str:
        return Token.create_refresh(user_id, device_id)

    @staticmethod
    async def blacklist_token(jti: str, ttl_seconds: int) -> None:
        await redis_client.set(redis_client.token_blacklist_key(jti), "1", ex=ttl_seconds)

    @staticmethod
    async def is_blacklisted(jti: str) -> bool:
        return await redis_client.get(redis_client.token_blacklist_key(jti)) is not None
