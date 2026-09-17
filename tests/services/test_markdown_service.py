from pathlib import Path

from pigo_notes.services.markdown_service import MarkdownService


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
