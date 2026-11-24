from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from pigo_notes.config import VaultConfig


@pytest.fixture
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app
    for widget in app.topLevelWidgets():
        widget.close()
    app.processEvents()


@pytest.fixture
def isolated_config(tmp_path: Path) -> VaultConfig:
    config = VaultConfig(app_root=tmp_path / "app", vault_root=tmp_path / "vault")
    config.app_root.mkdir()
    config.vault_root.mkdir()
    return config
