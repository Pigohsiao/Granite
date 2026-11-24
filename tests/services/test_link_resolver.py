from pathlib import Path

import pigo_notes.services as services


def resolver():
    resolver_type = getattr(services, "LinkResolver", None)
    assert resolver_type is not None, "LinkResolver is not implemented yet"
    return resolver_type


def test_link_resolution_rejects_unsafe_targets() -> None:
    resolver_type = resolver()
    candidates = [Path("Folder/Note.md")]
    for target in ("../../outside", "%2e%2e/%2e%2e/outside", "C:/outside.md", "\\\\server\\share", "file:///C:/secret"):
        result = resolver_type.resolve("Folder/Source.md", target, candidates)
        assert result.status == "rejected", target


def test_bare_name_prefers_same_folder_then_unique_vault_match() -> None:
    resolver_type = resolver()
    candidates = [Path("Folder/Note.md"), Path("Other/Remote.md")]

    same = resolver_type.resolve("Folder/Source.md", "Note", candidates)
    unique = resolver_type.resolve("Folder/Source.md", "Remote", candidates)

    assert same.status == "resolved" and same.candidates == (Path("Folder/Note.md"),)
    assert unique.status == "resolved" and unique.candidates == (Path("Other/Remote.md"),)


def test_duplicate_bare_names_are_ambiguous_and_missing_is_explicit() -> None:
    resolver_type = resolver()
    candidates = [Path("A/Note.md"), Path("B/Note.md")]

    ambiguous = resolver_type.resolve("Source.md", "Note", candidates)
    missing = resolver_type.resolve("Source.md", "Absent", candidates)

    assert ambiguous.status == "ambiguous"
    assert set(ambiguous.candidates) == {Path("A/Note.md"), Path("B/Note.md")}
    assert missing.status == "missing"


def test_relative_and_vault_root_paths_are_resolved_and_fragments_kept() -> None:
    resolver_type = resolver()
    candidates = [Path("Folder/Note.md"), Path("Shared/Page.md")]

    relative = resolver_type.resolve("Folder/Source.md", "./Note#Heading", candidates)
    rooted = resolver_type.resolve("Folder/Source.md", "Shared/Page", candidates)

    assert relative.status == "resolved"
    assert relative.candidates == (Path("Folder/Note.md"),)
    assert relative.fragment == "Heading"
    assert rooted.status == "resolved"
    assert rooted.candidates == (Path("Shared/Page.md"),)
