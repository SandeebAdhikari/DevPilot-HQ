import os
import json
import hashlib
import ast
import re
from pathlib import Path
from typing import Dict, Any
import os
import json
import hashlib
import ast
import re
from pathlib import Path
from typing import Dict, Any

REPO_CACHE_PATH = Path(".devpilot/repomap_cache.json")
REPO_MAP_PATH = Path(".devpilot/repomap.json")

SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", ".devpilot", ".vscode", ".next"}
SKIP_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "tsconfig.json", "vite.config.ts", "webpack.config.js",
    "Dockerfile", "Makefile", "CMakeLists.txt"
}

def get_file_hash(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def extract_python_metadata(filepath: Path) -> Dict[str, Any]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)

        top_level_funcs = {}
        classes = {}

        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                top_level_funcs[node.name] = {
                    "signature": f"def {node.name}(...)",
                    "docstring": ast.get_docstring(node)
                }
            elif isinstance(node, ast.ClassDef):
                method_map = {}
                for sub in node.body:
                    if isinstance(sub, ast.FunctionDef):
                        method_map[sub.name] = {
                            "signature": f"def {sub.name}(...)",
                            "docstring": ast.get_docstring(sub)
                        }
                classes[node.name] = {
                    "docstring": ast.get_docstring(node),
                    "methods": method_map
                }

        return {
            "language": "python",
            "functions": top_level_funcs,
            "classes": classes,
            "docstring": ast.get_docstring(tree),
            "path": str(filepath)
        }
    except Exception as e:
        return {"error": str(e)}

def extract_js_metadata(filepath: Path) -> Dict[str, Any]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        functions = re.findall(r'(?:export\s+)?function\s+(\w+)\s*\(', source)
        classes = re.findall(r'class\s+(\w+)\s*[{\(]', source)
        default_export = re.findall(r'export\s+default\s+function\s+(\w+)?', source)

        result = {
            "language": "javascript",
            "functions": {name: {"signature": f"function {name}(...)"} for name in functions},
            "classes": {name: {} for name in classes},
            "default_export": default_export[0] if default_export else None,
            "path": str(filepath)
        }

        return result
    except Exception as e:
        return {"error": str(e)}

def extract_metadata(filepath: Path) -> Dict[str, Any]:
    suffix = filepath.suffix.lower()

    if suffix == ".py":
        return extract_python_metadata(filepath)
    elif suffix in {".js", ".jsx", ".ts", ".tsx"}:
        return extract_js_metadata(filepath)
    return {
        "language": "unknown",
        "path": str(filepath),
        "note": "No extractor defined for this file type"
    }

def update_repomap(repo_path: str, use_git: bool = False, use_watchdog: bool = False) -> None:
    repo_root = Path(repo_path).resolve()
    prev_hashes = load_json(REPO_CACHE_PATH)
    repomap = load_json(REPO_MAP_PATH)

    new_hashes = {}
    updated_map = repomap.copy()
    changed_count = 0

    for file in repo_root.rglob("*"):
        if file.is_dir():
            continue
        if any(part in SKIP_DIRS for part in file.parts):
            continue
        if file.name in SKIP_FILES:
            continue

        rel_path = str(file.relative_to(repo_root))
        file_hash = get_file_hash(file)
        new_hashes[rel_path] = file_hash

        if rel_path not in prev_hashes or prev_hashes[rel_path] != file_hash:
            metadata = extract_metadata(file)
            if metadata.get("language") != "unknown":
                updated_map[rel_path] = metadata
                changed_count += 1

    for rel_path in list(updated_map):
        if not (repo_root / rel_path).exists():
            updated_map.pop(rel_path, None)
            new_hashes.pop(rel_path, None)

    save_json(REPO_MAP_PATH, updated_map)
    save_json(REPO_CACHE_PATH, new_hashes)

    print(f"✅ Repomap updated: {len(updated_map)} files mapped, {changed_count} changed.")

