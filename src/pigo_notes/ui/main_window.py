"""Obsidian-inspired, read-only two-pane workspace for a local Markdown Vault."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QSplitter, QTextBrowser, QToolBar, QTreeWidget, QTreeWidgetItem

from pigo_notes.config import VaultConfig
from pigo_notes.services.markdown_service import MarkdownService
from pigo_notes.services.vault_service import VaultService


class MainWindow(QMainWindow):
    """Focused two-pane reader with a collapsed hierarchical file explorer."""

    MIN_PREVIEW_FONT_SIZE = 12
    MAX_PREVIEW_FONT_SIZE = 28
    DEFAULT_PREVIEW_FONT_SIZE = 16

    def __init__(self, config: VaultConfig) -> None:
        super().__init__()
        self._config = config
        self._vault = VaultService(config.vault_root)
        self._markdown = MarkdownService()
        self._current_note: Path | None = None
        self._settings_path = config.app_root / "app_data" / "settings.json"
        self.preview_font_size = self._load_preview_font_size()

        self.setWindowTitle("Pigo Notes App")
        self.resize(1180, 780)
        self.setStyleSheet("""
            QMainWindow { background: #1e1f22; color: #dcddde; }
            QToolBar { background: #191a1d; border: 0; border-bottom: 1px solid #34363c; spacing: 4px; padding: 5px 7px; }
            QToolButton { color: #c9cbd0; background: transparent; border: 0; border-radius: 4px; padding: 5px 8px; }
            QToolButton:hover { background: #303239; color: #ffffff; }
            QTreeWidget { background: #191a1d; color: #c9cbd0; border: 0; border-right: 1px solid #34363c; outline: 0; }
            QTreeWidget::header { background: #191a1d; color: #999ca4; border: 0; border-bottom: 1px solid #2e3035; padding: 8px; font-weight: 600; }
            QTreeWidget::item { height: 27px; border-radius: 3px; padding-left: 3px; }
            QTreeWidget::item:hover { background: #2a2c31; }
            QTreeWidget::item:selected { background: #353141; color: #f0edff; border-left: 2px solid #a78bfa; }
            QTextBrowser { background: #242529; color: #dcddde; border: 0; padding: 26px 56px; selection-background-color: #5d557d; }
            QScrollBar:vertical { background: #1e1f22; width: 10px; margin: 0; }
            QScrollBar::handle:vertical { background: #42454c; min-height: 26px; border-radius: 4px; }
        """)
        self._build_workspace()
        self._build_toolbar()
        self.set_preview_font_size(self.preview_font_size, persist=False)
        self.refresh_tree()

    def show_for_user(self) -> None:
        """Open as a normal, movable Windows window instead of maximized."""
        self.showNormal()
        self.raise_()
        self.activateWindow()
    @property
    def current_note(self) -> Path | None:
        return self._current_note

    def _build_workspace(self) -> None:
        self.note_tree = QTreeWidget()
        self.note_tree.setHeaderLabel("檔案總管")
        self.note_tree.setIndentation(18)
        self.note_tree.itemSelectionChanged.connect(self._open_selected_note)

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

    def refresh_tree(self) -> None:
        self.note_tree.clear()
        folders: dict[Path, QTreeWidgetItem] = {}
        for note in self._vault.list_notes():
            parent = self._ensure_folder(note.relative_path.parent, folders)
            item = QTreeWidgetItem([note.relative_path.name])
            item.setData(0, Qt.ItemDataRole.UserRole, note.relative_path)
            if parent is None:
                self.note_tree.addTopLevelItem(item)
            else:
                parent.addChild(item)
        self.note_tree.collapseAll()

    def _ensure_folder(self, folder: Path, folders: dict[Path, QTreeWidgetItem]) -> QTreeWidgetItem | None:
        if folder == Path("."):
            return None
        if folder in folders:
            return folders[folder]
        parent = self._ensure_folder(folder.parent, folders)
        item = QTreeWidgetItem([folder.name])
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
        self.preview_font_size = max(self.MIN_PREVIEW_FONT_SIZE, min(self.MAX_PREVIEW_FONT_SIZE, size))
        self.note_preview.setStyleSheet(f"QTextBrowser {{ font-size: {self.preview_font_size}px; }}")
        self.decrease_font_action.setEnabled(self.preview_font_size > self.MIN_PREVIEW_FONT_SIZE)
        self.increase_font_action.setEnabled(self.preview_font_size < self.MAX_PREVIEW_FONT_SIZE)
        if persist:
            self._save_preview_font_size()

    def _open_selected_note(self) -> None:
        selected = self.note_tree.selectedItems()
        if not selected:
            return
        relative_path = selected[0].data(0, Qt.ItemDataRole.UserRole)
        if isinstance(relative_path, Path):
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
                if item.data(0, Qt.ItemDataRole.UserRole) is None:
                    item.setExpanded(True)
                    break
            folder = folder.parent

    def _load_preview_font_size(self) -> int:
        try:
            payload = json.loads(self._settings_path.read_text(encoding="utf-8"))
            value = int(payload.get("preview_font_size", self.DEFAULT_PREVIEW_FONT_SIZE))
            return max(self.MIN_PREVIEW_FONT_SIZE, min(self.MAX_PREVIEW_FONT_SIZE, value))
        except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError):
            return self.DEFAULT_PREVIEW_FONT_SIZE

    def _save_preview_font_size(self) -> None:
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"preview_font_size": self.preview_font_size}
        self._settings_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")