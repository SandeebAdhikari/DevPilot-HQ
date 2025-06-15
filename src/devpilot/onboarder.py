from pathlib import Path
from rich.console import Console
from devpilot.onboard import handle_onboard
from devpilot.explain import handle_explain
from devpilot.refactor import handle_refactor
import argparse

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
        help="Path to the file or codebase you want to analyze",
    )
    parser.add_argument(
        "--mode",
        type=str,
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
    return parser.parse_args()

def main():
    args = parse_args()

    if args.mode == "onboard":
        handle_onboard(str(args.repo_path), model=args.model, mode=args.mode, lang=args.lang)
    elif args.mode == "explain":
        handle_explain(str(args.repo_path), model=args.model, mode=args.mode, lang=args.lang)
    elif args.mode == "refactor":
        handle_refactor(str(args.repo_path), model=args.model, mode=args.mode, lang=args.lang)
    else:
        console.print(f"[red]❌ Unknown mode:[/] {args.mode}")

if __name__ == "__main__":
    main()

