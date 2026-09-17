import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from pigo_notes.config import VaultConfig
from pigo_notes.ui.main_window import MainWindow


def test_main_window_defaults_to_two_columns_and_toggles_layout(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    config = VaultConfig(app_root=tmp_path / "app", vault_root=tmp_path / "vault")
    config.app_root.mkdir(parents=True)
    config.vault_root.mkdir(parents=True)

    window = MainWindow(config)

    assert window.layout_mode == "two_column"
    assert not window.info_panel.isVisible()
    window.toggle_layout()
    assert window.layout_mode == "three_column"
    window.toggle_layout()
    assert window.layout_mode == "two_column"
    window.close()
    app.processEvents()
