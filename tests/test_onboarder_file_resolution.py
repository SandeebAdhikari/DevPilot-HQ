import json
from pathlib import Path
from pytest import MonkeyPatch

import devpilot.onboarder as onboarder


def test_resolve_mode_target_file_direct_path(tmp_path: Path):
    target = tmp_path / "a.py"
    target.write_text("print('x')", encoding="utf-8")

    resolved = onboarder.resolve_mode_target_file(target)
    assert resolved == target.resolve()


def test_resolve_mode_target_file_uses_last_onboarded_repo_for_unique_match(
    monkeypatch: MonkeyPatch, tmp_path: Path
):
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "src" / "main.py"
    target.parent.mkdir(parents=True)
    target.write_text("print('x')", encoding="utf-8")

    last_used = tmp_path / "last_used_path.json"
    last_used.write_text(json.dumps({"repo_path": str(repo)}), encoding="utf-8")
    monkeypatch.setattr(onboarder, "LAST_USED_PATH", last_used)

    resolved = onboarder.resolve_mode_target_file(Path("main.py"))
    assert resolved == target.resolve()


def test_resolve_mode_target_file_allows_relative_path_inside_last_repo(
    monkeypatch: MonkeyPatch, tmp_path: Path
):
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "pkg" / "util.py"
    target.parent.mkdir(parents=True)
    target.write_text("print('x')", encoding="utf-8")

    last_used = tmp_path / "last_used_path.json"
    last_used.write_text(json.dumps({"repo_path": str(repo)}), encoding="utf-8")
    monkeypatch.setattr(onboarder, "LAST_USED_PATH", last_used)

    resolved = onboarder.resolve_mode_target_file(Path("pkg/util.py"))
    assert resolved == target.resolve()


def test_resolve_mode_target_file_prompts_for_duplicate_names(
    monkeypatch: MonkeyPatch, tmp_path: Path
):
    repo = tmp_path / "repo"
    a = repo / "service_a" / "views.py"
    b = repo / "service_b" / "views.py"
    a.parent.mkdir(parents=True)
    b.parent.mkdir(parents=True)
    a.write_text("a", encoding="utf-8")
    b.write_text("b", encoding="utf-8")

    last_used = tmp_path / "last_used_path.json"
    last_used.write_text(json.dumps({"repo_path": str(repo)}), encoding="utf-8")
    monkeypatch.setattr(onboarder, "LAST_USED_PATH", last_used)

    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    def fake_input(prompt: str) -> str:
        _ = prompt
        return "2"
    monkeypatch.setattr("builtins.input", fake_input)

    resolved = onboarder.resolve_mode_target_file(Path("views.py"))
    assert resolved is not None
    assert resolved.name == "views.py"
    assert str(resolved.relative_to(repo)) == "service_b/views.py"


def test_disambiguation_labels_use_parent_and_file(tmp_path: Path):
    repo = tmp_path / "repo"
    a = repo / "src" / "component" / "view.py"
    b = repo / "component" / "main" / "view.py"
    a.parent.mkdir(parents=True)
    b.parent.mkdir(parents=True)
    a.write_text("a", encoding="utf-8")
    b.write_text("b", encoding="utf-8")

    labels = onboarder.build_disambiguation_labels([a, b], repo)

    assert labels[a] == "component/view.py"
    assert labels[b] == "main/view.py"


def test_disambiguation_labels_expand_when_parent_collides(tmp_path: Path):
    repo = tmp_path / "repo"
    a = repo / "apps" / "web" / "view.py"
    b = repo / "services" / "web" / "view.py"
    a.parent.mkdir(parents=True)
    b.parent.mkdir(parents=True)
    a.write_text("a", encoding="utf-8")
    b.write_text("b", encoding="utf-8")

    labels = onboarder.build_disambiguation_labels([a, b], repo)

    assert labels[a] == "apps/web/view.py"
    assert labels[b] == "services/web/view.py"
