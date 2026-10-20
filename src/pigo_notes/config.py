"""Application configuration for the fixed local Pigo Vault."""

from dataclasses import dataclass
import json
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

    def with_saved_vault(self, settings_path: Path | None = None) -> "VaultConfig":
        """Return this config with a previously selected, still-existing Vault."""
        settings_path = settings_path or self.app_root / "app_data" / "settings.json"
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            saved_path = settings.get("vault_root") if isinstance(settings, dict) else None
            saved_vault = Path(saved_path) if isinstance(saved_path, str) and saved_path.strip() else None
        except (OSError, json.JSONDecodeError):
            saved_vault = None
        if saved_vault is not None and saved_vault.is_dir():
            return VaultConfig(app_root=self.app_root, vault_root=saved_vault)
        return self

    def validate(self) -> None:
        if not self.app_root.exists():
            raise FileNotFoundError(f"App root does not exist: {self.app_root}")
        if not self.vault_root.is_dir():
            raise FileNotFoundError(f"Vault root does not exist: {self.vault_root}")
