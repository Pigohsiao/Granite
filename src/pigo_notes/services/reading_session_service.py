"""Small per-Vault reading history store; never writes note contents."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


class ReadingSessionService:
    MAX_RECENT = 20

    def __init__(self, app_root: Path, vault_root: Path) -> None:
        self.vault_root = vault_root.resolve()
        identity = str(vault_root.resolve()).casefold().encode("utf-8")
        digest = hashlib.sha256(identity).hexdigest()
        self.path = app_root / "app_data" / "reading" / f"{digest}.json"

    def recent(self) -> list[Path]:
        state = self._read_state()
        raw = state.get("recent", [])
        paths = [Path(item) for item in raw if self._valid(item) and self._exists(Path(item))] if isinstance(raw, list) else []
        history_raw = state.get("history", [])
        history = [item for item in history_raw if self._valid(item) and self._exists(Path(item))] if isinstance(history_raw, list) else []
        index = self._history_index(state, len(history))
        positions = state.get("positions", {})
        if not isinstance(positions, dict):
            positions = {}
        positions = {key: value for key, value in positions.items() if self._valid(key) and self._exists(Path(key))}
        clean = {**state, "recent": [path.as_posix() for path in paths[: self.MAX_RECENT]], "history": history, "history_index": index, "positions": positions}
        if clean != state:
            self._write_state(clean)
        return paths[: self.MAX_RECENT]

    def record(self, relative_path: Path) -> list[Path]:
        if not self._valid(relative_path.as_posix()) or not self._exists(relative_path):
            raise ValueError("Only existing Vault-relative Markdown paths can be recorded")
        state = self._read_state()
        history = [Path(item) for item in state.get("history", []) if self._valid(item)]
        index = self._history_index(state, len(history))
        history = history[: index + 1]
        if not history or history[-1] != relative_path:
            history.append(relative_path)
        history = history[-self.MAX_RECENT :]
        paths = [relative_path, *(path for path in self.recent() if path != relative_path)]
        paths = paths[: self.MAX_RECENT]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        state.update(
            recent=[path.as_posix() for path in paths],
            history=[path.as_posix() for path in history],
            history_index=len(history) - 1,
        )
        self._write_state(state)
        return paths

    def move_history(self, direction: int) -> Path | None:
        self.recent()  # prunes entries deleted from the Vault before choosing a destination
        state = self._read_state()
        history = [Path(item) for item in state.get("history", []) if self._valid(item)]
        index = self._history_index(state, len(history)) + direction
        if not 0 <= index < len(history):
            return None
        state["history_index"] = index
        self._write_state(state)
        return history[index]

    def set_position(self, relative_path: Path, value: int) -> None:
        state = self._read_state()
        positions = state.get("positions", {})
        if not isinstance(positions, dict):
            positions = {}
        positions[relative_path.as_posix()] = max(0, int(value))
        state["positions"] = positions
        self._write_state(state)

    def position(self, relative_path: Path) -> int:
        positions = self._read_state().get("positions", {})
        value = positions.get(relative_path.as_posix(), 0) if isinstance(positions, dict) else 0
        return max(0, value) if isinstance(value, int) else 0

    def _read_state(self) -> dict[str, object]:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _write_state(self, state: dict[str, object]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _exists(self, relative_path: Path) -> bool:
        try:
            candidate = (self.vault_root / relative_path).resolve()
            candidate.relative_to(self.vault_root)
            return candidate.is_file()
        except (OSError, ValueError):
            return False

    @staticmethod
    def _history_index(state: dict[str, object], history_length: int) -> int:
        if history_length <= 0:
            return -1
        try:
            index = int(state.get("history_index", history_length - 1))
        except (TypeError, ValueError):
            index = history_length - 1
        return min(max(0, index), history_length - 1)

    @staticmethod
    def _valid(value: object) -> bool:
        if not isinstance(value, str) or not value.strip():
            return False
        path = Path(value)
        return not path.is_absolute() and ".." not in path.parts and path.suffix.casefold() == ".md"
