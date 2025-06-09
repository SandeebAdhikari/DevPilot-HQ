#!/usr/bin/env python3

import argparse
from pathlib import Path
from devpilot.onboard import handle_onboard

def parse_args():
    parser = argparse.ArgumentParser(
        description="DevPilot Onboarder - Explain any codebase locally"
    )
    parser.add_argument(
        "repo_path",
        type=Path,
        help="Path to the codebase or file you want to analyze",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="llama2",
        help="Ollama model to use (e.g., codellama:13b, mistral, llama2)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="onboard",
        help="Prompt mode to use (onboard, explain, refactor)",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    handle_onboard(str(args.repo_path), model=args.model, mode=args.mode)

if __name__ == "__main__":
    main()

