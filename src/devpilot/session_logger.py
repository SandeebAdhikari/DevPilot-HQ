from pathlib import Path
from typing import List, Optional
from datetime import datetime
from rich.console import Console

console = Console()

class SessionLogger:
    def __init__(self, log_path: Path, use_timestamp: bool = False, format: str = "text"):
        """
        Args:
            log_path (Path): Full destination file path
            use_timestamp (bool): Whether to prepend timestamps to entries
            format (str): 'text' (default), 'markdown', or 'json' — controls how log is rendered
        """
        self.log_path = log_path
        self.entries: List[str] = []
        self.use_timestamp = use_timestamp
        self.format = format.lower()

    def log_entry(self, user_input: str, model_response: str):
        """
        Adds a prompt/response pair to the log buffer.
        """
        timestamp = f"[{datetime.now().isoformat()}] " if self.use_timestamp else ""
        
        if self.format == "markdown":
            self.entries.append(f"### Prompt\n```\n{user_input.strip()}\n```")
            self.entries.append(f"### Response\n```\n{model_response.strip()}\n```")
        elif self.format == "json":
            import json
            self.entries.append(json.dumps({
                "timestamp": datetime.now().isoformat() if self.use_timestamp else None,
                "prompt": user_input,
                "response": model_response
            }))
        else:  # plain text (default)
            self.entries.append(f"{timestamp}>>> {user_input.strip()}")
            self.entries.append(model_response.strip())

    def save(self):
        """
        Writes the buffered log to disk. Overwrites any existing content.
        """
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        if self.format == "json":
            joined = "[\n" + ",\n".join(self.entries) + "\n]"
        else:
            joined = "\n\n".join(self.entries)

        self.log_path.write_text(joined, encoding="utf-8")
        console.print(f"\n[green]✅ Log saved to:[/] {self.log_path}")

