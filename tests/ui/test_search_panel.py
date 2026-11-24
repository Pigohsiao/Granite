from pathlib import Path
import time

from PySide6.QtTest import QSignalSpy, QTest

from pigo_notes.services.vault_service import VaultService
from pigo_notes.ui.main_window import MainWindow


def test_search_input_is_debounced_and_emits_literal_query(isolated_config, qt_app) -> None:
    window = MainWindow(isolated_config)
    panel = getattr(window, "navigation_panel", None)
    assert panel is not None, "left-pane navigation panel is not implemented yet"
    spy = QSignalSpy(panel.searchRequested)
    panel.search_input.setText("中文 %_")

    QTest.qWait(100)
    assert spy.count() == 0
    assert spy.wait(500)
    assert spy.at(0)[0] == "中文 %_"
    window.close()


def test_search_result_opens_note_without_changing_tree_expansion(isolated_config, qt_app) -> None:
    VaultService(isolated_config.vault_root).save_note(Path("Folder/中文.md"), "# 找到的內容")
    window = MainWindow(isolated_config)
    panel = getattr(window, "navigation_panel", None)
    assert panel is not None, "left-pane navigation panel is not implemented yet"
    deadline = time.monotonic() + 3
    while window._index_controller._refresh_running and time.monotonic() < deadline:
        QTest.qWait(20)
    spy = QSignalSpy(window._index_controller.searchFinished)
    panel.show_mode("search")
    panel.search_input.setText("找到的內容")

    deadline = time.monotonic() + 4
    while (not panel.result_list.count()) and time.monotonic() < deadline:
        QTest.qWait(20)
    assert panel.result_list.count() == 1
    folder = window.note_tree.topLevelItem(0)
    assert folder.isExpanded() is False
    panel.result_list.itemClicked.emit(panel.result_list.item(0))

    assert window.current_note == Path("Folder/中文.md")
    assert folder.isExpanded() is False
    window.close()


def test_empty_search_does_not_show_every_note(isolated_config, qt_app) -> None:
    VaultService(isolated_config.vault_root).save_note(Path("A.md"), "alpha")
    window = MainWindow(isolated_config)
    panel = getattr(window, "navigation_panel", None)
    assert panel is not None, "left-pane navigation panel is not implemented yet"
    panel.show_mode("search")
    panel.search_input.clear()
    QTest.qWait(350)

    assert panel.result_list.count() == 0
    window.close()


def test_tag_mode_requests_indexed_tags_and_filters_search(isolated_config, qt_app) -> None:
    window = MainWindow(isolated_config)
    panel = window.navigation_panel
    requested = []
    panel.tagsRequested.connect(lambda: requested.append(True))
    panel.show_mode("tags")

    assert requested == [True]
    from pigo_notes.index_models import TagCount

    panel.set_tags([TagCount("work", 3)])
    panel.tag_list.itemClicked.emit(panel.tag_list.item(0))
    assert panel._tag == "work"
    assert panel.pages.currentWidget() is panel.search_page
    assert panel.clear_tag_button.isEnabled()
    panel.clear_tag_filter()
    assert panel._tag is None
    assert panel.clear_tag_button.isEnabled() is False
    window.close()
