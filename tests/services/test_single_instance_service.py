from pathlib import Path

from pigo_notes.services.single_instance_service import SingleInstanceGuard


def test_single_instance_guard_rejects_second_lock_until_first_releases(tmp_path: Path) -> None:
    lock_path = tmp_path / "app_data" / "pigo-notes-app.lock"
    first = SingleInstanceGuard(lock_path)
    second = SingleInstanceGuard(lock_path)

    assert first.try_acquire() is True
    assert second.try_acquire() is False

    first.release()

    assert second.try_acquire() is True
    second.release()
