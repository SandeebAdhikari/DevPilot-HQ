from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.markdown import Markdown

from devpilot.ollama_infer import run_ollama
from devpilot.prompt import get_prompt_path, load_prompt_template
from devpilot.interactive import interactive_follow_up
from devpilot.onboard import markdown_to_text
from devpilot.log_utils import resolve_log_path
from devpilot.session_logger import SessionLogger
from devpilot.detect_lang import resolve_language_with_user_prompt
from devpilot.mode_utils import get_prompt_version

console = Console()

def handle_refactor(file_path: str, model: str, mode: str = "refactor", lang: Optional[str] = None) -> str:
    try:
        code = Path(file_path).read_text(encoding="utf-8")
    except Exception as e:
        return f"   Error reading file: {e}"

    lang = resolve_language_with_user_prompt(Path(file_path), cli_lang=lang)
    version = get_prompt_version("refactor", lang)

    prompt_path = get_prompt_path(mode, version=version)
    prompt = load_prompt_template(prompt_path, lang=lang, code=code)

    if "{{" in prompt or "}}" in prompt:
        raise ValueError(f"   Unreplaced placeholders in prompt: {prompt_path}")

    console.print(f"\n[dim]--- Prompt Sent to {model} ---[/]")
    console.print(prompt)

    console.print(f"\n[blue]🧪 Running Ollama ({model})...[/]")
    response = run_ollama(prompt, model=model)

    plain_response = markdown_to_text(response)

    if not response.strip():
        console.print("\n[yellow]  Model returned no output.[/]")
    else:
        console.print("\n[bold green] Refactor Suggestions:[/]\n")
        console.print(Markdown(response))

    log_path = resolve_log_path(mode=mode, lang=lang, suppress_prompt=True)
    logger = SessionLogger(log_path, use_timestamp=True, format="markdown")
    logger.log_entry(prompt, plain_response)
    logger.save()

    interactive_follow_up(prompt, model, run_ollama, lang=lang)
    return response
