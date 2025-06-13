from pathlib import Path
from devpilot.ollama_infer import run_ollama
from devpilot.prompt import get_prompt_path
from devpilot.onboard import load_prompt_template, markdown_to_text
from devpilot.interactive import interactive_follow_up
from rich.console import Console
from rich.markdown import Markdown

console = Console()

def handle_explain(file_path: str, model: str, mode: str = "explain") -> str:
    try:
        code = Path(file_path).read_text(encoding="utf-8")
    except Exception as e:
        return f"❌ Error reading file: {e}"

    prompt_path = get_prompt_path(mode)
    prompt = load_prompt_template(prompt_path, code)

    console.print(f"\n[dim]--- Prompt Sent to {model} ---[/]")
    console.print(prompt)

    console.print(f"\n[blue]🧪 Running Ollama ({model})...[/]")
    response = run_ollama(prompt, model=model)

    plain_response = markdown_to_text(response)

    if not response.strip():
        console.print("\n[yellow]⚠️ Model returned no output.[/]")
    else:
        console.print("\n[bold green]✅ Explanation:[/]\n")
        console.print(Markdown(response))

    log_path = Path(file_path).parent / ".explain.txt"
    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write("----- PROMPT -----\n")
        log_file.write(prompt + "\n\n")
        log_file.write("----- RESPONSE -----\n")
        log_file.write(plain_response)

    console.print(f"\n[dim]📄 Log saved to {log_path}[/]")
    interactive_follow_up(prompt, model, run_ollama)

    return response

