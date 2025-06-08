import subprocess

def run_ollama(prompt: str, model: str = "llama2", timeout: int = 90) -> str:
    """
    Run a local LLM using Ollama with the given prompt and return its output.

    Args:
        prompt (str): The full prompt text to send to the model.
        model (str): The model to use (e.g., 'starcoder', 'codellama:13b', 'mistral').
        timeout (int): Maximum time (seconds) to wait for the model.

    Returns:
        str: The generated response from the model or an error message.
    """
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        if result.returncode != 0:
            error_msg = result.stderr.decode("utf-8").strip()
            raise RuntimeError(error_msg)
        output = result.stdout.decode("utf-8").strip()
        # Optionally, remove any leading/trailing model prompts
        output = output.split("\n")[-1] if ">>>" in output else output
        return output
    except Exception as e:
        return f"❌ Error running ollama ({model}): {str(e)}"

