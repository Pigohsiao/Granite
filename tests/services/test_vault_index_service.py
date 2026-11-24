from pathlib import Path
from threading import Event
from concurrent.futures import ThreadPoolExecutor

import pigo_notes.services as services
from pigo_notes.services.vault_service import VaultService


def index_type():
    service_type = getattr(services, "VaultIndexService", None)
    assert service_type is not None, "VaultIndexService is not implemented yet"
    return service_type


def test_incremental_refresh_reads_only_added_or_changed_notes(tmp_path, monkeypatch) -> None:
    root = tmp_path / "vault"
    root.mkdir()
    vault = VaultService(root)
    vault.save_note(Path("A.md"), "# Alpha\nneedle")
    vault.save_note(Path("B.md"), "# Beta")
    service = index_type()(root, tmp_path / "index.sqlite3")
    calls: list[Path] = []
    original_read = VaultService.read_note

    def track_read(instance, path):
        calls.append(path)
        return original_read(instance, path)

    monkeypatch.setattr(VaultService, "read_note", track_read)
    first = service.refresh(full=True, cancel=Event())
    assert first.updated == 2
    calls.clear()

    second = service.refresh(full=False, cancel=Event())
    assert second.updated == 0
    assert calls == []

    vault.save_note(Path("A.md"), "# Alpha\nchanged")
    third = service.refresh(full=False, cancel=Event())
    assert third.updated == 1
    assert calls == [Path("A.md")]


def test_index_search_properties_tags_backlinks_and_removal(tmp_path) -> None:
    root = tmp_path / "vault"
    root.mkdir()
    vault = VaultService(root)
    vault.save_note(Path("Source.md"), "---\ntags: [工作]\nowner: Pigo\n---\nSee [[Target]] laser %_\n")
    vault.save_note(Path("Target.md"), "# Target\n中文內容")
    service = index_type()(root, tmp_path / "index.sqlite3")
    service.refresh(full=True, cancel=Event())

    assert [hit.relative_path for hit in service.search("%_", None, 0, 100)] == [Path("Source.md")]
    assert [hit.relative_path for hit in service.search("", "工作", 0, 100)] == [Path("Source.md")]
    assert service.properties(Path("Source.md"))["owner"] == "Pigo"
    assert service.backlinks(Path("Target.md")) == [Path("Source.md")]
    assert [(item.tag, item.count) for item in service.tags()] == [("工作", 1)]

    (root / "Source.md").unlink()
    report = service.refresh(full=False, cancel=Event())
    assert report.removed == 1
    assert service.backlinks(Path("Target.md")) == []


def test_index_is_bound_to_one_vault_and_skips_hidden_directories(tmp_path) -> None:
    first_root = tmp_path / "first"
    first_root.mkdir()
    VaultService(first_root).save_note(Path(".hidden/Secret.md"), "secret")
    VaultService(first_root).save_note(Path("Visible.md"), "visible")
    database = tmp_path / "index.sqlite3"
    service = index_type()(first_root, database)
    service.refresh(full=True, cancel=Event())

    second_root = tmp_path / "second"
    second_root.mkdir()
    try:
        index_type()(second_root, database)
    except ValueError as error:
        assert "Vault" in str(error)
    else:
        raise AssertionError("an index database must not be reused for another Vault")

    assert [hit.relative_path for hit in service.search("secret", None, 0, 100)] == []
    assert [hit.relative_path for hit in service.search("visible", None, 0, 100)] == [Path("Visible.md")]


def test_unreadable_note_does_not_abort_or_erase_previous_index(tmp_path, monkeypatch) -> None:
    root = tmp_path / "vault"
    root.mkdir()
    VaultService(root).save_note(Path("Note.md"), "# original")
    service = index_type()(root, tmp_path / "index.sqlite3")
    service.refresh(full=True, cancel=Event())
    VaultService(root).save_note(Path("Note.md"), "# changed")
    original_read = VaultService.read_note

    def fail_one(instance, path):
        if path == Path("Note.md"):
            raise PermissionError("synthetic unreadable note")
        return original_read(instance, path)

    monkeypatch.setattr(VaultService, "read_note", fail_one)
    report = service.refresh(full=False, cancel=Event())

    assert report.errors
    assert [hit.relative_path for hit in service.search("original", None, 0, 100)] == [Path("Note.md")]


def test_cancelled_refresh_keeps_committed_index(tmp_path) -> None:
    root = tmp_path / "vault"
    root.mkdir()
    VaultService(root).save_note(Path("Keep.md"), "keep")
    service = index_type()(root, tmp_path / "index.sqlite3")
    service.refresh(full=True, cancel=Event())
    cancel = Event()
    cancel.set()

    report = service.refresh(full=True, cancel=cancel)

    assert report.cancelled
    assert [hit.relative_path for hit in service.search("keep", None, 0, 100)] == [Path("Keep.md")]


def test_folder_wikilink_resolves_to_indexed_backlink(tmp_path) -> None:
    root = tmp_path / "vault"
    root.mkdir()
    vault = VaultService(root)
    vault.save_note(Path("Folder/Target.md"), "# Target")
    vault.save_note(Path("Source.md"), "[[Folder/Target|target note]]")
    service = index_type()(root, tmp_path / "index.sqlite3")

    report = service.refresh(full=True, cancel=Event())

    assert report.errors == ()
    assert service.backlinks(Path("Folder/Target.md")) == [Path("Source.md")]


def test_refresh_completes_when_run_in_a_background_thread(tmp_path) -> None:
    root = tmp_path / "vault"
    root.mkdir()
    vault = VaultService(root)
    vault.save_note(Path("Folder/Target.md"), "# Target")
    vault.save_note(Path("Source.md"), "[[Folder/Target|target note]]")
    service = index_type()(root, tmp_path / "index.sqlite3")

    with ThreadPoolExecutor(max_workers=1) as executor:
        report = executor.submit(service.refresh, full=True, cancel=Event()).result(timeout=4)

    assert report.updated == 2
    assert service.backlinks(Path("Folder/Target.md")) == [Path("Source.md")]


def test_index_database_is_not_left_open_after_refresh(tmp_path) -> None:
    root = tmp_path / "vault"
    root.mkdir()
    VaultService(root).save_note(Path("Note.md"), "searchable")
    database = tmp_path / "index.sqlite3"
    service = index_type()(root, database)

    service.refresh(full=True, cancel=Event())

    renamed = database.with_suffix(".moved")
    database.rename(renamed)
    renamed.rename(database)
