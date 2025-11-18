import os
from typing import Optional, List, Dict

import requests


OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gpt-oss:120b-cloud")


def ask(question: str, context: Optional[str] = None, history: Optional[List[Dict[str, str]]] = None, timeout: int = 60) -> str:
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": "You analyze soil boring logs and geotechnical data to answer questions accurately."}
    ]
    if context:
        messages.append({"role": "user", "content": context})
    if history:
        for turn in history:
            role = turn.get("role") or "user"
            content = turn.get("content") or ""
            if content:
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": question})

    resp = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "messages": messages, "stream": False},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    # Ollama chat response shape: { message: { role, content }, ... }
    return (data.get("message") or {}).get("content", "")
