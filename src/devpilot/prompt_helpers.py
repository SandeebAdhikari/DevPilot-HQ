# Inside onboard.py or a new helper module if needed
from pathlib import Path
from typing import Optional
import json


from devpilot.detect_lang import infer_repo_language

def build_onboard_prompt_from_repomap(
    repomap_path: Path,
    relmap_path: Optional[Path] = None,
    lang: Optional[str] = None
) -> tuple[str, str]:
    if not repomap_path.exists():
        return ("❌ repomap.json not found. Run onboarding with --generate-map first.", "plaintext")

    try:
        with open(repomap_path, "r", encoding="utf-8") as f:
            repomap = json.load(f)
    except Exception as e:
        return (f"❌ Failed to load repomap: {e}", "plaintext")

    relmap: dict[str, dict[str, list[str]]] = {}
    if relmap_path and relmap_path.exists():
        try:
            with open(relmap_path, "r", encoding="utf-8") as f:
                relmap = json.load(f)
        except Exception:
            pass  # Silently ignore malformed relmap

    lines = ["**Project Overview:**", ""]

    lines.append("This codebase contains the following key files:\n")

    lang_counter: dict[str, int] = {}

    for file, data in repomap.items():
        file_lang = data.get("language", "plaintext").lower()
        lang_counter[file_lang] = lang_counter.get(file_lang, 0) + 1

        lines.append(f"**{file}**")

        classes = list(data.get("classes", {}).keys())
        functions = list(data.get("functions", {}).keys())

        if not classes and not functions:
            lines.append("*No summary available.*")
        else:
            if classes:
                lines.append("Classes:")
                for cls in classes:
                    lines.append(f"- {cls}")
            if functions:
                lines.append("Functions:")
                for fn in functions:
                    lines.append(f"- {fn}")

        rel: dict[str, list[str]] = relmap.get(file, {})
        imports = rel.get("imports", [])
        calls = rel.get("calls", [])
        if imports or calls:
            lines.append("  - Interacts with:")
            if imports:
                lines.append(f"    - Imports: {', '.join(sorted(imports))}")
            if calls:
                lines.append(f"    - Calls: {', '.join(sorted(calls))}")

        lines.append("")  # Spacer

    lines.append("**Language Breakdown:**")
    for l, count in sorted(lang_counter.items(), key=lambda x: -x[1]):
        lines.append(f"- {l}: {count} files")

    if not lang:
        lang = max(lang_counter.items(), key=lambda x: x[1])[0] if lang_counter else "plaintext"

    return "\n".join(lines), lang or "plaintext"



