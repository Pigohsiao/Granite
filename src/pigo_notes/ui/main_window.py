"""Main PySide6 workspace for a fixed local Markdown Vault."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QPlainTextEdit,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)

from pigo_notes.config import VaultConfig
from pigo_notes.services.markdown_service import MarkdownService
from pigo_notes.services.vault_service import VaultService


class MainWindow(QMainWindow):
    """Two-column-by-default note workspace with an optional information pane."""

    def __init__(self, config: VaultConfig) -> None:
        super().__init__()
        self._config = config
        self._vault = VaultService(config.vault_root)
        self._markdown = MarkdownService()
        self._current_note: Path | None = None
        self._settings_path = config.app_root / "app_data" / "settings.json"
        self.layout_mode = self._load_layout_mode()

        self.setWindowTitle("Pigo Notes App")
        self.resize(1280, 800)
        self._build_workspace()
        self._build_toolbar()
        self.refresh_tree()
        self._apply_layout()

    def _build_workspace(self) -> None:
        self.note_tree = QTreeWidget()
        self.note_tree.setHeaderLabel("Vault")
        self.note_tree.itemSelectionChanged.connect(self._open_selected_note)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("選擇一篇 Markdown 筆記開始編輯")
        self.editor.textChanged.connect(self._render_preview)
        self.preview = QTextBrowser()

        self.center_tabs = QTabWidget()
        self.center_tabs.addTab(self.editor, "編輯")
        self.center_tabs.addTab(self.preview, "預覽")

        self.info_panel = QTabWidget()
        self.info_preview = QTextBrowser()
        self.backlinks = QTextBrowser()
        self.git_info = QTextBrowser()
        self.git_info.setHtml("<p>Git 快速操作將顯示在工具列。</p>")
        self.info_panel.addTab(self.info_preview, "預覽")
        self.info_panel.addTab(self.backlinks, "反向連結")
        self.info_panel.addTab(self.git_info, "Git")

        self.workspace = QSplitter(Qt.Orientation.Horizontal)
        self.workspace.addWidget(self.note_tree)
        self.workspace.addWidget(self.center_tabs)
        self.workspace.addWidget(self.info_panel)
        self.workspace.setSizes([280, 720, 280])
        self.setCentralWidget(self.workspace)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("工具列")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        toggle = QAction("▯", self)
        toggle.setToolTip("切換雙欄／三欄版面")
        toggle.triggered.connect(self.toggle_layout)
        toolbar.addAction(toggle)

        refresh = QAction("↻", self)
        refresh.setToolTip("重新掃描 Vault")
        refresh.triggered.connect(self.refresh_tree)
        toolbar.addAction(refresh)

        save = QAction("儲存", self)
        save.setShortcut("Ctrl+S")
        save.triggered.connect(self.save_current_note)
        toolbar.addAction(save)

    def refresh_tree(self) -> None:
        self.note_tree.clear()
        for note in self._vault.list_notes():
            item = QTreeWidgetItem([note.relative_path.as_posix()])
            item.setData(0, Qt.ItemDataRole.UserRole, note.relative_path)
            self.note_tree.addTopLevelItem(item)

    def toggle_layout(self) -> None:
        self.layout_mode = "three_column" if self.layout_mode == "two_column" else "two_column"
        self._apply_layout()
        self._save_layout_mode()

    def save_current_note(self) -> None:
        if self._current_note is None:
            return
        self._vault.save_note(self._current_note, self.editor.toPlainText())
        self.statusBar().showMessage("已儲存", 2500)
        self._render_preview()

    def _open_selected_note(self) -> None:
        selected = self.note_tree.selectedItems()
        if not selected:
            return
        relative_path = selected[0].data(0, Qt.ItemDataRole.UserRole)
        self._current_note = Path(relative_path)
        self.editor.blockSignals(True)
        self.editor.setPlainText(self._vault.read_note(self._current_note))
        self.editor.blockSignals(False)
        self._render_preview()

    def _render_preview(self) -> None:
        rendered = self._markdown.render(self.editor.toPlainText())
        self.preview.setHtml(rendered)
        self.info_preview.setHtml(rendered)
        self._render_backlinks()

    def _render_backlinks(self) -> None:
        if self._current_note is None:
            self.backlinks.clear()
            return
        notes = {note.relative_path: self._vault.read_note(note.relative_path) for note in self._vault.list_notes()}
        targets = self._markdown.find_backlinks(notes, self._current_note.stem)
        if targets:
            self.backlinks.setHtml("<br>".join(path.as_posix() for path in targets))
        else:
            self.backlinks.setHtml("<p>沒有反向連結</p>")

    def _apply_layout(self) -> None:
        is_three_column = self.layout_mode == "three_column"
        self.info_panel.setVisible(is_three_column)
        self.workspace.setSizes([280, 650, 280 if is_three_column else 0])

    def _load_layout_mode(self) -> str:
        try:
            payload = json.loads(self._settings_path.read_text(encoding="utf-8"))
            return payload.get("layout_mode") if payload.get("layout_mode") in {"two_column", "three_column"} else "two_column"
        except (FileNotFoundError, json.JSONDecodeError):
            return "two_column"

    def _save_layout_mode(self) -> None:
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        self._settings_path.write_text(
            json.dumps({"layout_mode": self.layout_mode}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
