from pathlib import Path

def get_prompt_path(mode: str) -> Path:
    base = Path(__file__).resolve().parent.parent / "prompts"
    if mode == "explain":
        return base / "explain_prompt.txt"
    elif mode == "refactor":
        return base / "refactor_prompt.txt"
    else:
        return base / "base_prompt.txt"

