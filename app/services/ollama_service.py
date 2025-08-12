from typing import Dict, Any
import os, ollama

_client = ollama.Client(host=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"))

def chat(prompt: str, model: str | None = None) -> Dict[str, Any]:
    try:
        use_model = (model or os.getenv("OLLAMA_MODEL") or "llama3").strip()
        res = _client.chat(model=use_model, messages=[{"role":"user","content":prompt}])
        return {"ok": True, "reply": res.get("message", {}).get("content", ""), "model": use_model}
    except Exception as e:
        return {"ok": False, "error": f"Ollama error: {e}"}
