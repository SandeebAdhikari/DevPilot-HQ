import sys
from pathlib import Path

def get_prompt_path(mode: str, lang: str = "python") -> Path:
    print(f"🧠 Mode: {mode}, Language: {lang}")
    """
    Returns the appropriate prompt file based on mode and language.
    Tries language-specific version first, then falls back to default.
    """

    try:
        if getattr(sys, 'frozen', False):
            base = Path(getattr(sys, '_MEIPASS')) / "prompts"
        else:
            base = Path(__file__).resolve().parent.parent.parent / "prompts"
    except Exception as e:
        raise RuntimeError(f"Failed to resolve prompt path: {e}")

    # Try language-specific prompt first
    if lang:
        lang_specific = base / f"{mode}_{lang}_prompt.txt"
        if lang_specific.exists():
            return lang_specific

    # Fallback to generic prompt
    fallback_map = {
        "onboard": "onboard_prompt.txt",
        "explain": "explain_prompt.txt",
        "refactor": "refactor_prompt.txt"
    }
    return base / fallback_map.get(mode, "onboard_prompt.txt")

