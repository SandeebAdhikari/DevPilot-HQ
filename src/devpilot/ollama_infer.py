import os
import subprocess
import requests
import sys
import time
import json
from rich.console import Console 

console = Console()
def run_ollama(prompt: str, model: str = "llama2", timeout: int = 90, max_retries: int = 1) -> str:
    """
    Runs Ollama with HTTP streaming first, falls back to local CLI on failure.

    Args:
        prompt (str): Input prompt
        model (str): Model name
        timeout (int): Max wait time in seconds
        max_retries (int): Retry attempts if streaming fails

    Returns:
        str: Output from the model
    """
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    # Soft cap to prevent too long prompts
    if len(prompt) > 4000:
        console.print("[yellow]⚠️ Prompt may be too long. Truncating to ensure responsiveness.[/]")
        prompt = prompt[-4000:]  # keep last 4000 characters

    # Try streaming HTTP API first
    try:
        response = requests.post(
            f"{ollama_host}/api/generate",
            json={"model": model, "prompt": prompt, "stream": True},
            stream=True,
            timeout=timeout
        )
        response.raise_for_status()

        full_response = []
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                token = data.get("response", "")
                full_response.append(token)
                sys.stdout.write(token)
                sys.stdout.flush()
        print()  # newline after stream
        return "".join(full_response).strip()

    except Exception as e:
        print(f"\n[⚠️] Ollama HTTP API failed ({ollama_host}): {e}")
        print("[ℹ️] Falling back to native CLI...")

    # Fallback: native CLI
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.decode().strip())
        return result.stdout.decode("utf-8").strip()

    except Exception as e:
        return f"❌ Both Docker API and CLI failed: {e}"

