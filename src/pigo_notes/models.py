"""Typed application records."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Note:
    relative_path: Path

    @property
    def title(self) -> str:
        return self.relative_path.stem


@dataclass(frozen=True, slots=True)
class Task:
    source_path: Path
    line_number: int
    text: str
    completed: bool


@dataclass(frozen=True, slots=True)
class SearchResult:
    relative_path: Path
    snippet: str
