"""
MCP Tool registry — imports trigger @mcp.tool() registration.
"""
from app.mcp.tools.patient_tools import search_patient
from app.mcp.tools.risk_tools import get_patient_risk
from app.mcp.tools.prescription_tools import get_patient_prescriptions
from app.mcp.tools.dashboard_tools import get_dashboard_summary, get_recent_alerts
