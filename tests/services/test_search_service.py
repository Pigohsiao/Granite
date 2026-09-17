from pathlib import Path

from pigo_notes.services.search_service import SearchService


def test_search_matches_note_title_and_content_case_insensitively() -> None:
    results = SearchService().search(
        {
            Path("Projects/Alpha.md"): "The Laser roadmap",
            Path("Notes/Beta.md"): "A different topic",
        },
        "laser",
    )

    assert [result.relative_path for result in results] == [Path("Projects/Alpha.md")]
