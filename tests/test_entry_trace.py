import json
from pathlib import Path

from devpilot.entry_trace import (
    build_file_graph,
    detect_entrypoints,
    find_symbol_definitions,
    find_symbol_references,
    generate_entry_trace,
    generate_symbol_trace,
    sanitize_symbol_filename,
    trace_from_entries,
)


def test_detect_entrypoints_uses_filename_and_function_hints():
    relmap = {
        "main.py": {"symbols": {"functions": ["main"]}, "calls": ["run"], "imports": []},
        "worker.py": {"symbols": {"functions": ["process"]}, "calls": [], "imports": []},
    }
    entries = detect_entrypoints(relmap)
    assert entries
    assert entries[0][0] == "main.py"
    assert any("entry-like filename" in reason for reason in entries[0][1])


def test_build_graph_and_trace_links_files_by_calls_and_imports():
    relmap = {
        "main.py": {
            "symbols": {"functions": ["main"]},
            "calls": ["run"],
            "imports": ["service"],
        },
        "service.py": {
            "symbols": {"functions": ["run"]},
            "calls": ["helper"],
            "imports": [],
        },
        "helper.py": {
            "symbols": {"functions": ["helper"]},
            "calls": [],
            "imports": [],
        },
    }
    graph = build_file_graph(relmap)
    traces = trace_from_entries(graph, ["main.py"], max_depth=4)
    files = [path for _, path in traces["main.py"]]
    assert "main.py" in files
    assert "service.py" in files
    assert "helper.py" in files


def test_generate_entry_trace_writes_report(tmp_path: Path):
    relmap_path = tmp_path / "relmap.json"
    relmap_content = {
        "app.py": {"symbols": {"functions": ["start"]}, "calls": [], "imports": []},
    }
    relmap_path.write_text(json.dumps(relmap_content), encoding="utf-8")

    report, output_path = generate_entry_trace(relmap_path, output_path=tmp_path / "ENTRY_TRACE.md")

    assert "Entry Trace Report" in report
    assert "app.py" in report
    assert output_path == (tmp_path / "ENTRY_TRACE.md")
    assert output_path.exists()


def test_symbol_detection_and_reference_mapping():
    relmap = {
        "app.py": {
            "symbols": {"functions": ["start"], "classes": []},
            "calls": ["start"],
            "imports": [],
        },
        "worker.py": {
            "symbols": {"functions": ["run"], "classes": ["Starter"]},
            "calls": [],
            "imports": ["app"],
        },
    }

    defs = find_symbol_definitions(relmap, "start")
    refs = find_symbol_references(relmap, "start")
    assert defs == ["app.py"]
    assert refs == ["app.py"]


def test_generate_symbol_trace_writes_report(tmp_path: Path):
    relmap_path = tmp_path / "relmap.json"
    relmap_content = {
        "app.py": {"symbols": {"functions": ["start"], "classes": []}, "calls": ["run"], "imports": []},
        "worker.py": {"symbols": {"functions": ["run"], "classes": []}, "calls": [], "imports": []},
    }
    relmap_path.write_text(json.dumps(relmap_content), encoding="utf-8")

    report, output_path = generate_symbol_trace(
        "start",
        relmap_path,
        output_path=tmp_path / "SYMBOL_TRACE_start.md"
    )

    assert "Symbol Trace Report" in report
    assert "Definitions" in report
    assert "References" in report
    assert output_path == (tmp_path / "SYMBOL_TRACE_start.md")
    assert output_path.exists()


def test_symbol_filename_sanitization():
    assert sanitize_symbol_filename("my::symbol/name") == "my_symbol_name"


def test_generate_entry_trace_json_and_mermaid(tmp_path: Path):
    relmap_path = tmp_path / "relmap.json"
    relmap_content = {
        "main.py": {"symbols": {"functions": ["main"]}, "calls": ["run"], "imports": []},
        "worker.py": {"symbols": {"functions": ["run"]}, "calls": [], "imports": []},
    }
    relmap_path.write_text(json.dumps(relmap_content), encoding="utf-8")

    json_report, json_path = generate_entry_trace(relmap_path, format="json")
    mermaid_report, mermaid_path = generate_entry_trace(relmap_path, format="mermaid")

    assert '"entrypoints"' in json_report
    assert json_path.name == "ENTRY_TRACE.json"
    assert mermaid_report.startswith("graph TD")
    assert mermaid_path.name == "ENTRY_TRACE.mmd"


def test_generate_symbol_trace_json_and_mermaid(tmp_path: Path):
    relmap_path = tmp_path / "relmap.json"
    relmap_content = {
        "app.py": {"symbols": {"functions": ["start"], "classes": []}, "calls": ["run"], "imports": []},
        "worker.py": {"symbols": {"functions": ["run"], "classes": []}, "calls": [], "imports": []},
    }
    relmap_path.write_text(json.dumps(relmap_content), encoding="utf-8")

    json_report, json_path = generate_symbol_trace("start", relmap_path, format="json")
    mermaid_report, mermaid_path = generate_symbol_trace("start", relmap_path, format="mermaid")

    assert '"symbol": "start"' in json_report
    assert json_path.name == "SYMBOL_TRACE_start.json"
    assert mermaid_report.startswith("graph TD")
    assert mermaid_path.name == "SYMBOL_TRACE_start.mmd"
