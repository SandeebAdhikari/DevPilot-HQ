from devpilot.ollama_infer import run_ollama
from rich.tree import Tree
from rich.console import Console
from rich.markdown import Markdown
from pathlib import Path
from devpilot.prompt import get_prompt_path
from devpilot.log_utils import resolve_log_path
from devpilot.session_logger import SessionLogger
from devpilot.interactive import interactive_follow_up
from devpilot.detect_lang import detect_language_from_path
from typing import Optional
import re

console = Console()

def markdown_to_text(md: str) -> str:
    lines = md.splitlines()
    output = []

    for line in lines:
        if line.startswith("# "):
            header = line[2:].strip()
            output.append(header.upper())
            output.append("=" * len(header))
        elif line.startswith("## "):
            subheader = line[3:].strip()
            output.append(subheader)
            output.append("-" * len(subheader))
        elif line.startswith("* "):
            output.append(f"• {line[2:]}")
        else:
            output.append(line)

    return "\n".join(output)

def load_prompt_template(prompt_path: Path, content: str) -> str:
    try:
        template = prompt_path.read_text()
        return template.replace("{{content}}", content).strip()
    except FileNotFoundError:
        return f"❌ Prompt template not found at {prompt_path}"

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


def get_main_code_sample(repo_path: Path, lang: str = "python", max_lines: int = 20) -> str:
    """
    Tries to find a primary code file for a given language and returns the top lines.
    
    Args:
        repo_path (Path): Root of the codebase.
        lang (str): Programming language or framework (e.g., python, java, react, c).
        max_lines (int): Number of lines to preview.

    Returns:
        str: Code sample or fallback message.
    """
    main_files_by_lang = {
        "python": ["main.py", "manage.py", "app.py"],
        "react": ["src/index.js", "src/index.jsx", "src/main.tsx"],
        "java": ["Main.java", "App.java", "src/Main.java"],
        "c": ["main.c", "main.cpp", "src/main.c", "src/main.cpp"]
    }

    candidates = main_files_by_lang.get(lang.lower(), [])

    for relative_path in candidates:
        file_path = repo_path / relative_path
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return "\n".join(f.readlines()[:max_lines])
            except Exception as e:
                return f"⚠️ Failed to read {relative_path}: {e}"

    return f"⚠️ No recognized main file found for language: {lang}"


def handle_onboard(repo_path_str: str, model: str, mode: str = "onboard", lang=None) -> str:
    repo_path = Path(repo_path_str).resolve()

    if not repo_path.exists():
        console.print(f"[red]Error:[/] Path '{repo_path}' does not exist.")
        return ""


    lang = lang or detect_language_from_path(repo_path)
    prompt_path = get_prompt_path(mode, lang)

    if repo_path.is_file():
        console.print(f"[green]📄 Analyzing file:[/] {repo_path.name}\n")
        try:
            file_content = repo_path.read_text(encoding="utf-8")
        except Exception as e:
            console.print(f"[red]Error reading file:[/] {e}")
            return ""
        prompt = load_prompt_template(prompt_path, file_content)

    else:
        console.print(f"[green]📁 Scanning directory:[/] {repo_path}\n")
        tree = build_file_tree(repo_path)
        console.print(tree)

        console.print("\n[green]🧠 Generating prompt for local LLM...[/]")
        file_tree_text = render_file_tree_to_text(repo_path)
        prompt = load_prompt_template(prompt_path, file_tree_text)

        code_sample = get_main_code_sample(repo_path, lang=lang)
        prompt += f"\n\nHere is a sample of the main code:\n{code_sample}"

    console.print(f"\n[dim]--- Prompt Sent to {model} ---[/]")
    console.print(prompt)

    console.print(f"\n[blue]🧪 Running Ollama ({model})...[/]")
    response = run_ollama(prompt, model=model)

    plain_response = markdown_to_text(response)

    if not response.strip() or response.strip() in {"/", "1", "1111"}:
        console.print("\n[yellow]⚠️ Warning: Model response is empty or unhelpful.[/]")
        console.print("[dim]Try a larger codebase or switch to a different model.[/]")
    else:
        pretty_response = Markdown(response)
        console.print("\n[bold green]✅ Onboarding Summary:[/]\n")
        console.print(pretty_response)

    
    code_sample = get_main_code_sample(repo_path, lang=lang)
    log_path = resolve_log_path(mode="onboard", lang=lang, suppress_prompt=True)

    logger = SessionLogger(log_path, use_timestamp=True, format="markdown")
    logger.log_entry(prompt, plain_response)
    logger.save()

    interactive_follow_up(prompt, model, run_ollama, lang=lang)

    return response

