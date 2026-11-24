import os
import json
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QAbstractItemView, QFontComboBox, QMessageBox, QToolBar, QTreeWidget

from pigo_notes.config import VaultConfig
from pigo_notes.services.vault_service import VaultService
from pigo_notes.ui.main_window import MainWindow
import pigo_notes.ui.main_window as main_window_module


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


def test_preview_font_family_is_selected_and_persisted(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    config = make_config(tmp_path)
    window = MainWindow(config)

    selector = window.findChild(QFontComboBox)
    assert selector is not None
    selected_family = selector.currentFont().family()
    window.set_preview_font_family(selected_family)

    assert window.preview_font_family == selected_family
    assert window.note_preview.font().family() == selected_family
    window.close()

    restored = MainWindow(config)
    assert restored.preview_font_family == selected_family
    assert restored.note_preview.font().family() == selected_family
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

def test_file_explorer_marks_file_and_folder_delete_targets(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    config = make_config(tmp_path)
    VaultService(config.vault_root).save_note(Path("Folder/Note.md"), "# Note\n")
    window = MainWindow(config)

    folder = window.note_tree.topLevelItem(0)
    note = folder.child(0)
    assert folder.data(0, Qt.ItemDataRole.UserRole + 1) == "folder"
    assert note.data(0, Qt.ItemDataRole.UserRole + 1) == "file"
    assert folder.data(0, Qt.ItemDataRole.UserRole) == Path("Folder")
    assert note.data(0, Qt.ItemDataRole.UserRole) == Path("Folder/Note.md")
    window.close()
    app.processEvents()


def test_selecting_vault_folder_switches_tree_clears_preview_and_persists(tmp_path: Path, monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    config = make_config(tmp_path)
    VaultService(config.vault_root).save_note(Path("Old.md"), "# Old note\n")
    new_vault = tmp_path / "new-vault"
    new_vault.mkdir()
    VaultService(new_vault).save_note(Path("New/Note.md"), "# New note\n")
    window = MainWindow(config)
    window.note_tree.setCurrentItem(window.note_tree.topLevelItem(0))
    assert window.current_note == Path("Old.md")

    monkeypatch.setattr(main_window_module.QFileDialog, "getExistingDirectory", lambda *args: str(new_vault))
    window.select_vault_action.trigger()

    assert window._config.vault_root == new_vault
    assert window.current_note is None
    assert window.note_preview.toPlainText() == ""
    assert window.note_tree.topLevelItem(0).text(0) == "New"
    settings = json.loads(window._settings_path.read_text(encoding="utf-8"))
    assert settings["vault_root"] == str(new_vault)
    window.close()
    app.processEvents()


def test_canceling_vault_folder_selection_keeps_current_vault_and_preview(tmp_path: Path, monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    config = make_config(tmp_path)
    VaultService(config.vault_root).save_note(Path("Current.md"), "# Current note\n")
    window = MainWindow(config)
    window.note_tree.setCurrentItem(window.note_tree.topLevelItem(0))
    current_preview = window.note_preview.toHtml()

    monkeypatch.setattr(main_window_module.QFileDialog, "getExistingDirectory", lambda *args: "")
    window.select_vault_action.trigger()

    assert window._config.vault_root == config.vault_root
    assert window.current_note == Path("Current.md")
    assert window.note_preview.toHtml() == current_preview
    assert window.note_tree.topLevelItem(0).text(0) == "Current.md"
    window.close()
    app.processEvents()


def test_file_explorer_supports_delete_key_and_extended_selection(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(make_config(tmp_path))

    assert window.note_tree.selectionMode() == QAbstractItemView.SelectionMode.ExtendedSelection
    assert window.delete_shortcut.key() == QKeySequence(Qt.Key.Key_Delete)
    assert window.delete_shortcut.context() == Qt.ShortcutContext.WidgetWithChildrenShortcut
    window.close()
    app.processEvents()


def test_selected_recycle_targets_drop_children_of_selected_folders(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    config = make_config(tmp_path)
    vault = VaultService(config.vault_root)
    vault.save_note(Path("Folder/Child.md"), "# Child\n")
    vault.save_note(Path("Top.md"), "# Top\n")
    window = MainWindow(config)

    folder = window.note_tree.topLevelItem(0)
    child = folder.child(0)
    top = window.note_tree.topLevelItem(1)
    folder.setSelected(True)
    child.setSelected(True)
    top.setSelected(True)

    assert window._selected_recycle_targets() == [
        (Path("Folder"), True),
        (Path("Top.md"), False),
    ]
    window.close()
    app.processEvents()


def test_delete_shortcut_confirms_and_recycles_all_selected_items(tmp_path: Path, monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    config = make_config(tmp_path)
    vault = VaultService(config.vault_root)
    vault.save_note(Path("First.md"), "# First\n")
    vault.save_note(Path("Second.md"), "# Second\n")
    window = MainWindow(config)
    first, second = window.note_tree.topLevelItem(0), window.note_tree.topLevelItem(1)
    first.setSelected(True)
    second.setSelected(True)
    calls: list[list[tuple[Path, bool]]] = []

    def recycle_many(items: list[tuple[Path, bool]]) -> None:
        calls.append(items)
        for relative_path, is_directory in items:
            target = config.vault_root / relative_path
            target.rmdir() if is_directory else target.unlink()

    monkeypatch.setattr(window._recycle_bin, "move_many_to_recycle_bin", recycle_many)
    monkeypatch.setattr(QMessageBox, "exec", lambda _dialog: QMessageBox.StandardButton.Yes)

    window.delete_shortcut.activated.emit()

    assert calls == [[(Path("First.md"), False), (Path("Second.md"), False)]]
    assert not (config.vault_root / "First.md").exists()
    assert not (config.vault_root / "Second.md").exists()
    assert window.note_tree.topLevelItemCount() == 0
    window.close()
    app.processEvents()


def test_cancelled_delete_keeps_selected_files(tmp_path: Path, monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    config = make_config(tmp_path)
    VaultService(config.vault_root).save_note(Path("Keep.md"), "# Keep\n")
    window = MainWindow(config)
    window.note_tree.topLevelItem(0).setSelected(True)
    monkeypatch.setattr(QMessageBox, "exec", lambda _dialog: QMessageBox.StandardButton.No)

    window.delete_shortcut.activated.emit()

    assert (config.vault_root / "Keep.md").exists()
    window.close()
    app.processEvents()


def test_recycle_keeps_explorer_at_deleted_row_position(tmp_path: Path, monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    config = make_config(tmp_path)
    vault = VaultService(config.vault_root)
    for index in range(60):
        vault.save_note(Path(f"Folder/Note-{index:02}.md"), f"# Note {index}\n")
    window = MainWindow(config)
    window.show()
    app.processEvents()
    folder = window.note_tree.topLevelItem(0)
    folder.setExpanded(True)
    target = folder.child(30)
    window.note_tree.scrollToItem(target, QTreeWidget.ScrollHint.PositionAtCenter)
    app.processEvents()
    target_y = window.note_tree.visualItemRect(target).top()
    scroll_before = window.note_tree.verticalScrollBar().value()

    def recycle_many(items: list[tuple[Path, bool]]) -> None:
        for relative_path, is_directory in items:
            path = config.vault_root / relative_path
            path.rmdir() if is_directory else path.unlink()

    monkeypatch.setattr(window._recycle_bin, "move_many_to_recycle_bin", recycle_many)
    monkeypatch.setattr(QMessageBox, "exec", lambda _dialog: QMessageBox.StandardButton.Yes)
    target.setSelected(True)
    window.delete_shortcut.activated.emit()
    app.processEvents()

    restored_folder = window.note_tree.topLevelItem(0)
    restored_anchor = restored_folder.child(30)
    assert restored_folder.isExpanded()
    assert restored_anchor.text(0) == "Note-31.md"
    assert abs(window.note_tree.visualItemRect(restored_anchor).top() - target_y) <= 3, (
        f"before y={target_y}, scroll={scroll_before}; "
        f"after y={window.note_tree.visualItemRect(restored_anchor).top()}, "
        f"scroll={window.note_tree.verticalScrollBar().value()}"
    )
    assert window.note_tree.verticalScrollBar().value() > 0
    window.close()
    app.processEvents()

def test_refresh_tree_can_restore_expanded_folder_paths(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    config = make_config(tmp_path)
    VaultService(config.vault_root).save_note(Path("Folder/Note.md"), "# Note\n")
    window = MainWindow(config)

    window.refresh_tree(expanded_folders={Path("Folder")})

    assert window.note_tree.topLevelItem(0).isExpanded() is True
    window.close()
    app.processEvents()


def test_copy_note_full_path_places_resolved_vault_path_on_clipboard(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    config = make_config(tmp_path)
    relative_path = Path("Folder/Note.md")
    VaultService(config.vault_root).save_note(relative_path, "# Note\n")
    window = MainWindow(config)

    window._copy_note_full_path(relative_path)

    assert QApplication.clipboard().text() == str((config.vault_root / relative_path).resolve())
    window.close()
    app.processEvents()


def test_folder_context_menu_includes_copy_full_path_action(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    config = make_config(tmp_path)
    VaultService(config.vault_root).save_note(Path("Folder/Note.md"), "# Note\n")
    window = MainWindow(config)

    menu = window._build_file_menu(Path("Folder"), "folder")

    assert [action.text() for action in menu.actions()] == [
        "複製當前檔案完整路徑",
        "移到資源回收桶",
    ]
    menu.deleteLater()
    window.close()
    app.processEvents()


def test_preview_document_has_markdown_table_styles(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(make_config(tmp_path))

    stylesheet = window.note_preview.document().defaultStyleSheet()
    assert "table" in stylesheet
    assert "border-collapse" in stylesheet

    window.close()
    app.processEvents()


def test_main_window_starts_vault_scoped_background_index(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    config = make_config(tmp_path)
    window = MainWindow(config)

    assert window._index_controller is not None
    assert window._index_controller._config.vault_root == config.vault_root
    window.close()
    app.processEvents()


def test_vault_switch_updates_background_index_session(tmp_path: Path, monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    config = make_config(tmp_path)
    new_vault = tmp_path / "new-vault"
    new_vault.mkdir()
    window = MainWindow(config)
    monkeypatch.setattr(main_window_module.QFileDialog, "getExistingDirectory", lambda *args: str(new_vault))

    window.select_vault_folder()

    assert window._index_controller._config.vault_root == new_vault
    window.close()
    app.processEvents()
