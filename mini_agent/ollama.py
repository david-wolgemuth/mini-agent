import json
import sys

import requests


def call_ollama(messages, model, base_url, stream=True):
    """Send messages to Ollama chat API. Returns full response text.

    When stream=True, prints tokens to stdout as they arrive.
    """
    url = f"{base_url}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
    }

    resp = requests.post(url, json=payload, stream=stream, timeout=120)
    resp.raise_for_status()

    if not stream:
        data = resp.json()
        return data["message"]["content"]

    chunks = []
    for line in resp.iter_lines():
        if not line:
            continue
        data = json.loads(line)
        token = data.get("message", {}).get("content", "")
        if token:
            chunks.append(token)
            sys.stdout.write(token)
            sys.stdout.flush()
        if data.get("done"):
            break

    sys.stdout.write("\n")
    return "".join(chunks)
