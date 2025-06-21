from devpilot.detect_lang import detect_language_from_path
from pathlib import Path

def test_detect_python_file(tmp_path: Path):
    f = tmp_path / "main.py"
    f.write_text("// React component")
    assert detect_language_from_path(f) == "python"

def test_detect_react_file(tmp_path: Path):
    f = tmp_path / "App.jsx"
    f.write_text("// React component")
    assert detect_language_from_path(f) == "react"

def test_detect_java_file(tmp_path: Path):
    f = tmp_path / "Main.java"
    f.write_text("// React component")
    assert detect_language_from_path(f) == "java"


def test_detect_c_file(tmp_path: Path):
    f = tmp_path / "program.c"
    f.write_text("// React component")
    assert detect_language_from_path(f) == "c"

def test_detect_cpp_file(tmp_path: Path):
    f = tmp_path / "program.cpp"
    f.write_text("// React component")
    assert detect_language_from_path(f) == "cpp"

def test_fallback_unknown_extension(tmp_path: Path):
    f = tmp_path / "README.md"
    f.write_text("// React component")
    assert detect_language_from_path(f) == "python"

