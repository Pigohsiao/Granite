# Preview Font Family Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a persistent, Windows-native font selector that changes only the right-side Markdown preview.

**Architecture:** `MainWindow` owns the chosen font family, a `QFontComboBox`, and existing JSON persistence. The font-family setter updates only `QTextBrowser`; the existing size setter continues to control only the preview size.

**Tech Stack:** Python 3.13, PySide6, pytest, JSON settings.

---

### Task 1: Write the failing font-family UI test

**Files:**
- Modify: `tests/ui/test_main_window.py`
- Test: `tests/ui/test_main_window.py::test_preview_font_family_is_selected_and_persisted`

- [ ] Add `QFontComboBox` to the Qt widget imports and add a test that creates a `MainWindow`, finds the selector, takes `selector.currentFont().family()`, calls `window.set_preview_font_family(selected_family)`, and asserts both `window.preview_font_family` and `window.note_preview.font().family()` match.
- [ ] Close the first window, construct a new `MainWindow` from the same temporary config, and assert the selected family was restored to both state and preview widget.
- [ ] Run the focused test using `C:\Users\hsi67063\Documents\Pigo Notes App\.venv\Scripts\python.exe -m pytest tests/ui/test_main_window.py::test_preview_font_family_is_selected_and_persisted -vv --maxfail=1 --basetemp .pytest-font-family`; expect it to fail because neither the selector nor setter exists.
- [ ] Commit the test with `git add tests/ui/test_main_window.py` and `git commit -m "test: cover preview font family persistence"`.

### Task 2: Implement the selector and persistence

**Files:**
- Modify: `src/pigo_notes/ui/main_window.py`
- Test: `tests/ui/test_main_window.py::test_preview_font_family_is_selected_and_persisted`

- [ ] Import `QFont`, `QFontDatabase`, and `QFontComboBox`.
- [ ] After loading settings in `MainWindow.__init__`, initialise `preview_font_family` from `preview_font_family` or `QApplication.font().family()`, validating it against `QFontDatabase.families()`.
- [ ] After the `A＋` action in `_build_toolbar`, add `self.preview_font_selector = QFontComboBox(toolbar)`, set tooltip `選擇右側預覽字型`, cap width at 180 pixels, set it to the stored `QFont`, connect `currentFontChanged` to the setter, then add it to the toolbar.
- [ ] Add `set_preview_font_family(family, persist=True)`: validate the family, apply it through the preview widget's `QFont`, synchronise the combo without signal-loop recursion, and save only when requested.
- [ ] Extend `_save_settings()` to include `preview_font_family`; preserve the existing UTF-8 JSON output and existing fallback behavior for invalid settings.
- [ ] Keep `set_preview_font_size()` unchanged except for verifying it does not reset the preview family.
- [ ] Run the focused test again; expect PASS. Commit exact source and test files with `git commit -m "feat: select preview font family"`.

### Task 3: Full verification and handoff

**Files:**
- Modify: `STATUS_ALL.md` (ignored runtime log; do not stage)
- Test: `tests/`

- [ ] Run `C:\Users\hsi67063\Documents\Pigo Notes App\.venv\Scripts\python.exe -m pytest -vv --maxfail=1 --basetemp .pytest-basetemp-final` from the isolated worktree; expect all tests to pass.
- [ ] After merging to `main`, run `cmd /c "C:\Users\hsi67063\Desktop\啟動 Pigo Notes App.bat"` and manually verify that selecting a font changes only right-side preview text and survives restart.
- [ ] Append a UTF-8 `STATUS_ALL.md` entry with changes, verification, failures/blockers, and next step. Do not stage status, temporary pytest folders, or visual brainstorm artifacts.
