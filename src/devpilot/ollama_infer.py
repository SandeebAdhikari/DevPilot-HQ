import os
import subprocess
import requests
import sys
import time
import json
from rich.console import Console 
from typing import List

console = Console()

def run_ollama(
    prompt: str,
    model: str = "llama2",
    timeout: int = 90,
    max_retries: int = 1,
    system_prompt: str = "",
    stream: bool = True
) -> str:
    """
    Runs Ollama with optional system prompt and streaming.

    Args:
        prompt (str): User prompt
        model (str): Model name
        timeout (int): Timeout for inference
        max_retries (int): Retry attempts
        system_prompt (str): Optional system message prepended to prompt
        stream (bool): Whether to stream response or return full string

    Returns:
        str: Response from Ollama (streamed or full)
    """
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    if len(prompt) > 4000:
        console.print(f"[yellow]⚠️ Prompt may be too long. Truncating to ensure responsiveness.[/]")
        prompt = prompt[-4000:]

    # Combine system + user prompt
    if system_prompt:
        prompt = f"<<SYS>>\n{system_prompt.strip()}\n<</SYS>>\n\n{prompt.strip()}"

    try:
        response = requests.post(
            f"{ollama_host}/api/generate",
            json={"model": model, "prompt": prompt, "stream": stream},
            stream=stream,
            timeout=timeout
        )
        response.raise_for_status()

        if stream:
            full_response: List[str] = []
            for line in response.iter_lines():
                if line:
                    data = json.loads(line.decode("utf-8"))
                    token = data.get("response", "")
                    full_response.append(token)
                    sys.stdout.write(token)
                    sys.stdout.flush()
            print()
            return "".join(full_response).strip()
        else:
            data = response.json()
            return data.get("response", "").strip()

    except Exception as e:
        console.print(f"\n[⚠️] Ollama HTTP API failed ({ollama_host}): {e}")
        print("[ℹ️] Falling back to native CLI...")

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

