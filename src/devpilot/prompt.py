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



def load_prompt_template(prompt_path: Path, **kwargs: str) -> str:
    """
    Loads a prompt template and substitutes any {{placeholder}} in the file
    with corresponding values provided via kwargs.

    Args:
        prompt_path (Path): Path to the prompt template file
        **kwargs: Dictionary of placeholder names and values to substitute

    Returns:
        str: Fully rendered template string

    Raises:
        ValueError: If any placeholders remain unreplaced (i.e., "{{" still exists)
    """
    try:
        template = prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"❌ Prompt template not found: {prompt_path}"

    for key, value in kwargs.items():
        template = template.replace(f"{{{{{key}}}}}", value)

    if "{{" in template:
        raise ValueError(f"❌ Unreplaced placeholder found in template: {prompt_path}")

    return template.strip()
