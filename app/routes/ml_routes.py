from flask import Blueprint
from ..controllers.ml_controller import post_predict

ml_bp = Blueprint("ml", __name__)

@ml_bp.route("/predict", methods=["POST"])
def predict():
    return post_predict()
