# Pigo Notes App V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a testable Windows-local PySide6 application that reads and edits the fixed Pigo Vault, aggregates Markdown tasks, and exposes safe quick Git actions.

**Architecture:** The application keeps the Vault as the only note store. Focused services handle files, Markdown relationships, tasks, search, and restricted Git commands; the PySide6 UI composes them into a two-column workspace with an optional third information panel. Application settings and transient search data stay outside the Vault.

**Tech Stack:** Python 3.12+, PySide6, Markdown, pytest, PowerShell, Git for Windows.

---

## File structure

- `pyproject.toml` — dependency and test configuration.
- `src/pigo_notes/config.py` — fixed paths and app settings.
- `src/pigo_notes/models.py` — typed note, task, and Git result records.
- `src/pigo_notes/services/vault_service.py` — safe Vault scanning, UTF-8 reads/writes, daily-note creation.
- `src/pigo_notes/services/markdown_service.py` — Markdown rendering and `[[wiki link]]` parsing.
- `src/pigo_notes/services/task_service.py` — checkbox discovery and task-state writeback.
- `src/pigo_notes/services/search_service.py` — filename/content search.
- `src/pigo_notes/services/git_service.py` — only status-count, pull, commit-all, merge, push, branch actions.
- `src/pigo_notes/ui/main_window.py` — workspace, toolbars, panels, dialogs, and layout toggle.
- `src/pigo_notes/app.py` — application entry point.
- `tests/` — isolated tests using temporary Vault folders.

### Task 1: Bootstrap the Python project

**Files:**
- Create: `pyproject.toml`
- Create: `src/pigo_notes/__init__.py`
- Create: `src/pigo_notes/config.py`
- Create: `tests/test_config.py`

- [ ] Create `.venv` with `py -3 -m venv .venv`.
- [ ] Install `PySide6`, `Markdown`, and `pytest` inside the virtual environment.
- [ ] Write a failing test asserting `VaultConfig.default()` points to `C:\\Users\\hsi67063\\Documents\\Pigo_Obsidian`.
- [ ] Implement immutable `VaultConfig` with app-root and vault-root path validation.
- [ ] Run `python -m pytest tests/test_config.py -v` and expect PASS.
- [ ] Commit bootstrap files with message `chore: bootstrap PySide6 project`.

### Task 2: Implement safe UTF-8 Vault access

**Files:**
- Create: `src/pigo_notes/models.py`
- Create: `src/pigo_notes/services/vault_service.py`
- Create: `tests/services/test_vault_service.py`

- [ ] Test recursive `.md` discovery excludes `.git`, `.obsidian`, and hidden directories.
- [ ] Test UTF-8 note reading, atomic writing, and creation of a missing daily note.
- [ ] Implement `VaultService.list_notes()`, `read_note()`, `save_note()`, and `open_or_create_daily_note()`.
- [ ] Preserve line endings and reject a path outside the configured Vault.
- [ ] Run `python -m pytest tests/services/test_vault_service.py -v` and expect PASS.
- [ ] Commit with message `feat: add safe Vault note access`.

### Task 3: Implement Markdown links, rendering, search, and tasks

**Files:**
- Create: `src/pigo_notes/services/markdown_service.py`
- Create: `src/pigo_notes/services/search_service.py`
- Create: `src/pigo_notes/services/task_service.py`
- Create: `tests/services/test_markdown_service.py`
- Create: `tests/services/test_search_service.py`
- Create: `tests/services/test_task_service.py`

- [ ] Test parsing `[[Project]]` and resolving backlinks from a collection of notes.
- [ ] Test Markdown conversion produces HTML without executing raw script tags.
- [ ] Test filename/content search is case-insensitive.
- [ ] Test task aggregation parses `- [ ]` and `- [x]`, then rewrites exactly one selected checkbox.
- [ ] Implement small pure services for each behavior and return typed records from `models.py`.
- [ ] Run `python -m pytest tests/services -v` and expect PASS.
- [ ] Commit with message `feat: add Markdown search links and tasks`.

### Task 4: Implement restricted PowerShell Git service

**Files:**
- Create: `src/pigo_notes/services/git_service.py`
- Create: `tests/services/test_git_service.py`

- [ ] Test invalid branch names and empty commit messages are rejected before a subprocess starts.
- [ ] Test the runner always receives the fixed Vault path and only supports `pull`, `commit_all`, `merge`, `push`, `create_branch`, and `switch_branch`.
- [ ] Implement a command allowlist; use `powershell.exe -NoProfile -NonInteractive` and parameterized arguments, never user-supplied PowerShell text.
- [ ] Implement `changed_file_count()` only for the compact pre-commit summary.
- [ ] Run `python -m pytest tests/services/test_git_service.py -v` and expect PASS.
- [ ] Commit with message `feat: add safe Vault Git actions`.

### Task 5: Build the note workspace and layout toggle

**Files:**
- Create: `src/pigo_notes/ui/main_window.py`
- Create: `src/pigo_notes/app.py`
- Create: `tests/ui/test_main_window.py`

- [ ] Test a main window defaults to `two_column` layout and persists an explicit layout switch setting.
- [ ] Build a left Vault tree, central editor/preview tabs, and hidden right information panel.
- [ ] Add the compact `▯`/`▯▯` toolbar toggle; two-column is default and three-column reveals preview/backlinks/Git info.
- [ ] Open a selected note into the editor, render preview on text changes, and save with Ctrl+S.
- [ ] Run `python -m pytest tests/ui/test_main_window.py -v` with `QT_QPA_PLATFORM=offscreen` and expect PASS.
- [ ] Commit with message `feat: add Vault workspace UI`.

### Task 6: Add daily note and task interactions

**Files:**
- Modify: `src/pigo_notes/ui/main_window.py`
- Create: `tests/ui/test_task_interactions.py`

- [ ] Test the daily-note action calls `open_or_create_daily_note()`.
- [ ] Test toggling a task updates its source Markdown through `TaskService`.
- [ ] Add toolbar entries for Today and Tasks, and a task panel with open/completed filters.
- [ ] Show the source note for every task result and open it on selection.
- [ ] Run `python -m pytest tests/ui/test_task_interactions.py -v` and expect PASS.
- [ ] Commit with message `feat: add daily notes and task panel`.

### Task 7: Add compact Git quick actions and AI placeholder

**Files:**
- Modify: `src/pigo_notes/ui/main_window.py`
- Create: `tests/ui/test_git_actions.py`

- [ ] Test the Git menu exposes exactly Pull, Commit, Merge, Push, and Branch.
- [ ] Test Commit shows only the changed-file count and a message input before calling `commit_all()`.
- [ ] Add confirmation dialogs for pull, commit, merge, and push; add branch create/switch dialogs.
- [ ] Surface subprocess errors as concise dialogs and keep the App usable after failure.
- [ ] Add a disabled AI Assistant panel labelled “Coming soon — no data is sent in V1”.
- [ ] Run `python -m pytest tests/ui/test_git_actions.py -v` and expect PASS.
- [ ] Commit with message `feat: add quick Git controls`.

### Task 8: Package, verify, and document the test run

**Files:**
- Create: `README.md`
- Create: `scripts/run_app.ps1`
- Create: `tests/test_smoke.py`

- [ ] Test that the application can construct and close using the configured Vault without changing any note.
- [ ] Add a PowerShell launcher that activates `.venv` and starts `python -m pigo_notes.app`.
- [ ] Document setup, launch, tested capabilities, and the explicit V1 limitations.
- [ ] Run the full test suite with `python -m pytest -v` and `python -m compileall src`.
- [ ] Launch the App manually, verify note open/save, a task toggle, layout toggle, and Git menu visibility.
- [ ] Commit with message `docs: add Pigo Notes App usage guide`.
