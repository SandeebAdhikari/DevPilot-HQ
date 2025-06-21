import json
import ast
import re
from pathlib import Path
from typing import Dict, Set
from devpilot.ollama_infer import run_ollama


REPO_MAP_PATH = Path(".devpilot/repomap.json")
REL_MAP_PATH = Path(".devpilot/relmap.json")


def load_repomap(repofile: Path) -> Dict[str, dict[str, object]]:
    with repofile.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_python_symbols(file_path: Path) -> Dict[str, list[str]]:
    classes: Set[str] = set()
    functions: Set[str] = set()
    imports: Set[str] = set()
    calls: Set[str] = set()

    try:
        code = file_path.read_text(encoding="utf-8")
        tree = ast.parse(code)
    except Exception as e:
        #print(f"⚠️ Skipping {file_path} — AST parse failed: {e}")
        return {"classes": [], "functions": [], "imports": [], "calls": []}

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.add(str(node.name))  # Convert to string immediately

        elif isinstance(node, ast.FunctionDef):
            functions.add(str(node.name))  # Convert to string immediately

        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name:
                    imports.add(str(alias.name.split(".")[0]))  # Convert to string

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(str(node.module.split(".")[0]))  # Convert to string

        elif isinstance(node, ast.Call):
            try:
                if isinstance(node.func, ast.Name):
                    calls.add(str(node.func.id))  # Convert to string
                elif isinstance(node.func, ast.Attribute):
                    calls.add(str(node.func.attr))  # Convert to string
            except Exception as e:
                print(f"⚠️ Error parsing call in {file_path}: {e}")

    # Now directly sort the sets (all elements are strings)
    return {
        "classes": sorted(classes),
        "functions": sorted(functions),
        "imports": sorted(imports),
        "calls": sorted(calls)
    }

def build_relational_map(repofile: Path = REPO_MAP_PATH) -> None:
    """
    Enriches repomap.json by parsing Python files for relationships.
    Writes output to relmap.json.
    """
    repomap = load_repomap(repofile)
    relmap = {}

    for path_str, meta in repomap.items():
        path = Path(path_str)
        if path.suffix != ".py":
            continue  # Only support Python for now

        symbols = parse_python_symbols(path)
        meta["symbols"] = {
            "classes": symbols["classes"],
            "functions": symbols["functions"],
        }
        meta["imports"] = symbols["imports"]
        meta["calls"] = symbols["calls"]
        relmap[path_str] = meta

    REL_MAP_PATH.write_text(json.dumps(relmap, indent=2), encoding="utf-8")
    print(f"✅ Relational map saved to: {REL_MAP_PATH}")


def extract_relationships(repofile: Path = REL_MAP_PATH) -> Dict[str, Set[str]]:
    repomap = load_repomap(repofile)
    relations: Dict[str, Set[str]] = {}

    for file_path, metadata in repomap.items():
        # Ensure 'imports' and 'calls' are always lists
        imports_raw = metadata.get("imports")
        calls_raw = metadata.get("calls")

        if not isinstance(imports_raw, list):
            #print(f"⚠️ 'imports' in {file_path} is not a list: {type(imports_raw)}. Using empty list.")
            imports_raw = []

        if not isinstance(calls_raw, list):
            #print(f"⚠️ 'calls' in {file_path} is not a list: {type(calls_raw)}. Using empty list.")
            calls_raw = []

        # Filter only string elements and build sets
        imports = {str(i) for i in imports_raw if isinstance(i, str)}
        calls = {str(c) for c in calls_raw if isinstance(c, str)}

        relations[file_path] = imports.union(calls)

    return relations

def scaffold_docs(relmap_path: Path = REL_MAP_PATH) -> str:
    """
    Builds and saves a high-level Markdown doc from relmap.json.
    Output saved to .devpilot/README_AI.md.
    """
    if not relmap_path.exists():
        return "❌ relmap.json not found."

    relmap_data = load_repomap(relmap_path)
    relations = extract_relationships(relmap_path)
    lines = ["# Project Scaffold\n", "## Key Files and Relationships\n"]

    for file, meta in relmap_data.items():
        lines.append(f"- {file}")

        from typing import cast
        symbols = cast(dict[str, list[str]], meta.get("symbols", {}))
        classes = symbols.get("classes", [])
        funcs = symbols.get("functions", [])

        if classes:
            lines.append(f"  - Classes: {', '.join(classes)}")
        if funcs:
            lines.append(f"  - Functions: {', '.join(funcs)}")

        imports = relations.get(file, set())
        if imports:
            lines.append(f"  - Imports or Calls: {', '.join(sorted(imports))}")

        lines.append("")

    output = "\n".join(lines)

    output_path = relmap_path.parent / "README_AI.md"
    try:
        output_path.write_text(output, encoding="utf-8")
    except Exception as e:
        print(f"❌ Failed to write scaffold: {e}")

    return output


def summarize_docs(repofile: Path = REL_MAP_PATH, model: str = "llama2") -> str:
    """
    Generates an English summary of the codebase structure using LLM.
    Saves to .devpilot/README_SUMMARY.md.
    """
    scaffold = scaffold_docs(repofile)

    # Defensive: Strip control chars that may break Ollama input
    scaffold = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', scaffold)

    # Cap scaffold size to avoid overload (approx. 5K chars)
    if len(scaffold) > 5000:
        scaffold = scaffold[:5000] + "\n\n...(truncated)"

    # System prompt and user prompt as before
    system_prompt = "You are a technical writer. Summarize this codebase's structure for a README."
    user_prompt = f"Here’s a high-level scaffold of the project:\n\n{scaffold}"

    try:
        summary = run_ollama(
            prompt=user_prompt,
            model=model,
            stream=False,
            system_prompt=system_prompt
        )
    except Exception as e:
        print(f"[red]❌ Failed to summarize with LLM:[/] {e}")
        return ""

    # Output path
    summary_path = repofile.parent / "README_SUMMARY.md"
    try:
        summary_path.write_text(summary.strip(), encoding="utf-8")
        print(f"\n✅ Summary saved to: {summary_path}")
    except Exception as e:
        print(f"[red]❌ Failed to write summary:[/] {e}")

    return summary.strip()

