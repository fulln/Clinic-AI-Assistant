import uuid
from datetime import datetime

from src.domains.audit.entities import AuditAction, AuditLog, AuditOutcome


class AuditService:
    """Cross-cutting audit service. All writes are append-only."""

    def __init__(self, repository) -> None:
        self._repo = repository

    async def log(
        self,
        action: AuditAction,
        resource_type: str,
        outcome: AuditOutcome,
        actor_id: uuid.UUID | None = None,
        actor_role: str | None = None,
        session_id: uuid.UUID | None = None,
        resource_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        detail: dict | None = None,
    ) -> None:
        # Anonymize IP: zero the last octet (IPv4) or last group (IPv6)
        anon_ip: str | None = None
        if ip_address:
            parts = ip_address.split(".")
            if len(parts) == 4:
                anon_ip = ".".join(parts[:3] + ["0"])
            else:
                anon_ip = ip_address

        entry = AuditLog(
            action=action,
            resource_type=resource_type,
            outcome=outcome,
            actor_id=actor_id,
            actor_role=actor_role,
            session_id=session_id,
            resource_id=resource_id,
            ip_address=anon_ip,
            detail=detail or {},
        )
        await self._repo.append(entry)
