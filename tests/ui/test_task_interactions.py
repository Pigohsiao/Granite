import os
from datetime import date
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from pigo_notes.config import VaultConfig
from pigo_notes.services.vault_service import VaultService
from pigo_notes.ui.main_window import MainWindow


def test_today_creates_and_opens_the_daily_note(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    config = VaultConfig(tmp_path / "app", tmp_path / "vault")
    config.app_root.mkdir(parents=True)
    config.vault_root.mkdir(parents=True)
    window = MainWindow(config)

    window.open_today(date(2026, 9, 17))

    assert window.current_note == Path("Daily Notes/2026-09-17.md")
    assert window.note_preview.toPlainText() == "2026-09-17"
    window.close()
    app.processEvents()


def test_task_panel_lists_and_toggles_markdown_tasks(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    config = VaultConfig(tmp_path / "app", tmp_path / "vault")
    config.app_root.mkdir(parents=True)
    config.vault_root.mkdir(parents=True)
    VaultService(config.vault_root).save_note(Path("Tasks.md"), "- [ ] Review notes\n")
    window = MainWindow(config)

    window.refresh_tasks()

    assert window.task_list.count() == 1
    item = window.task_list.item(0)
    item.setCheckState(Qt.CheckState.Checked)
    assert VaultService(config.vault_root).read_note(Path("Tasks.md")) == "- [x] Review notes\n"
    window.close()
    app.processEvents()
