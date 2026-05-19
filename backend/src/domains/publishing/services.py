import uuid

from src.domains.agent.entities import Agent, AgentStatus, AgentType
from src.domains.agent.repository import IAgentRepository
from src.domains.publishing.aggregates import PublishingBatchAggregate
from src.domains.publishing.entities import PublishingBatch
from src.domains.publishing.repository import IPublishingRepository

_REQUIRED_FIELDS = {"name", "description", "agent_type"}


def _validate_agent_config(config: dict) -> str | None:
    """Return an error message if the config is invalid, else None."""
    missing = _REQUIRED_FIELDS - config.keys()
    if missing:
        return f"Missing required fields: {', '.join(sorted(missing))}"
    try:
        AgentType(config["agent_type"])
    except ValueError:
        return f"Invalid agent_type: {config['agent_type']}"
    wc = config.get("workflow_config", {})
    if not isinstance(wc, dict):
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
                workflow_config=config.get("workflow_config", {}),
                capabilities=config.get("capabilities", []),
                allowed_roles=config.get("allowed_roles", []),
                status=AgentStatus.PUBLISHED,
                version=config.get("version", "1.0.0"),
                created_by=batch.submitted_by,
                system_prompt_en=config.get("system_prompt_en"),
                system_prompt_zh=config.get("system_prompt_zh"),
                tools=list(config.get("tools") or []),
                max_tool_turns=int(config.get("max_tool_turns") or 3),
                llm_model=config.get("llm_model"),
                llm_temperature=config.get("llm_temperature"),
                llm_max_tokens=config.get("llm_max_tokens"),
            )

            try:
                existing_agent = await self._agent_repo.find_by_slug(slug)
                if existing_agent:
                    # Idempotent seed: keep whatever the operator has tuned in the
                    # management UI. The JSON file is a bootstrap default only.
                    aggregate.mark_item_success(index, existing_agent.id)
                    continue
                saved_agent = await self._agent_repo.save(agent)
                aggregate.mark_item_success(index, saved_agent.id)
            except Exception as exc:
                aggregate.mark_item_failed(index, str(exc))

        aggregate.finalize()
        await self._publishing_repo.update_batch(batch)
        return batch
