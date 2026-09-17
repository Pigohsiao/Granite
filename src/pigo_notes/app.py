"""Application launcher."""

import sys

from PySide6.QtWidgets import QApplication

from pigo_notes.config import VaultConfig
from pigo_notes.ui.main_window import MainWindow


def main() -> int:
    config = VaultConfig.default()
    config.validate()
    application = QApplication(sys.argv)
    window = MainWindow(config)
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
