import json
import hashlib
import ast
import re
from pathlib import Path
from typing import Dict, Any

REPO_CACHE_PATH = Path(".devpilot/repomap_cache.json")
REPO_MAP_PATH = Path(".devpilot/repomap.json")

SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", ".devpilot", ".next"}
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

def should_skip(path: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    if path.name in SKIP_FILES:
        return True
    return False

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

        result: Dict[str, Any] = {
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

def update_repomap(
    repo_root: Path,
    repomap_path: Path = REPO_MAP_PATH,
    cache_path: Path = REPO_CACHE_PATH,
    use_git: bool = False,
    use_watchdog: bool = False
) -> None:
    prev_hashes = load_json(cache_path)
    repomap = load_json(repomap_path)

    new_hashes: Dict[str, str] = {}
    changed_count = 0
    seen_files: set[str] = set()

    for file in repo_root.rglob("*"):
        if file.is_dir():
            continue

        rel_path = file.relative_to(repo_root)
        rel_path_str = str(rel_path)
        seen_files.add(rel_path_str)

        if should_skip(rel_path):
            continue

        file_hash = get_file_hash(file)
        new_hashes[rel_path_str] = file_hash

        if rel_path_str not in prev_hashes or prev_hashes[rel_path_str] != file_hash:
            metadata = extract_metadata(file)
            if metadata.get("language") != "unknown":
                repomap[rel_path_str] = metadata
                changed_count += 1

    # Always remove deleted or now-skipped files from repomap
    for rel_path_str in list(repomap):
        full_path = repo_root / rel_path_str
        if rel_path_str not in seen_files or should_skip(Path(rel_path_str)) or not full_path.exists():
            repomap.pop(rel_path_str, None)

    # Always clean up stale hashes
    for rel_path_str in list(prev_hashes):
        full_path = repo_root / rel_path_str
        if rel_path_str not in seen_files or should_skip(Path(rel_path_str)) or not full_path.exists():
            prev_hashes.pop(rel_path_str, None)

    save_json(repomap_path, repomap)
    save_json(cache_path, new_hashes)

    print(f"✅ Repomap updated: {len(repomap)} files mapped, {changed_count} changed.")

