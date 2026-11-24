from pathlib import Path

from pigo_notes.services.reading_session_service import ReadingSessionService


def test_recent_notes_are_deduplicated_capped_and_vault_scoped(tmp_path):
    root = tmp_path / "vault"
    other = tmp_path / "other"
    root.mkdir()
    other.mkdir()
    for index in range(25):
        (root / f"N{index}.md").write_text(f"# {index}", encoding="utf-8")
    history = ReadingSessionService(tmp_path / "app", root)
    isolated = ReadingSessionService(tmp_path / "app", other)

    for index in range(25):
        history.record(Path(f"N{index}.md"))
    history.record(Path("N24.md"))

    assert len(history.recent()) == 20
    assert history.recent()[0] == Path("N24.md")
    assert isolated.recent() == []


def test_recent_history_rejects_absolute_and_traversal_paths(tmp_path):
    history = ReadingSessionService(tmp_path, tmp_path / "vault")

    for invalid in (Path("../outside.md"), Path("C:/outside.md"), Path("attachment.pdf")):
        try:
            history.record(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted unsafe history path: {invalid}")


def test_back_forward_history_branching_and_positions_persist(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    for name in ("A.md", "B.md", "C.md"):
        (root / name).write_text("# note", encoding="utf-8")
    history = ReadingSessionService(tmp_path / "app", root)
    history.record(Path("A.md"))
    history.record(Path("B.md"))
    assert history.move_history(-1) == Path("A.md")
    assert history.move_history(1) == Path("B.md")
    assert history.move_history(1) is None
    history.move_history(-1)
    history.record(Path("C.md"))
    assert history.move_history(1) is None
    history.set_position(Path("C.md"), 123)
    assert history.position(Path("C.md")) == 123


def test_deleted_recent_and_history_entries_are_pruned(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    (root / "Keep.md").write_text("# keep", encoding="utf-8")
    history = ReadingSessionService(tmp_path / "app", root)
    history.record(Path("Keep.md"))
    (root / "Keep.md").unlink()

    assert history.recent() == []
    assert history.move_history(-1) is None


def test_corrupt_history_state_recovers_without_crashing(tmp_path):
    history = ReadingSessionService(tmp_path / "app", tmp_path / "vault")
    history.path.parent.mkdir(parents=True)
    history.path.write_text('{"recent": [], "history": [], "history_index": "bad"}', encoding="utf-8")

    assert history.recent() == []
    assert history.move_history(-1) is None
