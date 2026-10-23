"""
EcoLogix AI - Autonomous Agentic Cold-Chain Food Rescue & Spoilage Prevention System
Main Application Server (Flask REST API & Dashboard Host)
"""

import os
import json
import time
from flask import Flask, render_template, request, jsonify, send_file
from core.models import UserRole, IoTTelemetry, ActionRecommendation
from core.gemini_client import GeminiClient
from core.security import SecurityEngine
from database.db import db_instance
from agents.orchestrator import MultiAgentOrchestrator
from analytics.bigquery_engine import BigQueryAnalyticsEngine, BIGQUERY_SCHEMA_DDL, ANALYTICAL_ESG_QUERY

app = Flask(__name__)

# Initialize singletons
gemini_client = GeminiClient()
orchestrator = MultiAgentOrchestrator(gemini_client=gemini_client)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download")
@app.route("/api/download")
def download_project_zip():
    """
    Allows user to directly download the complete self-contained project ZIP package.
    Supports on-disk cached archive and on-the-fly dynamic packaging for serverless (Vercel) environments.
    """
    import io
    import zipfile

    zip_path = os.path.join(os.path.dirname(__file__), "EcoLogix_AI_System.zip")
    if os.path.exists(zip_path):
        return send_file(zip_path, as_attachment=True, download_name="EcoLogix_AI_System.zip")

    # Dynamic in-memory packaging for serverless deployment
    mem_buf = io.BytesIO()
    base_dir = os.path.dirname(__file__)
    with zipfile.ZipFile(mem_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for folder in ["core", "agents", "analytics", "database", "static", "templates", "tests"]:
            fpath = os.path.join(base_dir, folder)
            if os.path.exists(fpath):
                for root, _, files in os.walk(fpath):
                    if "__pycache__" in root:
                        continue
                    for file in files:
                        full_p = os.path.join(root, file)
                        rel_p = os.path.relpath(full_p, base_dir)
                        zf.write(full_p, rel_p)
        for fname in ["app.py", "README.md", "requirements.txt", "vercel.json"]:
            full_p = os.path.join(base_dir, fname)
            if os.path.exists(full_p):
                zf.write(full_p, fname)

    mem_buf.seek(0)
    return send_file(mem_buf, mimetype="application/zip", as_attachment=True, download_name="EcoLogix_AI_System.zip")


# ==========================================
# BATCH & INVENTORY ENDPOINTS
# ==========================================

@app.route("/api/batches", methods=["GET"])
def get_batches():
    batches = db_instance.get_all_batches()
    return jsonify([b.model_dump() for b in batches])


@app.route("/api/batches/<batch_id>", methods=["GET"])
def get_batch(batch_id):
    batch = db_instance.get_batch(batch_id)
    if not batch:
        return jsonify({"error": "Batch not found"}), 404
    return jsonify(batch.model_dump())


@app.route("/api/batches/<batch_id>/simulate", methods=["POST"])
def simulate_sensor_tick(batch_id):
    """
    Simulates real-world sensor fluctuations: temperature spike, cooling recovery, or door open.
    """
    data = request.get_json() or {}
    temp_delta = float(data.get("temp_delta_c", 0.0))
    duration_min = float(data.get("duration_min", 15.0))

    updated_batch = db_instance.simulate_telemetry_tick(batch_id, temp_delta, duration_min)
    if not updated_batch:
        return jsonify({"error": "Batch not found"}), 404

    orchestrator.record_audit_log(
        actor_id="IOT_GATEWAY_SIMULATOR",
        actor_role=UserRole.SYSTEM_AGENT,
        action_type="TELEMETRY_SPIKE_SIMULATED",
        batch_id=batch_id,
        details={
            "temp_delta_c": temp_delta,
            "duration_min": duration_min,
            "new_temp": updated_batch.telemetry_history[-1].temperature_c,
            "new_status": updated_batch.safety_status.value,
            "danger_zone_minutes": updated_batch.danger_zone_minutes,
        },
    )

    return jsonify(updated_batch.model_dump())


@app.route("/api/batches/reset", methods=["POST"])
def reset_batches():
    """
    Resets all inventory batches and recipient hubs to original seed state.
    """
    db_instance.initialize_seed_data()
    orchestrator.active_plans.clear()
    orchestrator.pending_hitl_plans.clear()
    orchestrator.record_audit_log(
        actor_id="SYSTEM_OPERATOR",
        actor_role=UserRole.SYSTEM_AGENT,
        action_type="DATABASE_RESET",
        batch_id=None,
        details={"status": "All scenario data reloaded to baseline."},
    )
    return jsonify({"status": "Database successfully reset to seed state."})


# ==========================================
# MULTI-AGENT ORCHESTRATION PIPELINE
# ==========================================

@app.route("/api/pipeline/run/<batch_id>", methods=["POST"])
def run_pipeline(batch_id):
    """
    Triggers the end-to-end multi-agent execution pipeline for a specific batch.
    """
    batch = db_instance.get_batch(batch_id)
    if not batch:
        return jsonify({"error": "Batch not found"}), 404

    hubs = db_instance.get_all_hubs()
    trace = orchestrator.run_pipeline_for_batch(batch=batch, candidate_hubs=hubs)
    return jsonify(trace)


@app.route("/api/pipeline/run-all", methods=["POST"])
def run_all_batches():
    """
    Triggers autonomous triage across all active inventory batches.
    """
    batches = db_instance.get_all_batches()
    hubs = db_instance.get_all_hubs()
    all_traces = []

    for b in batches:
        trace = orchestrator.run_pipeline_for_batch(batch=b, candidate_hubs=hubs)
        all_traces.append(trace)

    return jsonify({"traces": all_traces, "total_triaged": len(all_traces)})


# ==========================================
# ALLOCATION PLANS & HITL APPROVALS
# ==========================================

@app.route("/api/plans", methods=["GET"])
def get_plans():
    plans = list(orchestrator.active_plans.values())
    return jsonify([p.model_dump() for p in plans])


@app.route("/api/plans/<plan_id>/approve", methods=["POST"])
def approve_plan(plan_id):
    """
    Human-in-the-Loop (HITL) authorization by a certified Food Safety Officer.
    """
    data = request.get_json() or {}
    approver_name = data.get("approver_name", "Dr. Jane Reynolds, Food Safety Officer")
    role_str = data.get("role", UserRole.FOOD_SAFETY_OFFICER.value)

    try:
        role = UserRole(role_str)
    except ValueError:
        role = UserRole.FOOD_SAFETY_OFFICER

    success, plan, msg = orchestrator.approve_hitl_plan(plan_id, approver_name, role)
    if not success:
        return jsonify({"error": msg}), 403

    return jsonify({"status": msg, "plan": plan.model_dump()})


@app.route("/api/plans/<plan_id>/reject", methods=["POST"])
def reject_plan(plan_id):
    """
    Human rejection of a proposed allocation.
    """
    data = request.get_json() or {}
    officer_name = data.get("approver_name", "Dr. Jane Reynolds, Food Safety Officer")
    reason = data.get("reason", "Rejected due to secondary risk assessment.")

    plan = orchestrator.active_plans.get(plan_id)
    if not plan:
        return jsonify({"error": "Plan not found"}), 404

    plan.recommended_action = ActionRecommendation.ANAEROBIC_DIGESTION_BIOGAS
    plan.ai_reasoning += f" [HUMAN OFFICER REJECTION: {reason}]"
    plan.hitl_approved = False
    plan.meals_provided = 0

    if plan_id in orchestrator.pending_hitl_plans:
        del orchestrator.pending_hitl_plans[plan_id]

    orchestrator.record_audit_log(
        actor_id=officer_name,
        actor_role=UserRole.FOOD_SAFETY_OFFICER,
        action_type="HITL_DISPATCH_REJECTED",
        batch_id=plan.batch_id,
        details={"plan_id": plan_id, "rejection_reason": reason},
    )

    return jsonify({"status": "Plan successfully rejected and diverted to biogas.", "plan": plan.model_dump()})


# ==========================================
# CRYPTOGRAPHIC AUDIT LEDGER & SECURITY
# ==========================================

@app.route("/api/audit-ledger", methods=["GET"])
def get_audit_ledger():
    return jsonify(orchestrator.audit_ledger)


@app.route("/api/audit-ledger/verify", methods=["GET"])
def verify_audit_ledger():
    """
    Cryptographically verifies the entire SHA-256 block sequence for zero-tampering.
    """
    is_valid, error_msg = SecurityEngine.verify_ledger_integrity(orchestrator.audit_ledger)
    return jsonify({
        "integrity_intact": is_valid,
        "total_blocks": len(orchestrator.audit_ledger),
        "latest_hash": orchestrator.get_latest_hash(),
        "error": error_msg,
    })


# ==========================================
# GOOGLE CLOUD BIGQUERY & ESG ANALYTICS
# ==========================================

@app.route("/api/analytics/esg", methods=["GET"])
def get_esg_analytics():
    plans = list(orchestrator.active_plans.values())
    esg_summary = BigQueryAnalyticsEngine.aggregate_esg_impact(plans)
    return jsonify(esg_summary)


@app.route("/api/bigquery/export", methods=["GET"])
def export_bigquery():
    """
    Returns BigQuery streaming buffer rows and standard DDL & SQL analytics queries.
    """
    plans = list(orchestrator.active_plans.values())
    rows = [BigQueryAnalyticsEngine.format_plan_for_bigquery(p) for p in plans]
    return jsonify({
        "project_id": "google-cloud-ecologix-prod",
        "dataset": "ecologix_enterprise_dw",
        "total_rows_buffered": len(rows),
        "streaming_rows": rows,
        "bigquery_ddl": BIGQUERY_SCHEMA_DDL,
        "analytical_sql": ANALYTICAL_ESG_QUERY,
    })


# ==========================================
# CONFIGURATION & GEMINI API KEY
# ==========================================

@app.route("/api/config/status", methods=["GET"])
def get_config_status():
    is_live = gemini_client.is_live_configured()
    return jsonify({
        "live_gemini_active": is_live,
        "model": gemini_client.model,
        "engine_mode": f"Live Google Gemini API ({gemini_client.model})" if is_live else "EcoLogix Cognitive Engine (Zero-Config Offline Fallback)",
        "api_key_set": bool(gemini_client.api_key),
    })


@app.route("/api/config/gemini-key", methods=["POST"])
def set_gemini_key():
    data = request.get_json() or {}
    key = data.get("api_key", "").strip()
    if not key:
        return jsonify({"error": "Key cannot be empty"}), 400

    gemini_client.set_api_key(key)
    return jsonify({
        "status": "API key updated successfully.",
        "live_gemini_active": gemini_client.is_live_configured(),
        "engine_mode": "Live Google Gemini API" if gemini_client.is_live_configured() else "EcoLogix Cognitive Engine",
    })


if __name__ == "__main__":
    print("=" * 70)
    print("  EcoLogix AI - Autonomous Agentic Cold-Chain Food Rescue System")
    print("  Powering Sustainable Logistics, HACCP Safety & BigQuery ESG Analytics")
    print("  Google Cloud & Gemini Agentic System")
    print("=" * 70)
    app.run(host="127.0.0.1", port=5000, debug=True)
