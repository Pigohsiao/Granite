"""Opt-in scale check. All generated content stays inside pytest's temporary Vault."""

from pathlib import Path
from statistics import quantiles
from time import perf_counter
import sqlite3

import pytest

from pigo_notes.services.markdown_service import MarkdownService
from pigo_notes.services.vault_index_service import VaultIndexService
from pigo_notes.services.vault_service import VaultService


def p95(samples: list[float]) -> float:
    return quantiles(samples, n=20)[18]


@pytest.mark.performance
def test_10k_note_search_backlinks_and_preview_p95(tmp_path, capsys) -> None:
    root = tmp_path / "synthetic-vault"
    root.mkdir()
    vault = VaultService(root)
    service = VaultIndexService(root, tmp_path / "app" / "index.sqlite3")
    database = sqlite3.connect(service.database_path)
    database.execute("PRAGMA foreign_keys=ON")
    paths = [f"Notes/Note-{number:05}.md" for number in range(10_000)]
    database.executemany(
        "INSERT INTO notes VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
        ((path, path.casefold(), 40, 1, "synthetic", f"{path.casefold()}\nneedle common #shared [[target]]", "needle common #shared [[Target]]", "{}") for path in paths),
    )
    database.executemany(
        "INSERT INTO note_tags VALUES(?, ?, ?)", ((path, "shared", "shared") for path in paths)
    )
    database.executemany(
        "INSERT INTO note_links VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
        ((path, 0, "Target", None, "resolved", "Target.md", '["Target.md"]', path.casefold()) for path in paths),
    )
    database.commit()
    database.close()
    (root / "Target.md").write_text("# Target", encoding="utf-8")
    selected = Path("Notes/Note-05000.md")
    selected_path = root / selected
    selected_path.parent.mkdir(exist_ok=True)
    selected_path.write_text("# Note\nneedle common #shared [[Target]]\n", encoding="utf-8")

    search_samples = []
    backlink_samples = []
    for offset in range(30):
        started = perf_counter()
        service.search("needle", offset=offset * 100, limit=100)
        search_samples.append((perf_counter() - started) * 1000)
        started = perf_counter()
        service.backlinks(Path("Target.md"))
        backlink_samples.append((perf_counter() - started) * 1000)

    preview_samples = []
    markdown = MarkdownService()
    for _ in range(30):
        started = perf_counter()
        markdown.render(vault.read_note(selected))
        preview_samples.append((perf_counter() - started) * 1000)

    measured = {
        "synthetic_notes": 10_000,
        "search_p95_ms": round(p95(search_samples), 2),
        "backlinks_p95_ms": round(p95(backlink_samples), 2),
        "preview_read_render_p95_ms": round(p95(preview_samples), 2),
    }
    print(f"10k synthetic-note benchmark: {measured}")
    assert measured["search_p95_ms"] <= 500
    assert measured["backlinks_p95_ms"] <= 100
    assert measured["preview_read_render_p95_ms"] <= 200
