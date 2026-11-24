# Granite Indexed Reader Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Preserve the app's local, read-only, fast-preview identity while adding indexed search, safe internal-link navigation and backlinks, recent-note navigation, read-only Properties, and tag filtering.

**Architecture:** Use a per-Vault SQLite cache in the app's `app_data`, populated and incrementally refreshed off the UI thread. The same index serves search, tags, link resolution, and backlinks. Opening a note reads only that note and never triggers a full-Vault content scan. Keep the existing two-pane layout; use switchable navigation in the left pane and collapsible context panels on the right.

**Tech Stack:** Python 3.12+, PySide6, Python-Markdown, stdlib `sqlite3`; use PyYAML `safe_load` only if dependency review confirms the need and resource bounds are tested.

**Reference designs:** `docs/superpowers/specs/2026-09-17-pigo-notes-app-design.md`, `docs/superpowers/specs/2026-09-17-readonly-fast-preview-design.md`, `docs/superpowers/specs/2026-09-22-standard-markdown-preview-design.md`.

## Constraints

- Windows local desktop app; UTF-8 Markdown; do not write note contents for these reader features.
- Do not restore hidden task, Git, or AI panels; no editor, Graph, Canvas, cloud sync, or plugins in this scope.
- Index files are rebuildable local cache under app data, partitioned and identity-checked per canonical Vault path; never place them in a Vault or commit them.
- First startup and explicit refresh may enumerate/read changed Vault notes in background. Note selection must not scan/read other notes.
- Failed/cancelled rebuild must leave the last valid index usable; index failure must not disable ordinary note reading.
- Preserve the existing untracked plan files; do not commit or push any changes.
- QA is a separate fresh `gpt-6-luna` agent. Success requires score >=96/100 and every hard gate below.

## Review Focus / Required Tests

1. A note open must not cause a Vault-wide read (`test_open_note_reads_only_selected_file`).
2. Malformed frontmatter and unreadable files must not erase source or break the index (`test_invalid_frontmatter_is_preserved`, `test_unreadable_note_does_not_abort_refresh`).
3. Ambiguous, missing, encoded traversal, UNC, and dangerous-scheme links must not open arbitrary files (`test_link_resolution_rejects_unsafe_targets`).
4. Late search/index responses from an old query or Vault must not replace current results (`test_stale_response_is_ignored_after_vault_switch`).
5. Interrupted/corrupt rebuild must retain the last committed index (`test_failed_rebuild_keeps_previous_index`).

## Implementation Tasks

### Task 0 — Isolate tests from the real Vault and establish read-only contracts

**Files:** `tests/conftest.py`, `tests/test_smoke.py`, `tests/ui/test_reader_contract.py`.

- Replace real-default-Vault UI smoke setup with temporary app/Vault fixtures.
- Add tests proving that note open reads only the selected note, does not call `list_notes`/backlink scans, and preserves the current preview if a selected file cannot be read.
- Add fixture teardown asserting worker threads/windows are closed.
- Run tests first and confirm the targeted new tests fail for the expected missing behavior; do not access or mutate the user's real Vault.

### Task 1 — Parse note metadata and links safely

**Files:** add `src/pigo_notes/services/note_parser.py`, `src/pigo_notes/index_models.py`, `tests/services/test_note_parser.py`; update `services/markdown_service.py` and, only if needed, `pyproject.toml`.

- Define `NoteParser.parse(source: str) -> ParsedNote`, returning body, properties, normalized tags, wikilinks (target/label/fragment), and warnings.
- Parse frontmatter only at document start; invalid/oversized YAML is warning-only, retains readable body, and cannot construct arbitrary Python objects.
- Ignore apparent links/tags inside fenced/inline code and comments; merge frontmatter and inline tags without duplicates; heading markers are not tags.
- Verify tests for Chinese/Unicode, aliases/fragments, malformed YAML, code blocks, and resource bounds.

### Task 2 — Build a per-Vault incremental SQLite index and deterministic resolver

**Files:** add `services/vault_index_service.py`, `services/link_resolver.py`, `tests/services/test_vault_index_service.py`, `tests/services/test_link_resolver.py`.

- Store canonical Vault identity, schema/parser version, relative path, file size/mtime/content fingerprint, searchable text, properties, tags, and source/target links.
- Required service operations: `refresh(full, cancel)`, `upsert(path, source)`, `remove(paths)`, `search(query, tag, offset, limit)`, `backlinks(target)`, `properties(path)`, `tags()`, `resolve(source_path, target)`.
- Unchanged refresh reads zero note bodies; changing one note rereads one body; deletion removes that note's index rows. A changed target re-resolves link targets without rereading all source bodies.
- Resolve relative links from source folder, vault-root paths from root, and bare names by same-folder then unique match. Return explicit resolved/missing/ambiguous/rejected outcomes; never pick an arbitrary ambiguous match or create a missing note.
- Rebuild into a temporary DB and swap only after validation/commit. On cancellation, DB failure, or read errors preserve the last valid index; report per-file errors and never mistake unreadable files for deletions. Reject symlinks/junctions escaping the Vault.
- Test Vault isolation, hidden/system directories, Unicode/case, duplicates/ambiguity, corrupted schema/database, cancellation, and recovery.

### Task 3 — Coordinate background indexing and stale-result cancellation

**Files:** add `ui/index_controller.py`, `tests/ui/test_index_controller.py`; update `ui/main_window.py` and app shutdown wiring as necessary.

- Expose `start_vault`, `request_refresh(full=False)`, `request_search(query, tag, offset=0)`, `request_note_context(path)`, `shutdown`.
- Run filesystem enumeration, parsing, index updates, and queries off the GUI thread; SQLite connections are thread-local.
- Attach Vault-session and request IDs to responses; ignore stale responses after query/Vault changes. Cancel/cleanly join workers on close.
- Index status/errors are visible, but index failure never blocks normal preview. Opening a note can upsert its already-read content only.
- Test GUI heartbeat during slow indexing, Vault switch while indexing, out-of-order search responses, coalesced refreshes, and clean shutdown.

### Task 4 — Add indexed search and tag navigation

**Files:** add `ui/navigation_panel.py`, `tests/services/test_indexed_search.py`, `tests/ui/test_search_panel.py`; update `services/search_service.py`, `ui/main_window.py`.

- Add left-pane modes for file tree, search, recent, and tags without increasing the permanent pane count.
- Search literal filename/content substrings case-insensitively, including Chinese; SQL wildcard characters are literal. Show safe plain-text snippets, empty/loading/error states, debounce at 250 ms, page 100 results, and allow load-more.
- Combine text and selected tag with AND; empty query and no tag returns no results. Clicking a result opens that note without changing tree expansion/scroll state.
- Test no UI search call materializes all note bodies or calls `VaultService.read_note`.

### Task 5 — Route wikilinks safely and show indexed backlinks

**Files:** add `ui/preview_browser.py`, `tests/ui/test_note_navigation.py`; update `services/markdown_service.py`, `ui/main_window.py`.

- Route internal links through one handler; support `[[note]]`, `[[folder/note]]`, `[[note|label]]`, and fragments as supported by the resolver. If a fragment is not implemented, open the note and clearly do not imply heading-level navigation.
- Display indexed backlinks in a collapsible panel. Missing links show a friendly message; ambiguous links offer candidate paths and cancellation leaves the current note unchanged.
- Block traversal, UNC, absolute paths, unsafe schemes, and encoded path tricks. HTTP(S) may open externally only via an explicit user click. Do not load arbitrary local/remote resources in preview.
- Preserve code-block text, safe HTML rendering, Markdown tables/headings, fonts, themes, and exact folder expansion paths.
- Tests cover correct routing, ambiguity, missing links, unsafe inputs, indexed backlinks, and existing preview regressions.

### Task 6 — Recent reading, positions, and read-only Properties

**Files:** add `services/reading_session_service.py`, `ui/note_details_panel.py`, `tests/services/test_reading_session_service.py`, `tests/ui/test_reading_context.py`; update `ui/main_window.py`.

- Persist per-Vault recent history (max 20), back/forward navigation, and preview scroll positions in app data without overwriting existing settings fields.
- Deduplicate recent entries; opening a new branch clears forward history; clamp restored scroll position if content changed; remove deleted/missing entries safely.
- Show frontmatter Properties in a collapsed-by-default read-only panel; no editing controls. Tags panel supports exact tag filtering, count, and clear action.
- Tests cover history semantics, persistence/corrupt-state recovery, Vault isolation, properties read-only behavior, tag deduplication/filtering, deletion edge cases, and Delete-key behavior in the file tree.

### Task 7 — End-to-end, performance, documentation, and regression verification

**Files:** add `tests/integration/test_reader_workflow.py` and `tests/performance/test_reader_performance.py`; update `README.md` and pytest markers in `pyproject.toml` if needed.

- End-to-end with temporary Vault: index → Chinese search → open result → follow wikilink → inspect backlinks → back/restore position → filter tag → switch Vault → refresh external change → restart.
- Synthetic 10,000-note performance dataset only; never stress-test or write the user's real Vault.
- Measure warm note-open p95 <=200 ms (preview update), search p95 <=500 ms (excluding debounce), backlinks p95 <=100 ms; event-loop heartbeat <=200 ms during indexing. Report machine/runtime and cold/warm conditions.
- Run full test suite and manual Windows checks for drag bar, keyboard navigation, themes, font selection, close/shutdown, and existing multi-delete/selection-position behaviors.
- Document index location, refresh/rebuild, supported link/tag/frontmatter syntax, limitations, and recovery.

## QA Scoring and Hard Gates

| Area | Points |
|---|---:|
| Search and tags correctness | 20 |
| Wikilinks, ambiguity handling, backlinks | 20 |
| Index refresh/recovery/Vault isolation | 20 |
| Read-only safety/security/existing regression | 20 |
| Performance/background work/switch/close | 15 |
| Documentation and evidence quality | 5 |
| **Total** | **100** |

QA agent must be a fresh `gpt-6-luna` instance and report each case as expected behavior, observed result, evidence, and score impact. Passing requires **at least 96/100** and all gates below. If below target, return findings to the implementation agent, fix, rerun affected tests plus full regression, then request a fresh Luna QA review; do not lower the rubric.

- No new feature writes or edits Markdown in the Vault.
- Selecting/opening one note never reads/scans other note bodies.
- No Vault-external file or unsafe URL can be opened by internal navigation.
- Stale results from another query/Vault cannot affect current UI.
- Index failure/cancellation does not block reading or destroy prior valid index.
- Existing delete confirmation, selection/scroll preservation, fonts, themes, single-instance behavior remain passing.
- Automated tests use temporary Vaults only; no important test is skipped while claiming it passed.
- Existing untracked plans remain untouched and are not staged/committed.

## Deferred

True multi-tab editor, filesystem watcher/live updates, heading/block embeds, unlinked mentions, advanced Obsidian search syntax, full tag management, Graph, Canvas, AI, Markdown editing, cloud sync, and plugin system.
