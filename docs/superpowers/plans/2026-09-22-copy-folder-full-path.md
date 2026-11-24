# Copy Folder Full Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a user copy a folder's complete Windows path from the left file explorer's right-click menu.

**Architecture:** Extract the existing context-menu construction into a small `_build_file_menu` helper so it can be tested without opening a native menu. The existing Vault-relative clipboard helper remains responsible for both note and folder paths; the menu will add the copy action for both item kinds.

**Tech Stack:** Python 3.12, PySide6, pytest.

---

### Task 1: Show the copy action for folders

**Files:**
- Modify: `tests/ui/test_main_window.py`
- Modify: `src/pigo_notes/ui/main_window.py`

- [ ] **Step 1: Write the failing UI test**

Append this test to `tests/ui/test_main_window.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\ui\test_main_window.py::test_folder_context_menu_includes_copy_full_path_action -q --basetemp .test-tmp-copy-folder-red
```

Expected: FAIL with an `AttributeError` because `_build_file_menu` does not exist.

- [ ] **Step 3: Extract the shared menu builder**

In `src/pigo_notes/ui/main_window.py`, replace the direct `QMenu` construction in `_show_file_menu` with:

```python
menu = self._build_file_menu(relative_path, item_kind)
menu.exec(self.note_tree.viewport().mapToGlobal(position))
```

Add this helper before `_copy_note_full_path`:

```python
def _build_file_menu(self, relative_path: Path, item_kind: str) -> QMenu:
    menu = QMenu(self)
    copy_path_action = menu.addAction("複製當前檔案完整路徑")
    copy_path_action.triggered.connect(lambda: self._copy_note_full_path(relative_path))
    recycle_action = menu.addAction("移到資源回收桶")
    recycle_action.triggered.connect(lambda: self._confirm_recycle(relative_path, item_kind == "folder"))
    return menu
```

- [ ] **Step 4: Run the targeted test to verify it passes**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\ui\test_main_window.py::test_folder_context_menu_includes_copy_full_path_action -q --basetemp .test-tmp-copy-folder-green
```

Expected: PASS.

- [ ] **Step 5: Run the complete regression suite and checks**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .test-tmp-copy-folder-verify
.\.venv\Scripts\python.exe -m compileall -q src
git diff --check
```

Expected: all tests pass; compilation and Git whitespace checks produce no errors.

- [ ] **Step 6: Commit the implementation**

Run:

```powershell
git add src/pigo_notes/ui/main_window.py tests/ui/test_main_window.py
git commit -m "feat: copy folder path from explorer"
```

Expected: one commit containing only the folder context-menu extension and its test. `STATUS_ALL.md` remains local-only and excluded.
