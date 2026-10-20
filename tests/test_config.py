from pathlib import Path
import json

from pigo_notes.config import VaultConfig


def test_default_configuration_uses_the_fixed_pigo_vault() -> None:
    config = VaultConfig.default()

    assert config.vault_root == Path(r"C:\Users\hsi67063\Documents\Pigo_Obsidian")
    assert config.app_root == Path(r"C:\Users\hsi67063\Documents\Pigo Notes App")


def test_saved_existing_vault_path_is_restored(tmp_path: Path) -> None:
    app_root = tmp_path / "app"
    default_vault = tmp_path / "default-vault"
    saved_vault = tmp_path / "other-vault"
    app_root.mkdir()
    default_vault.mkdir()
    saved_vault.mkdir()
    settings_path = app_root / "app_data" / "settings.json"
    settings_path.parent.mkdir()
    settings_path.write_text(json.dumps({"vault_root": str(saved_vault)}), encoding="utf-8")

    config = VaultConfig(app_root=app_root, vault_root=default_vault).with_saved_vault(settings_path)

    assert config.vault_root == saved_vault


def test_missing_or_invalid_saved_vault_keeps_default(tmp_path: Path) -> None:
    app_root = tmp_path / "app"
    default_vault = tmp_path / "default-vault"
    app_root.mkdir()
    default_vault.mkdir()
    settings_path = app_root / "settings.json"
    settings_path.write_text(json.dumps({"vault_root": str(tmp_path / "missing")}), encoding="utf-8")

    config = VaultConfig(app_root=app_root, vault_root=default_vault).with_saved_vault(settings_path)

    assert config.vault_root == default_vault
