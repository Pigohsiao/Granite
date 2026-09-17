"""Markdown rendering and wiki-link relationships."""

import re
from pathlib import Path

import markdown


class MarkdownService:
    _WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
    _SCRIPT = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.IGNORECASE | re.DOTALL)

    def extract_wikilinks(self, source: str) -> set[str]:
        return {match.group(1).strip() for match in self._WIKILINK.finditer(source)}

    def find_backlinks(self, notes: dict[Path, str], target: str) -> list[Path]:
        return sorted(
            (path for path, source in notes.items() if target in self.extract_wikilinks(source)),
            key=lambda path: path.as_posix().lower(),
        )

    def render(self, source: str) -> str:
        safe_source = self._SCRIPT.sub("", source)
        return markdown.markdown(safe_source, extensions=["fenced_code", "tables"])
