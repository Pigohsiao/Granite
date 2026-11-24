"""Switchable file, search, recent, and tag navigation for the left pane."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class NavigationPanel(QWidget):
    searchRequested = Signal(str, object, int)
    resultActivated = Signal(object)
    tagsRequested = Signal()
    modeChanged = Signal(str)

    def __init__(self, file_tree: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._query = ""
        self._tag: str | None = None
        self._buttons = QButtonGroup(self)
        self._buttons.setExclusive(True)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        for mode, title in (("files", "檔案"), ("search", "搜尋"), ("recent", "最近"), ("tags", "標籤")):
            button = QPushButton(title, self)
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, value=mode: self.show_mode(value))
            self._buttons.addButton(button)
            bar.addWidget(button)
            if mode == "files":
                self.file_button = button
        root.addLayout(bar)

        self.pages = QStackedWidget(self)
        self.pages.addWidget(file_tree)
        self.search_page = QWidget(self)
        search_layout = QVBoxLayout(self.search_page)
        search_layout.setContentsMargins(4, 4, 4, 4)
        self.search_input = QLineEdit(self.search_page)
        self.search_input.setPlaceholderText("搜尋檔名與筆記內容")
        self.search_input.setClearButtonEnabled(True)
        self.clear_tag_button = QPushButton("清除標籤篩選", self.search_page)
        self.clear_tag_button.setEnabled(False)
        self.result_list = QListWidget(self.search_page)
        self.result_hint = QLabel("輸入文字開始搜尋", self.search_page)
        self.result_hint.setWordWrap(True)
        self.load_more_button = QPushButton("載入更多", self.search_page)
        self.load_more_button.hide()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.clear_tag_button)
        search_layout.addWidget(self.result_hint)
        search_layout.addWidget(self.result_list, 1)
        search_layout.addWidget(self.load_more_button)
        self.pages.addWidget(self.search_page)

        self.recent_list = QListWidget(self)
        self.pages.addWidget(self.recent_list)
        self.tag_list = QListWidget(self)
        self.pages.addWidget(self.tag_list)

        root.addWidget(self.pages, 1)

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(250)
        self.search_input.textChanged.connect(self._query_changed)
        self.search_timer.timeout.connect(self._emit_search)
        self.result_list.itemClicked.connect(self._activate_result)
        self.recent_list.itemClicked.connect(self._activate_result)
        self.tag_list.itemClicked.connect(self._activate_tag)
        self.load_more_button.clicked.connect(self.load_more)
        self.clear_tag_button.clicked.connect(self.clear_tag_filter)
        self.file_button.setChecked(True)

    def show_mode(self, mode: str) -> None:
        mapping = {"files": 0, "search": 1, "recent": 2, "tags": 3}
        if mode not in mapping:
            return
        self.pages.setCurrentIndex(mapping[mode])
        button = next((item for item in self._buttons.buttons() if item.text() == {"files": "檔案", "search": "搜尋", "recent": "最近", "tags": "標籤"}[mode]), None)
        if button is not None:
            button.setChecked(True)
        if mode == "search":
            self.search_input.setFocus()
        elif mode == "tags":
            self.tagsRequested.emit()
        self.modeChanged.emit(mode)

    def set_tags(self, tags) -> None:
        self.tag_list.clear()
        for item in tags:
            row = QListWidgetItem(f"#{item.tag}  ({item.count})")
            row.setData(Qt.ItemDataRole.UserRole, item.tag)
            self.tag_list.addItem(row)

    def set_recent(self, paths) -> None:
        self.recent_list.clear()
        for path in paths:
            row = QListWidgetItem(path.as_posix())
            row.setData(Qt.ItemDataRole.UserRole, path)
            self.recent_list.addItem(row)

    def _activate_tag(self, item: QListWidgetItem) -> None:
        tag = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(tag, str):
            self._tag = tag
            self.clear_tag_button.setEnabled(True)
            self._query = self.search_input.text()
            self.show_mode("search")
            self.searchRequested.emit(self._query, tag, 0)

    def clear_tag_filter(self) -> None:
        self._tag = None
        self.clear_tag_button.setEnabled(False)
        self.searchRequested.emit(self.search_input.text(), None, 0)

    def _query_changed(self, value: str) -> None:
        self._query = value
        self.search_timer.start()

    def _emit_search(self) -> None:
        self.searchRequested.emit(self._query, self._tag, 0)

    def set_results(self, results, *, append: bool = False) -> None:
        if not append:
            self.result_list.clear()
        for result in results:
            text = result.relative_path.as_posix()
            if result.snippet:
                text += "\n" + result.snippet
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, result.relative_path)
            self.result_list.addItem(item)
        self.result_hint.setText(f"找到 {self.result_list.count()} 篇筆記" if self.result_list.count() else "沒有符合的筆記")
        self.load_more_button.setVisible(len(results) >= 100)

    def clear_results(self) -> None:
        self.result_list.clear()
        self.result_hint.setText("輸入文字開始搜尋")
        self.load_more_button.hide()

    def _activate_result(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(path, Path):
            self.resultActivated.emit(path)

    def load_more(self) -> None:
        self.searchRequested.emit(self._query, self._tag, self.result_list.count())
