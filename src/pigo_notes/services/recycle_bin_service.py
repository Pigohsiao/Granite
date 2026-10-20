"""Windows Recycle Bin operations constrained to one Vault."""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Iterable
from pathlib import Path


class RecycleBinService:
    """Moves only Vault children to the Windows Recycle Bin."""

    _SCRIPT = """
        & {
            $Items = @(ConvertFrom-Json -InputObject $env:PIGO_RECYCLE_ITEMS)
            if ($Items.Count -eq 0) { throw 'Recycle targets are missing.' }
            Add-Type -AssemblyName Microsoft.VisualBasic
            $Failures = [System.Collections.Generic.List[string]]::new()
            foreach ($Item in $Items) {
                try {
                    if ($Item.kind -eq 'directory') {
                        [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory(
                            $Item.path,
                            [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs,
                            [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin)
                    } elseif ($Item.kind -eq 'file') {
                        [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile(
                            $Item.path,
                            [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs,
                            [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin)
                    } else {
                        throw 'Recycle target type is invalid.'
                    }
                } catch {
                    $Failures.Add("$($Item.path): $($_.Exception.Message)")
                }
            }
            if ($Failures.Count -gt 0) { throw ($Failures -join [Environment]::NewLine) }
        }
    """

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
        self.move_many_to_recycle_bin([(relative_path, is_directory)])

    def move_many_to_recycle_bin(self, items: Iterable[tuple[Path, bool]]) -> None:
        validated: list[dict[str, str]] = []
        seen: set[str] = set()
        for relative_path, is_directory in items:
            target = self.target_for(relative_path)
            if target.is_dir() != is_directory:
                raise ValueError("Target type does not match the requested recycle operation.")
            identity = str(target).casefold()
            if identity in seen:
                continue
            seen.add(identity)
            validated.append({"path": str(target), "kind": "directory" if is_directory else "file"})
        if not validated:
            return

        environment = os.environ.copy()
        environment["PIGO_RECYCLE_ITEMS"] = json.dumps(validated, ensure_ascii=False)
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", self._SCRIPT],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=environment,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Unable to move the target to the Recycle Bin.")
