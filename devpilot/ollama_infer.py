import os
import subprocess
import requests

def run_ollama(prompt: str, model: str = "llama2", timeout: int = 90) -> str:
    """
    Run an Ollama model either via Docker HTTP API or fallback to local CLI.

    Priority:
    1. If OLLAMA_HOST is set, use it as the HTTP target
    2. Otherwise try Docker default: http://localhost:11434
    3. If HTTP fails, fallback to native `ollama run` subprocess

    Args:
        prompt (str): The user prompt or input
        model (str): The model to use (e.g., 'llama2', 'codellama:7b')
        timeout (int): Max time to wait for the model (in seconds)

    Returns:
        str: The model's output text or an error message
    """
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    # Try Docker/HTTP API first
    try:
        response = requests.post(
            f"{ollama_host}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=timeout
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()

    except Exception as e:
        print(f"[⚠️] Ollama HTTP API failed ({ollama_host}): {e}")
        print("[ℹ️] Falling back to native CLI...")

    # Fallback to native CLI
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

