import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QToolBar

from pigo_notes.config import VaultConfig
from pigo_notes.services.vault_service import VaultService
from pigo_notes.ui.main_window import MainWindow


def make_config(tmp_path: Path) -> VaultConfig:
    config = VaultConfig(app_root=tmp_path / "app", vault_root=tmp_path / "vault")
    config.app_root.mkdir(parents=True, exist_ok=True)
    config.vault_root.mkdir(parents=True, exist_ok=True)
    return config


def test_file_tree_is_nested_and_collapsed_by_default(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    config = make_config(tmp_path)
    vault = VaultService(config.vault_root)
    vault.save_note(Path("Projects/2026/Plan.md"), "# Plan\n")
    vault.save_note(Path("Projects/Overview.md"), "# Overview\n")

    window = MainWindow(config)

    projects = window.note_tree.topLevelItem(0)
    assert projects.text(0) == "Projects"
    assert projects.childCount() == 2
    assert projects.isExpanded() is False
    window.close()
    app.processEvents()


def test_focus_workspace_removes_legacy_panes_and_actions(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(make_config(tmp_path))

    assert not hasattr(window, "info_panel")
    assert hasattr(window, "note_preview")
    labels = [action.text() for action in window.findChildren(QToolBar)[0].actions()]
    assert "今天" not in labels
    assert "任務" not in labels
    assert "儲存" not in labels
    window.close()
    app.processEvents()


def test_preview_font_size_is_bounded_and_persisted(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    config = make_config(tmp_path)
    window = MainWindow(config)

    assert window.preview_font_size == 16
    window.increase_preview_font()
    assert window.preview_font_size == 17
    for _ in range(30):
        window.decrease_preview_font()
    assert window.preview_font_size == 12
    assert window.decrease_font_action.isEnabled() is False
    window.close()

    restored = MainWindow(config)
    assert restored.preview_font_size == 12
    restored.close()
    app.processEvents()

def test_focus_workspace_uses_obsidian_inspired_dark_surfaces(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(make_config(tmp_path))

    assert "#1e1f22" in window.styleSheet()
    assert "QTreeWidget" in window.styleSheet()
    window.close()
    app.processEvents()

def test_focus_workspace_exposes_a_system_drag_bar(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(make_config(tmp_path))

    assert window.drag_bar.objectName() == "dragBar"
    assert window.drag_bar.window() is window
    window.close()
    app.processEvents()


def test_theme_toggle_is_persisted(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    config = make_config(tmp_path)
    window = MainWindow(config)

    assert window.theme_mode == "dark"
    window.toggle_theme()
    assert window.theme_mode == "light"
    assert "#f7f7f5" in window.styleSheet()
    window.close()

    restored = MainWindow(config)
    assert restored.theme_mode == "light"
    restored.close()
    app.processEvents()