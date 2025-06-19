from pathlib import Path
from rich.console import Console
from devpilot.onboard import handle_onboard
from devpilot.explain import handle_explain
from devpilot.refactor import handle_refactor
from devpilot.repomap_utils import update_repomap
from devpilot.constants import REPO_MAP_PATH, REPO_CACHE_PATH
import argparse
import json

console = Console()

LAST_USED_PATH = Path(".devpilot/last_used_path.json")

def parse_args():
    parser = argparse.ArgumentParser(
        prog="devpilot",
        description="DevPilot - Local codebase assistant"
    )
    parser.add_argument(
        "repo_path",
        type=Path,
        metavar="<repo_path>",
        nargs="?",
        help="Path to the file or codebase you want to analyze",
    )
    parser.add_argument(
        "--mode",
        choices=["onboard", "explain", "refactor"],
        default="onboard",
        help="Prompt mode to use: onboard, explain, or refactor",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="llama2",
        help="Ollama model to use (e.g., codellama:13b, mistral, llama2)",
    )
    parser.add_argument(
        "--lang",
        type=str,
        default=None,
        help="Optional language override (e.g., python, java, react, c)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Wipe .devpilot/repomap.json and repomap_cache.json (standalone only)"
    )
    parser.add_argument(
        "--generate-map",
        action="store_true",
        help="Standalone mode: generate mapping file for last used or current repo"
    )
    return parser.parse_args()

def main():
    args = parse_args()
 
    if args.clean and args.repo_path is None:
        for path in [REPO_MAP_PATH, REPO_CACHE_PATH]:
            try:
                path.write_text("{}")
                console.print(f"[green]🧹 Cleared:[/] {path}")
            except Exception as e:
                console.print(f"[red]❌ Failed to clear {path}:[/] {e}")
        return

    if args.generate_map and args.repo_path is None:
        try:
            with open(LAST_USED_PATH) as f:
                repo_path = Path(json.load(f)["repo_path"])
        except Exception:
            console.print("[red]❌ No previous repo path found. Please run onboarding first.")
            return

        update_repomap(
            repo_root=repo_path,
            repomap_path=REPO_MAP_PATH,
            cache_path=REPO_CACHE_PATH,
        )
        console.print("[green]✅ Repomap updated.[/]")
        try:
            view = input("👀 Do you want to view the mapping file now? [y/N] ").strip().lower()
            if view == "y":
                console.print(REPO_MAP_PATH.read_text())
        except KeyboardInterrupt:
            pass
        return

    if args.mode == "onboard":
        handle_onboard(
            str(args.repo_path),
            model=args.model,
            mode=args.mode,
            lang=args.lang
        )
    elif args.mode == "explain":
        handle_explain(str(args.repo_path), model=args.model, mode=args.mode, lang=args.lang)
    elif args.mode == "refactor":
        handle_refactor(str(args.repo_path), model=args.model, mode=args.mode, lang=args.lang)
    else:
        console.print(f"[red]❌ Unknown mode:[/] {args.mode}")

if __name__ == "__main__":
    main()

