from pathlib import Path

import pytest

from pigo_notes.services.git_service import GitResult, GitService


class FakeRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[Path, list[str]]] = []

    def run(self, repository: Path, git_args: list[str]) -> GitResult:
        self.calls.append((repository, git_args))
        return GitResult(True, "ok")


def test_invalid_branch_and_empty_message_never_start_a_git_command(tmp_path: Path) -> None:
    runner = FakeRunner()
    service = GitService(tmp_path, runner)

    with pytest.raises(ValueError, match="Commit message"):
        service.commit_all("   ")
    with pytest.raises(ValueError, match="Invalid branch"):
        service.create_branch("feature; rm -rf /")

    assert runner.calls == []


def test_allowed_actions_always_use_the_fixed_vault_repository(tmp_path: Path) -> None:
    runner = FakeRunner()
    service = GitService(tmp_path, runner)

    service.pull()
    service.commit_all("save notes")
    service.merge("feature/notes")
    service.push()
    service.create_branch("feature/tasks")
    service.switch_branch("main")

    assert runner.calls == [
        (tmp_path, ["pull"]),
        (tmp_path, ["add", "-A"]),
        (tmp_path, ["commit", "-m", "save notes"]),
        (tmp_path, ["merge", "feature/notes"]),
        (tmp_path, ["push"]),
        (tmp_path, ["switch", "-c", "feature/tasks"]),
        (tmp_path, ["switch", "main"]),
    ]
