from pathlib import Path

def get_prompt_path(mode: str, lang: str = "python") -> Path:
    print(f"🧠 Mode: {mode}, Language: {lang}")
    """
    Returns the appropriate prompt file based on mode and language.
    Tries language-specific version first, then falls back to default.

    Args:
        mode (str): One of "onboard", "explain", "refactor"
        lang (str): Optional language identifier (e.g., "java", "c", "react")

    Returns:
        Path: Path to the selected prompt file
    """
    base = Path(__file__).resolve().parent.parent.parent / "prompts"

    if lang:
        lang_specific = base / f"{mode}_{lang}_prompt.txt"
        if lang_specific.exists():
            return lang_specific

    if mode == "explain":
        return base / "explain_prompt.txt"
    elif mode == "refactor":
        return base / "refactor_prompt.txt"
    else:
        return base / "onboard_prompt.txt"

