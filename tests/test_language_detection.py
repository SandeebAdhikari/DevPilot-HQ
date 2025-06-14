from devpilot.onboard import detect_language_from_path

def test_detect_python_file(tmp_path):
    f = tmp_path / "main.py"
    f.write_text("print('hello')")  # simulate file
    assert detect_language_from_path(f) == "python"

def test_detect_react_file(tmp_path):
    f = tmp_path / "App.jsx"
    f.write_text("// react component")
    assert detect_language_from_path(f) == "react"

def test_detect_java_file(tmp_path):
    f = tmp_path / "MyClass.java"
    f.write_text("public class MyClass {}")
    assert detect_language_from_path(f) == "java"

def test_detect_unknown_file(tmp_path):
    f = tmp_path / "README.md"
    f.write_text("# readme")
    assert detect_language_from_path(f) == "python"  # fallback

