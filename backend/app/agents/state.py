import uuid
from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    """
    Standard state tracking object passed between clinical agents in the LangGraph runtime.
    Contains both transient execution variables and persistent metadata.
    """
    patient_id: uuid.UUID
    telegram_id: Optional[int]
    input_type: str  # "text" | "voice" | "prescription" | "report" | "checkin"
    raw_input_bytes: Optional[bytes]
    raw_input_text: Optional[str]
    preferred_language: str
    
    # AI Extractions
    extracted_data: Dict[str, Any]  # Holds parsed medicines or lab metrics
    symptom_answers: Dict[str, Any] # Holds daily question checklist answers
    
    # MCP Context (injected by mcp_router_node)
    mcp_context: Optional[Dict[str, Any]]

    # Clinical Security & Escalation
    risk_level: str  # "low" | "medium" | "high" | "critical"
    risk_message: Optional[str]
    
    # Conversational Responses
    chat_history: List[Dict[str, str]]
    response_english: str
    response_translated: str
    response_audio_bytes: Optional[bytes]
