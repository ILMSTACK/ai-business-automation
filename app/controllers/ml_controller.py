from flask import request, jsonify
from ..services.ml_service import predict

def post_predict():
    data = request.get_json(silent=True) or {}
    features = data.get("features")
    if not isinstance(features, list):
        return jsonify({"ok": False, "error": "Expected 'features' as a list of floats"}), 400
    res = predict(features)
    status = 200 if res.get("ok") else 500
    return jsonify(res), status
