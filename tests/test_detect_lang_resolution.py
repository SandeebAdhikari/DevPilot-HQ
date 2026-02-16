from pathlib import Path

from devpilot.detect_lang import (
    normalize_language,
    prompt_for_language_if_unknown,
    resolve_language_with_user_prompt,
)


def test_normalize_language_aliases():
    assert normalize_language("JS") == "react"
    assert normalize_language("c++") == "cpp"
    assert normalize_language("python") == "python"


def test_prompt_for_unknown_uses_user_input(monkeypatch, tmp_path: Path):
    unknown_file = tmp_path / "legacy.foo"
    unknown_file.write_text("x", encoding="utf-8")

    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    resolved = prompt_for_language_if_unknown("plaintext", unknown_file, input_func=lambda _: "rust")

    assert resolved == "rust"


def test_prompt_for_unknown_enter_keeps_generic(monkeypatch, tmp_path: Path):
    unknown_file = tmp_path / "legacy.foo"
    unknown_file.write_text("x", encoding="utf-8")

    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    resolved = prompt_for_language_if_unknown("plaintext", unknown_file, input_func=lambda _: "")

    assert resolved == "plaintext"


def test_prompt_for_unknown_non_interactive_stays_generic(monkeypatch, tmp_path: Path):
    unknown_file = tmp_path / "legacy.foo"
    unknown_file.write_text("x", encoding="utf-8")

    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    resolved = prompt_for_language_if_unknown("plaintext", unknown_file, input_func=lambda _: "java")

    assert resolved == "plaintext"


def test_resolve_language_with_cli_override():
    resolved = resolve_language_with_user_prompt(Path("anything.unknown"), cli_lang="TypeScript")
    assert resolved == "react"
