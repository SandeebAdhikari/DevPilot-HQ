from devpilot.ollama_infer import run_ollama
from rich.tree import Tree
from rich.console import Console
from pathlib import Path
from devpilot.prompt import get_prompt_path

console = Console()

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

def get_main_code_sample(repo_path: Path, max_lines=20) -> str:
    main_files = ["main.py", "manage.py", "app.py"]
    for file in main_files:
        file_path = repo_path / file
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return "\n".join(f.readlines()[:max_lines])
    return "No main code file found."

def handle_onboard(repo_path_str: str, model: str, mode: str = "onboard") -> str:
    repo_path = Path(repo_path_str).resolve()

    if not repo_path.exists():
        console.print(f"[red]Error:[/] Path '{repo_path}' does not exist.")
        return ""

    prompt_path = get_prompt_path(mode)

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

        code_sample = get_main_code_sample(repo_path)
        prompt += f"\n\nHere is a sample of the main code:\n{code_sample}"

    console.print(f"\n[dim]--- Prompt Sent to {model} ---[/]")
    console.print(prompt)

    console.print(f"\n[blue]🧪 Running Ollama ({model})...[/]")
    response = run_ollama(prompt, model=model)

    if not response.strip() or response.strip() in {"/", "1", "1111"}:
        console.print("\n[yellow]⚠️ Warning: Model response is empty or unhelpful.[/]")
        console.print("[dim]Try a larger codebase or switch to a different model.[/]")
    else:
        console.print("\n[bold green]✅ Onboarding Summary:[/]\n")
        console.print(response)

    log_path = repo_path.parent / ".onboarder_log.txt" if repo_path.is_file() else repo_path / ".onboarder_log.txt"
    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write("----- PROMPT -----\n")
        log_file.write(prompt + "\n\n")
        log_file.write("----- RESPONSE -----\n")
        log_file.write(response)

    console.print(f"\n[dim]📄 Log saved to {log_path}[/]")

    return response

