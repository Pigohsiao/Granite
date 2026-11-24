"""Data structures shared by the local Vault index and reader UI."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class WikiLink:
    target: str
    label: str | None = None
    fragment: str | None = None


@dataclass(frozen=True, slots=True)
class ParsedNote:
    body: str
    properties: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    wikilinks: list[WikiLink] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class TagCount:
    tag: str
    count: int


@dataclass(frozen=True, slots=True)
class SearchHit:
    relative_path: Path
    snippet: str


@dataclass(frozen=True, slots=True)
class LinkResolution:
    status: str
    candidates: tuple[Path, ...] = ()
    fragment: str | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class IndexUpdateReport:
    scanned: int = 0
    updated: int = 0
    removed: int = 0
    errors: tuple[str, ...] = ()
    cancelled: bool = False
