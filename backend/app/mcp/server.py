"""
AAROGYA MCP Server — FastMCP-based Model Context Protocol server.

Registers all healthcare tools and provides programmatic helpers:
  - call_mcp_tool(tool_name, args)  → invoke any tool by name
  - list_mcp_tools()                → introspect available tools
  - Standalone stdio mode           → `python -m app.mcp.server`
"""
import logging
from typing import Any, Dict, List

logger = logging.getLogger("aarogya.mcp.server")

# ---------------------------------------------------------------------------
# Tool registry – plain dict mapping name → callable
# ---------------------------------------------------------------------------

from app.mcp.tools.patient_tools import search_patient
from app.mcp.tools.risk_tools import get_patient_risk
from app.mcp.tools.prescription_tools import get_patient_prescriptions
from app.mcp.tools.dashboard_tools import get_dashboard_summary, get_recent_alerts

# Canonical registry
_TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "search_patient": {
        "fn": search_patient,
        "description": "Look up a patient by their UUID. Returns demographics, contact info, and risk assessment.",
        "parameters": {
            "patient_id": {
                "type": "string",
                "description": "UUID of the patient to look up.",
                "required": True,
            }
        },
    },
    "get_patient_risk": {
        "fn": get_patient_risk,
        "description": "Retrieve the current risk score and risk level for a patient.",
        "parameters": {
            "patient_id": {
                "type": "string",
                "description": "UUID of the patient.",
                "required": True,
            }
        },
    },
    "get_patient_prescriptions": {
        "fn": get_patient_prescriptions,
        "description": "Retrieve all prescriptions for a given patient including diagnosis and medicines.",
        "parameters": {
            "patient_id": {
                "type": "string",
                "description": "UUID of the patient.",
                "required": True,
            }
        },
    },
    "get_dashboard_summary": {
        "fn": get_dashboard_summary,
        "description": "Retrieve high-level dashboard summary — patient count, active alerts, prescriptions, and village health score.",
        "parameters": {},
    },
    "get_recent_alerts": {
        "fn": get_recent_alerts,
        "description": "Retrieve the 20 most recent unresolved risk alerts across all patients.",
        "parameters": {},
    },
}


# ---------------------------------------------------------------------------
# MCP Server facade
# ---------------------------------------------------------------------------

class MCPServer:
    """Lightweight MCP server that wraps the tool registry."""

    name: str = "aarogya-health"

    def __init__(self) -> None:
        logger.info(f"MCP Server '{self.name}' initialized with {len(_TOOL_REGISTRY)} tools.")

    # noinspection PyMethodMayBeStatic
    def list_tools(self) -> List[Dict[str, Any]]:
        """Return metadata for every registered tool."""
        tools = []
        for name, meta in _TOOL_REGISTRY.items():
            tools.append({
                "name": name,
                "description": meta["description"],
                "parameters": meta["parameters"],
            })
        return tools

    # noinspection PyMethodMayBeStatic
    def call_tool(self, tool_name: str, args: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Invoke a tool by name with keyword arguments."""
        if tool_name not in _TOOL_REGISTRY:
            return {"error": f"Unknown MCP tool: '{tool_name}'"}

        fn = _TOOL_REGISTRY[tool_name]["fn"]
        try:
            result = fn(**(args or {}))
            return result
        except Exception as exc:
            logger.error(f"MCP tool '{tool_name}' failed: {exc}")
            return {"error": f"Tool execution failed: {str(exc)}"}


# Module-level singleton
mcp_server = MCPServer()


# ---------------------------------------------------------------------------
# Convenience helpers (used by agent, bot, REST API)
# ---------------------------------------------------------------------------

def call_mcp_tool(tool_name: str, args: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Invoke an MCP tool by name. Thin wrapper around ``mcp_server.call_tool``."""
    return mcp_server.call_tool(tool_name, args)


def list_mcp_tools() -> List[Dict[str, Any]]:
    """Return the list of available MCP tools with descriptions and params."""
    return mcp_server.list_tools()


# ---------------------------------------------------------------------------
# Standalone stdio entry-point (for external MCP clients)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json, sys

    print(json.dumps({"server": mcp_server.name, "tools": list_mcp_tools()}), flush=True)

    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            tool_name = request.get("tool")
            tool_args = request.get("args", {})
            result = call_mcp_tool(tool_name, tool_args)
            print(json.dumps(result), flush=True)
        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)
