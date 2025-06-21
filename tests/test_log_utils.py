import json
from pathlib import Path
from devpilot.session_logger import log_session

def test_log_session_creates_file_and_index(tmp_path: Path, monkeypatch):
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
