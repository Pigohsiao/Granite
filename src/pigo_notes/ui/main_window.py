"""Obsidian-inspired, read-only two-pane workspace for a local Markdown Vault."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)

from pigo_notes.config import VaultConfig
from pigo_notes.services.markdown_service import MarkdownService
from pigo_notes.services.recycle_bin_service import RecycleBinService
from pigo_notes.services.vault_service import VaultService


class DragBar(QWidget):
    """A visible client-area strip that starts the native system window move."""

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.window().windowHandle()
            if handle is not None and handle.startSystemMove():
                event.accept()
                return
        super().mousePressEvent(event)


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
        self.refresh_tree()

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
        self.note_tree.itemSelectionChanged.connect(self._open_selected_note)
        self.note_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.note_tree.customContextMenuRequested.connect(self._show_file_menu)

        self.note_preview = QTextBrowser()
        self.note_preview.setOpenExternalLinks(True)
        self.note_preview.setPlaceholderText("選擇一篇 Markdown 筆記開始預覽")

        self.workspace = QSplitter(Qt.Orientation.Horizontal)
        self.workspace.addWidget(self.note_tree)
        self.workspace.addWidget(self.note_preview)
        self.workspace.setSizes([300, 880])
        self.setCentralWidget(self.workspace)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("工具列")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        refresh = QAction("↻", self)
        refresh.setToolTip("重新掃描檔案樹")
        refresh.triggered.connect(self.refresh_tree)
        toolbar.addAction(refresh)

        self.decrease_font_action = QAction("A−", self)
        self.decrease_font_action.setToolTip("縮小閱讀字型")
        self.decrease_font_action.triggered.connect(self.decrease_preview_font)
        toolbar.addAction(self.decrease_font_action)

        self.increase_font_action = QAction("A＋", self)
        self.increase_font_action.setToolTip("放大閱讀字型")
        self.increase_font_action.triggered.connect(self.increase_preview_font)
        toolbar.addAction(self.increase_font_action)

    def refresh_tree(self, *, expanded_folders: set[Path] | None = None) -> None:
        self.note_tree.clear()
        folders: dict[Path, QTreeWidgetItem] = {}
        for note in self._vault.list_notes():
            parent = self._ensure_folder(note.relative_path.parent, folders)
            item = QTreeWidgetItem([note.relative_path.name])
            item.setData(0, Qt.ItemDataRole.UserRole, note.relative_path)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, "file")
            if parent is None:
                self.note_tree.addTopLevelItem(item)
            else:
                parent.addChild(item)
        self.note_tree.collapseAll()
        for folder in expanded_folders or set():
            item = folders.get(folder)
            if item is not None:
                item.setExpanded(True)

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
        item_type = "資料夾" if is_directory else "檔案"
        answer = QMessageBox.question(
            self,
            "移到資源回收桶",
            f"確定將這個{item_type}移到 Windows 資源回收桶？\n\n{relative_path.as_posix()}",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        expanded_folders = self._expanded_folder_paths()
        try:
            self._recycle_bin.move_to_recycle_bin(relative_path, is_directory=is_directory)
        except (FileNotFoundError, OSError, RuntimeError, ValueError) as error:
            QMessageBox.warning(self, "無法移到資源回收桶", str(error))
            return
        if self._current_note is not None and (self._current_note == relative_path or is_directory and relative_path in self._current_note.parents):
            self._current_note = None
            self.note_preview.clear()
        self.refresh_tree(expanded_folders=expanded_folders)

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

    def _set_current_note(self, relative_path: Path) -> None:
        self._current_note = relative_path
        content = self._vault.read_note(relative_path)
        self.note_preview.setHtml(self._markdown.render(content))
        self._expand_note_ancestors(relative_path)

    def _expand_note_ancestors(self, relative_path: Path) -> None:
        folder = relative_path.parent
        while folder != Path("."):
            for item in self.note_tree.findItems(folder.name, Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive):
                if item.data(0, Qt.ItemDataRole.UserRole + 1) == "folder":
                    item.setExpanded(True)
                    break
            folder = folder.parent

    def _load_settings(self) -> dict[str, object]:
        try:
            payload = json.loads(self._settings_path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_settings(self) -> None:
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"preview_font_size": self.preview_font_size, "theme_mode": self.theme_mode}
        self._settings_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _bounded_font_size(self, value: object) -> int:
        try:
            size = int(value)
        except (TypeError, ValueError):
            size = self.DEFAULT_PREVIEW_FONT_SIZE
        return max(self.MIN_PREVIEW_FONT_SIZE, min(self.MAX_PREVIEW_FONT_SIZE, size))
