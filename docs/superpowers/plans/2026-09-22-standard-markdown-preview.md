# Standard Markdown Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render standard and extended Markdown as clearly styled rich content in the Pigo Notes App preview.

**Architecture:** Extend `MarkdownService.render` from a narrow extension list to Python-Markdown's built-in `extra` extension bundle. Give `MainWindow` a theme-aware document stylesheet so the HTML elements produced by the renderer remain clear in dark and light modes.

**Tech Stack:** Python 3.12, Python-Markdown, PySide6, pytest.

---

### Task 1: Render extended Markdown structures

**Files:**
- Modify: `tests/services/test_markdown_service.py`
- Modify: `src/pigo_notes/services/markdown_service.py`

- [ ] **Step 1: Write the failing renderer test**

Append this test:

```python
def test_markdown_preview_renders_extended_standard_structures() -> None:
    source = """# Heading

> Quoted text

Term
: Definition

A footnote.[^1]

[^1]: Footnote text
"""
    html = MarkdownService().render(source)

    assert "<h1>Heading</h1>" in html
    assert "<blockquote>" in html
    assert "<dl>" in html
    assert "footnote" in html
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\services\test_markdown_service.py::test_markdown_preview_renders_extended_standard_structures -q --basetemp .test-tmp-markdown-red
```

Expected: FAIL because the current extension list does not render definition lists or footnotes.

- [ ] **Step 3: Use the built-in extended Markdown bundle**

Replace the renderer extension list with:

```python
return markdown.markdown(safe_source, extensions=["extra"])
```

- [ ] **Step 4: Run the targeted test to verify it passes**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\services\test_markdown_service.py::test_markdown_preview_renders_extended_standard_structures -q --basetemp .test-tmp-markdown-green
```

Expected: PASS.

### Task 2: Apply theme-aware preview document styling

**Files:**
- Modify: `tests/ui/test_main_window.py`
- Modify: `src/pigo_notes/ui/main_window.py`

- [ ] **Step 1: Write the failing preview stylesheet test**

Append this test:

```python
def test_preview_document_has_markdown_table_styles(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(make_config(tmp_path))

    assert "table" in window.note_preview.document().defaultStyleSheet()
    assert "border-collapse" in window.note_preview.document().defaultStyleSheet()

    window.close()
    app.processEvents()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\ui\test_main_window.py::test_preview_document_has_markdown_table_styles -q --basetemp .test-tmp-markdown-style-red
```

Expected: FAIL because no document stylesheet is set.

- [ ] **Step 3: Add theme-aware HTML document styles**

Add dark and light preview CSS constants to `MainWindow` for headings, tables, table cells, blockquotes, horizontal rules, inline code, and preformatted code. In `_apply_theme`, call:

```python
self.note_preview.document().setDefaultStyleSheet(
    self.LIGHT_PREVIEW_CSS if self.theme_mode == "light" else self.DARK_PREVIEW_CSS
)
```

- [ ] **Step 4: Run the targeted test to verify it passes**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\ui\test_main_window.py::test_preview_document_has_markdown_table_styles -q --basetemp .test-tmp-markdown-style-green
```

Expected: PASS.

- [ ] **Step 5: Run complete regression and static checks**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -vv --maxfail=1 --basetemp .test-tmp-markdown-verify
.\.venv\Scripts\python.exe -m compileall -q src
git diff --check
```

Expected: all tests pass; compilation and Git whitespace checks produce no errors.

- [ ] **Step 6: Commit implementation**

Run:

```powershell
git add src/pigo_notes/services/markdown_service.py src/pigo_notes/ui/main_window.py tests/services/test_markdown_service.py tests/ui/test_main_window.py
git commit -m "feat: enhance markdown preview rendering"
```

Expected: one commit containing extended renderer support, preview styles, and tests. `STATUS_ALL.md` remains local-only and excluded.
