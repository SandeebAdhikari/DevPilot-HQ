import os
import subprocess
import requests

def run_ollama(prompt: str, model: str = "llama2", timeout: int = 90) -> str:
    """
    Run an Ollama model either via HTTP API (remote or Docker) or fallback to local CLI.

    Order:
    1. Use HTTP API if OLLAMA_HOST is set or defaults to localhost
    2. If that fails, fallback to native CLI

    Args:
        prompt (str): The user prompt or input
        model (str): The model to use (e.g., 'llama2', 'codellama:7b')
        timeout (int): Max time to wait for the model (in seconds)

    Returns:
        str: The model's output text or an error message
    """
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    # Try HTTP API (Docker/Remote)
    try:
        response = requests.post(
            f"{ollama_host}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=timeout
        )
        response.raise_for_status()
        output = response.json().get("response", "").strip()

        if not output or output in {"/", "1", "1111", "0"}:
            return (
                "❌ Received empty or invalid response from HTTP API.\n"
                "👉 Try another model (e.g., `codellama:13b`) or increase prompt richness."
            )

        return output

    except Exception as e:
        print(f"[⚠️] Ollama HTTP API failed ({ollama_host}): {e}")
        print("[ℹ️] Falling back to native CLI...")

    # Fallback: CLI
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )

        if result.returncode != 0:
            return f"❌ Ollama CLI Error [{result.returncode}]: {result.stderr.decode().strip()}"

        output = result.stdout.decode("utf-8").strip()

        if not output or output in {"/", "1", "1111", "0"}:
            return (
                "❌ Received empty or invalid response from CLI.\n"
                "👉 Try a different model or check if the prompt is too short."
            )

        return output

    except subprocess.TimeoutExpired:
        return f"❌ Timeout: Model '{model}' exceeded {timeout}s limit"
    except FileNotFoundError:
        return "❌ Ollama not found. Is it installed and in your PATH?"
    except Exception as e:
        return f"❌ Both HTTP and CLI execution failed: {e}"

