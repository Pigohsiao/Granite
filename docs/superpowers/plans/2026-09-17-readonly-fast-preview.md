# Read-only Fast Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將筆記工作區改為唯讀單檔預覽，消除開檔時的全 Vault 反向連結掃描。

**Architecture:** `MainWindow` 以 `QTextBrowser` 作為唯一筆記內容元件。選取筆記時透過 `VaultService.read_note` 讀取一個檔案，再交給 `MarkdownService.render`。任務、Git 與 AI 面板維持在可選三欄資訊面板中；反向連結在索引功能完成前不計算。

**Tech Stack:** Python 3.13、PySide6、pytest、Markdown。

---

### Task 1: 先鎖定唯讀預覽行為

**Files:**
- Modify: `tests/ui/test_main_window.py`
- Modify: `tests/ui/test_task_interactions.py`

- [ ] **Step 1: 寫入失敗測試**

```python
assert not hasattr(window, "editor")
window._set_current_note(Path("Example.md"))
assert "Example" in window.note_preview.toPlainText()
```

以 monkeypatch 將 `window._render_backlinks` 替換成會拋出 `AssertionError` 的函式，再選取筆記；測試應證明唯讀開檔流程不再呼叫它。

- [ ] **Step 2: 驗證測試失敗**

Run: `python -m pytest tests/ui/test_main_window.py tests/ui/test_task_interactions.py -v`
Expected: FAIL，因為目前仍有 `editor`，且 `_set_current_note` 仍呼叫 `_render_backlinks`。

### Task 2: 實作唯讀單檔預覽

**Files:**
- Modify: `src/pigo_notes/ui/main_window.py`
- Test: `tests/ui/test_main_window.py`
- Test: `tests/ui/test_task_interactions.py`

- [ ] **Step 1: 以 `QTextBrowser` 取代 editor/preview 分頁**

建立 `self.note_preview = QTextBrowser()`，直接設為中間欄位；移除 `QPlainTextEdit`、`QTabWidget` 的 editor/preview 用途、`save_current_note` 與工具列的儲存按鈕。

- [ ] **Step 2: 將 `_set_current_note` 縮減為單檔讀取與渲染**

```python
self._current_note = relative_path
content = self._vault.read_note(relative_path)
rendered = self._markdown.render(content)
self.note_preview.setHtml(rendered)
if self.layout_mode == "three_column":
    self.info_preview.setHtml(rendered)
```

不要呼叫 `_render_backlinks`，也不要呼叫 `list_notes()`。

- [ ] **Step 3: 調整 Today 測試**

將原本對 `window.editor.toPlainText()` 的斷言改為對 `window.note_preview.toPlainText()` 的斷言。

- [ ] **Step 4: 驗證目標測試通過**

Run: `python -m pytest tests/ui/test_main_window.py tests/ui/test_task_interactions.py -v`
Expected: PASS。

### Task 3: 完整驗證與文件

**Files:**
- Modify: `README.md`
- Test: `tests/`

- [ ] **Step 1: 更新 README**

將功能描述改為「唯讀 Markdown 預覽」，移除編輯與 Ctrl+S 儲存說明。

- [ ] **Step 2: 執行完整驗證**

Run: `python -m pytest -v --basetemp .tmp_pytest` and `python -m compileall src`
Expected: 所有測試通過且編譯成功。

- [ ] **Step 3: 提交**

```bash
git add src/pigo_notes/ui/main_window.py tests/ui/test_main_window.py tests/ui/test_task_interactions.py README.md docs/superpowers
git commit -m "feat: add fast read-only note preview"
```