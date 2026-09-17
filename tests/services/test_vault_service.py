from datetime import date
from pathlib import Path

import pytest

from pigo_notes.services.vault_service import VaultService


def test_list_notes_excludes_hidden_and_system_directories(tmp_path: Path) -> None:
    (tmp_path / "Projects").mkdir()
    (tmp_path / "Projects" / "plan.md").write_text("# Plan", encoding="utf-8")
    (tmp_path / ".obsidian").mkdir()
    (tmp_path / ".obsidian" / "config.md").write_text("hidden", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "ignored.md").write_text("hidden", encoding="utf-8")

    notes = VaultService(tmp_path).list_notes()

    assert [note.relative_path.as_posix() for note in notes] == ["Projects/plan.md"]


def test_save_and_read_note_use_utf8_and_reject_paths_outside_vault(tmp_path: Path) -> None:
    service = VaultService(tmp_path)

    service.save_note(Path("中文/測試.md"), "# 你好\n內容")

    assert service.read_note(Path("中文/測試.md")) == "# 你好\n內容"
    with pytest.raises(ValueError, match="outside the Vault"):
        service.save_note(Path("../escape.md"), "no")


def test_open_or_create_daily_note_creates_then_reuses_same_file(tmp_path: Path) -> None:
    service = VaultService(tmp_path)

    created = service.open_or_create_daily_note(date(2026, 9, 17))
    reused = service.open_or_create_daily_note(date(2026, 9, 17))

    assert created == Path("Daily Notes/2026-09-17.md")
    assert reused == created
    assert (tmp_path / created).read_text(encoding="utf-8") == "# 2026-09-17\n"
