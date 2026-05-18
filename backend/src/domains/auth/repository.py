import uuid
from abc import ABC, abstractmethod

from src.domains.auth.entities import User


class IUserRepository(ABC):
    @abstractmethod
    async def find_by_id(self, user_id: uuid.UUID) -> User | None: ...

    @abstractmethod
    async def find_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    async def save(self, user: User) -> User: ...
