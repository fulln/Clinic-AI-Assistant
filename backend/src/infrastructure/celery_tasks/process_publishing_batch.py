import asyncio
import uuid

from src.infrastructure.celery_app import celery_app


@celery_app.task(name="process_publishing_batch", bind=True, max_retries=3)
def process_publishing_batch(self, batch_id: str) -> dict:
    """Celery task: process a publishing batch by ID."""

    async def _run():
        from src.interfaces.api.dependencies import AsyncSessionLocal
        from src.domains.publishing.services import BatchPublishingService
        from src.infrastructure.db.repositories.agent_repo import AgentRepository
        from src.infrastructure.db.repositories.publishing_repo import PublishingRepository

        async with AsyncSessionLocal() as session:
            try:
                agent_repo = AgentRepository(session)
                publishing_repo = PublishingRepository(session)
                svc = BatchPublishingService(
                    agent_repo=agent_repo,
                    publishing_repo=publishing_repo,
                )
                batch = await svc.process_batch(
                    batch_id=uuid.UUID(batch_id),
                    items=[],  # items already persisted from submit_batch
                )
                await session.commit()
                return {
                    "batch_id": str(batch.id),
                    "status": batch.status.value,
                    "success_count": batch.success_count,
                    "failure_count": batch.failure_count,
                }
            except Exception:
                await session.rollback()
                raise

    try:
        return asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)
