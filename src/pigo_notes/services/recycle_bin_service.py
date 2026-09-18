"""Windows Recycle Bin operations constrained to one Vault."""

from __future__ import annotations

from pathlib import Path
import os
import subprocess


class RecycleBinService:
    """Moves only Vault children to the Windows Recycle Bin."""

    _SCRIPT = (
        "& { $Target = $env:PIGO_RECYCLE_TARGET; $Kind = $env:PIGO_RECYCLE_KIND; "
        "if ([string]::IsNullOrWhiteSpace($Target) -or [string]::IsNullOrWhiteSpace($Kind)) { throw 'Recycle target is missing.' }; "
        "Add-Type -AssemblyName Microsoft.VisualBasic; "
        "if ($Kind -eq 'directory') { "
        "[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory($Target, "
        "[Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs, "
        "[Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin) "
        "} else { "
        "[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile($Target, "
        "[Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs, "
        "[Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin) "
        "} }"
    )

    def __init__(self, vault_root: Path) -> None:
        self._vault_root = vault_root.resolve()

    def target_for(self, relative_path: Path) -> Path:
        target = (self._vault_root / relative_path).resolve()
        try:
            target.relative_to(self._vault_root)
        except ValueError as error:
            raise ValueError("Target must remain inside the configured Vault.") from error
        if target == self._vault_root:
            raise ValueError("The Vault root cannot be deleted.")
        if not target.exists():
            raise FileNotFoundError(target)
        return target

    def move_to_recycle_bin(self, relative_path: Path, *, is_directory: bool) -> None:
        target = self.target_for(relative_path)
        if target.is_dir() != is_directory:
            raise ValueError("Target type does not match the requested recycle operation.")
        environment = os.environ.copy()
        environment["PIGO_RECYCLE_TARGET"] = str(target)
        environment["PIGO_RECYCLE_KIND"] = "directory" if is_directory else "file"
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", self._SCRIPT],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=environment,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Unable to move the target to the Recycle Bin.")