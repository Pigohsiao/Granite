from pathlib import Path

from pigo_notes.services.task_service import TaskService
from pigo_notes.services.vault_service import VaultService


def test_tasks_are_aggregated_and_toggling_updates_the_source_note(tmp_path: Path) -> None:
    vault = VaultService(tmp_path)
    vault.save_note(Path("Daily Notes/2026-09-17.md"), "- [ ] Draft report\n- [x] Sent email\n")
    service = TaskService(vault)

    tasks = service.list_tasks()

    assert [(task.text, task.completed) for task in tasks] == [("Draft report", False), ("Sent email", True)]
    service.set_completed(tasks[0], True)
    assert vault.read_note(Path("Daily Notes/2026-09-17.md")) == "- [x] Draft report\n- [x] Sent email\n"
