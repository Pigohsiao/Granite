from html.parser import HTMLParser
from pathlib import Path

from pigo_notes.services.markdown_service import MarkdownService


class _TableProbe(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._table = []
            self.tables.append(self._table)
        elif tag == "tr" and self._table is not None:
            self._row = []
            self._table.append(self._row)
        elif tag in {"th", "td"} and self._row is not None:
            self._cell = []
            self._row.append("")

    def handle_data(self, data: str) -> None:
        if self._cell is not None and self._row is not None:
            self._cell.append(data)
            self._row[-1] = "".join(self._cell).strip()

    def handle_endtag(self, tag: str) -> None:
        if tag in {"th", "td"}:
            self._cell = None
        elif tag == "tr":
            self._row = None
        elif tag == "table":
            self._table = None


def _probe_tables(html: str) -> _TableProbe:
    probe = _TableProbe()
    probe.feed(html)
    return probe


def test_wikilinks_and_backlinks_are_resolved_from_markdown() -> None:
    service = MarkdownService()
    notes = {
        Path("Home.md"): "See [[Project Alpha]] and [[People/Ada|Ada]].",
        Path("Other.md"): "No link here.",
    }

    assert service.extract_wikilinks(notes[Path("Home.md")]) == {"Project Alpha", "People/Ada"}
    assert service.find_backlinks(notes, "Project Alpha") == [Path("Home.md")]


def test_markdown_preview_does_not_preserve_script_tags() -> None:
    html = MarkdownService().render("# Heading\n<script>alert('x')</script>")

    assert "<h1>Heading</h1>" in html
    assert "<script" not in html


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


def test_preview_hides_valid_frontmatter_but_preserves_malformed_frontmatter() -> None:
    service = MarkdownService()

    html = service.render("---\ntitle: Secret metadata\ntags: [work]\n---\n# Visible")
    malformed = service.render("---\ntags: [unfinished\n---\n# Still readable")

    assert "Secret metadata" not in html
    assert "Visible" in html
    assert "unfinished" in malformed
    assert "Still readable" in malformed


def test_wikilink_extraction_ignores_code_and_html_comments() -> None:
    source = """[[Visible]] `[[Inline]]`
```md
[[Fenced]]
```
<!-- [[Comment]] -->"""

    assert MarkdownService().extract_wikilinks(source) == {"Visible"}


def test_preview_renders_internal_links_with_safe_reader_route() -> None:
    html = MarkdownService().render("[[Folder/Note#Part|Display]]")

    assert 'href="pigo-note://open/Folder%2FNote%23Part%7CDisplay"' in html
    assert ">Display</a>" in html


def test_preview_does_not_turn_wikilinks_inside_code_or_comments_into_routes() -> None:
    html = MarkdownService().render("[[Visible]] `[[Inline]]`\n\n```md\n[[Fenced]]\n```\n<!-- [[Comment]] -->")

    assert html.count("pigo-note://open/") == 1
    assert "[[Inline]]" in html
    assert "[[Fenced]]" in html
    assert "<!-- [[Comment]] -->" in html
    assert "pigo-note://open/Comment" not in html


def test_markdown_preview_renders_standard_multiline_table() -> None:
    source = """| 欄位 | 負責人 |
| --- | --- |
| 設計 | Pigo |
| 驗證 | Luna |
"""

    html = MarkdownService().render(source)
    probe = _probe_tables(html)

    assert len(probe.tables) == 1, f"HTML: {html!r}"
    assert probe.tables[0] == [["欄位", "負責人"], ["設計", "Pigo"], ["驗證", "Luna"]]


def test_markdown_preview_renders_compact_four_column_table() -> None:
    source = "| 行動 | 負責人 | 期限 | 狀態 | | --- | --- | --- | --- | | 參閱報表 | 收件者 | 未提供 | 郵件請求 |"

    html = MarkdownService().render(source)
    probe = _probe_tables(html)

    assert len(probe.tables) == 1, f"HTML: {html!r}"
    assert probe.tables[0] == [
        ["行動", "負責人", "期限", "狀態"],
        ["參閱報表", "收件者", "未提供", "郵件請求"],
    ]


def test_markdown_preview_normalizes_user_example_to_four_columns() -> None:
    source = "**行動要求列表** | 行動 | 負責人 | 期限 | 狀態 | |---|---|---|---|---| | 參閱兩份 VCSEL IE/daily report 附件 | 收件者（未逐一指定） | 未提供 | 郵件請求 |"

    html = MarkdownService().render(source)
    probe = _probe_tables(html)

    assert html.index("<strong>行動要求列表</strong>") < html.index("<table>")
    assert len(probe.tables) == 1, f"HTML: {html!r}"
    assert probe.tables[0] == [
        ["行動", "負責人", "期限", "狀態"],
        ["參閱兩份 VCSEL IE/daily report 附件", "收件者（未逐一指定）", "未提供", "郵件請求"],
    ]


def test_pipe_prose_is_not_promoted_to_table() -> None:
    html = MarkdownService().render("This prose | has pipes | but is not a table.")

    assert "<table>" not in html


def test_inline_code_pipe_is_preserved() -> None:
    html = MarkdownService().render("`left | right` is inline code, not a table.")

    assert "<table>" not in html
    assert "<code>left | right</code>" in html


def test_fenced_code_pipe_is_preserved() -> None:
    source = "```text\n| A | B |\n| --- | --- |\n| 1 | 2 |\n```"

    html = MarkdownService().render(source)

    assert "<table>" not in html
    assert "<pre><code" in html
    assert "| --- | --- |" in html


def test_escaped_pipe_is_preserved_in_cell() -> None:
    source = "| A | B |\n| --- | --- |\n| left\\|right | value |"

    html = MarkdownService().render(source)
    probe = _probe_tables(html)

    assert len(probe.tables) == 1, f"HTML: {html!r}"
    assert probe.tables[0] == [["A", "B"], ["left|right", "value"]]


def test_mismatched_table_column_count_is_not_guessed() -> None:
    source = "| A | B | C | | --- | --- | --- | --- | | one | two | three |"

    html = MarkdownService().render(source)

    assert "<table>" not in html
