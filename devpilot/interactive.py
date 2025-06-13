from rich.console import Console
from rich.markdown import Markdown

console = Console()

MAX_PROMPT_CHARS = 4000  # Soft cap on total prompt length

def interactive_follow_up(prompt: str, model: str, run_model_func) -> None:
    """
    Continuously prompt the user for follow-up questions and re-query the model,
    with a soft cap to prevent oversized prompts from stalling LLMs.
    """
    full_prompt = prompt

    while True:
        follow_up = console.input("\n[bold yellow]🔁 Ask a follow-up or press Enter to finish:[/] ")
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

