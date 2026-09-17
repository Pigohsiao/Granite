"""Restricted PowerShell-backed Git operations for the fixed Vault."""

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Protocol


@dataclass(frozen=True, slots=True)
class GitResult:
    succeeded: bool
    output: str


class GitRunner(Protocol):
    def run(self, repository: Path, git_args: list[str]) -> GitResult: ...


class PowerShellGitRunner:
    """Runs a fixed Git argument list through PowerShell without shell input."""

    _SCRIPT = "& { param([string]$repo, [string[]]$gitArgs) & git -C $repo @gitArgs }"

    def run(self, repository: Path, git_args: list[str]) -> GitResult:
        command = [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            self._SCRIPT,
            str(repository),
            *git_args,
        ]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        output = (completed.stdout + completed.stderr).strip()
        return GitResult(completed.returncode == 0, output)


class GitService:
    _BRANCH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")

    def __init__(self, vault_root: Path, runner: GitRunner | None = None) -> None:
        self._vault_root = vault_root.resolve()
        self._runner = runner or PowerShellGitRunner()

    def pull(self) -> GitResult:
        return self._run(["pull"])

    def commit_all(self, message: str) -> GitResult:
        cleaned = message.strip()
        if not cleaned:
            raise ValueError("Commit message cannot be empty")
        staged = self._run(["add", "-A"])
        if not staged.succeeded:
            return staged
        return self._run(["commit", "-m", cleaned])

    def merge(self, branch_name: str) -> GitResult:
        return self._run(["merge", self._validate_branch(branch_name)])

    def push(self) -> GitResult:
        return self._run(["push"])

    def create_branch(self, branch_name: str) -> GitResult:
        return self._run(["switch", "-c", self._validate_branch(branch_name)])

    def switch_branch(self, branch_name: str) -> GitResult:
        return self._run(["switch", self._validate_branch(branch_name)])

    def changed_file_count(self) -> int:
        result = self._run(["status", "--porcelain"])
        if not result.succeeded:
            return 0
        return len([line for line in result.output.splitlines() if line.strip()])

    def _run(self, git_args: list[str]) -> GitResult:
        return self._runner.run(self._vault_root, git_args)

    def _validate_branch(self, branch_name: str) -> str:
        cleaned = branch_name.strip()
        if (
            not self._BRANCH.fullmatch(cleaned)
            or ".." in cleaned
            or cleaned.endswith(".")
            or cleaned.endswith("/")
        ):
            raise ValueError("Invalid branch name")
        return cleaned
