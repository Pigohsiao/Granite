"""Background orchestration for per-Vault index operations."""

from __future__ import annotations

import hashlib
from threading import Event
from typing import Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from pigo_notes.config import VaultConfig
from pigo_notes.services.vault_index_service import VaultIndexService


class _JobSignals(QObject):
    finished = Signal(object, int, int, str, object, object)


class _Job(QRunnable):
    def __init__(self, session: int, request: int, kind: str, callback: Callable[[], object]) -> None:
        super().__init__()
        self.session = session
        self.request = request
        self.kind = kind
        self.callback = callback
        self.signals = _JobSignals()
        self.job_id = id(self)

    def run(self) -> None:
        try:
            self.signals.finished.emit(self.job_id, self.session, self.request, self.kind, self.callback(), "")
        except Exception as error:  # surface worker failures without killing the UI thread
            self.signals.finished.emit(self.job_id, self.session, self.request, self.kind, None, str(error))


class IndexController(QObject):
    searchFinished = Signal(int, int, object, str)
    contextFinished = Signal(int, object, object, object, str)
    refreshFinished = Signal(int, object, str)
    tagsFinished = Signal(int, object, str)
    statusChanged = Signal(str)

    def __init__(self, config: VaultConfig, *, service_factory: Callable[[VaultConfig], object] | None = None) -> None:
        super().__init__()
        self._config = config
        self._service_factory = service_factory or self._create_service
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(4)
        self._session = 0
        self._request = 0
        self._refresh_running = False
        self._refresh_pending = False
        self._pending_full = False
        self._refresh_cancel = Event()
        self._search_cancel = Event()
        self._shutting_down = False
        self._jobs: dict[int, _Job] = {}

    @staticmethod
    def index_path_for(config: VaultConfig):
        identity = str(config.vault_root.resolve()).casefold().encode("utf-8")
        digest = hashlib.sha256(identity).hexdigest()
        return config.app_root / "app_data" / "indexes" / digest / "index.sqlite3"

    @classmethod
    def _create_service(cls, config: VaultConfig) -> VaultIndexService:
        return VaultIndexService(config.vault_root, cls.index_path_for(config))

    def start_vault(self, config: VaultConfig) -> None:
        self._session += 1
        self._config = config
        self._refresh_cancel.set()
        self._search_cancel.set()
        self.request_refresh(full=False)

    def request_refresh(self, *, full: bool = False) -> None:
        if self._shutting_down:
            return
        if self._refresh_running:
            self._refresh_pending = True
            self._pending_full = self._pending_full or full
            if full:
                self._refresh_cancel.set()
            return
        self._launch_refresh(full)

    def _launch_refresh(self, full: bool) -> None:
        self._refresh_running = True
        self._refresh_cancel = Event()
        session = self._session
        config = self._config
        self.statusChanged.emit("索引更新中…")

        def refresh():
            return self._service_factory(config).refresh(full=full, cancel=self._refresh_cancel)

        self._submit(session, 0, "refresh", refresh)

    def request_search(self, query: str, tag: str | None = None, offset: int = 0) -> None:
        if self._shutting_down:
            return
        self._search_cancel.set()
        self._search_cancel = Event()
        self._request += 1
        request = self._request
        session = self._session
        config = self._config
        self.statusChanged.emit("搜尋中…")

        def search():
            service = self._service_factory(config)
            return service.search(query, tag, offset, 100)

        self._submit(session, request, "search", search)

    def request_note_context(self, relative_path, *, source: str | None = None) -> None:
        if self._shutting_down:
            return
        session = self._session
        config = self._config

        def context():
            service = self._service_factory(config)
            if source is not None:
                service.upsert(relative_path, source)
            return relative_path, service.properties(relative_path), service.backlinks(relative_path)

        self._submit(session, 0, "context", context)

    def request_tags(self) -> None:
        if self._shutting_down:
            return
        session, config = self._session, self._config

        def tags():
            return self._service_factory(config).tags()

        self._submit(session, 0, "tags", tags)

    def resolve_link(self, source_path, target):
        """Resolve one clicked link against this Vault's local index, never a filesystem scan."""
        return self._service_factory(self._config).resolve(source_path, target)

    def _submit(self, session: int, request: int, kind: str, callback: Callable[[], object]) -> None:
        job = _Job(session, request, kind, callback)
        job.signals.finished.connect(self._handle_result)
        self._jobs[job.job_id] = job
        self._pool.start(job)

    def _handle_result(
        self, job_id: int, session: int, request: int, kind: str, result: object, error: str
    ) -> None:
        self._jobs.pop(job_id, None)
        if kind == "refresh":
            self._refresh_running = False
            if session == self._session:
                self.refreshFinished.emit(session, result, error)
                self.statusChanged.emit(error or "索引已更新")
            if self._refresh_pending and not self._shutting_down:
                full = self._pending_full
                self._refresh_pending = self._pending_full = False
                self._launch_refresh(full)
            return
        if session != self._session:
            return
        if kind == "search" and request == self._request:
            self.searchFinished.emit(session, request, result or [], error)
            self.statusChanged.emit(error or "")
        elif kind == "context" and not error and isinstance(result, tuple):
            self.contextFinished.emit(session, result[0], result[1], result[2], "")
        elif kind == "tags":
            self.tagsFinished.emit(session, result or [], error)

    def shutdown(self) -> None:
        if self._shutting_down:
            return
        self._shutting_down = True
        self._refresh_pending = False
        self._refresh_cancel.set()
        self._search_cancel.set()
        self._pool.waitForDone()
