# Copy Note Full Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a user copy the selected Markdown note's complete Windows path from the left file explorer's right-click menu.

**Architecture:** Keep the behavior inside `MainWindow`, alongside the existing file context menu. A small helper resolves a known Vault-relative note path, checks it remains inside the Vault, then writes it to Qt's clipboard and displays a brief status-bar confirmation.

**Tech Stack:** Python 3.12, PySide6, pytest.

---

### Task 1: Add clipboard behavior with a test-first workflow

**Files:**
- Modify: `tests/ui/test_main_window.py`
- Modify: `src/pigo_notes/ui/main_window.py`

- [ ] **Step 1: Write the failing UI test**

Add this test at the end of `tests/ui/test_main_window.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails for the missing helper**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\ui\test_main_window.py::test_copy_note_full_path_places_resolved_vault_path_on_clipboard -q --basetemp .test-tmp-copy-path-red
```

Expected: FAIL with an `AttributeError` stating that `MainWindow` does not have `_copy_note_full_path`.

- [ ] **Step 3: Add the minimal clipboard helper and right-click action**

In `src/pigo_notes/ui/main_window.py`, import `QApplication` from `PySide6.QtWidgets`. In `_show_file_menu`, add the action only when `item_kind == "file"`:

```python
if item_kind == "file":
    copy_path_action = menu.addAction("複製當前檔案完整路徑")
    copy_path_action.triggered.connect(lambda: self._copy_note_full_path(relative_path))
```

Add this helper before `_confirm_recycle`:

```python
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
```

- [ ] **Step 4: Run the targeted test to verify it passes**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\ui\test_main_window.py::test_copy_note_full_path_places_resolved_vault_path_on_clipboard -q --basetemp .test-tmp-copy-path-green
```

Expected: PASS.

- [ ] **Step 5: Run the complete regression suite and static checks**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .test-tmp-copy-path-verify
.\.venv\Scripts\python.exe -m compileall -q src
git diff --check
```

Expected: all tests pass; compilation and Git whitespace checks produce no errors.

- [ ] **Step 6: Commit the implementation**

Run:

```powershell
git add src/pigo_notes/ui/main_window.py tests/ui/test_main_window.py
git commit -m "feat: copy note path from explorer"
```

Expected: one commit containing only the clipboard feature and its test. `STATUS_ALL.md` remains local-only and excluded.
