"""Markdown checkbox aggregation and safe state writeback."""

import re

from pigo_notes.models import Task
from pigo_notes.services.vault_service import VaultService


class TaskService:
    _TASK = re.compile(r"^(\s*[-*+]\s+\[([ xX])\]\s+)(.*)$")
    _CHECKBOX = re.compile(r"\[[ xX]\]")

    def __init__(self, vault: VaultService) -> None:
        self._vault = vault

    def list_tasks(self) -> list[Task]:
        tasks: list[Task] = []
        for note in self._vault.list_notes():
            for line_number, line in enumerate(self._vault.read_note(note.relative_path).splitlines()):
                match = self._TASK.match(line)
                if match:
                    tasks.append(
                        Task(
                            source_path=note.relative_path,
                            line_number=line_number,
                            text=match.group(3),
                            completed=match.group(2).casefold() == "x",
                        )
                    )
        return tasks

    def set_completed(self, task: Task, completed: bool) -> None:
        lines = self._vault.read_note(task.source_path).splitlines(keepends=True)
        if task.line_number >= len(lines):
            raise ValueError("Task source line no longer exists")
        source_line = lines[task.line_number]
        match = self._TASK.match(source_line.rstrip("\r\n"))
        if not match or match.group(3) != task.text:
            raise ValueError("Task source no longer matches")
        lines[task.line_number] = self._CHECKBOX.sub(
            "[x]" if completed else "[ ]", source_line, count=1
        )
        self._vault.save_note(task.source_path, "".join(lines))
