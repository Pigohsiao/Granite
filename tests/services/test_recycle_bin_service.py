import json
from pathlib import Path

import pytest

from pigo_notes.services.recycle_bin_service import RecycleBinService


def test_target_for_allows_only_existing_items_inside_vault(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    note = vault / "Notes" / "Readme.md"
    note.parent.mkdir(parents=True)
    note.write_text("# Readme\n", encoding="utf-8")
    service = RecycleBinService(vault)

    assert service.target_for(Path("Notes/Readme.md")) == note
    with pytest.raises(ValueError):
        service.target_for(Path("../outside.md"))
    with pytest.raises(ValueError):
        service.target_for(Path("."))
    with pytest.raises(FileNotFoundError):
        service.target_for(Path("Missing.md"))


def test_recycle_uses_fixed_windows_recycle_bin_script(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vault = tmp_path / "vault"
    note = vault / "Readme.md"
    vault.mkdir()
    note.write_text("# Readme\n", encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> object:
        captured["command"] = command
        captured["kwargs"] = kwargs
        return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr("pigo_notes.services.recycle_bin_service.subprocess.run", fake_run)
    RecycleBinService(vault).move_to_recycle_bin(Path("Readme.md"), is_directory=False)

    command = captured["command"]
    assert isinstance(command, list)
    assert "SendToRecycleBin" in command[4]
    assert str(note) not in command
    assert captured["kwargs"]["capture_output"] is True
    assert captured["kwargs"]["text"] is True
    assert captured["kwargs"]["encoding"] == "utf-8"
    items = json.loads(captured["kwargs"]["env"]["PIGO_RECYCLE_ITEMS"])
    assert items == [{"path": str(note), "kind": "file"}]


def test_recycle_many_items_uses_one_powershell_process(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vault = tmp_path / "vault"
    folder = vault / "Folder"
    folder.mkdir(parents=True)
    first_note = folder / "First.md"
    second_note = vault / "Second.md"
    first_note.write_text("# First\n", encoding="utf-8")
    second_note.write_text("# Second\n", encoding="utf-8")
    calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_run(command: list[str], **kwargs: object) -> object:
        calls.append((command, kwargs))
        return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr("pigo_notes.services.recycle_bin_service.subprocess.run", fake_run)
    RecycleBinService(vault).move_many_to_recycle_bin(
        [(Path("Folder"), True), (Path("Second.md"), False)]
    )

    assert len(calls) == 1
    command, kwargs = calls[0]
    assert "SendToRecycleBin" in command[4]
    assert kwargs["env"]["PIGO_RECYCLE_ITEMS"] == json.dumps(
        [
            {"path": str(folder.resolve()), "kind": "directory"},
            {"path": str(second_note.resolve()), "kind": "file"},
        ]
    )
