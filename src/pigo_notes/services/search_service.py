"""Case-insensitive note search."""

from pathlib import Path

from pigo_notes.models import SearchResult


class SearchService:
    def search(self, notes: dict[Path, str], query: str) -> list[SearchResult]:
        needle = query.strip().casefold()
        if not needle:
            return []
        results: list[SearchResult] = []
        for relative_path, source in notes.items():
            title_match = needle in relative_path.stem.casefold()
            content_match = needle in source.casefold()
            if title_match or content_match:
                results.append(SearchResult(relative_path, self._snippet(source, needle)))
        return sorted(results, key=lambda item: item.relative_path.as_posix().lower())

    def _snippet(self, source: str, needle: str) -> str:
        for line in source.splitlines():
            if needle in line.casefold():
                return line.strip()
        return source.splitlines()[0].strip() if source.splitlines() else ""
