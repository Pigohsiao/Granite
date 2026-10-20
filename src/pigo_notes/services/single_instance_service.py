"""Cross-process single-instance lock for the desktop application."""

from pathlib import Path

from PySide6.QtCore import QLockFile


class SingleInstanceGuard:
    """Own a lock file for as long as this application instance is running."""

    def __init__(self, lock_path: Path) -> None:
        self._lock = QLockFile(str(lock_path))

    def try_acquire(self) -> bool:
        Path(self._lock.fileName()).parent.mkdir(parents=True, exist_ok=True)
        return self._lock.tryLock(0)

    def release(self) -> None:
        if self._lock.isLocked():
            self._lock.unlock()
