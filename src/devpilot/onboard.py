from devpilot.ollama_infer import run_ollama
from rich.tree import Tree
from rich.console import Console
from rich.markdown import Markdown
from pathlib import Path
from devpilot.log_utils import resolve_log_path
from devpilot.session_logger import SessionLogger
from devpilot.interactive import interactive_follow_up
from devpilot.detect_lang import detect_language_from_path, infer_repo_language
from devpilot.repomap_utils import update_repomap
from typing import Optional
from typing import List
import json

console = Console()

def markdown_to_text(md: str) -> str:
    lines = md.splitlines()
    output: list[str] = []

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
    output: List[str] = []

    def walk(path: Path, prefix: str = ""):
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


def handle_onboard(
    repo_path_str: str,
    model: str,
    mode: str = "onboard",
    lang: Optional[str] = None
) -> str:
    from devpilot.prompt_helpers import build_onboard_prompt_from_repomap
    from devpilot.prompt import get_prompt_path, load_prompt_template

    repo_path = Path(repo_path_str).resolve()

    if not repo_path.exists():
        console.print(f"[red]Error:[/] Path '{repo_path}' does not exist.")
        return ""

    lang = lang or detect_language_from_path(repo_path)

    if repo_path.is_dir():
        Path(".devpilot").mkdir(exist_ok=True)
        with open(".devpilot/last_used_path.json", "w") as f:
            json.dump({"repo_path": str(repo_path)}, f)

        console.print(f"[green]📁 Scanning directory:[/] {repo_path}\n")
        tree = build_file_tree(repo_path)
        console.print(tree)

        update_repomap(
            repo_root=repo_path,
            repomap_path=Path(".devpilot/repomap.json"),
            cache_path=Path(".devpilot/repomap_cache.json"),
        )

        console.print("\n[green]🧠 Building prompt from repomap...[/]")

        if not lang:
            with open(".devpilot/repomap.json", "r", encoding="utf-8") as f:
                repomap_data = json.load(f)
            lang = infer_repo_language(repomap_data)
            console.print(f"[cyan]🔎 Inferred language:[/] {lang}")

        repomap_summary_str, _ = build_onboard_prompt_from_repomap(
            Path(".devpilot/repomap.json"),
            relmap_path=Path(".devpilot/relmap.json"),
            lang=lang
        )

        
        prompt_path = get_prompt_path(mode)
        prompt = load_prompt_template(prompt_path, content=repomap_summary_str, lang=lang)

    elif repo_path.is_file():
        console.print(f"[green]📄 Analyzing file:[/] {repo_path.name}\n")
        try:
            file_content = repo_path.read_text(encoding="utf-8")
        except Exception as e:
            console.print(f"[red]Error reading file:[/] {e}")
            return ""
        prompt_path = get_prompt_path(mode)
        prompt = load_prompt_template(prompt_path, content=file_content, lang=lang)

    else:
        console.print(f"[red]Error:[/] '{repo_path}' is neither file nor directory.")
        return ""

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

    log_path = resolve_log_path(mode="onboard", lang=lang, suppress_prompt=True)
    logger = SessionLogger(log_path, use_timestamp=True, format="markdown")
    logger.log_entry(prompt, plain_response)
    logger.save()

    if not lang:
        with open(".devpilot/repomap.json", "r", encoding="utf-8") as f:
            repomap_data = json.load(f)
        lang = infer_repo_language(repomap_data)
        console.print(f"[cyan]🔎 Inferred language:[/] {lang}")

    interactive_follow_up(prompt, model, run_ollama, lang=lang)

    return response

