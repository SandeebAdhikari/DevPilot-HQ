from pathlib import Path
from typing import Optional
from rich.console import Console
from devpilot.onboard import handle_onboard
from devpilot.explain import handle_explain
from devpilot.refactor import handle_refactor
from devpilot.repomap_utils import update_repomap, refresh_repomap
from devpilot.constants import LAST_USED_PATH
import argparse
import json
import sys

console = Console()


def get_last_onboarded_repo() -> Optional[Path]:
    try:
        data = json.loads(LAST_USED_PATH.read_text(encoding="utf-8"))
        repo_path = Path(data["repo_path"]).expanduser().resolve()
        return repo_path if repo_path.exists() and repo_path.is_dir() else None
    except Exception:
        return None


def _candidate_label(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def _build_disambiguation_labels(candidates: list[Path], repo_root: Path) -> dict[Path, str]:
    rel_parts: dict[Path, tuple[str, ...]] = {}
    for candidate in candidates:
        try:
            rel = candidate.relative_to(repo_root)
            rel_parts[candidate] = rel.parts
        except ValueError:
            rel_parts[candidate] = candidate.parts

    # Start with parent/file where possible; expand ancestors only if collisions remain.
    depth = 2
    max_depth = max((len(parts) for parts in rel_parts.values()), default=1)
    while depth <= max_depth:
        labels = {
            candidate: "/".join(parts[-depth:]) if len(parts) >= depth else "/".join(parts)
            for candidate, parts in rel_parts.items()
        }
        if len(set(labels.values())) == len(candidates):
            return labels
        depth += 1

    return {candidate: "/".join(parts) for candidate, parts in rel_parts.items()}


def build_disambiguation_labels(candidates: list[Path], repo_root: Path) -> dict[Path, str]:
    return _build_disambiguation_labels(candidates, repo_root)


def _choose_file_from_candidates(candidates: list[Path], repo_root: Path) -> Optional[Path]:
    if not candidates:
        return None
    if len(candidates) == 1:
        selected = candidates[0]
        console.print(f"[green]Using:[/] {_candidate_label(selected, repo_root)}")
        return selected

    labels = build_disambiguation_labels(candidates, repo_root)
    console.print("[yellow]Multiple files found with that name. Select one:[/]")
    for idx, candidate in enumerate(candidates, start=1):
        console.print(f"{idx}. {labels[candidate]}")

    if not sys.stdin.isatty():
        console.print("[red]Non-interactive terminal: cannot select between multiple matches.[/]")
        return None

    while True:
        raw = input("Enter number (or press Enter to cancel): ").strip()
        if not raw:
            return None
        if raw.isdigit():
            chosen = int(raw)
            if 1 <= chosen <= len(candidates):
                return candidates[chosen - 1]
        console.print("[yellow]Invalid selection. Try again.[/]")


def resolve_mode_target_file(repo_path_arg: Optional[Path]) -> Optional[Path]:
    if repo_path_arg is None:
        console.print("[red]Please provide a file path or file name.[/]")
        return None

    user_path = Path(repo_path_arg).expanduser()

    if user_path.exists():
        if user_path.is_file():
            return user_path.resolve()
        console.print(f"[red]Expected a file, got directory:[/] {user_path}")
        return None

    repo_root = get_last_onboarded_repo()
    if not repo_root:
        console.print("[red]No onboarded repo context found. Run onboarding on a directory first.[/]")
        return None

    # If user passed a relative path (e.g., src/main.py), try exact path inside onboarded repo.
    if not user_path.is_absolute() and user_path.parent != Path("."):
        candidate = (repo_root / user_path).resolve()
        if candidate.exists() and candidate.is_file():
            return candidate
        console.print(f"[red]File not found in onboarded repo:[/] {user_path}")
        return None

    matches = sorted(
        [p for p in repo_root.rglob(user_path.name) if p.is_file()],
        key=lambda p: _candidate_label(p, repo_root),
    )

    if not matches:
        console.print(f"[red]Could not find '{user_path.name}' under onboarded repo:[/] {repo_root}")
        return None

    return _choose_file_from_candidates(matches, repo_root)

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
        "--refresh-map",
        action="store_true",
        help="Prototype mode: attempt incremental repomap refresh using file mtimes"
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
    parser.add_argument(
        "--trace-entry",
        action="store_true",
        help="Detect likely entry files and generate inter-file trace report from relmap"
    )
    parser.add_argument(
        "--trace-symbol",
        type=str,
        metavar="SYMBOL",
        help="Trace a function/class symbol through definitions, references, and downstream file graph"
    )
    parser.add_argument(
        "--trace-format",
        choices=["md", "json", "mermaid"],
        default="md",
        help="Output format for --trace-entry and --trace-symbol (md, json, mermaid)"
    )

    return parser.parse_args()

def main():
    args = parse_args()

    if args.relmap:
        from devpilot.constants import REPO_MAP_PATH, REL_MAP_PATH
        if not REPO_MAP_PATH.exists():
            console.print("[red]   repomap.json not found. Run onboarding first.")
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
            console.print(f"[red]   Failed during relmap processing:[/] {e}")
        return

    if getattr(args, "trace_entry", False):
        from devpilot.constants import REPO_MAP_PATH, REL_MAP_PATH
        from devpilot.rel_map import build_relational_map
        from devpilot.entry_trace import generate_entry_trace
        from devpilot.session_logger import log_session

        if not REL_MAP_PATH.exists():
            if not REPO_MAP_PATH.exists():
                console.print("[red]   repomap.json not found. Run onboarding first.[/]")
                return
            try:
                build_relational_map(REPO_MAP_PATH)
            except Exception as e:
                console.print(f"[red]   Failed to build relmap for trace:[/] {e}")
                return

        try:
            report, output_path = generate_entry_trace(REL_MAP_PATH, format=args.trace_format)
            console.print(f"[green] Entry trace saved to:[/] {output_path}")
            console.print(report)
            suffix = output_path.suffix.lstrip(".") or "txt"
            log_session(
                session_id="entry_trace",
                content=report,
                format="markdown" if args.trace_format == "md" else "text",
                suffix=suffix
            )
        except Exception as e:
            console.print(f"[red]   Failed to generate entry trace:[/] {e}")
        return

    if args.trace_symbol:
        from devpilot.constants import REPO_MAP_PATH, REL_MAP_PATH
        from devpilot.rel_map import build_relational_map
        from devpilot.entry_trace import generate_symbol_trace, sanitize_symbol_filename
        from devpilot.session_logger import log_session

        if not REL_MAP_PATH.exists():
            if not REPO_MAP_PATH.exists():
                console.print("[red]   repomap.json not found. Run onboarding first.[/]")
                return
            try:
                build_relational_map(REPO_MAP_PATH)
            except Exception as e:
                console.print(f"[red]   Failed to build relmap for symbol trace:[/] {e}")
                return

        try:
            report, output_path = generate_symbol_trace(
                args.trace_symbol,
                REL_MAP_PATH,
                format=args.trace_format
            )
            safe_symbol = sanitize_symbol_filename(args.trace_symbol)
            console.print(f"[green] Symbol trace saved to:[/] {output_path}")
            console.print(report)
            suffix = output_path.suffix.lstrip(".") or "txt"
            log_session(
                session_id=f"trace_symbol_{safe_symbol}",
                content=report,
                format="markdown" if args.trace_format == "md" else "text",
                suffix=suffix
            )
        except Exception as e:
            console.print(f"[red]   Failed to generate symbol trace:[/] {e}")
        return

    if args.scaffold_docs:
        from devpilot.rel_map import scaffold_docs
        try:
            from pathlib import Path
            relmap_path = Path(".devpilot/relmap.json")
            if not relmap_path.exists():
                console.print("[red]   relmap.json not found.[/]")
                return
            doc = scaffold_docs(relmap_path)
            console.print(doc)
        except Exception as e:
            console.print(f"[red]   Failed to scaffold docs:[/] {e}")
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
                console.print(f"[red]   Failed to clear {path}:[/] {e}")
        return


    if args.generate_map and args.repo_path is None:
        try:
            from pathlib import Path
            from devpilot.constants import REPO_MAP_PATH, REPO_CACHE_PATH, LAST_USED_PATH
            with open(LAST_USED_PATH) as f:
                repo_path: Path = Path(json.load(f)["repo_path"])
        except Exception:
            console.print(f"[red]   No previous repo path found. Please run onboarding first.")
            return

        update_repomap(
            repo_root=repo_path,
            repomap_path=REPO_MAP_PATH,
            cache_path=REPO_CACHE_PATH,
        )
        console.print("[green] Repomap updated.[/]")
        try:
            view = input("👀 Do you want to view the mapping file now? [y/N] ").strip().lower()
            if view == "y":
                console.print(REPO_MAP_PATH.read_text())
        except KeyboardInterrupt:
            pass
        return

    if args.refresh_map and args.repo_path is None:
        try:
            from pathlib import Path
            from devpilot.constants import REPO_MAP_PATH, REPO_CACHE_PATH, LAST_USED_PATH
            with open(LAST_USED_PATH) as f:
                repo_path: Path = Path(json.load(f)["repo_path"])
        except Exception:
            console.print(f"[red]   No previous repo path found. Please run onboarding first.")
            return

        refresh_repomap(
            repo_root=repo_path,
            repomap_path=REPO_MAP_PATH,
            cache_path=REPO_CACHE_PATH,
        )
        console.print("[green] Repomap refreshed (prototype).[/]")
        return

    if args.preview_prompt:
        from devpilot.prompt import get_prompt_path, load_prompt_template
        from devpilot.mode_utils import get_prompt_version

        # Onboarding requires existing maps
        if args.mode == "onboard":
            from pathlib import Path
            from devpilot.prompt_helpers import build_onboard_prompt_from_repomap
            repomap_path = Path(".devpilot/repomap.json")
            relmap_path = Path(".devpilot/relmap.json")
            if not repomap_path.exists():
                console.print("[red]   repomap.json not found. Run --generate-map first.[/]")
                return
            scaffold, _ = build_onboard_prompt_from_repomap(repomap_path, relmap_path)
            prompt_path = get_prompt_path("onboard")
            final_prompt = load_prompt_template(
                prompt_path,
                repomap_summary=scaffold,
                lang=args.lang or "plaintext"
            )

        else:
            file_path = resolve_mode_target_file(args.repo_path)
            if not file_path:
                return
            code = file_path.read_text()
            from devpilot.detect_lang import resolve_language_with_user_prompt
            resolved_lang = resolve_language_with_user_prompt(file_path, cli_lang=args.lang)
            version = get_prompt_version(args.mode, resolved_lang)
            prompt_path = get_prompt_path(args.mode, version=version)
            final_prompt = load_prompt_template(prompt_path, code=code, lang=resolved_lang)

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
            from devpilot.rel_map import build_relational_map, scaffold_docs, summarize_docs
            from devpilot.constants import REPO_MAP_PATH, REL_MAP_PATH
            build_relational_map(REPO_MAP_PATH)
            scaffold_docs(REL_MAP_PATH)
            summarize_docs(REL_MAP_PATH, model=args.model)
            
        except Exception as e:
            console.print(f"[yellow]  Relmap generation failed:[/] {e}")

    elif args.mode == "explain":
        file_path = resolve_mode_target_file(args.repo_path)
        if not file_path:
            return
        handle_explain(str(file_path), model=args.model, mode=args.mode, lang=args.lang)
    elif args.mode == "refactor":
        file_path = resolve_mode_target_file(args.repo_path)
        if not file_path:
            return
        handle_refactor(str(file_path), model=args.model, mode=args.mode, lang=args.lang)
    else:
        console.print(f"[red]   Unknown mode:[/] {args.mode}")

if __name__ == "__main__":
    main()
