from pathlib import Path

PROMPT_DIR = Path(__file__).parent / "prompts"

def get_prompt_path(mode: str, version: int = 1) -> Path:
    """
    Returns the prompt path for the given mode and version.

    Args:
        mode (str): One of 'onboard', 'explain', 'refactor', 'scaffold'
        version (int): Prompt version number (default is 1)

    Returns:
        Path: Full path to the prompt file

    Raises:
        ValueError: If an invalid mode is provided
    """
    valid_modes = {"onboard", "explain", "refactor", "scaffold"}
    if mode not in valid_modes:
        raise ValueError(f"Invalid mode '{mode}'. Must be one of: {', '.join(valid_modes)}")

    return PROMPT_DIR / f"{mode}_v{version}.txt"

