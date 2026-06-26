"""
EdgeFramework — API de estado
Permite monitorizar el framework via HTTP.

Uso:
    uvicorn edge_framework.api.status:app --port 8080

Endpoints:
    GET /status    → estado del framework
    GET /health    → health check
    GET /metrics   → métricas del día
"""

from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI(
    title="EdgeFramework API",
    description="API de monitorización para EdgeFramework",
    version="0.2.0"
)

# Estado compartido (se actualiza desde el engine)
_state = {
    "running": False,
    "started_at": None,
    "connector": None,
    "mode": None,
    "balance": 0.0,
    "trades_today": 0,
    "pnl_today": 0.0,
    "last_cycle": None,
    "signals_evaluated": 0,
    "signals_approved": 0,
}


def update_state(**kwargs):
    """Actualizar estado desde el engine."""
    _state.update(kwargs)


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/status")
def status():
    return {
        "framework": "EdgeFramework",
        "version": "0.2.0",
        "running": _state["running"],
        "started_at": _state["started_at"],
        "connector": _state["connector"],
        "mode": _state["mode"],
        "balance": _state["balance"],
        "last_cycle": _state["last_cycle"],
    }


@app.get("/metrics")
def metrics():
    return {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "trades_today": _state["trades_today"],
        "pnl_today": _state["pnl_today"],
        "signals_evaluated": _state["signals_evaluated"],
        "signals_approved": _state["signals_approved"],
    }


@app.get("/positions")
def positions():
    return {
        "positions": _state.get("positions", []),
        "count": len(_state.get("positions", []))
    }