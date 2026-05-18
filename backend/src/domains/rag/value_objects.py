"""T084 — RAG domain value objects."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Embedding:
    values: list[float]
    dimension: int = 1536

    def __post_init__(self) -> None:
        if len(self.values) != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dimension}, "
                f"got {len(self.values)}"
            )


@dataclass(frozen=True)
class ChunkMetadata:
    page_number: int | None = None
    section_title: str | None = None

    def to_dict(self) -> dict:
        return {
            "page_number": self.page_number,
            "section_title": self.section_title,
        }
