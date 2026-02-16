from typing import Callable
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from devpilot.session_logger import SessionLogger
from devpilot.log_utils import resolve_log_path
import time

console = Console()
MAX_PROMPT_CHARS = 4000  # Soft cap on total prompt length
MAX_FILE_CONTEXT_CHARS = 2000

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


def _handle_inline_explain_command(follow_up: str, model: str, lang: str) -> bool:
    """
    Supports interactive inline command format:
      /explain/<file_or_path>
    Only slash format is treated as a command; everything else is normal follow-up text.
    """
    raw_target = ""
    if follow_up.startswith("/explain/"):
        raw_target = follow_up[len("/explain/"):].strip()
    elif follow_up.startswith("/explain "):
        raw_target = follow_up[len("/explain "):].strip()
    else:
        return False

    if not raw_target:
        console.print("[yellow]Please provide a file name after '/explain'.[/]")
        return True

    from devpilot.onboarder import resolve_mode_target_file
    from devpilot.explain import handle_explain

    resolved = resolve_mode_target_file(Path(raw_target))
    if not resolved:
        return True

    console.print(f"\n[blue]🧪 Running inline explain for:[/] {resolved}")
    handle_explain(str(resolved), model=model, mode="explain", lang=lang, interactive=False)
    return True


def _handle_inline_refactor_command(follow_up: str, model: str, lang: str) -> bool:
    """
    Supports interactive inline command format:
      /refactor/<file_or_path>
    """
    raw_target = ""
    if follow_up.startswith("/refactor/"):
        raw_target = follow_up[len("/refactor/"):].strip()
    elif follow_up.startswith("/refactor "):
        raw_target = follow_up[len("/refactor "):].strip()
    else:
        return False

    if not raw_target:
        console.print("[yellow]Please provide a file name after '/refactor'.[/]")
        return True

    from devpilot.onboarder import resolve_mode_target_file
    from devpilot.refactor import handle_refactor

    resolved = resolve_mode_target_file(Path(raw_target))
    if not resolved:
        return True

    console.print(f"\n[blue]🧪 Running inline refactor for:[/] {resolved}")
    handle_refactor(str(resolved), model=model, mode="refactor", lang=lang, interactive=False)
    return True


def _handle_inline_file_context_command(
    follow_up: str,
) -> tuple[bool, str, str]:
    """
    Supports interactive file-context commands:
      /file/<file_or_path>
      /file <file_or_path>
      /clearfile

    Returns:
      handled, context_block, context_label
    """
    if follow_up == "/clearfile":
        console.print("[green]Cleared focused file context.[/]")
        return True, "", ""

    raw_target = ""
    if follow_up.startswith("/file/"):
        raw_target = follow_up[len("/file/"):].strip()
    elif follow_up.startswith("/file "):
        raw_target = follow_up[len("/file "):].strip()
    else:
        return False, "", ""

    if not raw_target:
        console.print("[yellow]Please provide a file name after '/file'.[/]")
        return True, "", ""

    from devpilot.onboarder import resolve_mode_target_file

    resolved = resolve_mode_target_file(Path(raw_target))
    if not resolved:
        return True, "", ""

    try:
        content = resolved.read_text(encoding="utf-8")
    except Exception as e:
        console.print(f"[red]Failed to read focused file:[/] {e}")
        return True, "", ""

    if len(content) > MAX_FILE_CONTEXT_CHARS:
        content = content[:MAX_FILE_CONTEXT_CHARS] + "\n... (truncated)"

    context_block = (
        f"\n\nFocused file context ({resolved}):\n"
        f"```text\n{content}\n```"
    )
    console.print(f"[green]Focused file set:[/] {resolved}")
    console.print("[dim]Now ask normal follow-up questions; they will include this file context.[/]")
    return True, context_block, str(resolved)


def _handle_inline_at_file_reference(
    follow_up: str,
) -> tuple[bool, str, str, str]:
    """
    Supports inline focused-file syntax:
      @<file_or_path> <question>
      @<file_or_path>

    Returns:
      handled, context_block, context_label, rewritten_follow_up
    """
    if not follow_up.startswith("@"):
        return False, "", "", ""

    raw = follow_up[1:].strip()
    if not raw:
        console.print("[yellow]Use '@<file>' or '@<file> <question>'.[/]")
        return True, "", "", ""

    parts = raw.split(maxsplit=1)
    raw_target = parts[0].strip()
    rewritten_follow_up = parts[1].strip() if len(parts) > 1 else ""

    from devpilot.onboarder import resolve_mode_target_file

    resolved = resolve_mode_target_file(Path(raw_target))
    if not resolved:
        return True, "", "", ""

    try:
        content = resolved.read_text(encoding="utf-8")
    except Exception as e:
        console.print(f"[red]Failed to read focused file:[/] {e}")
        return True, "", "", ""

    if len(content) > MAX_FILE_CONTEXT_CHARS:
        content = content[:MAX_FILE_CONTEXT_CHARS] + "\n... (truncated)"

    context_block = (
        f"\n\nFocused file context ({resolved}):\n"
        f"```text\n{content}\n```"
    )
    console.print(f"[green]Focused file set:[/] {resolved}")

    if not rewritten_follow_up:
        console.print("[dim]Now ask normal follow-up questions; they will include this file context.[/]")

    return True, context_block, str(resolved), rewritten_follow_up


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
    focused_context_block = ""
    focused_context_label = ""

    logger.log_entry("INITIAL PROMPT CONTEXT", prompt)

    while True:
        follow_up = safe_input("\n🔁 Ask a follow-up or press Enter to finish: ")
        if not follow_up.strip():
            break

        handled, new_context_block, new_context_label, rewritten_follow_up = _handle_inline_at_file_reference(follow_up.strip())
        if handled:
            focused_context_block = new_context_block
            focused_context_label = new_context_label
            if not rewritten_follow_up:
                continue
            follow_up = rewritten_follow_up

        if _handle_inline_explain_command(follow_up.strip(), model=model, lang=lang):
            continue

        if _handle_inline_refactor_command(follow_up.strip(), model=model, lang=lang):
            continue

        handled, new_context_block, new_context_label = _handle_inline_file_context_command(follow_up.strip())
        if handled:
            focused_context_block = new_context_block
            focused_context_label = new_context_label
            continue

        trial_prompt = full_prompt
        if focused_context_block:
            trial_prompt += focused_context_block
        trial_prompt += f"\n\nUser follow-up: {follow_up}"
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

        logged_follow_up = follow_up
        if focused_context_label:
            logged_follow_up = f"[focused: {focused_context_label}] {follow_up}"
        logger.log_entry(logged_follow_up, response)

    logger.save()
