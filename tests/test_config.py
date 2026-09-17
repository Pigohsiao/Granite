from pathlib import Path

from pigo_notes.config import VaultConfig


def test_default_configuration_uses_the_fixed_pigo_vault() -> None:
    config = VaultConfig.default()

    assert config.vault_root == Path(r"C:\Users\hsi67063\Documents\Pigo_Obsidian")
    assert config.app_root == Path(r"C:\Users\hsi67063\Documents\Pigo Notes App")
