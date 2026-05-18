from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.audit.entities import AuditLog
from src.infrastructure.db.models import AuditLogModel


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, entry: AuditLog) -> None:
        row = AuditLogModel(
            id=entry.id,
            actor_id=entry.actor_id,
            actor_role=entry.actor_role,
            session_id=entry.session_id,
            action=entry.action.value,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            outcome=entry.outcome.value,
            ip_address=entry.ip_address,
            detail=entry.detail,
            created_at=entry.created_at,
        )
        self._session.add(row)
        await self._session.flush()
