import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from pigo_notes.config import VaultConfig
from pigo_notes.services.vault_service import VaultService
from pigo_notes.ui.main_window import MainWindow


def make_window(tmp_path: Path) -> MainWindow:
    config = VaultConfig(app_root=tmp_path / "app", vault_root=tmp_path / "vault")
    config.app_root.mkdir(parents=True)
    config.vault_root.mkdir(parents=True, exist_ok=True)
    return MainWindow(config)


def test_main_window_defaults_to_two_columns_and_toggles_layout(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    window = make_window(tmp_path)

    assert window.layout_mode == "two_column"
    assert not window.info_panel.isVisible()
    window.toggle_layout()
    assert window.layout_mode == "three_column"
    window.toggle_layout()
    assert window.layout_mode == "two_column"
    window.close()
    app.processEvents()


def test_selected_note_uses_read_only_preview_without_backlink_scan(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    VaultService(tmp_path / "vault").save_note(Path("Example.md"), "# Example\n\nFast preview\n")
    window = make_window(tmp_path)

    def backlink_scan_must_not_run() -> None:
        raise AssertionError("A note click must not scan backlinks across the Vault")

    window._render_backlinks = backlink_scan_must_not_run
    window._set_current_note(Path("Example.md"))

    assert not hasattr(window, "editor")
    assert "Example" in window.note_preview.toPlainText()
    assert "Fast preview" in window.note_preview.toPlainText()
    window.close()
    app.processEvents()