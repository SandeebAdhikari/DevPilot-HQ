from pathlib import Path
from typing import List, Optional
from datetime import datetime
from rich.console import Console
from typing import Any
from rich.table import Table
import json
import shutil
import atexit


console = Console()

LAST_USED_PATH = Path(".devpilot/last_used_path.json")
LOG_INDEX_PATH = Path(".devpilot/log_index.json")

class SessionLogger:
    def __init__(
        self,
        log_path: Path,
        use_timestamp: bool = False,
        format: str = "text",
        autosave: bool = False,
        rotate_backup: bool = False,
        memory_only: bool = False,
        batch_size: Optional[int] = None,
    ):
        """
        Args:
            log_path (Path): File path for log output
            use_timestamp (bool): Include ISO timestamp in entries
            format (str): 'text' | 'markdown' | 'json'
            autosave (bool): Save after every entry
            rotate_backup (bool): Make backup before overwrite
            memory_only (bool): Disable disk I/O — keeps log in memory
            batch_size (int): Only save after this many new entries
        """
        self.log_path = log_path
        self.entries: List[str] = []
        self.use_timestamp = use_timestamp
        self.format = format.lower()
        self.autosave = autosave
        self.rotate_backup = rotate_backup
        self.memory_only = memory_only
        self.batch_size = batch_size
        self._unsaved_count = 0
        self._registered_shutdown = False

        if not self.memory_only:
            atexit.register(self._safe_shutdown)
            self._registered_shutdown = True

    def log_entry(self, user_input: str, model_response: str):
        """
        Logs a prompt/response pair. Saves immediately or in batch depending on config.
        """
        timestamp = f"[{datetime.now().isoformat()}] " if self.use_timestamp else ""

        if self.format == "markdown":
            self.entries.append(f"### Prompt\n```\n{user_input.strip()}\n```")
            self.entries.append(f"### Response\n```\n{model_response.strip()}\n```")
        elif self.format == "json":
            self.entries.append(json.dumps({
                "timestamp": datetime.now().isoformat() if self.use_timestamp else None,
                "prompt": user_input,
                "response": model_response
            }))
        else:
            self.entries.append(f"{timestamp}>>> {user_input.strip()}")
            self.entries.append(model_response.strip())

        self._unsaved_count += 2

        if self.memory_only:
            return

        if self.autosave and not self.batch_size:
            self.save()
        elif self.batch_size and self._unsaved_count >= self.batch_size:
            self.save()

    def log_error(self, message: str, save: bool = False):
        """
        Logs an error-like message to console. Optionally appends it to the log file.
        """
        console.print(f"[bold red]❌ {message}[/]")

        if save and not self.memory_only:
            entry = f"[ERROR] {datetime.now().isoformat() if self.use_timestamp else ''} {message}"
            self.entries.append(entry)
            self._unsaved_count += 1
            self.save()

    def save(self):
        """
        Writes the buffered log to disk. Overwrites existing content.
        """
        if self.memory_only:
            return

        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        if self.rotate_backup and self.log_path.exists():
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_path = self.log_path.with_name(f"{self.log_path.stem}_{ts}{self.log_path.suffix}")
            shutil.copy2(self.log_path, backup_path)
            console.print(f"[yellow]📁 Backup created:[/] {backup_path}")

        if self.format == "json":
            joined = "[\n" + ",\n".join(self.entries) + "\n]"
        else:
            joined = "\n\n".join(self.entries)

        self.log_path.write_text(joined, encoding="utf-8")
        self._unsaved_count = 0
        console.print(f"\n[green]✅ Log saved to:[/] {self.log_path}")

    def flush(self):
        """
        Writes unsaved entries to disk silently (no Rich output).
        """
        if self.memory_only or self._unsaved_count == 0:
            return

        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        if self.format == "json":
            joined = "[\n" + ",\n".join(self.entries) + "\n]"
        else:
            joined = "\n\n".join(self.entries)

        self.log_path.write_text(joined, encoding="utf-8")
        self._unsaved_count = 0

    def shutdown(self):
        """
        Public method to flush unsaved entries before exiting manually.
        """
        if not self.memory_only and self._unsaved_count > 0:
            self.save()

    def _safe_shutdown(self):
        """
        Called automatically by atexit on interpreter shutdown.
        """
        try:
            self.shutdown()
        except Exception:
            pass  # Never block CLI shutdown
        

def get_last_used_repo() -> Path:
    """
    Loads the last used repo path from .devpilot/last_used_path.json.
    Returns:
        Path: Absolute path to the last used repo
    Raises:
        FileNotFoundError: If the file doesn't exist
        KeyError: If the file is malformed
    """
    if not LAST_USED_PATH.exists():
        raise FileNotFoundError("No last used repo found. Run onboarding first.")

    with LAST_USED_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return Path(data["repo_path"])


def list_logs(show: bool = True) -> List[dict[str, str]]:
    """
    Lists all sessions saved in .devpilot/log_index.json.
    
    Args:
        show (bool): If True, prints a table to console.
    Returns:
        List of log metadata dicts.
    """
    if not LOG_INDEX_PATH.exists():
        if show:
            console.print("[yellow]⚠️ No logs have been saved yet.[/]")
        return []

    try:
        with LOG_INDEX_PATH.open("r", encoding="utf-8") as f:
            entries = json.load(f)
    except Exception as e:
        if show:
            console.print(f"[red]❌ Failed to load log index:[/] {e}")
        return []

    if show:
        table = Table(title="DevPilot Log Sessions")
        table.add_column("Session ID", style="cyan", no_wrap=True)
        table.add_column("Path", style="magenta")
        table.add_column("Saved At", style="green")
        table.add_column("Format", style="yellow")

        for entry in entries:
            table.add_row(
                entry.get("session_id", "?"),
                entry.get("path", "?"),
                entry.get("saved_at", "?"),
                entry.get("format", "?")
            )

        console.print(table)

    return entries

def restore_log(session_id: str, show: bool = True) -> Optional[str]:
    """
    Restores and prints a previous session log by session_id.

    Args:
        session_id (str): The session ID to restore.
        show (bool): If True, prints the log contents.

    Returns:
        str or None: Contents of the log file, or None if not found.
    """
    if not LOG_INDEX_PATH.exists():
        console.print("[red]❌ No log index found.[/]")
        return None

    try:
        with LOG_INDEX_PATH.open("r", encoding="utf-8") as f:
            logs = json.load(f)
    except Exception as e:
        console.print(f"[red]❌ Failed to load log index:[/] {e}")
        return None

    match = next((entry for entry in logs if entry["session_id"] == session_id), None)

    if not match:
        console.print(f"[red]❌ No session found with ID:[/] {session_id}")
        return None

    log_path = Path(match["path"])
    if not log_path.exists():
        console.print(f"[red]❌ Log file not found:[/] {log_path}")
        return None

    contents = log_path.read_text(encoding="utf-8")
    if show:
        console.print(f"\n[bold green]📂 Restored log:[/] [cyan]{session_id}[/]\n")
        console.print(contents)

    return contents
def cleanup_logs(older_than_days: int, show: bool = True) -> int:
    """
    Deletes log files older than N days and cleans up the log index.

    Args:
        older_than_days (int): Age threshold in days.
        show (bool): If True, print summary of deleted logs.

    Returns:
        int: Number of logs removed.
    """
    if not LOG_INDEX_PATH.exists():
        if show:
            console.print("[yellow]⚠️ No log index found.[/]")
        return 0

    try:
        with LOG_INDEX_PATH.open("r", encoding="utf-8") as f:
            logs = json.load(f)
    except Exception as e:
        if show:
            console.print(f"[red]❌ Failed to read log index:[/] {e}")
        return 0

    threshold = datetime.now().timestamp() - (older_than_days * 86400)
    kept: list[dict[str, str]] = []
    removed: list[dict[str, str]] = []

    for entry in logs:
        try:
            saved_at = datetime.fromisoformat(entry["saved_at"]).timestamp()
            if saved_at < threshold:
                removed.append(entry)
            else:
                kept.append(entry)
        except Exception:
            kept.append(entry)  # if malformed, we keep it

    for entry in removed:
        path = Path(entry["path"])
        if path.exists():
            try:
                path.unlink()
                if show:
                    console.print(f"[red]🗑 Deleted:[/] {path}")
            except Exception as e:
                if show:
                    console.print(f"[yellow]⚠️ Could not delete {path}:[/] {e}")

    # Write updated log index
    with LOG_INDEX_PATH.open("w", encoding="utf-8") as f:
        json.dump(kept, f, indent=2)

    if show:
        console.print(f"\n[green]✅ Cleaned {len(removed)} old logs.[/]")
    return len(removed)

def scaffold_docs(repofile: Path) -> str:
    """
    Builds a scaffold documentation string from repomap.json and relationship map.
    """
    from devpilot.rel_map import extract_relationships

    if not repofile.exists():
        return "❌ repomap.json not found."

    with repofile.open("r", encoding="utf-8") as f:
        repomap = json.load(f)

    relations = extract_relationships(repofile)
    lines = ["# Project Scaffold\n", "## Key Files and Relationships\n"]

    for file, meta in repomap.items():
        lines.append(f"- {file}")

        symbols = meta.get("symbols", {})
        classes = symbols.get("classes", [])
        funcs = symbols.get("functions", [])

        if classes:
            lines.append(f"  - Classes: {', '.join(classes)}")
        if funcs:
            lines.append(f"  - Functions: {', '.join(funcs)}")

        imports = relations.get(file, set())
        if imports:
            lines.append(f"  - Imports: {', '.join(sorted(imports))}")

        lines.append("")  # empty line for spacing

    return "\n".join(lines)

def log_session(
    session_id: str,
    content: str,
    format: str = "markdown",
    suffix: str = "md",
    show: bool = True,
) -> Optional[Path]:
    """
    Saves a standalone session log and updates log_index.json.

    Args:
        session_id (str): Unique name (e.g. 'onboard_20240620')
        content (str): The text to write
        format (str): 'markdown', 'text', or 'json'
        suffix (str): file extension (md, txt, json)
        show (bool): Print success message

    Returns:
        Path to saved log, or None on failure
    """
    log_dir = Path(".devpilot/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{session_id}.{suffix}"

    try:
        log_path.write_text(content, encoding="utf-8")
        entry = {
            "session_id": session_id,
            "path": str(log_path),
            "saved_at": datetime.now().isoformat(),
            "format": format,
        }

        existing: list[dict[str, Any]] = []
        if LOG_INDEX_PATH.exists():
            with LOG_INDEX_PATH.open("r", encoding="utf-8") as f:
                existing = json.load(f)

        existing.insert(0, entry)

        with LOG_INDEX_PATH.open("w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)

        if show:
            console.print(f"[green]📁 Session logged to:[/] {log_path}")

        return log_path

    except Exception as e:
        console.print(f"[red]❌ Failed to log session:[/] {e}")
        return None
