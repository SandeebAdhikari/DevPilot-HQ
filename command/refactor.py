from ollama_infer import run_ollama
from pathlib import Path

def handle_refactor(file_path: str, model: str) -> str:
    code = Path(file_path).read_text()

    prompt_path = Path(__file__).parent.parent / "prompts" / "refactor_prompt.txt"
    prompt_template = prompt_path.read_text()

    prompt = prompt_template.replace("<CODE_BLOCK>", code)
    return run_ollama(prompt, model)

