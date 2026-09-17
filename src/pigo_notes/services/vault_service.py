"""Safe UTF-8 access to a fixed Markdown Vault."""

from datetime import date
from pathlib import Path

from pigo_notes.models import Note


class VaultService:
    _SKIPPED_DIRECTORIES = {".git", ".obsidian"}

    def __init__(self, vault_root: Path) -> None:
        self._vault_root = vault_root.resolve()

    def list_notes(self) -> list[Note]:
        notes: list[Note] = []
        for candidate in self._vault_root.rglob("*.md"):
            relative = candidate.relative_to(self._vault_root)
            if self._is_skipped(relative):
                continue
            notes.append(Note(relative))
        return sorted(notes, key=lambda note: note.relative_path.as_posix().lower())

    def read_note(self, relative_path: Path) -> str:
        return self._resolve(relative_path).read_text(encoding="utf-8")

    def save_note(self, relative_path: Path, content: str) -> None:
        target = self._resolve(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(content, encoding="utf-8", newline="")
        temporary.replace(target)

    def open_or_create_daily_note(self, note_date: date) -> Path:
        relative_path = Path("Daily Notes") / f"{note_date.isoformat()}.md"
        target = self._resolve(relative_path)
        if not target.exists():
            self.save_note(relative_path, f"# {note_date.isoformat()}\n")
        return relative_path

    def _resolve(self, relative_path: Path) -> Path:
        candidate = (self._vault_root / relative_path).resolve()
        try:
            candidate.relative_to(self._vault_root)
        except ValueError as exc:
            raise ValueError("Path is outside the Vault") from exc
        return candidate

    def _is_skipped(self, relative_path: Path) -> bool:
        return any(part.startswith(".") or part in self._SKIPPED_DIRECTORIES for part in relative_path.parts)
