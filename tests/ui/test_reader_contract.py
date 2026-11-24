from pathlib import Path

import pytest

from pigo_notes.services.vault_service import VaultService
from pigo_notes.ui.main_window import MainWindow


def test_open_note_reads_only_selected_file(isolated_config, qt_app, monkeypatch) -> None:
    vault = VaultService(isolated_config.vault_root)
    vault.save_note(Path("A.md"), "# A")
    vault.save_note(Path("B.md"), "# B")
    window = MainWindow(isolated_config)
    calls: list[Path] = []
    original_read = window._vault.read_note

    def track_read(path: Path) -> str:
        calls.append(path)
        return original_read(path)

    monkeypatch.setattr(window._vault, "read_note", track_read)
    window._set_current_note(Path("B.md"))

    assert calls == [Path("B.md")]
    window.close()
    qt_app.processEvents()


def test_open_note_never_scans_vault_or_finds_backlinks(isolated_config, qt_app, monkeypatch) -> None:
    VaultService(isolated_config.vault_root).save_note(Path("Note.md"), "# Note")
    window = MainWindow(isolated_config)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("opening one note must not scan the Vault")

    monkeypatch.setattr(window._vault, "list_notes", forbidden)
    monkeypatch.setattr(window._markdown, "find_backlinks", forbidden)
    window._set_current_note(Path("Note.md"))

    assert window.current_note == Path("Note.md")
    window.close()
    qt_app.processEvents()


def test_failed_open_preserves_current_preview(isolated_config, qt_app) -> None:
    VaultService(isolated_config.vault_root).save_note(Path("Current.md"), "# Current")
    window = MainWindow(isolated_config)
    window._set_current_note(Path("Current.md"))
    before_html = window.note_preview.toHtml()

    with pytest.raises(FileNotFoundError):
        window._set_current_note(Path("Missing.md"))

    assert window.current_note == Path("Current.md")
    assert window.note_preview.toHtml() == before_html
    window.close()
    qt_app.processEvents()
