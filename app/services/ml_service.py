from pathlib import Path
from typing import List, Dict, Any
import joblib
from sklearn.exceptions import NotFittedError

MODEL_PATH = Path(__file__).resolve().parent.parent / "ml" / "models" / "model.joblib"
SPECIES = {0: "setosa", 1: "versicolor", 2: "virginica"}

_model_cache = None

def _load_model():
    global _model_cache
    if _model_cache is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}")
        _model_cache = joblib.load(MODEL_PATH)
    return _model_cache

def predict(features: List[float]) -> Dict[str, Any]:
    try:
        model = _load_model()
        pred = model.predict([features])[0]
        proba = model.predict_proba([features])[0].tolist() if hasattr(model, "predict_proba") else None

        pred_idx = int(pred)
        out = {
            "ok": True,
            "prediction": pred_idx,
            "label": SPECIES.get(pred_idx),
        }
        if proba is not None:
            out["probabilities"] = [{"label": SPECIES[i], "p": float(p)} for i, p in enumerate(proba)]
        return out
    except FileNotFoundError as e:
        return {"ok": False, "error": str(e)}
    except NotFittedError:
        return {"ok": False, "error": "Model not fitted yet."}
    except Exception as e:
        return {"ok": False, "error": f"Prediction error: {e}"}
