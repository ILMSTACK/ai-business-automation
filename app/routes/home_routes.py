from flask import Blueprint
from ..controllers.home_controller import index, chat_page

home_bp = Blueprint("home", __name__)

@home_bp.route("/", methods=["GET"])
def home_index():
    return index()

@home_bp.route("/chat", methods=["GET"])
def home_chat():
    return chat_page()
