from flask import Blueprint
from ..controllers.llm_controller import post_chat, post_chat_stream

llm_bp = Blueprint("llm", __name__)

@llm_bp.route("/chat", methods=["POST"])
def chat():
    return post_chat()

@llm_bp.route("/chat/stream", methods=["POST"])
def chat_stream():
    return post_chat_stream()
