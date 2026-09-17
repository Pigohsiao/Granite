"""Main PySide6 workspace for a fixed local Markdown Vault."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QInputDialog,
    QMenu,
    QMessageBox,
    QMainWindow,
    QPlainTextEdit,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QToolBar,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
)

from pigo_notes.config import VaultConfig
from pigo_notes.models import Task
from pigo_notes.services.git_service import GitResult, GitService
from pigo_notes.services.markdown_service import MarkdownService
from pigo_notes.services.task_service import TaskService
from pigo_notes.services.vault_service import VaultService


class MainWindow(QMainWindow):
    """Two-column-by-default note workspace with an optional information pane."""

    def __init__(self, config: VaultConfig) -> None:
        super().__init__()
        self._config = config
        self._vault = VaultService(config.vault_root)
        self._tasks = TaskService(self._vault)
        self._git = GitService(config.vault_root)
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

    @property
    def current_note(self) -> Path | None:
        return self._current_note

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
        self.task_list = QListWidget()
        self.task_list.itemChanged.connect(self._task_checked)
        self.info_panel.addTab(self.info_preview, "預覽")
        self.info_panel.addTab(self.backlinks, "反向連結")
        self.info_panel.addTab(self.task_list, "任務")
        self.info_panel.addTab(self.git_info, "Git")
        self.ai_placeholder = QTextBrowser()
        self.ai_placeholder.setHtml("<p><b>AI Assistant</b></p><p>Coming soon — no data is sent in V1.</p>")
        self.info_panel.addTab(self.ai_placeholder, "AI")

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

        today = QAction("今天", self)
        today.setToolTip("開啟今日筆記")
        today.triggered.connect(self.open_today)
        toolbar.addAction(today)

        tasks = QAction("任務", self)
        tasks.setToolTip("顯示所有 Markdown 待辦")
        tasks.triggered.connect(self.refresh_tasks)
        toolbar.addAction(tasks)

        git_button = QToolButton()
        git_button.setText("⑂")
        git_button.setToolTip("Git 快速操作")
        self.git_menu = QMenu(self)
        for label, handler in (("Pull", self.pull_vault), ("Commit", self.commit_vault), ("Merge", self.merge_vault), ("Push", self.push_vault), ("Branch", self.branch_vault)):
            action = self.git_menu.addAction(label)
            action.triggered.connect(handler)
        git_button.setMenu(self.git_menu)
        git_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        toolbar.addWidget(git_button)

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

    def refresh_tasks(self) -> None:
        self.task_list.blockSignals(True)
        self.task_list.clear()
        for task in self._tasks.list_tasks():
            item = QListWidgetItem(f"{task.source_path.as_posix()} — {task.text}")
            item.setData(Qt.ItemDataRole.UserRole, task)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if task.completed else Qt.CheckState.Unchecked)
            self.task_list.addItem(item)
        self.task_list.blockSignals(False)
        self.layout_mode = "three_column"
        self._apply_layout()
        self.info_panel.setCurrentWidget(self.task_list)

    def open_today(self, note_date: date | None = None) -> None:
        relative_path = self._vault.open_or_create_daily_note(note_date or date.today())
        self.refresh_tree()
        self._set_current_note(relative_path)

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


    def pull_vault(self) -> None:
        if self._confirm("Pull", "從遠端拉取目前分支的變更？"):
            self._show_git_result("Pull", self._git.pull())

    def commit_vault(self) -> None:
        count = self._git.changed_file_count()
        message, accepted = QInputDialog.getText(self, "Commit", f"將提交 {count} 個已變更檔案。提交訊息：")
        if accepted and message.strip() and self._confirm("Commit", f"提交 {count} 個已變更檔案？"):
            self._show_git_result("Commit", self._git.commit_all(message))

    def merge_vault(self) -> None:
        branch, accepted = QInputDialog.getText(self, "Merge", "要合併的分支：")
        if accepted and branch.strip() and self._confirm("Merge", f"合併分支 {branch.strip()}？"):
            self._show_git_result("Merge", self._git.merge(branch))

    def push_vault(self) -> None:
        if self._confirm("Push", "推送目前分支到遠端？"):
            self._show_git_result("Push", self._git.push())

    def branch_vault(self) -> None:
        action, accepted = QInputDialog.getItem(self, "Branch", "動作：", ["建立", "切換"], 0, False)
        if not accepted:
            return
        branch, accepted = QInputDialog.getText(self, "Branch", "分支名稱：")
        if not accepted or not branch.strip():
            return
        result = self._git.create_branch(branch) if action == "建立" else self._git.switch_branch(branch)
        self._show_git_result("Branch", result)

    def _confirm(self, title: str, message: str) -> bool:
        return QMessageBox.question(self, title, message) == QMessageBox.StandardButton.Yes

    def _show_git_result(self, action: str, result: GitResult) -> None:
        message = result.output or ("完成" if result.succeeded else "失敗")
        if result.succeeded:
            QMessageBox.information(self, action, message)
        else:
            QMessageBox.warning(self, action, message)
    def _task_checked(self, item: QListWidgetItem) -> None:
        task = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(task, Task):
            return
        self._tasks.set_completed(task, item.checkState() == Qt.CheckState.Checked)
        self.refresh_tasks()

    def _open_selected_note(self) -> None:
        selected = self.note_tree.selectedItems()
        if selected:
            self._set_current_note(Path(selected[0].data(0, Qt.ItemDataRole.UserRole)))

    def _set_current_note(self, relative_path: Path) -> None:
        self._current_note = relative_path
        self.editor.blockSignals(True)
        self.editor.setPlainText(self._vault.read_note(relative_path))
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
        self.backlinks.setHtml("<br>".join(path.as_posix() for path in targets) if targets else "<p>沒有反向連結</p>")

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
        self._settings_path.write_text(json.dumps({"layout_mode": self.layout_mode}, ensure_ascii=False, indent=2), encoding="utf-8")
