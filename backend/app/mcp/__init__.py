"""
AAROGYA MCP (Model Context Protocol) — Server & Tool exports.

Provides a FastMCP-based tool registry for patient data, risk scores,
prescriptions, and dashboard analytics.
"""
from app.mcp.server import mcp_server, call_mcp_tool, list_mcp_tools

from app.mcp.tools.patient_tools import search_patient
from app.mcp.tools.risk_tools import get_patient_risk
from app.mcp.tools.prescription_tools import get_patient_prescriptions
from app.mcp.tools.dashboard_tools import get_dashboard_summary, get_recent_alerts

__all__ = [
    "mcp_server",
    "call_mcp_tool",
    "list_mcp_tools",
    "search_patient",
    "get_patient_risk",
    "get_patient_prescriptions",
    "get_dashboard_summary",
    "get_recent_alerts",
]
