import uuid

from src.domains.agent.entities import Agent, AgentStatus, AgentType
from src.domains.agent.repository import IAgentRepository
from src.domains.publishing.aggregates import PublishingBatchAggregate
from src.domains.publishing.entities import PublishingBatch
from src.domains.publishing.repository import IPublishingRepository

_REQUIRED_FIELDS = {"name", "description", "agent_type", "workflow_config"}


def _validate_agent_config(config: dict) -> str | None:
    """Return an error message if the config is invalid, else None."""
    missing = _REQUIRED_FIELDS - config.keys()
    if missing:
        return f"Missing required fields: {', '.join(sorted(missing))}"
    try:
        AgentType(config["agent_type"])
    except ValueError:
        return f"Invalid agent_type: {config['agent_type']}"
    if not isinstance(config["workflow_config"], dict):
        return "workflow_config must be a dict"
    return None


class BatchPublishingService:
    def __init__(
        self,
        agent_repo: IAgentRepository,
        publishing_repo: IPublishingRepository,
    ) -> None:
        self._agent_repo = agent_repo
        self._publishing_repo = publishing_repo

    async def process_batch(
        self,
        batch_id: uuid.UUID,
        items: list[dict],
    ) -> PublishingBatch:
        batch = await self._publishing_repo.find_batch_by_id(batch_id)
        if batch is None:
            raise ValueError(f"PublishingBatch {batch_id} not found")

        aggregate = PublishingBatchAggregate(batch)

        # Ensure items are loaded into the aggregate (they may already be from the repo)
        # If the batch already has items (persisted), use them; otherwise add from list
        if not batch.items:
            for item_config in items:
                aggregate.add_item(item_config)
            await self._publishing_repo.update_batch(batch)

        from src.domains.publishing.entities import BatchStatus
        batch.status = BatchStatus.PROCESSING
        await self._publishing_repo.update_batch(batch)

        for index, item in enumerate(batch.items):
            config = item.agent_config
            error = _validate_agent_config(config)
            if error:
                aggregate.mark_item_failed(index, error)
                continue

            slug = config.get("slug") or config["name"].lower().replace(" ", "-")

            agent = Agent(
                name=config["name"],
                slug=slug,
                description=config["description"],
                agent_type=AgentType(config["agent_type"]),
                workflow_config=config["workflow_config"],
                capabilities=config.get("capabilities", []),
                allowed_roles=config.get("allowed_roles", []),
                status=AgentStatus.PUBLISHED,
                version=config.get("version", "1.0.0"),
                created_by=batch.submitted_by,
            )

            try:
                existing_agent = await self._agent_repo.find_by_slug(slug)
                if existing_agent:
                    agent.id = existing_agent.id
                    agent.created_at = existing_agent.created_at
                    agent.created_by = existing_agent.created_by
                saved_agent = await self._agent_repo.save(agent)
                aggregate.mark_item_success(index, saved_agent.id)
            except Exception as exc:
                aggregate.mark_item_failed(index, str(exc))

        aggregate.finalize()
        await self._publishing_repo.update_batch(batch)
        return batch
