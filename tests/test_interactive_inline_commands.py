from pathlib import Path
from pytest import MonkeyPatch

import devpilot.interactive as interactive


def test_inline_explain_command_triggers_file_explain(monkeypatch: MonkeyPatch):
    called = {}
    target = Path("/tmp/fake/views.py")

    import devpilot.onboarder
    import devpilot.explain

    monkeypatch.setattr(devpilot.onboarder, "resolve_mode_target_file", lambda _: target)

    def fake_handle_explain(file_path: str, model: str, mode: str, lang: str, interactive: bool):
        called["file_path"] = file_path
        called["model"] = model
        called["mode"] = mode
        called["lang"] = lang
        called["interactive"] = interactive
        return "ok"

    monkeypatch.setattr(devpilot.explain, "handle_explain", fake_handle_explain)

    handled = interactive._handle_inline_explain_command("/explain/views.py", model="llama2", lang="python")

    assert handled is True
    assert called["file_path"] == str(target)
    assert called["model"] == "llama2"
    assert called["mode"] == "explain"
    assert called["lang"] == "python"
    assert called["interactive"] is False


def test_inline_explain_command_ignores_non_command():
    handled = interactive._handle_inline_explain_command("explain views.py", model="llama2", lang="python")
    assert handled is False


def test_inline_explain_command_old_format_no_longer_triggers():
    handled = interactive._handle_inline_explain_command("explain/views.py", model="llama2", lang="python")
    assert handled is False


def test_inline_refactor_command_triggers_file_refactor(monkeypatch: MonkeyPatch):
    called = {}
    target = Path("/tmp/fake/views.py")

    import devpilot.onboarder
    import devpilot.refactor

    monkeypatch.setattr(devpilot.onboarder, "resolve_mode_target_file", lambda _: target)

    def fake_handle_refactor(file_path: str, model: str, mode: str, lang: str, interactive: bool):
        called["file_path"] = file_path
        called["model"] = model
        called["mode"] = mode
        called["lang"] = lang
        called["interactive"] = interactive
        return "ok"

    monkeypatch.setattr(devpilot.refactor, "handle_refactor", fake_handle_refactor)

    handled = interactive._handle_inline_refactor_command("/refactor/views.py", model="llama2", lang="python")

    assert handled is True
    assert called["file_path"] == str(target)
    assert called["model"] == "llama2"
    assert called["mode"] == "refactor"
    assert called["lang"] == "python"
    assert called["interactive"] is False


def test_inline_refactor_command_old_format_no_longer_triggers():
    handled = interactive._handle_inline_refactor_command("refactor/views.py", model="llama2", lang="python")
    assert handled is False


def test_inline_file_context_command_sets_context(monkeypatch: MonkeyPatch):
    target = Path("/tmp/fake/views.py")
    content = "def x():\n    return 1\n"

    import devpilot.onboarder
    monkeypatch.setattr(devpilot.onboarder, "resolve_mode_target_file", lambda _: target)
    monkeypatch.setattr(Path, "read_text", lambda self, encoding="utf-8": content)

    handled, context_block, context_label = interactive._handle_inline_file_context_command("/file/views.py")

    assert handled is True
    assert "Focused file context" in context_block
    assert "def x()" in context_block
    assert context_label == str(target)


def test_inline_file_context_command_clear():
    handled, context_block, context_label = interactive._handle_inline_file_context_command("/clearfile")
    assert handled is True
    assert context_block == ""
    assert context_label == ""


def test_inline_at_file_reference_sets_context_and_rewrites_question(monkeypatch: MonkeyPatch):
    target = Path("/tmp/fake/views.py")
    content = "def x():\n    return 1\n"

    import devpilot.onboarder
    monkeypatch.setattr(devpilot.onboarder, "resolve_mode_target_file", lambda _: target)
    monkeypatch.setattr(Path, "read_text", lambda self, encoding="utf-8": content)

    handled, context_block, context_label, rewritten = interactive._handle_inline_at_file_reference(
        "@views.py what does this file do?"
    )

    assert handled is True
    assert "Focused file context" in context_block
    assert context_label == str(target)
    assert rewritten == "what does this file do?"


def test_inline_at_file_reference_sets_context_without_rewritten_question(monkeypatch: MonkeyPatch):
    target = Path("/tmp/fake/views.py")
    content = "def x():\n    return 1\n"

    import devpilot.onboarder
    monkeypatch.setattr(devpilot.onboarder, "resolve_mode_target_file", lambda _: target)
    monkeypatch.setattr(Path, "read_text", lambda self, encoding="utf-8": content)

    handled, context_block, context_label, rewritten = interactive._handle_inline_at_file_reference("@views.py")

    assert handled is True
    assert "Focused file context" in context_block
    assert context_label == str(target)
    assert rewritten == ""


def test_inline_at_file_reference_supports_line_target(monkeypatch: MonkeyPatch):
    target = Path("/tmp/fake/views.py")
    content = "a\nb\nc\nd\ne\nf\ng\n"

    import devpilot.onboarder
    monkeypatch.setattr(devpilot.onboarder, "resolve_mode_target_file", lambda _: target)
    monkeypatch.setattr(Path, "read_text", lambda self, encoding="utf-8": content)

    handled, context_block, context_label, rewritten = interactive._handle_inline_at_file_reference(
        "@views.py:3 what happens here?"
    )

    assert handled is True
    assert "Focused file context" in context_block
    assert ">    3 | c" in context_block
    assert context_label.endswith(":3")
    assert rewritten == "what happens here?"


def test_implicit_file_reference_sets_context_and_rewrites_question(monkeypatch: MonkeyPatch):
    target = Path("/tmp/fake/views.py")
    content = "def x():\n    return 1\n"

    import devpilot.onboarder
    monkeypatch.setattr(devpilot.onboarder, "resolve_mode_target_file", lambda _: target)
    monkeypatch.setattr(Path, "read_text", lambda self, encoding="utf-8": content)

    handled, context_block, context_label, rewritten = interactive._handle_implicit_file_reference(
        "views.py what does this file do?"
    )

    assert handled is True
    assert "Focused file context" in context_block
    assert context_label == str(target)
    assert rewritten == "what does this file do?"


def test_implicit_file_reference_plain_sentence_does_not_trigger():
    handled, _, _, _ = interactive._handle_implicit_file_reference("can you explain this flow")
    assert handled is False
