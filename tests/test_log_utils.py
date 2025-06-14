from devpilot.log_utils import resolve_log_path

def test_log_filename_python():
    path = resolve_log_path("explain", lang="python", suppress_prompt=True)
    assert path.name == "explain_python.txt"

def test_log_filename_with_mode_only():
    path = resolve_log_path("onboard", suppress_prompt=True)
    assert path.name == "onboard.txt"

