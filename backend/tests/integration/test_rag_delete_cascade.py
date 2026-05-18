from sqlalchemy import inspect

from src.infrastructure.db.models import DocumentModel, KnowledgeBaseModel


def test_knowledge_base_documents_relationship_uses_delete_cascade() -> None:
    relationship = inspect(KnowledgeBaseModel).relationships.documents

    assert "delete" in relationship.cascade
    assert "delete-orphan" in relationship.cascade
    assert relationship.passive_deletes is True


def test_document_chunks_relationship_uses_delete_cascade() -> None:
    relationship = inspect(DocumentModel).relationships.chunks

    assert "delete" in relationship.cascade
    assert "delete-orphan" in relationship.cascade
    assert relationship.passive_deletes is True
