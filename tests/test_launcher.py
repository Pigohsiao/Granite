from pathlib import Path


def test_windows_launcher_sets_local_source_path_and_runs_the_app() -> None:
    launcher = Path("scripts/run_app.ps1")

    assert launcher.exists()
    source = launcher.read_text(encoding="utf-8")
    assert "PYTHONPATH" in source
    assert "pigo_notes.app" in source
