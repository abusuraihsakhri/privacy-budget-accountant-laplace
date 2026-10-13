"""
FastAPI REST API Server for Privacy Budget Accountant Laplace.
"""
from typing import Dict, Any, List
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from .base import SecurityException
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Privacy Budget Accountant Laplace API",
    description="Legacy threshold-based task audit API; does not provide a persistent differential privacy ledger.",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


WEB_DIR = Path(__file__).resolve().parent.parent / "web"


@app.get("/", include_in_schema=False)
def browser_app():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/app.js", include_in_schema=False)
def browser_script():
    return FileResponse(WEB_DIR / "app.js", media_type="text/javascript")


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "privacy-budget-accountant-laplace", "domain": "Privacy-Preserving Federated Healthcare & FHE", "standard": "HIPAA Safe Harbor §164.514 / Google SecAgg Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
    except SecurityException:
        raise HTTPException(status_code=422, detail="Input contains a prohibited identifier")
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
