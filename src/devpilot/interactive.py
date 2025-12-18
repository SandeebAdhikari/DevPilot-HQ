from typing import Callable
from rich.console import Console
from rich.markdown import Markdown
from devpilot.session_logger import SessionLogger
from devpilot.log_utils import resolve_log_path
import time

console = Console()
MAX_PROMPT_CHARS = 4000  # Soft cap on total prompt length

def safe_input(prompt: str, retries: int = 3, delay: float = 0.3) -> str:
    """
    Attempts to read input safely under high CPU load. Retries if input is prematurely empty.
    """
    for _ in range(retries):
        try:
            user_input = console.input(prompt)
            if user_input.strip():
                return user_input
            time.sleep(delay)
        except EOFError:
            time.sleep(delay)
    return ""  # Fall back if user truly entered nothing or terminal is broken

def interactive_follow_up(
    prompt: str,
    model: str,
    run_model_func: Callable[..., str], 
    lang: str = "python"
) -> None:
    """
    Continuously prompt the user for follow-up questions and re-query the model,
    with a soft cap to prevent oversized prompts from stalling LLMs.
    Logs all follow-ups and responses using SessionLogger, and writes once at the end.
    """
    full_prompt = prompt
    log_path = resolve_log_path(mode="interactive", lang=lang, suppress_prompt=True)
    logger = SessionLogger(log_path, use_timestamp=True, format="markdown")

    logger.log_entry("INITIAL PROMPT CONTEXT", prompt)

    while True:
        follow_up = safe_input("\n🔁 Ask a follow-up or press Enter to finish: ")
        if not follow_up.strip():
            break

        trial_prompt = full_prompt + f"\n\nUser follow-up: {follow_up}"
        if len(trial_prompt) > MAX_PROMPT_CHARS:
            console.print("[dim]  Prompt is getting large. Truncating earlier parts to fit model context.[/]")
            trial_prompt = trial_prompt[-MAX_PROMPT_CHARS:]

        console.print(f"\n[blue]🧪 Re-querying Ollama...[/]")

        try:
            response = run_model_func(trial_prompt, model=model).strip()
        except Exception as e:
            console.print(f"[red]   Error running model:[/] {e}")
            continue

        if not response:
            console.print("[yellow]  Model returned no output. Retrying once...[/]")
            try:
                response = run_model_func(trial_prompt, model=model).strip()
            except Exception as e:
                console.print(f"[red]Retry failed:[/] {e}")
                continue

        full_prompt = trial_prompt
        console.print("\n[bold green]🤖 Model response:[/]\n")
        console.print(Markdown(response))

        logger.log_entry(follow_up, response)

    logger.save()
