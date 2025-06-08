#!/usr/bin/env python3

import argparse
from pathlib import Path
from rich.console import Console
from rich.tree import Tree
from ollama_infer import run_ollama

console = Console()
PROMPT_TEMPLATE_PATH = Path(__file__).parent / "prompts" / "base_prompt.txt"

def parse_args():
    parser = argparse.ArgumentParser(
        description="DevPilot Onboarder - Explain any codebase locally"
    )
    parser.add_argument(
        "repo_path",
        type=Path,
        help="Path to the codebase you want to onboard",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="llama2",  # Changed from "starcoder" for better results
        help="Ollama model to use (e.g., codellama:13b, mistral, llama2)",
    )
    return parser.parse_args()

def build_file_tree(base_path: Path) -> Tree:
    tree = Tree(f":file_folder: [bold blue]{base_path.name}[/]", guide_style="bold bright_blue")

    def add_nodes(directory: Path, node: Tree):
        try:
            entries = sorted(directory.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
            for entry in entries:
                label = f"[bold]{entry.name}[/]" if entry.is_dir() else entry.name
                child = node.add(label)
                if entry.is_dir():
                    add_nodes(entry, child)
        except PermissionError:
            node.add("[red]Permission denied[/]")

    add_nodes(base_path, tree)
    return tree

def render_file_tree_to_text(base_path: Path) -> str:
    output = []

    def walk(path: Path, prefix=""):
        try:
            entries = sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
            for i, entry in enumerate(entries):
                connector = "└── " if i == len(entries) - 1 else "├── "
                output.append(f"{prefix}{connector}{entry.name}")
                if entry.is_dir():
                    extension = "    " if i == len(entries) - 1 else "│   "
                    walk(entry, prefix + extension)
        except PermissionError:
            output.append(f"{prefix}└── [Permission Denied]")

    output.append(base_path.name)
    walk(base_path)
    return "\n".join(output)

def get_main_code_sample(repo_path: Path, max_lines=20) -> str:
    main_files = ["main.py", "manage.py", "app.py"]
    for file in main_files:
        file_path = repo_path / file
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return "\n".join(f.readlines()[:max_lines])
    return "No main code file found."

def load_prompt_template(file_tree_text: str) -> str:
    try:
        template = PROMPT_TEMPLATE_PATH.read_text()
        final = template.replace("{{file_tree}}", file_tree_text)
        final += "\n\nAvoid placeholder tokens, repetition, or random numbers. Use clear, useful bullet points."
        return final
    except FileNotFoundError:
        return f"❌ Prompt template not found at {PROMPT_TEMPLATE_PATH}"

def main():
    args = parse_args()
    repo_path = args.repo_path.resolve()

    if not repo_path.exists() or not repo_path.is_dir():
        console.print(f"[red]Error:[/] Path '{repo_path}' does not exist or is not a directory.")
        return

    console.print(f"[green]📁 Scanning repo:[/] {repo_path}\n")
    tree = build_file_tree(repo_path)
    console.print(tree)

    console.print("\n[green]🧠 Generating prompt for local LLM...[/]")
    file_tree_text = render_file_tree_to_text(repo_path)
    prompt = load_prompt_template(file_tree_text)

    # Add code sample to the prompt
    main_code_sample = get_main_code_sample(repo_path)
    prompt += f"\n\nHere is a sample of the main code:\n{main_code_sample}"

    console.print(f"\n[dim]--- Prompt Sent to {args.model} ---[/]")
    console.print(prompt)

    console.print(f"\n[blue]🧪 Running Ollama ({args.model})...[/]")
    response = run_ollama(prompt, model=args.model)

    if not response.strip() or response.strip() in {"/", "1", "1111"}:
        console.print("\n[yellow]⚠️ Warning: Model response is empty or unhelpful.[/]")
        console.print("[dim]Try a larger codebase or switch to a different model.[/]")
    else:
        console.print("\n[bold green]✅ Onboarding Summary:[/]\n")
        console.print(response)

    log_path = repo_path / ".onboarder_log.txt"
    with open(log_path, "w") as log_file:
        log_file.write("----- PROMPT -----\n")
        log_file.write(prompt + "\n\n")
        log_file.write("----- RESPONSE -----\n")
        log_file.write(response)
    console.print(f"\n[dim]📄 Log saved to {log_path}[/]")

if __name__ == "__main__":
    main()

