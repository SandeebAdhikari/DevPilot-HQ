import json
import re
from collections import deque
from pathlib import Path
from typing import Any, Literal, cast

from devpilot.constants import REL_MAP_PATH

ENTRY_BASENAME_HINTS = {
    "__main__.py",
    "main.py",
    "app.py",
    "server.py",
    "manage.py",
    "wsgi.py",
    "asgi.py",
    "cli.py",
}

ENTRY_FUNCTION_HINTS = {
    "main",
    "run",
    "start",
    "serve",
    "bootstrap",
}

TraceFormat = Literal["md", "json", "mermaid"]
RelMap = dict[str, dict[str, Any]]
FileGraph = dict[str, set[str]]
TraceNodes = dict[str, list[tuple[int, str]]]


def _as_dict_str_any(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    raw_dict = cast(dict[object, Any], value)
    out: dict[str, Any] = {}
    for k, v in raw_dict.items():
        if isinstance(k, str):
            out[k] = v
    return out


def load_relmap(path: Path = REL_MAP_PATH) -> RelMap:
    with path.open("r", encoding="utf-8") as f:
        raw_obj: object = json.load(f)

    if not isinstance(raw_obj, dict):
        return {}
    raw_dict = cast(dict[object, object], raw_obj)

    normalized: RelMap = {}
    for key, value in raw_dict.items():
        if isinstance(key, str) and isinstance(value, dict):
            normalized[key] = _as_dict_str_any(value)
    return normalized


def detect_entrypoints(relmap: RelMap) -> list[tuple[str, list[str]]]:
    candidates: list[tuple[str, list[str], int]] = []

    for file_path, meta in relmap.items():
        reasons: list[str] = []
        basename = Path(file_path).name.lower()
        score = 0

        if basename in ENTRY_BASENAME_HINTS:
            reasons.append(f"entry-like filename: {basename}")
            score += 3

        symbols = _as_dict_str_any(meta.get("symbols"))
        funcs_raw = symbols.get("functions", [])
        functions = [str(fn).lower() for fn in funcs_raw if isinstance(fn, str)]
        for fn in functions:
            if fn in ENTRY_FUNCTION_HINTS:
                reasons.append(f"entry-like function: {fn}()")
                score += 2
                break

        calls_raw = meta.get("calls", [])
        calls = [str(c).lower() for c in calls_raw] if isinstance(calls_raw, list) else []
        if any(c in {"run", "serve", "start"} for c in calls):
            reasons.append("contains startup-style call sites")
            score += 1

        if reasons:
            candidates.append((file_path, reasons, score))

    if not candidates and relmap:
        # Fallback: include first python file so report still has a starting point.
        first_file = sorted(relmap.keys())[0]
        candidates.append((first_file, ["fallback: first mapped file"], 0))

    candidates.sort(key=lambda item: (-item[2], item[0]))
    return [(path, reasons) for path, reasons, _ in candidates]


def _build_symbol_index(relmap: RelMap) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    for file_path, meta in relmap.items():
        symbols = _as_dict_str_any(meta.get("symbols"))
        for key in ("functions", "classes"):
            values = symbols.get(key, [])
            if not isinstance(values, list):
                continue
            for symbol_value in values:
                if not isinstance(symbol_value, str):
                    continue
                symbol_name: str = symbol_value
                index.setdefault(symbol_name, set()).add(file_path)
    return index


def _build_module_stem_index(relmap: RelMap) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    for file_path in relmap:
        stem = Path(file_path).stem
        index.setdefault(stem, set()).add(file_path)
    return index


def build_file_graph(relmap: RelMap) -> FileGraph:
    symbol_index = _build_symbol_index(relmap)
    stem_index = _build_module_stem_index(relmap)
    graph: FileGraph = {file_path: set() for file_path in relmap}

    for file_path, meta in relmap.items():
        edges: set[str] = set()

        calls_raw = meta.get("calls", [])
        if isinstance(calls_raw, list):
            for call_name in calls_raw:
                if not isinstance(call_name, str):
                    continue
                for target in symbol_index.get(call_name, set()):
                    if target != file_path:
                        edges.add(target)

        imports_raw = meta.get("imports", [])
        if isinstance(imports_raw, list):
            for module in imports_raw:
                if not isinstance(module, str):
                    continue
                for target in stem_index.get(module, set()):
                    if target != file_path:
                        edges.add(target)

        graph[file_path] = edges

    return graph


def trace_from_entries(
    graph: FileGraph,
    entrypoints: list[str],
    max_depth: int = 4,
) -> TraceNodes:
    traces: TraceNodes = {}

    for entry in entrypoints:
        if entry not in graph:
            traces[entry] = [(0, entry)]
            continue

        visited: set[str] = {entry}
        queue: deque[tuple[str, int]] = deque([(entry, 0)])
        trace: list[tuple[int, str]] = [(0, entry)]

        while queue:
            node, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for nxt in sorted(graph.get(node, set())):
                if nxt in visited:
                    continue
                visited.add(nxt)
                trace.append((depth + 1, nxt))
                queue.append((nxt, depth + 1))

        traces[entry] = trace

    return traces


def render_entry_trace_markdown(
    entrypoints: list[tuple[str, list[str]]],
    traces: TraceNodes,
) -> str:
    lines = ["# Entry Trace Report", ""]
    if not entrypoints:
        lines.append("No entrypoints detected.")
        return "\n".join(lines)

    lines.append("## Detected Entrypoints")
    for path, reasons in entrypoints:
        lines.append(f"- `{path}`")
        for reason in reasons:
            lines.append(f"  - {reason}")
    lines.append("")

    lines.append("## Reachability Traces")
    for path, _ in entrypoints:
        lines.append(f"### `{path}`")
        trace = traces.get(path, [])
        if len(trace) <= 1:
            lines.append("- No downstream mapped files found.")
            lines.append("")
            continue

        for depth, file_path in trace:
            indent = "  " * depth
            marker = "->" if depth > 0 else "*"
            lines.append(f"{indent}{marker} `{file_path}`")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def _entry_trace_output_path(base_dir: Path, format: TraceFormat) -> Path:
    if format == "json":
        return base_dir / "ENTRY_TRACE.json"
    if format == "mermaid":
        return base_dir / "ENTRY_TRACE.mmd"
    return base_dir / "ENTRY_TRACE.md"


def generate_entry_trace(
    relmap_path: Path = REL_MAP_PATH,
    output_path: Path | None = None,
    format: TraceFormat = "md",
    max_depth: int = 4,
) -> tuple[str, Path]:
    if not relmap_path.exists():
        missing_path = output_path or _entry_trace_output_path(relmap_path.parent, format)
        return "   relmap.json not found.", missing_path

    relmap = load_relmap(relmap_path)
    entrypoints = detect_entrypoints(relmap)
    graph = build_file_graph(relmap)
    traces = trace_from_entries(graph, [path for path, _ in entrypoints], max_depth=max_depth)

    payload: dict[str, Any] = {
        "entrypoints": [{"path": p, "reasons": r} for p, r in entrypoints],
        "traces": {root: [{"depth": d, "path": p} for d, p in nodes] for root, nodes in traces.items()},
    }

    if format == "json":
        content = json.dumps(payload, indent=2)
        target = output_path or (relmap_path.parent / "ENTRY_TRACE.json")
    elif format == "mermaid":
        content = render_entry_trace_mermaid(graph, traces)
        target = output_path or (relmap_path.parent / "ENTRY_TRACE.mmd")
    else:
        content = render_entry_trace_markdown(entrypoints, traces)
        target = output_path or (relmap_path.parent / "ENTRY_TRACE.md")

    target.write_text(content, encoding="utf-8")
    return content, target


def sanitize_symbol_filename(symbol: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", symbol.strip())
    cleaned = cleaned.strip("._")
    return cleaned or "symbol"


def find_symbol_definitions(relmap: RelMap, symbol: str) -> list[str]:
    found: list[str] = []
    target = symbol.strip()
    if not target:
        return found

    for file_path, meta in relmap.items():
        symbols = _as_dict_str_any(meta.get("symbols"))
        funcs = symbols.get("functions", [])
        classes = symbols.get("classes", [])
        if isinstance(funcs, list) and any(isinstance(x, str) and x == target for x in funcs):
            found.append(file_path)
            continue
        if isinstance(classes, list) and any(isinstance(x, str) and x == target for x in classes):
            found.append(file_path)
    return sorted(found)


def find_symbol_references(relmap: RelMap, symbol: str) -> list[str]:
    found: list[str] = []
    target = symbol.strip()
    if not target:
        return found

    symbol_lower = target.lower()
    for file_path, meta in relmap.items():
        calls = meta.get("calls", [])
        imports = meta.get("imports", [])
        if isinstance(calls, list) and any(isinstance(x, str) and x == target for x in calls):
            found.append(file_path)
            continue
        if isinstance(imports, list) and any(isinstance(x, str) and x.lower() == symbol_lower for x in imports):
            found.append(file_path)
            continue
    return sorted(found)


def render_symbol_trace_markdown(
    symbol: str,
    definitions: list[str],
    references: list[str],
    traces: TraceNodes,
) -> str:
    lines = [f"# Symbol Trace Report: `{symbol}`", ""]

    lines.append("## Definitions")
    if definitions:
        for path in definitions:
            lines.append(f"- `{path}`")
    else:
        lines.append("- No direct definition found in mapped symbols.")
    lines.append("")

    lines.append("## References")
    if references:
        for path in references:
            lines.append(f"- `{path}`")
    else:
        lines.append("- No direct call/import references found.")
    lines.append("")

    lines.append("## Downstream Reachability From Definitions")
    if not definitions:
        lines.append("- Skipped (no definition roots found).")
    else:
        for root in definitions:
            lines.append(f"### `{root}`")
            trace = traces.get(root, [])
            if len(trace) <= 1:
                lines.append("- No downstream mapped files found.")
                lines.append("")
                continue
            for depth, file_path in trace:
                indent = "  " * depth
                marker = "->" if depth > 0 else "*"
                lines.append(f"{indent}{marker} `{file_path}`")
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def _symbol_trace_output_path(base_dir: Path, safe_symbol: str, format: TraceFormat) -> Path:
    if format == "json":
        return base_dir / f"SYMBOL_TRACE_{safe_symbol}.json"
    if format == "mermaid":
        return base_dir / f"SYMBOL_TRACE_{safe_symbol}.mmd"
    return base_dir / f"SYMBOL_TRACE_{safe_symbol}.md"


def generate_symbol_trace(
    symbol: str,
    relmap_path: Path = REL_MAP_PATH,
    output_path: Path | None = None,
    format: TraceFormat = "md",
    max_depth: int = 4,
) -> tuple[str, Path]:
    if not relmap_path.exists():
        safe_symbol = sanitize_symbol_filename(symbol)
        missing_path = output_path or _symbol_trace_output_path(relmap_path.parent, safe_symbol, format)
        return "   relmap.json not found.", missing_path

    relmap = load_relmap(relmap_path)
    graph = build_file_graph(relmap)
    definitions = find_symbol_definitions(relmap, symbol)
    references = find_symbol_references(relmap, symbol)
    traces = trace_from_entries(graph, definitions, max_depth=max_depth)

    payload: dict[str, Any] = {
        "symbol": symbol,
        "definitions": definitions,
        "references": references,
        "traces": {root: [{"depth": d, "path": p} for d, p in nodes] for root, nodes in traces.items()},
    }

    safe_symbol = sanitize_symbol_filename(symbol)
    if format == "json":
        content = json.dumps(payload, indent=2)
        target = output_path or (relmap_path.parent / f"SYMBOL_TRACE_{safe_symbol}.json")
    elif format == "mermaid":
        content = render_symbol_trace_mermaid(symbol, graph, definitions, references, traces)
        target = output_path or (relmap_path.parent / f"SYMBOL_TRACE_{safe_symbol}.mmd")
    else:
        content = render_symbol_trace_markdown(symbol, definitions, references, traces)
        target = output_path or (relmap_path.parent / f"SYMBOL_TRACE_{safe_symbol}.md")

    target.write_text(content, encoding="utf-8")
    return content, target


def _node_id(path: str) -> str:
    return "N_" + re.sub(r"[^A-Za-z0-9_]", "_", path)


def _reachable_nodes_from_traces(traces: TraceNodes) -> set[str]:
    nodes: set[str] = set()
    for entries in traces.values():
        for _, path in entries:
            nodes.add(path)
    return nodes


def render_entry_trace_mermaid(
    graph: FileGraph,
    traces: TraceNodes,
) -> str:
    reachable = _reachable_nodes_from_traces(traces)
    lines = ["graph TD"]

    for node in sorted(reachable):
        lines.append(f'  {_node_id(node)}["{node}"]')

    for src in sorted(reachable):
        for dst in sorted(graph.get(src, set())):
            if dst in reachable:
                lines.append(f"  {_node_id(src)} --> {_node_id(dst)}")

    return "\n".join(lines).strip() + "\n"


def render_symbol_trace_mermaid(
    symbol: str,
    graph: FileGraph,
    definitions: list[str],
    references: list[str],
    traces: TraceNodes,
) -> str:
    reachable = _reachable_nodes_from_traces(traces)
    for path in definitions:
        reachable.add(path)
    for path in references:
        reachable.add(path)

    lines = ["graph TD", f'  SYMBOL["symbol: {symbol}"]']
    for node in sorted(reachable):
        lines.append(f'  {_node_id(node)}["{node}"]')

    for d in sorted(definitions):
        lines.append(f"  SYMBOL --> {_node_id(d)}")
    for r in sorted(references):
        lines.append(f"  {_node_id(r)} --> SYMBOL")

    for src in sorted(reachable):
        for dst in sorted(graph.get(src, set())):
            if dst in reachable:
                lines.append(f"  {_node_id(src)} --> {_node_id(dst)}")

    return "\n".join(lines).strip() + "\n"
