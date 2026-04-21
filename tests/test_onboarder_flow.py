import argparse
from pathlib import Path
from pytest import MonkeyPatch

import devpilot.onboarder as onboarder
import devpilot.prompt as prompt_module
import devpilot.prompt_helpers as prompt_helpers
import devpilot.rel_map as rel_map
import devpilot.session_logger as session_logger
from devpilot.constants import REPO_MAP_PATH, REL_MAP_PATH


def _args(**overrides):
    base = {
        "repo_path": None,
        "mode": "onboard",
        "model": "llama2",
        "lang": None,
        "clean": False,
        "generate_map": False,
        "list_logs": False,
        "restore_log": None,
        "cleanup_logs": None,
        "scaffold_docs": False,
        "preview_prompt": False,
        "relmap": False,
        "trace_entry": False,
        "trace_symbol": None,
        "trace_format": "md",
        "refresh_map": False,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def test_preview_onboard_uses_repomap_summary(monkeypatch: MonkeyPatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".devpilot").mkdir(parents=True)
    (tmp_path / ".devpilot" / "repomap.json").write_text("{}", encoding="utf-8")

    captured = {}

    def fake_build(*args, **kwargs):
        return "repo scaffold summary", "python"

    def fake_get_prompt_path(mode: str, version: int = 1):
        return Path(f"{mode}_v{version}.txt")

    def fake_load_prompt_template(_prompt_path: Path, **kwargs):
        captured.update(kwargs)
        return "rendered"

    monkeypatch.setattr(onboarder, "parse_args", lambda: _args(preview_prompt=True, mode="onboard"))
    monkeypatch.setattr(prompt_helpers, "build_onboard_prompt_from_repomap", fake_build)
    monkeypatch.setattr(prompt_module, "get_prompt_path", fake_get_prompt_path)
    monkeypatch.setattr(prompt_module, "load_prompt_template", fake_load_prompt_template)

    onboarder.main()

    assert captured["repomap_summary"] == "repo scaffold summary"
    assert "content" not in captured


def test_onboard_pipeline_runs_build_then_scaffold_then_summary(monkeypatch: MonkeyPatch):
    order = []

    def fake_build(path: Path):
        order.append(("build", path))

    def fake_scaffold(path: Path):
        order.append(("scaffold", path))
        return "doc"

    def fake_summary(path: Path, model: str = "llama2"):
        order.append(("summary", path, model))
        return "summary"

    monkeypatch.setattr(onboarder, "parse_args", lambda: _args(mode="onboard", repo_path=Path("any_repo")))
    monkeypatch.setattr(onboarder, "handle_onboard", lambda *args, **kwargs: "ok")
    monkeypatch.setattr(rel_map, "build_relational_map", fake_build)
    monkeypatch.setattr(rel_map, "scaffold_docs", fake_scaffold)
    monkeypatch.setattr(rel_map, "summarize_docs", fake_summary)

    onboarder.main()

    assert order == [
        ("build", REPO_MAP_PATH),
        ("scaffold", REL_MAP_PATH),
        ("summary", REL_MAP_PATH, "llama2"),
    ]


def test_session_logger_scaffold_docs_delegates_to_rel_map(monkeypatch: MonkeyPatch, tmp_path: Path):
    relmap_path = tmp_path / "relmap.json"
    called = {}

    def fake_relmap_scaffold(path: Path):
        called["path"] = path
        return "generated"

    monkeypatch.setattr(rel_map, "scaffold_docs", fake_relmap_scaffold)

    result = session_logger.scaffold_docs(relmap_path)

    assert result == "generated"
    assert called["path"] == relmap_path
