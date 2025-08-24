from flask import jsonify, send_file, request
from flask_restx import Namespace, Resource, fields, reqparse
from werkzeug.datastructures import FileStorage
import io, csv, os, json, requests

from app.models.dt_csv_upload import CsvUpload
from app.services.csv_service import (
    save_upload, validate_upload, load_df_for,
    compute_sales_metrics, compute_inventory_metrics,
    generate_insight_for, REQUIRED,
)

# Define allowed types for CSV
CTYPE_ENUM = ("sales", "inventory")

# Initialize Namespace for CSV operations
api = Namespace("csv", description="CSV templates, uploads, dashboard & insights")

# ------------ Swagger models ------------

# Model for the status of CSV upload
status_model = api.model("CsvStatus", {
    "id": fields.Integer,
    "csv_type": fields.String(enum=list(CTYPE_ENUM)),
    "status": fields.String(description="uploaded|validated|invalid|processed|failed"),
    "row_count": fields.Integer,
    "created_at": fields.String,
    "validated_at": fields.String(allow_none=True),
})

# Model for the successful upload response
upload_ok_model = api.model("CsvUploadOk", {
    "ok": fields.Boolean(example=True),
    "upload_id": fields.Integer,
    "row_count": fields.Integer(description="Row count if validated"),
    "missing": fields.List(fields.String, description="Missing required columns (if any)"),
    "error": fields.String(description="Error message (if any)"),
})

# Model for dashboard data (KPI, trends, etc.)
dashboard_model = api.model("CsvDashboard", {
    "ok": fields.Boolean(example=True),
    "csv_type": fields.String(enum=list(CTYPE_ENUM)),
    "kpis": fields.Raw(description="KPIs dict"),
    "sales_trend": fields.Raw(description="Only for sales"),
    "top_items": fields.Raw(description="Only for sales"),
    "inventory_levels": fields.Raw(description="Only for inventory"),
    "cogs_trend": fields.Raw(description="Only for inventory"),
})

# Model for insight generation (using Ollama)
insight_model = api.model("CsvInsight", {
    "ok": fields.Boolean(example=True),
    "metrics": fields.Raw(description="Same shape as /dashboard (or combined for pair/batch)"),
    "insight": fields.String(description="LLM-generated text"),
    "error": fields.String(description="Error message (if any)"),
})

# ------------ Parsers ------------

# File upload parser
upload_parser = api.parser()
upload_parser.add_argument(
    "type", choices=list(CTYPE_ENUM), required=True, location="args",
    help="CSV type: sales or inventory"
)
upload_parser.add_argument(
    "file", type=FileStorage, required=True, location="files",
    help="CSV file"
)
# NEW: optional batch_id for grouping uploads (e.g., sales+inventory)
upload_parser.add_argument(
    "batch_id", type=str, required=False, location="args",
    help="Optional batch id to group related uploads"
)

# ------------ Endpoints ------------

@api.route("/templates/<string:ctype>")
@api.param("ctype", "CSV template type", enum=list(CTYPE_ENUM))
class CsvTemplate(Resource):
    @api.doc("download_csv_template", produces=["text/csv"])
    def get(self, ctype: str):
        """Download header-only CSV template (sales/inventory)"""
        if ctype not in CTYPE_ENUM:
            return jsonify({"ok": False, "error": "unknown type"}), 400
        headers = REQUIRED[ctype]
        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow(headers)
        mem = io.BytesIO(si.getvalue().encode("utf-8"))
        mem.seek(0)
        return send_file(
            mem,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"{ctype}_template.csv",
        )

@api.route("/upload")
class CsvUploadResource(Resource):
    @api.doc("upload_csv")
    @api.expect(upload_parser)
    @api.response(200, "Upload accepted", upload_ok_model)
    @api.response(400, "Validation error", upload_ok_model)
    def post(self):
        """Upload CSV (multipart) and validate (<=100 rows; ignore extra columns)"""
        args = upload_parser.parse_args()
        ctype = args["type"]
        f = args["file"]
        batch_id = args.get("batch_id")  # <-- NEW
        try:
            # Save and validate the uploaded CSV
            rec = save_upload(f, ctype, user_id=None, batch_id=batch_id)  # <-- pass batch_id
            ok, info = validate_upload(rec)
            status = 200 if ok else 400
            return {"ok": ok, "upload_id": rec.id, **info}, status
        except Exception as e:
            return {"ok": False, "error": str(e)}, 400

@api.route("/<int:upload_id>/status")
@api.param("upload_id", "Upload ID")
class CsvStatus(Resource):
    @api.doc("get_csv_status")
    @api.marshal_with(status_model)
    def get(self, upload_id: int):
        """Get CSV upload status"""
        rec = CsvUpload.query.get_or_404(upload_id)
        return {
            "id": rec.id,
            "csv_type": rec.csv_type,
            "status": rec.status,
            "row_count": rec.row_count,
            "created_at": rec.created_at.isoformat(),
            "validated_at": rec.validated_at.isoformat() if rec.validated_at else None,
        }

@api.route("/dashboard/<int:upload_id>")
@api.param("upload_id", "Upload ID")
class CsvDashboard(Resource):
    @api.doc("get_dashboard_data")
    @api.response(200, "OK", dashboard_model)
    @api.response(400, "Not ready", dashboard_model)
    def get(self, upload_id: int):
        """Return chart-ready JSON for the uploaded CSV"""
        rec = CsvUpload.query.get_or_404(upload_id)
        if rec.status not in ("validated", "processed"):
            return {"ok": False, "error": f"not ready: {rec.status}"}, 400
        df = load_df_for(rec)
        data = compute_sales_metrics(df) if rec.csv_type == "sales" else compute_inventory_metrics(df)
        return {"ok": True, "csv_type": rec.csv_type, **data}, 200

@api.route("/insight/<int:upload_id>")
@api.param("upload_id", "Upload ID")
class CsvInsight(Resource):
    @api.doc("generate_insight")
    @api.response(200, "OK", insight_model)
    @api.response(400, "Not ready / error", insight_model)
    def post(self, upload_id: int):
        """Generate KPI summary & insights using Ollama (single upload)"""
        rec = CsvUpload.query.get_or_404(upload_id)
        if rec.status not in ("validated", "processed"):
            return {"ok": False, "error": f"not ready: {rec.status}"}, 400
        try:
            result = generate_insight_for(rec)
            return {"ok": True, **result}, 200
        except Exception as e:
            return {"ok": False, "error": str(e)}, 400

# ---------- NEW: list uploads (by batch) ----------

@api.route("/uploads")
class CsvUploads(Resource):
    @api.doc("list_uploads", params={"batch_id": "Optional batch id to filter"})
    def get(self):
        """
        List uploads by batch_id (optional). If no batch_id, return latest 50.
        """
        bid = request.args.get("batch_id", type=str)
        q = CsvUpload.query
        if bid:
            q = q.filter_by(batch_id=bid)
        rows = q.order_by(CsvUpload.id.desc()).limit(50).all()
        return [{
            "id": r.id,
            "csv_type": r.csv_type,
            "status": r.status,
            "row_count": r.row_count,
            "batch_id": r.batch_id,
            "created_at": r.created_at.isoformat(),
            "validated_at": r.validated_at.isoformat() if r.validated_at else None,
            "original_filename": r.original_filename,
        } for r in rows]

# ---------- NEW: pair insight (sales + inventory) ----------

@api.route("/insight/pair")
class CsvInsightPair(Resource):
    @api.doc("generate_pair_insight", params={
        "sales_id": "Sales upload ID",
        "inventory_id": "Inventory upload ID",
        "batch_id": "Optional: if provided, picks latest validated sales & inventory in the batch"
    })
    @api.response(200, "OK", insight_model)
    @api.response(400, "Not ready / error", insight_model)
    def post(self):
        """
        Generate combined insight using two uploads (sales + inventory).
        Accepts either:
          - query params: ?sales_id=..&inventory_id=..
          - or ?batch_id=... (picks most recent validated of each type)
        """
        sales_id = request.args.get("sales_id", type=int)
        inv_id   = request.args.get("inventory_id", type=int)
        batch_id = request.args.get("batch_id", type=str)

        sales_rec, inv_rec = None, None

        if batch_id:
            q = CsvUpload.query.filter_by(batch_id=batch_id, status="validated")
            sales_rec = q.filter_by(csv_type="sales").order_by(CsvUpload.id.desc()).first()
            inv_rec   = q.filter_by(csv_type="inventory").order_by(CsvUpload.id.desc()).first()
        else:
            if sales_id:
                sales_rec = CsvUpload.query.get(sales_id)
            if inv_id:
                inv_rec = CsvUpload.query.get(inv_id)

        if not sales_rec or sales_rec.status not in ("validated","processed"):
            return {"ok": False, "error": "sales upload not ready or missing"}, 400
        if not inv_rec or inv_rec.status not in ("validated","processed"):
            return {"ok": False, "error": "inventory upload not ready or missing"}, 400

        # Build metrics
        sales_df = load_df_for(sales_rec)
        inv_df   = load_df_for(inv_rec)
        sales_m  = compute_sales_metrics(sales_df)
        inv_m    = compute_inventory_metrics(inv_df)

        combined = {
            "sales": sales_m,
            "inventory": inv_m
        }

        # Call Ollama once with combined JSON
        model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        host  = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        metrics_json = json.dumps(combined, default=str, ensure_ascii=False)[:8000]
        prompt = f"""You are a retail analyst. Using the combined JSON (sales + inventory), return:
1) 6 concise, numbered insights that connect sales and inventory (e.g., stockouts impacting revenue, high AOV items vs. on-hand)
2) 4 prioritized actions (bullets), referencing SKUs/dates if relevant
Keep it short and practical.
JSON:
{metrics_json}
"""
        try:
            r = requests.post(
                f"{host}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=120
            )
            r.raise_for_status()
            resp = r.json().get("response", "").strip()
            return {"ok": True, "metrics": combined, "insight": resp}, 200
        except Exception as e:
            return {"ok": False, "error": str(e)}, 400

# ---------- NEW: batch insight (N CSVs in one batch) ----------

@api.route("/insight/batch")
class CsvInsightBatch(Resource):
    @api.doc("generate_batch_insight", params={
        "batch_id": "Batch id to aggregate all validated uploads"
    })
    @api.response(200, "OK", insight_model)
    @api.response(400, "Not ready / error", insight_model)
    def post(self):
        """
        Generate combined insight over ALL validated uploads in a batch.
        Query: ?batch_id=abc
        It aggregates per-type metrics (sales, inventory) across multiple files.
        """
        import pandas as pd

        batch_id = request.args.get("batch_id", type=str)
        if not batch_id:
            return {"ok": False, "error": "batch_id is required"}, 400

        rows = (CsvUpload.query
                 .filter_by(batch_id=batch_id)
                 .filter(CsvUpload.status.in_(("validated","processed")))
                 .order_by(CsvUpload.id.asc())
                 .all())
        if not rows:
            return {"ok": False, "error": "no validated uploads in this batch"}, 400

        sales_dfs, inv_dfs = [], []
        for r in rows:
            df = load_df_for(r)
            if r.csv_type == "sales":
                sales_dfs.append(df)
            else:
                inv_dfs.append(df)

        combined = {}
        if sales_dfs:
            sales_df = (pd.concat(sales_dfs, ignore_index=True)
                        if len(sales_dfs) > 1 else sales_dfs[0])
            combined["sales"] = compute_sales_metrics(sales_df)
        if inv_dfs:
            inv_df = (pd.concat(inv_dfs, ignore_index=True)
                      if len(inv_dfs) > 1 else inv_dfs[0])
            combined["inventory"] = compute_inventory_metrics(inv_df)

        if not combined:
            return {"ok": False, "error": "no data to analyze in batch"}, 400

        # Ollama
        model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        host  = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        metrics_json = json.dumps(combined, default=str, ensure_ascii=False)[:8000]
        prompt = f"""You are a retail analyst. Using the aggregated JSON (may include multiple sales and inventory files),
return:
1) 6 concise, numbered insights connecting sales and inventory (e.g., stockouts causing missed revenue, fast movers vs on-hand).
2) 4 prioritized actions (bullets), referencing SKUs/dates if relevant.
Be brief and practical.

JSON:
{metrics_json}
"""
        try:
            r = requests.post(
                f"{host}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=120
            )
            r.raise_for_status()
            resp = r.json().get("response", "").strip()
            return {"ok": True, "metrics": combined, "insight": resp}, 200
        except Exception as e:
            return {"ok": False, "error": str(e)}, 400
