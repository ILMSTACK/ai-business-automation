# app/services/csv_service.py

import csv, hashlib, io, os, json
from datetime import datetime
import pandas as pd
from flask import current_app
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.dt_csv_upload import CsvUpload
import requests

# -------- Required headers --------
REQ_SALES = ["invoice_id","invoice_date","customer_id","item_id","qty","unit_price"]
REQ_INV   = ["move_id","move_date","item_id","type","qty","unit_cost"]
REQUIRED = {"sales": REQ_SALES, "inventory": REQ_INV}
TYPES = ("sales","inventory")

# -------- Helpers --------

def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".",1)[1].lower() == "csv"

def _sha256_file(fpath: str) -> str:
    h = hashlib.sha256()
    with open(fpath,'rb') as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _csv_root_folder() -> str:
    return current_app.config.get(
        "UPLOAD_FOLDER",
        os.path.join(current_app.root_path, "..", "public", "storage"),
    )

def _max_rows() -> int:
    return int(current_app.config.get("MAX_CSV_ROWS", 100))

# -------- Upload + Validate --------

def save_upload(file_storage, csv_type: str, user_id=None, batch_id=None) -> CsvUpload:
    """
    Save raw CSV to public/storage/<user_id>/<id>-<type>.csv and create DB row.
    """
    if csv_type not in TYPES:
        raise ValueError("invalid type")
    if not _allowed_file(file_storage.filename):
        raise ValueError("only .csv allowed")

    # ensure folder
    root = _csv_root_folder()
    uid = str(user_id or "anonymous")
    folder = os.path.join(root, uid)
    os.makedirs(folder, exist_ok=True)

    # temp name first
    original = secure_filename(file_storage.filename)
    tmp_path = os.path.join(folder, f"tmp_{original}")
    file_storage.save(tmp_path)
    size_bytes = os.path.getsize(tmp_path)

    # create DB row to get id
    rec = CsvUpload(
        user_id=user_id,
        csv_type=csv_type,
        csv_path="",  # fill after we know id
        original_filename=original,
        size_bytes=size_bytes,
        status="uploaded",
        batch_id=batch_id,
    )
    db.session.add(rec)
    db.session.commit()

    final_path = os.path.join(folder, f"{rec.id}-{csv_type}.csv")
    os.replace(tmp_path, final_path)

    # compute hash
    rec.csv_path = os.path.abspath(final_path)
    rec.content_sha256 = _sha256_file(final_path)
    db.session.commit()
    return rec

def _read_head_and_headers(path: str, required_cols: list[str]):
    """
    Read first 101 rows (enforce limit) and return (cols, missing, too_many_rows).
    """
    df = pd.read_csv(path, nrows=_max_rows() + 1)
    cols = [str(c).strip() for c in df.columns.tolist()]
    missing = [c for c in required_cols if c not in cols]
    too_many_rows = len(df) > _max_rows()
    return cols, missing, too_many_rows

def validate_upload(rec: CsvUpload):
    req = REQUIRED[rec.csv_type]
    cols, missing, too_many = _read_head_and_headers(rec.csv_path, req)

    if missing:
        rec.status = "invalid"
        rec.error_msg = f"Missing columns: {missing}"
        rec.detected_columns = json.dumps(cols)
        rec.validated_at = datetime.utcnow()
        db.session.commit()
        return False, {"missing": missing}

    # re-read with usecols to ignore extras
    df = pd.read_csv(rec.csv_path, usecols=req)

    if len(df) > _max_rows():
        rec.status = "invalid"
        rec.error_msg = "Row limit exceeded"
        rec.detected_columns = json.dumps(cols)
        rec.validated_at = datetime.utcnow()
        db.session.commit()
        return False, {"error": "Row limit exceeded"}

    try:
        # Dates
        date_col = "invoice_date" if rec.csv_type == "sales" else "move_date"
        pd.to_datetime(df[date_col], format="%Y-%m-%d", errors="raise")

        # Numerics
        num_cols = ["qty","unit_price"] if rec.csv_type == "sales" else ["qty","unit_cost"]
        for c in num_cols:
            pd.to_numeric(df[c], errors="raise")

        # Inventory type enum
        if rec.csv_type == "inventory":
            # normalize case
            df["type"] = df["type"].astype(str).str.upper().str.strip()
            allowed = {"IN","OUT","ADJ"}
            if not set(df["type"].unique()).issubset(allowed):
                raise ValueError("type must be IN|OUT|ADJ")
    except Exception as e:
        rec.status = "invalid"
        rec.error_msg = f"type/date error: {e}"
        rec.detected_columns = json.dumps(cols)
        rec.validated_at = datetime.utcnow()
        db.session.commit()
        return False, {"error": str(e)}

    rec.status = "validated"
    rec.row_count = len(df)
    rec.detected_columns = json.dumps(cols)
    rec.validated_at = datetime.utcnow()
    db.session.commit()
    return True, {"row_count": len(df)}

# -------- Metrics --------

def compute_sales_metrics(df: pd.DataFrame):
    df = df.copy()
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0)
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce").fillna(0.0)

    df["revenue"] = df["qty"] * df["unit_price"]
    revenue = float(df["revenue"].sum())
    units = int(df["qty"].sum())
    orders = int(df["invoice_id"].nunique())
    aov = float(revenue / orders) if orders else 0.0

    # Explicit string date column, then group by it
    df["date"] = df["invoice_date"].dt.date.astype(str)
    trend = (
        df.groupby("date", as_index=False)
          .agg(revenue=("revenue","sum"), units=("qty","sum"))
    )

    # Top items
    top_items = (
        df.groupby("item_id", as_index=False)
          .agg(revenue=("revenue","sum"), units=("qty","sum"))
          .sort_values(["revenue","units"], ascending=False)
          .head(10)
    )

    return {
        "kpis": {
            "revenue": revenue,
            "units_sold": units,
            "orders": orders,
            "aov": aov,
        },
        "sales_trend": trend.to_dict(orient="records"),
        "top_items": top_items.to_dict(orient="records"),
    }

def compute_inventory_metrics(df: pd.DataFrame):
    df = df.copy()
    df["move_date"] = pd.to_datetime(df["move_date"], errors="coerce")
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0)
    df["unit_cost"] = pd.to_numeric(df["unit_cost"], errors="coerce").fillna(0.0)
    df["type"] = df["type"].astype(str).str.upper().str.strip()

    # Signed qty for on-hand
    def sgn(t, q): return q if t=="IN" else (-q if t=="OUT" else q)
    df["signed_qty"] = df.apply(lambda r: sgn(r["type"], r["qty"]), axis=1)
    soh = (
        df.groupby("item_id", as_index=False)["signed_qty"]
          .sum()
          .rename(columns={"signed_qty": "on_hand"})
    )

    # COGS + trend
    outs = df[df["type"]=="OUT"].copy()
    outs["cogs_line"] = outs["qty"] * outs["unit_cost"]

    if outs.empty:
        cogs = 0.0
        cogs_trend = pd.DataFrame(columns=["date","cogs"])
    else:
        cogs = float(outs["cogs_line"].sum())
        outs["date"] = outs["move_date"].dt.date.astype(str)   # explicit date column
        cogs_trend = (
            outs.groupby("date", as_index=False)["cogs_line"].sum()
                .rename(columns={"cogs_line":"cogs"})
        )

    # Simple WAC (IN + positive ADJ)
    inp = df[(df["type"]=="IN") | ((df["type"]=="ADJ") & (df["qty"]>0))].copy()
    if not inp.empty:
        inp["value"] = inp["qty"] * inp["unit_cost"]
        wac = (
            inp.groupby("item_id")[["value","qty"]].sum()
               .assign(wac=lambda x: x["value"] / x["qty"])
               .reset_index()[["item_id","wac"]]
        )
    else:
        wac = pd.DataFrame(columns=["item_id","wac"])

    levels = soh.merge(wac, on="item_id", how="left").fillna({"wac": 0})
    levels["value"] = levels["on_hand"] * levels["wac"]

    # Clean possible NaN to pure Python (safe for JSON)
    levels = levels.replace({pd.NA: 0}).fillna(0)

    return {
        "kpis": {"cogs": float(cogs)},
        "inventory_levels": levels.to_dict(orient="records"),
        "cogs_trend": cogs_trend.to_dict(orient="records"),
    }

def load_df_for(rec: CsvUpload) -> pd.DataFrame:
    usecols = REQUIRED[rec.csv_type]
    # Ignore extra columns; let Pandas infer types
    return pd.read_csv(rec.csv_path, usecols=usecols)

# -------- Insight (Ollama) --------

def generate_insight_for(rec: CsvUpload):
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    host  = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

    df = load_df_for(rec)
    metrics = compute_sales_metrics(df) if rec.csv_type == "sales" else compute_inventory_metrics(df)

    # Robust JSON for prompt
    metrics_json = json.dumps(metrics, default=str, ensure_ascii=False)[:8000]

    prompt = f"""You are a retail analyst. Using the JSON below, return:
1) 5 concise, numbered insights
2) 3 actions (bullets)
Keep it short and practical.
JSON:
{metrics_json}
"""

    r = requests.post(
        f"{host}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120,
    )
    r.raise_for_status()
    resp = r.json().get("response", "").strip()
    return {"metrics": metrics, "insight": resp}
