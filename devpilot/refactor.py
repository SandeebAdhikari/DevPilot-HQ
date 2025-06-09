from pathlib import Path
from devpilot.ollama_infer import run_ollama
from devpilot.prompt import get_prompt_path
from devpilot.onboard import load_prompt_template  # reuse shared logic

def handle_refactor(file_path: str, model: str) -> str:
    try:
        code = Path(file_path).read_text(encoding="utf-8")
    except Exception as e:
        return f"❌ Error reading file: {e}"

    prompt_path = get_prompt_path("refactor")
    prompt = load_prompt_template(prompt_path, code)

    return run_ollama(prompt, model=model)

