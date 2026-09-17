import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from pigo_notes.config import VaultConfig
from pigo_notes.ui.main_window import MainWindow


def test_git_menu_exposes_only_the_five_quick_actions(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    config = VaultConfig(tmp_path / "app", tmp_path / "vault")
    config.app_root.mkdir(parents=True)
    config.vault_root.mkdir(parents=True)
    window = MainWindow(config)

    assert [action.text() for action in window.git_menu.actions()] == ["Pull", "Commit", "Merge", "Push", "Branch"]
    window.close()
    app.processEvents()
