"""Train a tiny classifier on Iris and save model.joblib.
Run: python app/ml/train/train_example.py
"""
from pathlib import Path
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import joblib

BASE = Path(__file__).resolve().parents[1]
SAVE_TO = BASE / "models" / "model.joblib"
SAVE_TO.parent.mkdir(parents=True, exist_ok=True)

X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

clf = LogisticRegression(max_iter=200)
clf.fit(X_train, y_train)
acc = clf.score(X_test, y_test)

joblib.dump(clf, SAVE_TO)
print(f"Saved model to: {SAVE_TO}")
print(f"Test accuracy: {acc:.3f}")
