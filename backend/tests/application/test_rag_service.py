import uuid
from unittest.mock import AsyncMock, Mock

from src.application.rag_service import RAGApplicationService
from src.domains.rag.entities import KnowledgeBase


async def test_delete_kb_removes_uploaded_files() -> None:
    owner_id = uuid.uuid4()
    kb = KnowledgeBase(name="Test KB", owner_id=owner_id)
    repo = AsyncMock()
    repo.find_by_id.return_value = kb
    audit = AsyncMock()
    storage = Mock()

    service = RAGApplicationService(
        kb_repo=repo,
        audit=audit,
        file_storage=storage,
    )

    await service.delete_kb(kb.id, owner_id, "doctor")

    repo.delete_kb.assert_awaited_once_with(kb.id)
    storage.delete_kb_dir.assert_called_once_with(str(kb.id))
