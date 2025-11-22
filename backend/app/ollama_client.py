import os
from typing import Optional, List, Dict

import requests
from requests import RequestException


OLLAMA_URL = os.environ.get("OLLAMA_URL", "").strip()
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gpt-oss:120b-cloud")


UNAVAILABLE_MSG = (
    "AI service unavailable: cannot reach Ollama. "
    "Set OLLAMA_URL (e.g., http://localhost:11434/api/chat) or disable AI features."
)


def ask(question: str, context: Optional[str] = None, history: Optional[List[Dict[str, str]]] = None, timeout: int = 60) -> str:
    if not OLLAMA_URL:
        return "AI service unavailable: OLLAMA_URL is not configured."

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

    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "messages": messages, "stream": False},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return (data.get("message") or {}).get("content", "")
    except RequestException:
        return UNAVAILABLE_MSG
