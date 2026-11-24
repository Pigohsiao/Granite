from pathlib import Path
import time
from urllib.parse import quote

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices, QTextDocument
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QInputDialog

from pigo_notes.services.vault_service import VaultService
from pigo_notes.ui.main_window import MainWindow


def wait_for(predicate, qt_app, timeout=15):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        QTest.qWait(20)
    assert predicate()


def test_wikilink_opens_target_and_displays_indexed_backlinks(isolated_config, qt_app) -> None:
    vault = VaultService(isolated_config.vault_root)
    vault.save_note(Path("Source.md"), "See [[Folder/Target|target note]].")
    vault.save_note(Path("Folder/Target.md"), "# Target")
    window = MainWindow(isolated_config)
    wait_for(lambda: not window._index_controller._refresh_running, qt_app)
    window._set_current_note(Path("Source.md"))
    target = "Folder/Target"
    window._route_preview_link(QUrl(f"pigo-note://open/{quote(target, safe='')}"))

    wait_for(lambda: window.current_note == Path("Folder/Target.md"), qt_app)
    wait_for(lambda: window.note_details.backlink_list.count() == 1, qt_app)
    assert window.note_details.backlink_list.item(0).data(256) == Path("Source.md")
    assert not window.note_details.backlinks_group.isChecked()
    window.close()


def test_unsafe_internal_link_is_rejected_without_changing_preview(isolated_config, qt_app) -> None:
    VaultService(isolated_config.vault_root).save_note(Path("Current.md"), "# Current")
    window = MainWindow(isolated_config)
    wait_for(lambda: not window._index_controller._refresh_running, qt_app)
    window._set_current_note(Path("Current.md"))
    before_html = window.note_preview.toHtml()
    target = quote("../../outside", safe="")

    window._route_preview_link(QUrl(f"pigo-note://open/{target}"))
    QTest.qWait(100)

    assert window.current_note == Path("Current.md")
    assert window.note_preview.toHtml() == before_html
    assert "拒絕" in window.statusBar().currentMessage()
    window.close()


def test_preview_never_auto_opens_external_links(isolated_config, qt_app, monkeypatch) -> None:
    VaultService(isolated_config.vault_root).save_note(Path("Current.md"), "# Current")
    window = MainWindow(isolated_config)
    window.note_preview.setHtml('<a href="https://example.com">external</a>')
    opened = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: opened.append(url) or True)

    assert window.note_preview.openExternalLinks() is False
    assert window.note_preview.loadResource(
        QTextDocument.ResourceType.ImageResource, QUrl("file:///C:/Windows/win.ini")
    ) is None
    assert window.note_preview.loadResource(
        QTextDocument.ResourceType.ImageResource, QUrl("https://example.com/pixel.png")
    ) is None
    window._route_preview_link(QUrl("javascript:alert(1)"))
    window._route_preview_link(QUrl("file:///C:/Windows/win.ini"))
    assert opened == []
    assert window.current_note is None
    window.close()


def test_ambiguous_link_cancel_leaves_current_note_unchanged(isolated_config, qt_app, monkeypatch) -> None:
    vault = VaultService(isolated_config.vault_root)
    vault.save_note(Path("Source.md"), "[[Note]]")
    vault.save_note(Path("A/Note.md"), "# A")
    vault.save_note(Path("B/Note.md"), "# B")
    window = MainWindow(isolated_config)
    wait_for(lambda: not window._index_controller._refresh_running, qt_app)
    window._set_current_note(Path("Source.md"))
    monkeypatch.setattr(QInputDialog, "getItem", lambda *args, **kwargs: ("", False))

    window._route_preview_link(QUrl(f"pigo-note://open/{quote('Note', safe='')}"))
    QTest.qWait(100)

    assert window.current_note == Path("Source.md")
    window.close()


def test_recent_and_back_forward_navigation_are_vault_local(isolated_config, qt_app) -> None:
    vault = VaultService(isolated_config.vault_root)
    vault.save_note(Path("A.md"), "# A")
    vault.save_note(Path("B.md"), "# B")
    window = MainWindow(isolated_config)
    window._set_current_note(Path("A.md"))
    window._set_current_note(Path("B.md"))

    window._move_reading_history(-1)
    assert window.current_note == Path("A.md")
    window._move_reading_history(1)
    assert window.current_note == Path("B.md")
    assert window.navigation_panel.recent_list.item(0).text() == "B.md"
    window.close()


def test_properties_are_visible_read_only_and_collapsed_by_default(isolated_config, qt_app) -> None:
    VaultService(isolated_config.vault_root).save_note(Path("Meta.md"), "---\ntitle: Reader\nowner: Pigo\n---\n# Body")
    window = MainWindow(isolated_config)
    window._set_current_note(Path("Meta.md"))
    wait_for(lambda: "Pigo" in window.note_details.properties_text.text(), qt_app)

    assert not window.note_details.properties_group.isChecked()
    assert window.note_details.properties_text.text().find('"owner": "Pigo"') >= 0
    window.close()
