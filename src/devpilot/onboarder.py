from pathlib import Path
from rich.console import Console
from devpilot.onboard import handle_onboard
from devpilot.explain import handle_explain
from devpilot.refactor import handle_refactor
from devpilot.repomap_utils import update_repomap
import argparse
import json

console = Console()

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

    parser.add_argument(
        "--list-logs",
        action="store_true",
        help="List all saved session logs from .devpilot/log_index.json"
    )

    parser.add_argument(
        "--restore-log",
        type=str,
        metavar="SESSION_ID",
        help="Restore and print a log by session ID from log_index.json"
    )

    parser.add_argument(
        "--cleanup-logs",
        type=int,
        metavar="DAYS",
        help="Delete logs older than the specified number of days"
    )

    parser.add_argument(
        "--scaffold-docs",
        action="store_true",
        help="Generate a high-level codebase scaffold summary from repomap"
    )

    parser.add_argument(
        "--preview-prompt",
        action="store_true",
        help="Show the final rendered prompt for debugging (requires --mode and --repo_path)"
    )

    parser.add_argument(
        "--relmap",
        action="store_true",
        help="Build relational map from repomap.json"
    )

    return parser.parse_args()

def main():
    args = parse_args()

    if args.relmap:
        from devpilot.constants import REPO_MAP_PATH, REL_MAP_PATH
        if not REPO_MAP_PATH.exists():
            console.print("[red]❌ repomap.json not found. Run onboarding first.")
            return

        console.print("[blue]🔍 Building relational map and scaffold docs...[/]")
        from devpilot.rel_map import build_relational_map, scaffold_docs, summarize_docs
        from devpilot.session_logger import log_session

        try:
            build_relational_map(REPO_MAP_PATH)

            scaffold_docs(REL_MAP_PATH)

            summarize_docs(REL_MAP_PATH, model=args.model)

            summary_path = REL_MAP_PATH.parent / "README_SUMMARY.md"
            if summary_path.exists():
                content = summary_path.read_text(encoding="utf-8")
                log_session(
                    session_id="relmap_summary",
                    content=content,
                    format="markdown",
                    suffix="md"
                )
            else:
                from pathlib import Path
                ai_path = Path(REL_MAP_PATH).parent / "README_AI.md"
                if ai_path.exists():
                    content = ai_path.read_text(encoding="utf-8")
                    log_session(
                        session_id="relmap_scaffold",
                        content=content,
                        format="markdown",
                        suffix="md"
                    )

        except Exception as e:
            console.print(f"[red]❌ Failed during relmap processing:[/] {e}")
        return

    if args.scaffold_docs:
        from devpilot.rel_map import scaffold_docs
        try:
            from pathlib import Path
            relmap_path = Path(".devpilot/relmap.json")
            if not relmap_path.exists():
                console.print("[red]❌ relmap.json not found.[/]")
                return
            doc = scaffold_docs(relmap_path)
            console.print(doc)
        except Exception as e:
            console.print(f"[red]❌ Failed to scaffold docs:[/] {e}")
        return


    if args.cleanup_logs:
        from devpilot.session_logger import cleanup_logs 
        cleanup_logs(args.cleanup_logs)
        return


    if args.restore_log:
       from devpilot.session_logger import restore_log
       restore_log(args.restore_log)
       return

    if args.list_logs:
       from devpilot.session_logger import list_logs
       list_logs()
       return
 
    if args.clean and args.repo_path is None:
        from devpilot.constants import REPO_MAP_PATH, REPO_CACHE_PATH
        for path in [REPO_MAP_PATH, REPO_CACHE_PATH]:
            try:
                path.write_text("{}")
                console.print(f"[green]🧹 Cleared:[/] {path}")
            except Exception as e:
                console.print(f"[red]❌ Failed to clear {path}:[/] {e}")
        return


    if args.generate_map and args.repo_path is None:
        try:
            from pathlib import Path
            from devpilot.constants import REPO_MAP_PATH, REPO_CACHE_PATH, LAST_USED_PATH
            with open(LAST_USED_PATH) as f:
                repo_path: Path = Path(json.load(f)["repo_path"])
        except Exception:
            console.print(f"[red]❌ No previous repo path found. Please run onboarding first.")
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

    if args.preview_prompt:
        from devpilot.prompt import get_prompt_path, load_prompt_template

        # Onboarding requires existing maps
        if args.mode == "onboard":
            from pathlib import Path
            from devpilot.prompt_helpers import build_onboard_prompt_from_repomap
            repomap_path = Path(".devpilot/repomap.json")
            relmap_path = Path(".devpilot/relmap.json")
            if not repomap_path.exists():
                console.print("[red]❌ repomap.json not found. Run --generate-map first.[/]")
                return
            scaffold, _ = build_onboard_prompt_from_repomap(repomap_path, relmap_path)
            prompt_path = get_prompt_path("onboard")
            final_prompt = load_prompt_template(prompt_path, content=scaffold, lang=args.lang or "plaintext")

        else:
            if not args.repo_path:
                console.print("[red]❌ --preview-prompt requires <repo_path> for explain/refactor.[/]")
                return
            from pathlib import Path
            file_path = Path(args.repo_path)
            if not file_path.exists():
                console.print(f"[red]❌ File not found:[/] {file_path}")
                return
            code = file_path.read_text()
            prompt_path = get_prompt_path(args.mode)
            final_prompt = load_prompt_template(prompt_path, content=code, lang=args.lang or "plaintext")

        console.rule(f"[bold cyan]🔍 Previewing Prompt: {prompt_path.name}")
        console.print(final_prompt)
        return



    if args.mode == "onboard":
        handle_onboard(
        str(args.repo_path),
        model=args.model,
        mode=args.mode,
        lang=args.lang
    )
        try:
            from devpilot.rel_map import scaffold_docs, summarize_docs
            from devpilot.constants import REPO_MAP_PATH
            repofile = REPO_MAP_PATH
            scaffold_docs(repofile)
            summarize_docs(repofile, model=args.model)
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Relmap generation failed:[/] {e}")

    elif args.mode == "explain":
        handle_explain(str(args.repo_path), model=args.model, mode=args.mode, lang=args.lang)
    elif args.mode == "refactor":
        handle_refactor(str(args.repo_path), model=args.model, mode=args.mode, lang=args.lang)
    else:
        console.print(f"[red]❌ Unknown mode:[/] {args.mode}")

if __name__ == "__main__":
    main()

