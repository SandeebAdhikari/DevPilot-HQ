from devpilot.prompt import get_prompt_path
from pathlib import Path

def test_prompt_path_python_explain():
    result = get_prompt_path("explain", "python")
    assert Path(result).name == "explain_prompt.txt"

def test_prompt_path_react_fallback():
    result = get_prompt_path("refactor", "react")
    assert Path(result).name in {"refactor_react_prompt.txt", "refactor_prompt.txt"}

