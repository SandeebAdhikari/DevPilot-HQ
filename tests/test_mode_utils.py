from devpilot.mode_utils import get_prompt_version


def test_explain_prompt_version_mapping():
    assert get_prompt_version("explain", "python") == 1
    assert get_prompt_version("explain", "java") == 2
    assert get_prompt_version("explain", "c") == 3
    assert get_prompt_version("explain", "cpp") == 4
    assert get_prompt_version("explain", "react") == 5


def test_explain_unknown_language_uses_generic_prompt():
    assert get_prompt_version("explain", "rust") == 6
    assert get_prompt_version("explain", "plaintext") == 6


def test_refactor_prompt_version_mapping():
    assert get_prompt_version("refactor", "python") == 1
    assert get_prompt_version("refactor", "c") == 2
    assert get_prompt_version("refactor", "cpp") == 2
    assert get_prompt_version("refactor", "java") == 3
    assert get_prompt_version("refactor", "react") == 4


def test_refactor_unknown_language_uses_safe_generic_prompt():
    assert get_prompt_version("refactor", "go") == 5
    assert get_prompt_version("refactor", "plaintext") == 5
