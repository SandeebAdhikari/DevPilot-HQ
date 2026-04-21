import json
from pathlib import Path
from pytest import MonkeyPatch
from devpilot.session_logger import log_session

def test_log_session_creates_file_and_index(tmp_path: Path, monkeypatch: MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    session_id = "test_session"
    content = "This is a test log."

    test_devpilot_dir = tmp_path / ".devpilot"
    test_devpilot_dir.mkdir(parents=True, exist_ok=True)
    monkey_index = test_devpilot_dir / "log_index.json"

    import devpilot.session_logger
    monkeypatch.setattr(devpilot.session_logger, "LOG_INDEX_PATH", monkey_index)

    # Call the function
    result_path = log_session(session_id, content, suffix="md", show=False)


    assert result_path is not None
    assert result_path.exists()
    assert result_path.read_text(encoding="utf-8") == content

    assert monkey_index.exists()
    log_data = json.loads(monkey_index.read_text(encoding="utf-8"))
    assert log_data[0]["session_id"] == session_id
    assert log_data[0]["path"] == str(result_path)
    assert log_data[0]["format"] == "markdown"


def test_log_session_dedupes_repeated_session_and_path(tmp_path: Path, monkeypatch: MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    session_id = "same_session"
    content = "Run output"

    test_devpilot_dir = tmp_path / ".devpilot"
    test_devpilot_dir.mkdir(parents=True, exist_ok=True)
    monkey_index = test_devpilot_dir / "log_index.json"

    import devpilot.session_logger
    monkeypatch.setattr(devpilot.session_logger, "LOG_INDEX_PATH", monkey_index)

    log_session(session_id, content, suffix="md", show=False)
    log_session(session_id, content, suffix="md", show=False)

    log_data = json.loads(monkey_index.read_text(encoding="utf-8"))
    assert len(log_data) == 1
    assert log_data[0]["session_id"] == session_id
