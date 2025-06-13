from pathlib import Path
from rich.console import Console

console = Console()

def resolve_log_path(mode: str, log_path=None, lang: str = "", suppress_prompt: bool = False) -> Path:
    """
    Resolve the path for the log file based on mode, language, or user-specified path.
    Defaults to ~/Documents/{mode}_{lang}.txt if unspecified.

    Args:
        mode (str): Mode of operation ("onboard", "explain", "refactor", etc.)
        log_path (str | None): Optional manual override
        lang (str): Language code to suffix filename (e.g., "java", "react", "c")
        suppress_prompt (bool): Skip interactive prompt

    Returns:
        Path: Final resolved log path
    """
    if log_path is not None:
        return Path(log_path).expanduser().resolve()

    lang_suffix = f"_{lang}" if lang else ""
    default_name = f"{mode}{lang_suffix}.txt" if mode in {"explain", "refactor", "onboard", "interactive"} else ".onboarder_log.txt"
    documents_dir = Path.home() / "Documents"
    default_path = documents_dir / default_name

    if suppress_prompt:
        return default_path

    console.print(f"\n[blue]💾 Where should the log file be saved?[/]")
    user_input = input(f"Enter path [press Enter to use default: {default_path}]: ").strip()

    return Path(user_input).expanduser().resolve() if user_input else default_path

