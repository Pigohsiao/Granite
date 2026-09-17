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
