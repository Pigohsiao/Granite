"""Obsidian-inspired, read-only two-pane workspace for a local Markdown Vault."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QDesktopServices, QFont, QFontDatabase, QKeySequence, QMouseEvent, QShortcut, QTextDocument
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QFontComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pigo_notes.config import VaultConfig
from pigo_notes.services.markdown_service import MarkdownService
from pigo_notes.services.recycle_bin_service import RecycleBinService
from pigo_notes.services.reading_session_service import ReadingSessionService
from pigo_notes.services.vault_service import VaultService
from pigo_notes.ui.index_controller import IndexController
from pigo_notes.ui.navigation_panel import NavigationPanel


class DragBar(QWidget):
    """A visible client-area strip that starts the native system window move."""

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.window().windowHandle()
            if handle is not None and handle.startSystemMove():
                event.accept()
                return
        super().mousePressEvent(event)


class SafePreviewBrowser(QTextBrowser):
    """Reader preview that never fetches images or local/remote embedded resources."""

    def loadResource(self, resource_type: int, name: QUrl):
        if resource_type == QTextDocument.ResourceType.ImageResource:
            return None
        url = name if isinstance(name, QUrl) else QUrl(str(name))
        if url.scheme().casefold() in {"file", "http", "https", "ftp", "data", "javascript"}:
            return None
        return super().loadResource(resource_type, name)


@dataclass(frozen=True)
class _TreePosition:
    path: Path
    viewport_y: int
    scroll_value: int
    fallback_slots: tuple[tuple[Path, int], ...]


class MainWindow(QMainWindow):
    """Focused two-pane reader with a movable window and collapsed file explorer."""

    MIN_PREVIEW_FONT_SIZE = 12
    MAX_PREVIEW_FONT_SIZE = 28
    DEFAULT_PREVIEW_FONT_SIZE = 16
    DEFAULT_THEME = "dark"

    DARK_STYLESHEET = """
        QMainWindow { background: #1e1f22; color: #dcddde; }
        #dragBar { background: #17181b; border-bottom: 1px solid #34363c; }
        #dragTitle { color: #b9bbc0; font-size: 12px; font-weight: 600; }
        QToolBar { background: #191a1d; border: 0; border-bottom: 1px solid #34363c; spacing: 4px; padding: 5px 7px; }
        QToolButton, QPushButton { color: #c9cbd0; background: transparent; border: 0; border-radius: 4px; padding: 5px 8px; }
        QToolButton:hover, QPushButton:hover { background: #303239; color: #ffffff; }
        QTreeWidget { background: #191a1d; color: #c9cbd0; border: 0; border-right: 1px solid #34363c; outline: 0; }
        QTreeWidget::header { background: #191a1d; color: #999ca4; border: 0; border-bottom: 1px solid #2e3035; padding: 8px; font-weight: 600; }
        QTreeWidget::item { height: 27px; border-radius: 3px; padding-left: 3px; }
        QTreeWidget::item:hover { background: #2a2c31; }
        QTreeWidget::item:selected { background: #353141; color: #f0edff; border-left: 2px solid #a78bfa; }
        QTextBrowser { background: #242529; color: #dcddde; border: 0; padding: 26px 56px; selection-background-color: #5d557d; }
        QScrollBar:vertical { background: #1e1f22; width: 10px; margin: 0; }
        QScrollBar::handle:vertical { background: #42454c; min-height: 26px; border-radius: 4px; }
    """

    LIGHT_STYLESHEET = """
        QMainWindow { background: #f7f7f5; color: #27282b; }
        #dragBar { background: #eeeeeb; border-bottom: 1px solid #d5d5d0; }
        #dragTitle { color: #55575c; font-size: 12px; font-weight: 600; }
        QToolBar { background: #f0f0ed; border: 0; border-bottom: 1px solid #d5d5d0; spacing: 4px; padding: 5px 7px; }
        QToolButton, QPushButton { color: #4a4c52; background: transparent; border: 0; border-radius: 4px; padding: 5px 8px; }
        QToolButton:hover, QPushButton:hover { background: #dddde0; color: #16171a; }
        QTreeWidget { background: #f0f0ed; color: #3a3b40; border: 0; border-right: 1px solid #d5d5d0; outline: 0; }
        QTreeWidget::header { background: #f0f0ed; color: #76777c; border: 0; border-bottom: 1px solid #d5d5d0; padding: 8px; font-weight: 600; }
        QTreeWidget::item { height: 27px; border-radius: 3px; padding-left: 3px; }
        QTreeWidget::item:hover { background: #e1e1e3; }
        QTreeWidget::item:selected { background: #e5defa; color: #302b45; border-left: 2px solid #8064d8; }
        QTextBrowser { background: #f7f7f5; color: #27282b; border: 0; padding: 26px 56px; selection-background-color: #c9bdf1; }
        QScrollBar:vertical { background: #f7f7f5; width: 10px; margin: 0; }
        QScrollBar::handle:vertical { background: #c5c5c7; min-height: 26px; border-radius: 4px; }
    """

    DARK_PREVIEW_CSS = """
        body { color: #dcddde; line-height: 1.6; }
        h1, h2, h3 { color: #f0edff; margin-top: 1.2em; }
        h1 { border-bottom: 1px solid #4a4c54; padding-bottom: 0.3em; }
        table { border-collapse: collapse; margin: 1em 0; }
        th, td { border: 1px solid #4a4c54; padding: 6px 10px; }
        th { background: #303239; }
        blockquote { border-left: 3px solid #a78bfa; color: #b9bbc0; margin-left: 0; padding-left: 12px; }
        hr { border: 0; border-top: 1px solid #4a4c54; }
        code { background: #303239; color: #f0edff; }
        pre { background: #191a1d; border: 1px solid #34363c; padding: 12px; }
    """

    LIGHT_PREVIEW_CSS = """
        body { color: #27282b; line-height: 1.6; }
        h1, h2, h3 { color: #27282b; margin-top: 1.2em; }
        h1 { border-bottom: 1px solid #d5d5d0; padding-bottom: 0.3em; }
        table { border-collapse: collapse; margin: 1em 0; }
        th, td { border: 1px solid #c5c5c7; padding: 6px 10px; }
        th { background: #eeeeeb; }
        blockquote { border-left: 3px solid #8064d8; color: #55575c; margin-left: 0; padding-left: 12px; }
        hr { border: 0; border-top: 1px solid #d5d5d0; }
        code { background: #eeeeeb; color: #27282b; }
        pre { background: #f0f0ed; border: 1px solid #d5d5d0; padding: 12px; }
    """

    def __init__(self, config: VaultConfig) -> None:
        super().__init__()
        self._config = config
        self._vault = VaultService(config.vault_root)
        self._markdown = MarkdownService()
        self._recycle_bin = RecycleBinService(config.vault_root)
        self._current_note: Path | None = None
        self._settings_path = config.app_root / "app_data" / "settings.json"
        settings = self._load_settings()
        self.preview_font_size = self._bounded_font_size(settings.get("preview_font_size", self.DEFAULT_PREVIEW_FONT_SIZE))
        self.preview_font_family = self._validated_preview_font_family(
            settings.get("preview_font_family", QApplication.font().family())
        )
        self.theme_mode = settings.get("theme_mode", self.DEFAULT_THEME)
        if self.theme_mode not in {"dark", "light"}:
            self.theme_mode = self.DEFAULT_THEME

        self.setWindowTitle("Pigo Notes App")
        self.resize(1180, 780)
        self._build_drag_bar()
        self._build_workspace()
        self._build_toolbar()
        self._apply_theme(persist=False)
        self.set_preview_font_size(self.preview_font_size, persist=False)
        self.set_preview_font_family(self.preview_font_family, persist=False)
        self._index_controller = IndexController(config)
        self._index_controller.statusChanged.connect(self.statusBar().showMessage)
        self._index_controller.searchFinished.connect(self._search_finished)
        self._index_controller.contextFinished.connect(self._note_context_finished)
        self._index_controller.tagsFinished.connect(self._tags_finished)
        self._index_controller.refreshFinished.connect(self._refresh_finished)
        self.navigation_panel.tagsRequested.connect(self._index_controller.request_tags)
        self._reading_session = ReadingSessionService(config.app_root, config.vault_root)
        self.navigation_panel.set_recent(self._reading_session.recent())
        self._update_history_actions()
        self._search_offset = 0
        self.refresh_tree()
        self._index_controller.start_vault(config)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._position_save_timer.stop()
        self._save_preview_position()
        controller = getattr(self, "_index_controller", None)
        if controller is not None:
            controller.shutdown()
        super().closeEvent(event)

    @property
    def current_note(self) -> Path | None:
        return self._current_note

    def show_for_user(self) -> None:
        """Open as a normal, movable Windows window instead of maximized."""
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _build_drag_bar(self) -> None:
        self.drag_bar = DragBar(self)
        self.drag_bar.setObjectName("dragBar")
        layout = QHBoxLayout(self.drag_bar)
        layout.setContentsMargins(12, 4, 8, 4)
        title = QLabel("Pigo Notes App  •  拖曳這裡移動整個視窗")
        title.setObjectName("dragTitle")
        layout.addWidget(title)
        layout.addStretch()
        self.theme_button = QPushButton(self.drag_bar)
        self.theme_button.setToolTip("切換明亮／黑暗模式")
        self.theme_button.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_button)
        self.setMenuWidget(self.drag_bar)

    def _build_workspace(self) -> None:
        self.note_tree = QTreeWidget()
        self.note_tree.setHeaderLabel("檔案總管")
        self.note_tree.setIndentation(18)
        self.note_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.note_tree.itemSelectionChanged.connect(self._open_selected_note)
        self.note_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.note_tree.customContextMenuRequested.connect(self._show_file_menu)
        self.delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self.note_tree)
        self.delete_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.delete_shortcut.activated.connect(self._confirm_selected_recycle)

        self.note_preview = SafePreviewBrowser()
        self.note_preview.setOpenExternalLinks(False)
        self.note_preview.anchorClicked.connect(self._route_preview_link)
        self.note_preview.setPlaceholderText("選擇一篇 Markdown 筆記開始預覽")

        self.note_details = QWidget()
        details_layout = QVBoxLayout(self.note_details)
        details_layout.setContentsMargins(8, 4, 8, 8)
        self.note_details.backlinks_group = QGroupBox("反向連結（最多 100 篇）")
        self.note_details.backlinks_group.setCheckable(True)
        self.note_details.backlinks_group.setChecked(False)
        backlinks_layout = QVBoxLayout(self.note_details.backlinks_group)
        self.note_details.backlink_list = QListWidget()
        self.note_details.backlink_list.itemActivated.connect(self._open_backlink_item)
        backlinks_layout.addWidget(self.note_details.backlink_list)
        self.note_details.backlinks_group.toggled.connect(
            lambda checked: self._set_group_contents_visible(self.note_details.backlinks_group, checked)
        )
        self._set_group_contents_visible(self.note_details.backlinks_group, False)
        details_layout.addWidget(self.note_details.backlinks_group)
        self.note_details.properties_group = QGroupBox("Properties")
        self.note_details.properties_group.setCheckable(True)
        self.note_details.properties_group.setChecked(False)
        properties_layout = QVBoxLayout(self.note_details.properties_group)
        self.note_details.properties_text = QLabel("選取筆記後顯示唯讀屬性")
        self.note_details.properties_text.setWordWrap(True)
        properties_layout.addWidget(self.note_details.properties_text)
        details_layout.addWidget(self.note_details.properties_group)
        self.note_details.properties_group.toggled.connect(
            lambda checked: self._set_group_contents_visible(self.note_details.properties_group, checked)
        )
        self._set_group_contents_visible(self.note_details.properties_group, False)

        self.reader_pane = QWidget()
        reader_layout = QVBoxLayout(self.reader_pane)
        reader_layout.setContentsMargins(0, 0, 0, 0)
        reader_layout.setSpacing(0)
        reader_layout.addWidget(self.note_preview, 1)
        reader_layout.addWidget(self.note_details)
        self._position_save_timer = QTimer(self)
        self._position_save_timer.setSingleShot(True)
        self._position_save_timer.setInterval(300)
        self._position_save_timer.timeout.connect(self._save_preview_position)
        self.note_preview.verticalScrollBar().valueChanged.connect(lambda _value: self._position_save_timer.start())

        self.navigation_panel = NavigationPanel(self.note_tree)
        self.navigation_panel.searchRequested.connect(self._run_search)
        self.navigation_panel.resultActivated.connect(self._open_search_result)
        self.workspace = QSplitter(Qt.Orientation.Horizontal)
        self.workspace.addWidget(self.navigation_panel)
        self.workspace.addWidget(self.reader_pane)
        self.workspace.setSizes([300, 880])
        self.setCentralWidget(self.workspace)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("工具列")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.back_action = QAction("←", self)
        self.back_action.setToolTip("返回上一個閱讀位置")
        self.back_action.triggered.connect(lambda: self._move_reading_history(-1))
        toolbar.addAction(self.back_action)
        self.forward_action = QAction("→", self)
        self.forward_action.setToolTip("前往下一個閱讀位置")
        self.forward_action.triggered.connect(lambda: self._move_reading_history(1))
        toolbar.addAction(self.forward_action)

        refresh = QAction("↻", self)
        refresh.setToolTip("重新掃描檔案樹")
        refresh.triggered.connect(self.refresh_tree)
        toolbar.addAction(refresh)

        self.select_vault_action = QAction("📂", self)
        self.select_vault_action.setToolTip("選擇 Vault 資料夾")
        self.select_vault_action.triggered.connect(self.select_vault_folder)
        toolbar.addAction(self.select_vault_action)

        self.decrease_font_action = QAction("A−", self)
        self.decrease_font_action.setToolTip("縮小閱讀字型")
        self.decrease_font_action.triggered.connect(self.decrease_preview_font)
        toolbar.addAction(self.decrease_font_action)

        self.increase_font_action = QAction("A＋", self)
        self.increase_font_action.setToolTip("放大閱讀字型")
        self.increase_font_action.triggered.connect(self.increase_preview_font)
        toolbar.addAction(self.increase_font_action)

        self.preview_font_selector = QFontComboBox(toolbar)
        self.preview_font_selector.setToolTip("選擇右側預覽字型")
        self.preview_font_selector.setMaximumWidth(180)
        self.preview_font_selector.setCurrentFont(QFont(self.preview_font_family))
        self.preview_font_selector.currentFontChanged.connect(
            lambda font: self.set_preview_font_family(font.family())
        )
        toolbar.addWidget(self.preview_font_selector)

    def select_vault_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "選擇 Vault 資料夾",
            str(self._config.vault_root),
        )
        if not selected:
            return
        new_root = Path(selected)
        if not new_root.is_dir():
            return
        if new_root == self._config.vault_root:
            return

        self._config = VaultConfig(app_root=self._config.app_root, vault_root=new_root)
        self._vault = VaultService(new_root)
        self._recycle_bin = RecycleBinService(new_root)
        self._current_note = None
        self.note_preview.clear()
        self.refresh_tree()
        self.navigation_panel.clear_results()
        self._index_controller.start_vault(self._config)
        self._reading_session = ReadingSessionService(self._config.app_root, self._config.vault_root)
        self.navigation_panel.set_recent(self._reading_session.recent())
        self._save_settings()

    def refresh_tree(
        self,
        *,
        expanded_folders: set[Path] | None = None,
        tree_position: _TreePosition | None = None,
    ) -> None:
        self.note_tree.clear()
        folders: dict[Path, QTreeWidgetItem] = {}
        items_by_path: dict[Path, QTreeWidgetItem] = {}
        for note in self._vault.list_notes():
            parent = self._ensure_folder(note.relative_path.parent, folders)
            items_by_path.update(folders)
            item = QTreeWidgetItem([note.relative_path.name])
            item.setData(0, Qt.ItemDataRole.UserRole, note.relative_path)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, "file")
            items_by_path[note.relative_path] = item
            if parent is None:
                self.note_tree.addTopLevelItem(item)
            else:
                parent.addChild(item)
        self.note_tree.collapseAll()
        for folder in expanded_folders or set():
            item = folders.get(folder)
            if item is not None:
                item.setExpanded(True)
        if tree_position is not None:
            self._restore_tree_position(tree_position, items_by_path)

    def _ensure_folder(self, folder: Path, folders: dict[Path, QTreeWidgetItem]) -> QTreeWidgetItem | None:
        if folder == Path("."):
            return None
        if folder in folders:
            return folders[folder]
        parent = self._ensure_folder(folder.parent, folders)
        item = QTreeWidgetItem([folder.name])
        item.setData(0, Qt.ItemDataRole.UserRole, folder)
        item.setData(0, Qt.ItemDataRole.UserRole + 1, "folder")
        item.setExpanded(False)
        if parent is None:
            self.note_tree.addTopLevelItem(item)
        else:
            parent.addChild(item)
        folders[folder] = item
        return item

    def increase_preview_font(self) -> None:
        self.set_preview_font_size(self.preview_font_size + 1)

    def decrease_preview_font(self) -> None:
        self.set_preview_font_size(self.preview_font_size - 1)

    def set_preview_font_size(self, size: int, *, persist: bool = True) -> None:
        self.preview_font_size = self._bounded_font_size(size)
        self.note_preview.setStyleSheet(f"QTextBrowser {{ font-size: {self.preview_font_size}px; }}")
        self.decrease_font_action.setEnabled(self.preview_font_size > self.MIN_PREVIEW_FONT_SIZE)
        self.increase_font_action.setEnabled(self.preview_font_size < self.MAX_PREVIEW_FONT_SIZE)
        if persist:
            self._save_settings()

    def set_preview_font_family(self, family: object, *, persist: bool = True) -> None:
        self.preview_font_family = self._validated_preview_font_family(family)
        font = self.note_preview.font()
        font.setFamily(self.preview_font_family)
        self.note_preview.setFont(font)
        if self.preview_font_selector.currentFont().family() != self.preview_font_family:
            self.preview_font_selector.setCurrentFont(QFont(self.preview_font_family))
        if persist:
            self._save_settings()

    def toggle_theme(self) -> None:
        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
        self._apply_theme(persist=True)

    def _apply_theme(self, *, persist: bool) -> None:
        self.setStyleSheet(self.LIGHT_STYLESHEET if self.theme_mode == "light" else self.DARK_STYLESHEET)
        self.note_preview.document().setDefaultStyleSheet(
            self.LIGHT_PREVIEW_CSS if self.theme_mode == "light" else self.DARK_PREVIEW_CSS
        )
        self.theme_button.setText("☾" if self.theme_mode == "dark" else "☀")
        if persist:
            self._save_settings()

    def _show_file_menu(self, position: object) -> None:
        item = self.note_tree.itemAt(position)
        if item is None:
            return
        relative_path = item.data(0, Qt.ItemDataRole.UserRole)
        item_kind = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if item_kind not in {"file", "folder"} or not isinstance(relative_path, Path):
            return
        menu = self._build_file_menu(relative_path, item_kind)
        menu.exec(self.note_tree.viewport().mapToGlobal(position))

    def _build_file_menu(self, relative_path: Path, item_kind: str) -> QMenu:
        menu = QMenu(self)
        copy_path_action = menu.addAction("複製當前檔案完整路徑")
        copy_path_action.triggered.connect(lambda: self._copy_note_full_path(relative_path))
        recycle_action = menu.addAction("移到資源回收桶")
        recycle_action.triggered.connect(lambda: self._confirm_recycle(relative_path, item_kind == "folder"))
        return menu

    def _copy_note_full_path(self, relative_path: Path) -> None:
        vault_root = self._config.vault_root.resolve()
        target = (vault_root / relative_path).resolve()
        try:
            target.relative_to(vault_root)
        except ValueError:
            QMessageBox.warning(self, "無法複製路徑", "檔案路徑不在目前 Vault 內。")
            return
        QApplication.clipboard().setText(str(target))
        self.statusBar().showMessage("已複製完整檔案路徑", 3000)

    def _confirm_recycle(self, relative_path: Path, is_directory: bool) -> None:
        item = self._tree_item_for_path(relative_path)
        self._confirm_recycle_targets([(relative_path, is_directory)], anchor_item=item)

    def _confirm_selected_recycle(self) -> None:
        selected = self.note_tree.selectedItems()
        if not selected:
            return

        selected_targets = self._selected_recycle_targets()
        current_item = self.note_tree.currentItem()
        anchor_item = current_item if current_item in selected else selected[0]
        self._confirm_recycle_targets(selected_targets, anchor_item=anchor_item)

    def _selected_recycle_targets(self) -> list[tuple[Path, bool]]:
        selected: list[tuple[Path, bool]] = []
        selected_folders: set[Path] = set()
        for item in self.note_tree.selectedItems():
            relative_path = item.data(0, Qt.ItemDataRole.UserRole)
            kind = item.data(0, Qt.ItemDataRole.UserRole + 1)
            if not isinstance(relative_path, Path) or kind not in {"file", "folder"}:
                continue
            is_directory = kind == "folder"
            selected.append((relative_path, is_directory))
            if is_directory:
                selected_folders.add(relative_path)
        return [
            (path, is_directory)
            for path, is_directory in selected
            if not any(parent != path and parent in path.parents for parent in selected_folders)
        ]

    def _confirm_recycle_targets(
        self,
        targets: list[tuple[Path, bool]],
        *,
        anchor_item: QTreeWidgetItem | None = None,
    ) -> None:
        if not targets:
            return
        details = "\n".join(
            f"{'[資料夾]' if is_directory else '[檔案]'} {path.as_posix()}"
            for path, is_directory in targets
        )
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle("移到資源回收桶")
        dialog.setText(f"確定將選取的 {len(targets)} 個項目移到 Windows 資源回收桶？")
        dialog.setInformativeText(details)
        dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        dialog.setDefaultButton(QMessageBox.StandardButton.No)
        if dialog.exec() != QMessageBox.StandardButton.Yes:
            return

        expanded_folders = self._expanded_folder_paths()
        if anchor_item is None:
            anchor_item = self._tree_item_for_path(targets[0][0])
        tree_position = self._capture_tree_position(anchor_item) if anchor_item is not None else None
        error: Exception | None = None
        try:
            self._recycle_bin.move_many_to_recycle_bin(targets)
        except (FileNotFoundError, OSError, RuntimeError, ValueError) as caught_error:
            error = caught_error
        if self._current_note is not None and not (self._config.vault_root / self._current_note).exists():
            self._current_note = None
            self.note_preview.clear()
        self.refresh_tree(expanded_folders=expanded_folders, tree_position=tree_position)
        if error is not None:
            QMessageBox.warning(self, "無法完整移到資源回收桶", str(error))

    def _tree_item_for_path(self, path: Path) -> QTreeWidgetItem | None:
        matches = self.note_tree.findItems(
            path.name,
            Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive,
            0,
        )
        for item in matches:
            if item.data(0, Qt.ItemDataRole.UserRole) == path:
                return item
        return None

    def _capture_tree_position(self, item: QTreeWidgetItem) -> _TreePosition:
        path = item.data(0, Qt.ItemDataRole.UserRole)
        fallback_slots: list[tuple[Path, int]] = []
        child = item
        while True:
            parent = child.parent()
            if parent is None:
                fallback_slots.append((Path("."), self.note_tree.indexOfTopLevelItem(child)))
                break
            parent_path = parent.data(0, Qt.ItemDataRole.UserRole)
            fallback_slots.append((parent_path, parent.indexOfChild(child)))
            child = parent
        return _TreePosition(
            path=path,
            viewport_y=self.note_tree.visualItemRect(item).top(),
            scroll_value=self.note_tree.verticalScrollBar().value(),
            fallback_slots=tuple(fallback_slots),
        )

    def _restore_tree_position(
        self,
        position: _TreePosition,
        items_by_path: dict[Path, QTreeWidgetItem],
    ) -> None:
        item = items_by_path.get(position.path)
        if item is None:
            for parent_path, sibling_index in position.fallback_slots:
                parent_item = items_by_path.get(parent_path) if parent_path != Path(".") else None
                if parent_path != Path(".") and parent_item is None:
                    continue
                child_count = parent_item.childCount() if parent_item is not None else self.note_tree.topLevelItemCount()
                if child_count:
                    index = min(sibling_index, child_count - 1)
                    item = parent_item.child(index) if parent_item is not None else self.note_tree.topLevelItem(index)
                    break
                if parent_item is not None:
                    item = parent_item
                    break
        if item is None:
            return

        parent = item.parent()
        while parent is not None:
            parent.setExpanded(True)
            parent = parent.parent()
        self.note_tree.scrollToItem(item, QTreeWidget.ScrollHint.EnsureVisible)
        self.note_tree.doItemsLayout()
        if 0 <= position.viewport_y < self.note_tree.viewport().height():
            item_rect = self.note_tree.visualItemRect(item)
            pixel_delta = item_rect.top() - position.viewport_y
            row_height = max(item_rect.height(), 1)
            scroll_delta = round(pixel_delta / row_height)
            self.note_tree.verticalScrollBar().setValue(
                self.note_tree.verticalScrollBar().value() + scroll_delta
            )
        else:
            self.note_tree.verticalScrollBar().setValue(position.scroll_value)

    def _expanded_folder_paths(self) -> set[Path]:
        expanded: set[Path] = set()

        def visit(item: QTreeWidgetItem) -> None:
            if item.data(0, Qt.ItemDataRole.UserRole + 1) == "folder" and item.isExpanded():
                relative_path = item.data(0, Qt.ItemDataRole.UserRole)
                if isinstance(relative_path, Path):
                    expanded.add(relative_path)
            for index in range(item.childCount()):
                visit(item.child(index))

        for index in range(self.note_tree.topLevelItemCount()):
            visit(self.note_tree.topLevelItem(index))
        return expanded
    def _open_selected_note(self) -> None:
        selected = self.note_tree.selectedItems()
        if not selected:
            return
        relative_path = selected[0].data(0, Qt.ItemDataRole.UserRole)
        item_kind = selected[0].data(0, Qt.ItemDataRole.UserRole + 1)
        if item_kind == "file" and isinstance(relative_path, Path):
            self._set_current_note(relative_path)

    def _set_current_note(self, relative_path: Path, *, expand_tree: bool = True, record_history: bool = True) -> None:
        if self._current_note is not None:
            self._reading_session.set_position(
                self._current_note, self.note_preview.verticalScrollBar().value()
            )
        content = self._vault.read_note(relative_path)
        self._current_note = relative_path
        self.note_preview.setHtml(self._markdown.render(content))
        if record_history:
            self._reading_session.record(relative_path)
        self.navigation_panel.set_recent(self._reading_session.recent())
        QTimer.singleShot(0, lambda: self.note_preview.verticalScrollBar().setValue(self._reading_session.position(relative_path)))
        self._update_history_actions()
        if expand_tree:
            self._expand_note_ancestors(relative_path)
        self._index_controller.request_note_context(relative_path, source=content)

    def _save_preview_position(self) -> None:
        if self._current_note is not None and hasattr(self, "_reading_session"):
            self._reading_session.set_position(self._current_note, self.note_preview.verticalScrollBar().value())

    def _move_reading_history(self, direction: int) -> None:
        path = self._reading_session.move_history(direction)
        if path is None:
            return
        try:
            self._set_current_note(path, record_history=False)
        except (OSError, UnicodeError, ValueError):
            self.statusBar().showMessage("閱讀歷史中的筆記已不存在")
        self._update_history_actions()

    def _update_history_actions(self) -> None:
        if not hasattr(self, "back_action"):
            return
        state = self._reading_session._read_state()
        history = state.get("history", [])
        index = state.get("history_index", -1)
        self.back_action.setEnabled(isinstance(index, int) and index > 0)
        self.forward_action.setEnabled(isinstance(history, list) and isinstance(index, int) and index < len(history) - 1)

    def _route_preview_link(self, url: QUrl) -> None:
        scheme = url.scheme().casefold()
        if scheme in {"http", "https"}:
            if url.isValid() and url.host() and not url.userName() and not url.password():
                QDesktopServices.openUrl(url)
            else:
                self.statusBar().showMessage("拒絕無效的外部連結")
            return
        if scheme != "pigo-note" or url.host().casefold() != "open":
            self.statusBar().showMessage("拒絕不安全的連結")
            return
        encoded = url.path(QUrl.ComponentFormattingOption.FullyEncoded).lstrip("/")
        try:
            target = unquote(encoded, errors="strict")
        except (UnicodeDecodeError, ValueError):
            self.statusBar().showMessage("拒絕無效的筆記連結")
            return
        if self._current_note is None:
            self.statusBar().showMessage("請先開啟一篇筆記")
            return
        try:
            resolution = self._index_controller.resolve_link(self._current_note, target)
        except (OSError, ValueError, RuntimeError, sqlite3.Error) as error:
            self.statusBar().showMessage(f"無法解析筆記連結：{error}")
            return
        if resolution.status == "rejected":
            self.statusBar().showMessage("拒絕不安全的筆記路徑")
            return
        if resolution.status == "missing":
            self.statusBar().showMessage("找不到這篇筆記")
            return
        if resolution.status == "ambiguous":
            choices = [path.as_posix() for path in resolution.candidates]
            choice, accepted = QInputDialog.getItem(self, "選擇筆記", "找到多篇同名筆記：", choices, 0, False)
            if not accepted or choice not in choices:
                return
            resolved = resolution.candidates[choices.index(choice)]
        else:
            resolved = resolution.candidates[0]
        try:
            self._set_current_note(resolved)
            if resolution.fragment:
                self.statusBar().showMessage(f"已開啟 {resolved.as_posix()}（片段 #{resolution.fragment} 尚未定位）")
        except (OSError, UnicodeError, ValueError) as error:
            self.statusBar().showMessage(f"無法開啟筆記：{error}")

    def _note_context_finished(self, _session: int, path: object, properties: object, backlinks: object, _error: str) -> None:
        if path != self._current_note:
            return
        self.note_details.properties_text.setText(
            json.dumps(properties, ensure_ascii=False, indent=2) if properties else "沒有 Properties"
        )
        self.note_details.backlink_list.clear()
        for backlink in backlinks or []:
            from PySide6.QtWidgets import QListWidgetItem

            item = QListWidgetItem(backlink.as_posix())
            item.setData(Qt.ItemDataRole.UserRole, backlink)
            self.note_details.backlink_list.addItem(item)

    def _tags_finished(self, _session: int, tags: object, error: str) -> None:
        if error:
            self.statusBar().showMessage(f"載入標籤失敗：{error}")
            return
        self.navigation_panel.set_tags(tags or [])

    def _refresh_finished(self, _session: int, _report: object, error: str) -> None:
        if error:
            self.statusBar().showMessage(f"索引更新失敗：{error}")
        else:
            self._index_controller.request_tags()

    def _open_backlink_item(self, item: object) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(path, Path):
            self._set_current_note(path)

    @staticmethod
    def _set_group_contents_visible(group: QGroupBox, visible: bool) -> None:
        layout = group.layout()
        if layout is not None:
            for index in range(layout.count()):
                widget = layout.itemAt(index).widget()
                if widget is not None:
                    widget.setVisible(visible)
        group.setMaximumHeight(16777215 if visible else 34)

    def _run_search(self, query: str, tag: object, offset: int) -> None:
        self._search_offset = offset
        if offset == 0:
            self.navigation_panel.clear_results()
        self._index_controller.request_search(query, tag if isinstance(tag, str) else None, offset)

    def _search_finished(self, _session: int, _request: int, results: object, error: str) -> None:
        if error:
            self.statusBar().showMessage(f"搜尋失敗：{error}")
            self.navigation_panel.result_hint.setText("搜尋索引目前無法使用")
            return
        self.navigation_panel.set_results(results or [], append=self._search_offset > 0)

    def _open_search_result(self, relative_path: object) -> None:
        if isinstance(relative_path, Path):
            try:
                self._set_current_note(relative_path, expand_tree=False)
            except (OSError, UnicodeError, ValueError) as error:
                self.statusBar().showMessage(f"無法開啟筆記：{error}")

    def _expand_note_ancestors(self, relative_path: Path) -> None:
        folder = relative_path.parent
        while folder != Path("."):
            item = self._tree_item_for_path(folder)
            if item is not None:
                item.setExpanded(True)
            folder = folder.parent

    def _load_settings(self) -> dict[str, object]:
        try:
            payload = json.loads(self._settings_path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_settings(self) -> None:
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "preview_font_size": self.preview_font_size,
            "preview_font_family": self.preview_font_family,
            "theme_mode": self.theme_mode,
            "vault_root": str(self._config.vault_root),
        }
        self._settings_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _validated_preview_font_family(self, value: object) -> str:
        family = str(value).strip() if value is not None else ""
        return family if family in QFontDatabase.families() else QApplication.font().family()

    def _bounded_font_size(self, value: object) -> int:
        try:
            size = int(value)
        except (TypeError, ValueError):
            size = self.DEFAULT_PREVIEW_FONT_SIZE
        return max(self.MIN_PREVIEW_FONT_SIZE, min(self.MAX_PREVIEW_FONT_SIZE, size))
