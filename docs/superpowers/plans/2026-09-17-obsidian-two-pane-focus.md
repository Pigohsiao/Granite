# Obsidian Two-Pane Focus Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立預設收合的階層檔案樹與唯讀閱讀區，並提供可持久化的預覽字型大小調整。

**Architecture:** `MainWindow` 由一個 `QSplitter` 組成：左側 `QTreeWidget` 以資料夾節點組織相對路徑，右側 `QTextBrowser` 唯讀渲染目前檔案。`settings.json` 增加 `preview_font_size`；工具列只留下重新掃描與 `A−`／`A＋`。

**Tech Stack:** Python 3.13、PySide6、pytest、Markdown。

---

### Task 1: 建立失敗的階層檔案樹與唯讀工具列測試

**Files:**
- Modify: `tests/ui/test_main_window.py`

- [ ] **Step 1: 寫入測試**

```python
VaultService(config.vault_root).save_note(Path("Projects/2026/Plan.md"), "# Plan\n")
window.refresh_tree()
projects = window.note_tree.topLevelItem(0)
assert projects.text(0) == "Projects"
assert projects.childCount() == 1
assert projects.isExpanded() is False
assert "今天" not in [action.text() for action in window.findChildren(QToolBar)[0].actions()]
```

另驗證 `info_panel` 不存在，中央僅有 `note_preview`。

- [ ] **Step 2: 執行並確認失敗**

Run: `python -m pytest tests/ui/test_main_window.py -v`
Expected: FAIL，因為現有檔案樹為平面清單且資訊面板仍存在。

### Task 2: 實作雙欄階層與預設收合

**Files:**
- Modify: `src/pigo_notes/ui/main_window.py`
- Test: `tests/ui/test_main_window.py`

- [ ] **Step 1: 建立資料夾節點 helper**

```python
def _folder_item(self, parents: dict[Path, QTreeWidgetItem], path: Path) -> QTreeWidgetItem:
    if path in parents:
        return parents[path]
    parent = self._folder_item(parents, path.parent) if path.parent != Path(".") else None
    item = QTreeWidgetItem([path.name])
    item.setData(0, Qt.ItemDataRole.UserRole, path)
    (parent.addChild(item) if parent else self.note_tree.addTopLevelItem(item))
    parents[path] = item
    return item
```

- [ ] **Step 2: 建立檔案葉節點並預設收合**

每個 `Note.relative_path` 的 parent 用 helper 建立；葉節點資料為相對檔案路徑。最後呼叫 `self.note_tree.collapseAll()`。

- [ ] **Step 3: 移除第三欄與舊操作**

移除 `info_panel`、任務、Git、AI、Today、儲存與版面切換；QSplitter 只加入檔案樹與 `note_preview`。

- [ ] **Step 4: 執行目標測試**

Run: `python -m pytest tests/ui/test_main_window.py -v`
Expected: PASS。

### Task 3: 以 TDD 加入預覽字型大小

**Files:**
- Modify: `tests/ui/test_main_window.py`
- Modify: `src/pigo_notes/ui/main_window.py`

- [ ] **Step 1: 寫入失敗測試**

```python
assert window.preview_font_size == 16
window.increase_preview_font()
assert window.preview_font_size == 17
for _ in range(30): window.decrease_preview_font()
assert window.preview_font_size == 12
assert window.decrease_font_action.isEnabled() is False
```

- [ ] **Step 2: 執行並確認失敗**

Run: `python -m pytest tests/ui/test_main_window.py::test_preview_font_size_is_bounded_and_persisted -v`
Expected: FAIL，因為目前沒有字型大小 API。

- [ ] **Step 3: 最小實作**

載入 `preview_font_size`，缺省為 16；`set_preview_font_size` 將值限制在 12–28、套用 `QTextBrowser.setStyleSheet` 並儲存設定。`increase_preview_font` 和 `decrease_preview_font` 分別調整一級。

- [ ] **Step 4: 執行目標測試**

Run: `python -m pytest tests/ui/test_main_window.py -v`
Expected: PASS。

### Task 4: 完整驗證與文件

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 更新使用說明**

說明雙欄專注模式、預設收合資料夾、唯讀預覽和 `A−`／`A＋` 字型大小。

- [ ] **Step 2: 完整驗證**

Run: `python -m pytest -v --basetemp .tmp_pytest` and `python -m compileall src`
Expected: 全數通過。

- [ ] **Step 3: 提交**

```bash
git add src/pigo_notes/ui/main_window.py tests/ui/test_main_window.py README.md docs/superpowers
git commit -m "feat: add Obsidian two-pane focus mode"
```