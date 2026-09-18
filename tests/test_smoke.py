import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from pigo_notes.config import VaultConfig
from pigo_notes.ui.main_window import MainWindow


def test_application_constructs_against_the_configured_vault() -> None:
    config = VaultConfig.default()
    config.validate()
    app = QApplication.instance() or QApplication([])

    window = MainWindow(config)

    assert window.windowTitle() == "Pigo Notes App"
    window.close()
    app.processEvents()


def test_main_window_opens_in_normal_state(tmp_path) -> None:
    config = VaultConfig(app_root=tmp_path / "app", vault_root=tmp_path / "vault")
    config.app_root.mkdir(parents=True)
    config.vault_root.mkdir(parents=True)
    app = QApplication.instance() or QApplication([])
    window = MainWindow(config)

    window.showMaximized()
    window.show_for_user()

    assert not window.isMaximized()
    window.close()
    app.processEvents()