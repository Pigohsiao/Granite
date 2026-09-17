"""Application configuration for the fixed local Pigo Vault."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class VaultConfig:
    """Locations owned by the Windows-local application."""

    app_root: Path
    vault_root: Path

    @classmethod
    def default(cls) -> "VaultConfig":
        return cls(
            app_root=Path(r"C:\Users\hsi67063\Documents\Pigo Notes App"),
            vault_root=Path(r"C:\Users\hsi67063\Documents\Pigo_Obsidian"),
        )

    def validate(self) -> None:
        if not self.app_root.exists():
            raise FileNotFoundError(f"App root does not exist: {self.app_root}")
        if not self.vault_root.is_dir():
            raise FileNotFoundError(f"Vault root does not exist: {self.vault_root}")
