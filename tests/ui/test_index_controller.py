import time
from pathlib import Path

import pigo_notes.ui as ui
from PySide6.QtCore import QTimer
from PySide6.QtTest import QSignalSpy, QTest

from pigo_notes.index_models import IndexUpdateReport, SearchHit
from pigo_notes.config import VaultConfig
from pigo_notes.services.vault_service import VaultService


def controller_type():
    value = getattr(ui, "IndexController", None)
    assert value is not None, "IndexController is not implemented yet"
    return value


class SlowIndex:
    def __init__(self, config: VaultConfig) -> None:
        self.config = config

    def refresh(self, *, full=False, cancel=None):
        time.sleep(0.25)
        return IndexUpdateReport()

    def search(self, query, tag, offset, limit):
        if query == "old":
            time.sleep(0.15)
            return [SearchHit(Path("Old.md"), query)]
        if self.config.vault_root.name == "A":
            time.sleep(0.15)
        return [SearchHit(Path(f"{self.config.vault_root.name}.md"), query)]

    def properties(self, _path):
        return {}

    def backlinks(self, _path):
        return []


def test_index_work_does_not_block_qt_event_loop(tmp_path, qt_app) -> None:
    config = VaultConfig(tmp_path / "app", tmp_path / "vault")
    config.app_root.mkdir()
    config.vault_root.mkdir()
    controller = controller_type()(config, service_factory=SlowIndex)
    ticks: list[None] = []
    timer = QTimer()
    timer.timeout.connect(lambda: ticks.append(None))
    timer.start(10)

    controller.start_vault(config)
    QTest.qWait(100)
    timer.stop()

    assert len(ticks) >= 5
    controller.shutdown()


def test_stale_search_response_is_ignored_after_vault_switch(tmp_path, qt_app) -> None:
    app_root = tmp_path / "app"
    app_root.mkdir()
    first = app_root / "A"
    second = app_root / "B"
    first.mkdir()
    second.mkdir()
    config_a = VaultConfig(app_root, first)
    config_b = VaultConfig(app_root, second)
    controller = controller_type()(config_a, service_factory=SlowIndex)
    spy = QSignalSpy(controller.searchFinished)

    controller.start_vault(config_a)
    controller.request_search("query")
    controller.start_vault(config_b)
    controller.request_search("query")

    deadline = time.monotonic() + 3
    while spy.count() < 1 and time.monotonic() < deadline:
        QTest.qWait(20)
    assert spy.count() == 1, (controller._pool.activeThreadCount(), len(controller._jobs), controller._refresh_running)
    assert [hit.relative_path for hit in spy.at(0)[2]] == [Path("B.md")]
    controller.shutdown()


def test_stale_search_response_is_ignored_after_newer_query(tmp_path, qt_app) -> None:
    app_root = tmp_path / "app"
    root = tmp_path / "vault"
    app_root.mkdir()
    root.mkdir()
    config = VaultConfig(app_root, root)
    controller = controller_type()(config, service_factory=SlowIndex)
    spy = QSignalSpy(controller.searchFinished)
    controller.request_search("old")
    controller.request_search("new")

    deadline = time.monotonic() + 3
    while spy.count() < 1 and time.monotonic() < deadline:
        QTest.qWait(20)
    assert spy.count() == 1, (
        controller._pool.activeThreadCount(), len(controller._jobs), controller._refresh_running
    )
    assert spy.at(0)[2][0].snippet == "new"
    controller.shutdown()


def test_refresh_requests_are_coalesced_and_shutdown_joins_workers(tmp_path, qt_app) -> None:
    app_root = tmp_path / "app"
    root = tmp_path / "vault"
    app_root.mkdir()
    root.mkdir()
    config = VaultConfig(app_root, root)
    calls: list[bool] = []

    class CountingIndex(SlowIndex):
        def refresh(self, *, full=False, cancel=None):
            calls.append(full)
            return super().refresh(full=full, cancel=cancel)

    controller = controller_type()(config, service_factory=CountingIndex)
    spy = QSignalSpy(controller.refreshFinished)
    controller.start_vault(config)
    for _ in range(8):
        controller.request_refresh()
    deadline = time.monotonic() + 3
    while spy.count() < 2 and time.monotonic() < deadline:
        QTest.qWait(20)
    controller.shutdown()

    assert spy.count() == 2
    assert calls == [False, False]


def test_real_index_refresh_result_reaches_controller(isolated_config, qt_app, monkeypatch) -> None:
    from pigo_notes.services.vault_index_service import VaultIndexService

    VaultService(isolated_config.vault_root).save_note(Path("Folder/Target.md"), "# Target")
    VaultService(isolated_config.vault_root).save_note(Path("Source.md"), "[[Folder/Target|target]]")
    events: list[str] = []
    original_refresh = VaultIndexService.refresh

    def trace_refresh(service, *, full=False, cancel=None):
        events.append("refresh-start")
        result = original_refresh(service, full=full, cancel=cancel)
        events.append("refresh-return")
        return result

    monkeypatch.setattr(VaultIndexService, "refresh", trace_refresh)
    for method_name in ("_scan_files", "_upsert", "_resolve_all_links"):
        original_method = getattr(VaultIndexService, method_name)

        def traced_method(self, *args, _method=original_method, _name=method_name, **kwargs):
            events.append(f"{_name}-start")
            result = _method(self, *args, **kwargs)
            events.append(f"{_name}-return")
            return result

        monkeypatch.setattr(VaultIndexService, method_name, traced_method)
    controller = controller_type()(isolated_config)
    spy = QSignalSpy(controller.refreshFinished)

    controller.start_vault(isolated_config)
    deadline = time.monotonic() + 10
    while spy.count() == 0 and time.monotonic() < deadline:
        QTest.qWait(20)

    assert spy.count() == 1, (
        events, controller._pool.activeThreadCount(), len(controller._jobs), controller._refresh_running
    )
    assert controller._refresh_running is False
    assert spy.at(0)[2] == ""
    controller.shutdown()
