from flask import request, jsonify, Response
from ..services.ollama_service import chat as ollama_chat
import os, ollama

def post_chat():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    model  = (data.get("model")  or os.getenv("OLLAMA_MODEL") or "llama3").strip()
    if not prompt:
        return jsonify({"ok": False, "error": "Missing 'prompt'"}), 400
    res = ollama_chat(prompt, model)
    status = 200 if res.get("ok") else 500
    return jsonify(res), status

def post_chat_stream():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    model  = (data.get("model")  or os.getenv("OLLAMA_MODEL") or "llama3").strip()
    if not prompt:
        return jsonify({"ok": False, "error": "Missing 'prompt'"}), 400

    client = ollama.Client(host=os.getenv("OLLAMA_HOST","http://127.0.0.1:11434"))
    def gen():
        try:
            for chunk in client.chat(model=model, messages=[{"role":"user","content":prompt}], stream=True):
                token = chunk.get("message", {}).get("content", "")
                if token:
                    yield token
        except Exception as e:
            yield f"\n[ERROR] {e}"
    return Response(gen(), mimetype="text/plain")
