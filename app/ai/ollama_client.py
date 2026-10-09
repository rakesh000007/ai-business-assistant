"""
Ollama Client
-------------
Handles communication between Flask
and the locally running Ollama model.
"""

import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"


def generate_response(prompt):
    """
    Send a prompt to Ollama and return
    the generated AI response.
    """

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "think": False
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=300
        )

        response.raise_for_status()

        data = response.json()

        return data.get(
            "response",
            "Sorry, I could not generate a response."
        ).strip()

    except requests.exceptions.ConnectionError:
        return (
            "Ollama is not running. "
            "Please start Ollama and try again."
        )

    except requests.exceptions.Timeout:
        return (
            "The AI took too long to respond. "
            "Please try again."
        )

    except requests.exceptions.RequestException as e:
        return f"Ollama error: {str(e)}"

    except Exception as e:
        return f"Unexpected AI error: {str(e)}"