from pathlib import Path
from rich.console import Console

console = Console()

def resolve_log_path(log_path=None, default_name=".onboarder_log.txt") -> Path:
    """
    Ask user where to save log file. If they press Enter, defaults to ~/Documents/.
    """
    if log_path is not None:
        return Path(log_path).expanduser().resolve()

    documents_dir = Path.home() / "Documents"
    default_path = documents_dir / default_name
    console.print(f"\n[blue]💾 Where should the log file be saved?[/]")
    user_input = input(f"Enter path [press Enter to use default: {default_path}]: ").strip()

    return Path(user_input).expanduser().resolve() if user_input else default_path

