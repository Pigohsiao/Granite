"""Application launcher."""

import sys

from PySide6.QtWidgets import QApplication

from pigo_notes.config import VaultConfig
from pigo_notes.services.single_instance_service import SingleInstanceGuard
from pigo_notes.ui.main_window import MainWindow


def main() -> int:
    config = VaultConfig.default().with_saved_vault()
    config.validate()
    instance_guard = SingleInstanceGuard(config.app_root / "app_data" / "pigo-notes-app.lock")
    if not instance_guard.try_acquire():
        return 0

    try:
        application = QApplication(sys.argv)
        window = MainWindow(config)
        window.show_for_user()
        return application.exec()
    finally:
        instance_guard.release()


if __name__ == "__main__":
    raise SystemExit(main())
