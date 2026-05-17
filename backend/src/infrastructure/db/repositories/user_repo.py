import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.auth.entities import User, UserRole
from src.domains.auth.repository import IUserRepository
from src.infrastructure.db.models import UserModel


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def find_by_username(self, username: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def save(self, user: User) -> User:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user.id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = UserModel(
                id=user.id,
                username=user.username,
                password_hash=user.password_hash,
                role=user.role.value,
                display_name=user.display_name,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
            self._session.add(row)
        else:
            row.username = user.username
            row.password_hash = user.password_hash
            row.role = user.role.value
            row.display_name = user.display_name
            row.is_active = user.is_active
            row.updated_at = user.updated_at
        await self._session.flush()
        return user

    @staticmethod
    def _to_domain(row: UserModel) -> User:
        return User(
            id=row.id,
            username=row.username,
            password_hash=row.password_hash,
            role=UserRole(row.role),
            display_name=row.display_name,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
