"""
MCP REST API — Exposes MCP tools over HTTP for the Next.js dashboard.

Endpoints:
  GET  /mcp/health              → MCP server status
  GET  /mcp/tools               → List available tools
  POST /mcp/tools/{name}/execute → Execute a tool with args
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

from app.api.auth import get_current_user
from app.models.user import User
from app.mcp.server import mcp_server, call_mcp_tool, list_mcp_tools

logger = logging.getLogger("aarogya.api.mcp")

router = APIRouter(prefix="/mcp", tags=["mcp"])


class ToolExecuteRequest(BaseModel):
    args: Optional[Dict[str, Any]] = {}


@router.get("/search_patient")
def mcp_search_patient(patient_id: str, current_user: User = Depends(get_current_user)):
    """Lookup patient details via MCP tool."""
    return {"tool": "search_patient", "result": call_mcp_tool("search_patient", {"patient_id": patient_id})}

@router.get("/get_patient_risk")
def mcp_get_patient_risk(patient_id: str, current_user: User = Depends(get_current_user)):
    """Retrieve patient risk via MCP tool."""
    return {"tool": "get_patient_risk", "result": call_mcp_tool("get_patient_risk", {"patient_id": patient_id})}

@router.get("/get_patient_prescriptions")
def mcp_get_patient_prescriptions(patient_id: str, current_user: User = Depends(get_current_user)):
    """Retrieve patient prescriptions via MCP tool."""
    return {"tool": "get_patient_prescriptions", "result": call_mcp_tool("get_patient_prescriptions", {"patient_id": patient_id})}

@router.get("/dashboard_summary")
def mcp_dashboard_summary(current_user: User = Depends(get_current_user)):
    """Retrieve dashboard summary via MCP tool (alias for existing summary)."""
    return {"tool": "get_dashboard_summary", "result": call_mcp_tool("get_dashboard_summary", {})}



@router.get("/tools")
def mcp_list_tools(current_user: User = Depends(get_current_user)):
    """List all available MCP tools with descriptions and parameter schemas."""
    return {"tools": list_mcp_tools()}


@router.post("/tools/{tool_name}/execute")
def mcp_execute_tool(
    tool_name: str,
    body: ToolExecuteRequest,
    current_user: User = Depends(get_current_user),
):
    """Execute an MCP tool by name with the provided arguments."""
    result = call_mcp_tool(tool_name, body.args)
    if "error" in result and "Unknown MCP tool" in result["error"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return {"tool": tool_name, "result": result}
