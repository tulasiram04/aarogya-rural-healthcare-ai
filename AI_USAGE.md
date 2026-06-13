# AI Usage

## Models Used
- Gemini 2.5 Flash
- LangGraph

## AI Components
1. **Prescription OCR Extraction**: High-precision recognition of handwritten and structured prescriptions, digitizing medical details automatically.
2. **Medicine Recognition**: Mapping extracted components to structured database representations.
3. **Reminder Generation**: Extracting dosage instructions and timing intervals from text to build scheduling models.
4. **Risk Assessment**: Evaluating patient metrics and historical observations against a health risk matrix to flag anomalies.
5. **Lab Report Explanation**: Breaking down complex biomarker readings into readable summaries.
6. **MCP Tool Integration**: Translating conversational user intent into REST API structures using Model Context Protocol schemas.

## Human Oversight
All AI outputs are advisory and should be reviewed by healthcare professionals. They are meant to complement clinic checkups, not replace clinical decision-making.

## MCP Usage
AAROGYA uses Model Context Protocol (MCP) tools for:
- Patient lookup (`search_patient`)
- Risk assessment (`get_patient_risk`)
- Prescription retrieval (`get_patient_prescriptions`)
- Dashboard analytics (`get_dashboard_summary`, `get_recent_alerts`)
