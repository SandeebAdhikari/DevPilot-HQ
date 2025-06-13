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

def interactive_follow_up(prompt: str, model: str, run_model_func, lang: str = "python") -> None:
    """
    Continuously prompt the user for follow-up questions and re-query the model,
    with a soft cap to prevent oversized prompts from stalling LLMs.
    Logs all follow-ups and responses using SessionLogger, and writes once at the end.
    """
    full_prompt = prompt
    log_path = resolve_log_path(mode="interactive", lang=lang, suppress_prompt=True)
    logger = SessionLogger(log_path)

    # Optionally log the initial prompt context
    logger.log_entry("INITIAL PROMPT CONTEXT", prompt)

    while True:
        follow_up = safe_input("\n[bold yellow]🔁 Ask a follow-up or press Enter to finish:[/] ")
        if not follow_up.strip():
            break

        full_prompt += f"\n\nUser follow-up: {follow_up}"

        # Soft truncate if too long
        if len(full_prompt) > MAX_PROMPT_CHARS:
            console.print("[dim]⚠️ Prompt is getting large. Truncating earlier parts to fit model context.[/]")
            full_prompt = full_prompt[-MAX_PROMPT_CHARS:]

        console.print(f"\n[blue]🧪 Re-querying Ollama...[/]")

        try:
            response = run_model_func(full_prompt, model=model).strip()
        except Exception as e:
            console.print(f"[red]❌ Error running model:[/] {e}")
            continue

        if not response:
            console.print("[yellow]⚠️ Model returned no output. Retrying once...[/]")
            try:
                response = run_model_func(full_prompt, model=model).strip()
            except Exception as e:
                console.print(f"[red]Retry failed:[/] {e}")
                continue

        console.print("\n[bold green]🤖 Model response:[/]\n")
        console.print(Markdown(response))

        # Log this interaction
        logger.log_entry(follow_up, response)

    # Save once at the end
    logger.save()

