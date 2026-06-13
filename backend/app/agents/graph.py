import json
import logging
import os
import uuid
import re
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.services.ocr import ocr_service
from app.services.translation import translation_service
from app.services.voice import voice_service
from app.services.gemini import gemini_service
from app.core.database import SessionLocal
from app.models.logs import RiskAlert, SymptomLog, ChatHistory, ActivityLog
from app.models.medical import Prescription, LabReport, Reminder
from app.models.patient import Patient
from app.services.activity import create_activity_log
from app.services.doctor_assignment import assign_doctor_to_patient
from app.services.risk_score import calculate_predictive_risk_score
from app.mcp.server import call_mcp_tool
from datetime import datetime, timezone, time, timedelta

logger = logging.getLogger("aarogya.agents")

# Define uploads directory structure
PRESCRIPTION_DIR = "/workspace/uploads/prescriptions"
REPORT_DIR = "/workspace/uploads/reports"
os.makedirs(PRESCRIPTION_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# --- Agent Node Implementations ---

def classifier_node(state: AgentState) -> Dict[str, Any]:
    """Classifies inputs and prepares transcription/translation if input is voice."""
    logger.info(f"Classifier Node: Processing input type '{state['input_type']}'")
    updated = {}
    
    if state["input_type"] == "voice" and state["raw_input_bytes"]:
        # Transcribe audio to English
        transcript = voice_service.transcribe_voice(state["raw_input_bytes"])
        updated["raw_input_text"] = transcript
        # Determine if voice checkin or normal conversation
        if "checkin" in transcript.lower() or "symptom" in transcript.lower() or "fever" in transcript.lower():
            updated["input_type"] = "checkin"
        else:
            updated["input_type"] = "text"
            
    elif state["input_type"] == "text" and state["raw_input_text"]:
        # Translate query to English if local language
        eng_text = translation_service.translate_to_english(state["raw_input_text"], state["preferred_language"])
        updated["raw_input_text"] = eng_text
        
    return updated


def prescription_reader_node(state: AgentState) -> Dict[str, Any]:
    """Extracts structured medicine lists from prescription images."""
    logger.info("Prescription Reader Node: Extracting medications")
    
    db = SessionLocal()
    image_url = f"/uploads/prescriptions/{state['patient_id']}.jpg"
    progress_cb = state.get("progress_callback")
    
    # Save prescription image to local shared directory
    if state["raw_input_bytes"]:
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(PRESCRIPTION_DIR, filename)
        try:
            with open(filepath, "wb") as f:
                f.write(state["raw_input_bytes"])
            image_url = f"/uploads/prescriptions/{filename}"
            logger.info(f"PRESCRIPTION IMAGE SAVED to {filepath}")
            if progress_cb:
                try:
                    progress_cb(10)
                except Exception as p_err:
                    logger.error(f"Error calling progress callback (10%): {p_err}")
        except Exception as file_err:
            logger.error(f"Failed to save prescription file: {str(file_err)}")

    extracted = None
    ai_failed = False
    try:
        if not state["raw_input_bytes"]:
            raise ValueError("No input image bytes provided")
        extracted = ocr_service.ocr_prescription(state["raw_input_bytes"])
        if not extracted or (not extracted.get("medicines") and not extracted.get("diagnosis")):
            ai_failed = True
        else:
            if progress_cb:
                try:
                    progress_cb(30)
                except Exception as p_err:
                    logger.error(f"Error calling progress callback (30%): {p_err}")
    except Exception as gem_err:
        logger.error(f"GEMINI FAILURE: Prescription OCR extraction failed: {str(gem_err)}")
        ai_failed = True

    if ai_failed:
        extracted = {"issue_date": None, "diagnosis": "Analysis Unavailable", "medicines": []}
        response_msg = "Prescription uploaded successfully. AI analysis is temporarily unavailable."
    else:
        # Deduplicate and normalize
        raw_meds = extracted.get("medicines", [])
        merged_meds = {}
        for med in raw_meds:
            name = med.get("name")
            if not name:
                continue
            normalized_name = name.strip().title()
            if normalized_name not in merged_meds:
                merged_meds[normalized_name] = {
                    "name": normalized_name,
                    "dosage": med.get("dosage", "As prescribed"),
                    "frequency": med.get("frequency", "once daily"),
                    "duration": med.get("duration", "30 days"),
                    "schedule_time": med.get("schedule_time", "08:00:00"),
                    "duration_days": med.get("duration_days", 30)
                }
            else:
                existing = merged_meds[normalized_name]
                if not existing["dosage"] or existing["dosage"] == "As prescribed":
                    existing["dosage"] = med.get("dosage")
                if not existing["frequency"] or existing["frequency"] == "once daily":
                    existing["frequency"] = med.get("frequency")
                    existing["schedule_time"] = med.get("schedule_time", "08:00:00")
                if not existing["duration"] or existing["duration"] == "30 days":
                    existing["duration"] = med.get("duration")
        
        extracted["medicines"] = list(merged_meds.values())
        if progress_cb:
            try:
                progress_cb(60)
            except Exception as p_err:
                logger.error(f"Error calling progress callback (60%): {p_err}")
        meds_summary = "\n".join([f"- {m.get('name')} ({m.get('dosage')} - {m.get('frequency')})" for m in extracted.get("medicines")])
        response_msg = f"I have read your prescription and scheduled reminders for:\n{meds_summary}"

    # Save to database
    db_rx = None
    prescription_id = None
    try:
        db_rx = Prescription(
            patient_id=state["patient_id"],
            raw_image_url=image_url,
            raw_ocr_text=json.dumps(extracted),
            structured_data=extracted.get("medicines", []),
            issue_date=datetime.now(timezone.utc).date(),
            telegram_id=state.get("telegram_id"),
            diagnosis=extracted.get("diagnosis", "Unknown Diagnosis")
        )
        db.add(db_rx)
        db.commit()
        db.refresh(db_rx)
        prescription_id = db_rx.id
        logger.info(f"PRESCRIPTION SAVED (id={prescription_id})")

        # Log Activity
        patient = db.query(Patient).filter(Patient.id == state["patient_id"]).first()
        patient_name = patient.full_name if patient else "Patient"
        act_msg = f"🩺 {patient_name} uploaded prescription" + (" (AI analysis unavailable)" if ai_failed else "")
        create_activity_log(db, state["patient_id"], "PRESCRIPTION_UPLOADED", act_msg)

        # Spawn active reminders if AI succeeded
        if not ai_failed:
            for med in extracted.get("medicines", []):
                try:
                    t_str = med.get("schedule_time", "08:00:00")
                    h, m, s = map(int, t_str.split(":"))
                    rem_time = time(h, m, s)
                except Exception:
                    rem_time = time(8, 0, 0)
                    
                db_rem = Reminder(
                    patient_id=state["patient_id"],
                    prescription_id=prescription_id,
                    medicine_name=med.get("name", "Unknown Medicine"),
                    dosage=med.get("dosage", "1 tablet"),
                    schedule_time=rem_time,
                    frequency=med.get("frequency", "daily"),
                    is_active=True,
                    end_date=datetime.now(timezone.utc).date() + timedelta(days=med.get("duration_days", 30))
                )
                db.add(db_rem)
                logger.info("REMINDER GENERATED")
            db.commit()
            if progress_cb:
                try:
                    progress_cb(85)
                except Exception as p_err:
                    logger.error(f"Error calling progress callback (85%): {p_err}")
    except Exception as e:
        logger.error(f"Error saving prescription/reminders: {str(e)}")
        db.rollback()
    finally:
        db.close()
        
    return {
        "extracted_data": {
            "prescription_id": str(prescription_id) if prescription_id else None,
            "medicines": extracted.get("medicines", []),
            "diagnosis": extracted.get("diagnosis"),
            "metrics": {}
        },
        "response_english": response_msg
    }


def report_explainer_node(state: AgentState) -> Dict[str, Any]:
    """Extracts lab values and writes simplified medical guides."""
    logger.info("Report Explainer Node: Extracting biomarkers")
    
    db = SessionLocal()
    file_url = f"/uploads/reports/{state['patient_id']}.jpg"
    
    # Save report image to local shared directory
    if state["raw_input_bytes"]:
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(REPORT_DIR, filename)
        try:
            with open(filepath, "wb") as f:
                f.write(state["raw_input_bytes"])
            file_url = f"/uploads/reports/{filename}"
            logger.info(f"LAB REPORT IMAGE SAVED to {filepath}")
        except Exception as file_err:
            logger.error(f"Failed to save report file: {str(file_err)}")

    extracted = None
    ai_failed = False
    try:
        if not state["raw_input_bytes"]:
            raise ValueError("No input image bytes provided")
        extracted = ocr_service.ocr_lab_report(state["raw_input_bytes"])
        if not extracted or (not extracted.get("metrics") and not extracted.get("summary")):
            ai_failed = True
    except Exception as gem_err:
        logger.error(f"GEMINI FAILURE: Lab report OCR failed: {str(gem_err)}")
        ai_failed = True

    if ai_failed:
        extracted = {"report_type": "Lab Report", "metrics": {}, "summary": "Analysis Unavailable"}
        ai_explanation = "Lab report uploaded successfully. Detailed AI explanation is temporarily unavailable."
        response_msg = "Lab report uploaded successfully. Detailed AI explanation is temporarily unavailable."
    else:
        # Generate dynamic AI explanation
        try:
            prompt = f"""
            You are a patient-friendly healthcare AI.
            Explain these lab report results in simple, easy-to-understand terms for a rural patient:
            {json.dumps(extracted.get("metrics"))}
            
            Provide:
            1. What the parameters mean.
            2. Any abnormal values and what they imply.
            3. Simple, practical lifestyle recommendations.
            Keep the tone reassuring and encouraging.
            """
            ai_explanation = gemini_service.generate_content(prompt)
        except Exception as gem_err2:
            logger.error(f"GEMINI FAILURE: Lab explanation generation failed: {str(gem_err2)}")
            ai_explanation = extracted.get("summary", "Analysis completed but explanation is unavailable.")
        
        metrics_str = ", ".join([f"{k}: {v.get('value')} {v.get('unit')}" for k, v in extracted.get("metrics", {}).items()])
        response_msg = f"Your lab report contains:\n{metrics_str}\n\nAI Explanation:\n{ai_explanation}"

    # Save to database
    try:
        db_rep = LabReport(
            patient_id=state["patient_id"],
            file_url=file_url,
            report_type=extracted.get("report_type", "Blood Test"),
            raw_ocr_text=json.dumps(extracted),
            extracted_metrics=extracted.get("metrics", {}),
            ai_explanation=ai_explanation,
            summary_local_lang=""
        )
        db.add(db_rep)
        db.commit()
        logger.info("LAB REPORT SAVED")

        # Log Activity
        patient = db.query(Patient).filter(Patient.id == state["patient_id"]).first()
        patient_name = patient.full_name if patient else "Patient"
        act_msg = f"🩸 {patient_name} uploaded lab report" + (" (AI analysis unavailable)" if ai_failed else "")
        create_activity_log(db, state["patient_id"], "LAB_REPORT_UPLOADED", act_msg)
    except Exception as e:
        logger.error(f"Error saving lab report: {str(e)}")
        db.rollback()
    finally:
        db.close()
        
    return {
        "extracted_data": extracted,
        "response_english": response_msg
    }


def symptom_monitor_node(state: AgentState) -> Dict[str, Any]:
    """Evaluates symptom entries and scores clinical severity."""
    logger.info("Symptom Monitor Node: Analyzing symptom profile")
    input_text = state["raw_input_text"] or ""
    
    prompt = f"""
    Analyze these symptoms reported by a patient: "{input_text}"
    Assess clinical severity and suggest specific recommendations.
    Return your analysis STRICTLY in JSON format matching the schema below.
    Do not add any markdown formatting, comments, or explanations outside the JSON block.

    Expected JSON format:
    {{
      "severity": "Low" | "Medium" | "High",
      "severity_score": 5, // 1-10 integer representation (Low: 1-4, Medium: 5-7, High: 8-10)
      "symptoms": "Fever, Cough, etc. (normalized list of symptoms as a comma-separated string)",
      "recommendation": "• recommendation 1\\n• recommendation 2\\n• recommendation 3",
      "answers": {{
         "fever": "yes", // map symptoms found
         "shortness_of_breath": "yes"
      }}
    }}
    """
    severity = "Low"
    severity_score = 0
    symptoms_str = input_text
    recommendation = "• Drink plenty of fluids.\n• Monitor your symptoms closely.\n• Seek medical attention if symptoms worsen."
    symptom_answers = {}
    ai_failed = False
    
    try:
        res = gemini_service.generate_content(prompt)
        clean = res.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        severity = data.get("severity", "Low")
        severity_score = data.get("severity_score", 0)
        symptoms_str = data.get("symptoms", input_text)
        recommendation = data.get("recommendation", recommendation)
        symptom_answers = data.get("answers", {})
    except Exception as e:
        logger.error(f"GEMINI FAILURE: Symptom scoring failed: {str(e)}")
        ai_failed = True

    # Save to DB
    db = SessionLocal()
    try:
        db_sym = SymptomLog(
            patient_id=state["patient_id"],
            answers=symptom_answers,
            transcript=input_text,
            severity_score=severity_score,
            symptoms=symptoms_str,
            severity=severity,
            recommendation=recommendation
        )
        db.add(db_sym)
        db.commit()
        logger.info("SYMPTOM LOG SAVED")

        # Log Activity
        patient = db.query(Patient).filter(Patient.id == state["patient_id"]).first()
        patient_name = patient.full_name if patient else "Patient"
        if severity in ["Medium", "High"]:
            act_msg = f"⚠️ {patient_name} reported {symptoms_str or 'symptoms'} (Severity: {severity})"
        else:
            act_msg = f"✅ {patient_name} completed daily check-in"
        create_activity_log(db, state["patient_id"], "CHECKIN_SUBMITTED", act_msg)
    except Exception as e:
        logger.error(f"Error saving symptom log: {str(e)}")
        db.rollback()
    finally:
        db.close()

    response_msg = f"Logged your symptom updates.\n\nSeverity: {severity}\n\nRecommendations:\n{recommendation}"
    return {
        "symptom_answers": symptom_answers,
        "extracted_data": {"severity_score": severity_score, "severity": severity, "symptoms": symptoms_str},
        "response_english": response_msg
    }


def mcp_router_node(state: AgentState) -> Dict[str, Any]:
    """Detects MCP-eligible queries and injects structured tool results into state."""
    logger.info("MCP Router Node: Checking for MCP-eligible intent")
    raw_text = (state.get("raw_input_text") or "").lower().strip()

    if not raw_text:
        return {}

    import re
    uuid_pattern = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
    found_ids = re.findall(uuid_pattern, state.get("raw_input_text") or "")
    patient_id = found_ids[0] if found_ids else None

    mcp_result = None
    tool_used = None

    # Intent matching — ordered by specificity
    if patient_id and any(kw in raw_text for kw in ["prescription", "medicine", "medication", "rx"]):
        mcp_result = call_mcp_tool("get_patient_prescriptions", {"patient_id": patient_id})
        tool_used = "get_patient_prescriptions"
    elif patient_id and any(kw in raw_text for kw in ["risk", "score", "danger", "severity"]):
        mcp_result = call_mcp_tool("get_patient_risk", {"patient_id": patient_id})
        tool_used = "get_patient_risk"
    elif patient_id and any(kw in raw_text for kw in ["patient", "lookup", "search", "find", "details", "info", "show"]):
        mcp_result = call_mcp_tool("search_patient", {"patient_id": patient_id})
        tool_used = "search_patient"
    elif any(kw in raw_text for kw in ["alert", "warning", "danger"]):
        mcp_result = call_mcp_tool("get_recent_alerts")
        tool_used = "get_recent_alerts"
    elif any(kw in raw_text for kw in ["summary", "dashboard", "overview", "stats", "statistics"]):
        mcp_result = call_mcp_tool("get_dashboard_summary")
        tool_used = "get_dashboard_summary"

    if mcp_result and "error" not in mcp_result:
        logger.info(f"MCP Router: Tool '{tool_used}' matched, injecting context")
        return {
            "mcp_context": {
                "tool": tool_used,
                "result": mcp_result,
            }
        }

    return {}


def chat_flow_node(state: AgentState) -> Dict[str, Any]:
    """Normal clinical chat node reasoning about medical history."""
    logger.info("Chat Flow Node: Formulating conversational advice")
    db = SessionLocal()
    history_context = ""
    try:
        # Load last 5 messages for context
        chats = db.query(ChatHistory).filter(ChatHistory.patient_id == state["patient_id"]).order_by(ChatHistory.created_at.desc()).limit(5).all()
        history_context = "\n".join([f"{c.sender}: {c.message}" for c in reversed(chats)])
    except Exception:
        pass
    finally:
        db.close()

    # Build MCP context section if available
    mcp_section = ""
    mcp_ctx = state.get("mcp_context")
    if mcp_ctx and isinstance(mcp_ctx, dict):
        import json
        mcp_section = f"""
    MCP Tool Data (from {mcp_ctx.get('tool', 'unknown tool')}):
    {json.dumps(mcp_ctx.get('result', {}), indent=2, default=str)}

    Use this data to provide a precise, data-driven answer.
    """

    prompt = f"""
    You are AAROGYA, a knowledgeable, friendly rural doctor agent.
    Provide empathetic medical information based on this query: "{state['raw_input_text']}"
    
    Context:
    Last messages:
    {history_context}
    {mcp_section}
    Guideline: Keep language extremely clear, free of complex jargon, and encouraging. Never perform definitive medical diagnoses. Suggest consulting their assigned doctor if needed.
    """
    response_msg = gemini_service.generate_content(prompt)
    return {"response_english": response_msg}


def risk_detector_node(state: AgentState) -> Dict[str, Any]:
    """Safety firewall node checks parameters, raises DB alerts and triggers SMS notifications."""
    logger.info("Risk Detector Node: Assessing critical thresholds")
    risk_level = "low"
    risk_msg = ""
    
    # DB connection for historical check
    db = SessionLocal()
    try:
        raw_text = (state.get("raw_input_text") or "").lower()
        patient_id = state["patient_id"]
        
        alerts_to_create = []
        
        # Rule 1: Fever Alert
        fever_duration_match = re.search(r'fever\s+(?:for|lasting)?\s*(\d+)\s*days?', raw_text)
        fever_days = 0
        if fever_duration_match:
            fever_days = int(fever_duration_match.group(1))
            
        five_days_ago = datetime.now(timezone.utc) - timedelta(days=5)
        fever_logs = db.query(SymptomLog).filter(
            SymptomLog.patient_id == patient_id,
            SymptomLog.created_at >= five_days_ago
        ).all()
        
        fever_count = sum(1 for l in fever_logs if "fever" in (l.symptoms or "").lower() or (l.answers and l.answers.get("fever") == "yes"))
        if fever_days > 5 or fever_count >= 2:
            alerts_to_create.append({
                "severity": "High",
                "reason": "Persistent fever for more than 5 days",
                "message": f"Persistent fever for more than 5 days ({fever_days if fever_days > 0 else 'repeated'} days logged)",
                "recommendation": "Schedule clinical checkup, keep hydrated, monitor temperature hourly, and administer prescribed antipyretics."
            })
            risk_level = "high"
            
        # Rule 2: High Blood Sugar Alert
        sugar_triggered = False
        metrics = state.get("extracted_data", {}).get("metrics", {})
        for metric_name, details in metrics.items():
            if isinstance(details, dict):
                val = details.get("value")
                if val is not None:
                    try:
                        val_f = float(val)
                        if "sugar" in metric_name.lower() or "glucose" in metric_name.lower():
                            if val_f > 250:
                                sugar_triggered = True
                    except ValueError:
                        pass
                        
        sugar_match = re.search(r'(?:sugar|glucose|sugars)\s+(?:is|of)?\s*(\d+(?:\.\d+)?)', raw_text)
        if sugar_match:
            try:
                sugar_val = float(sugar_match.group(1))
                if sugar_val > 250:
                    sugar_triggered = True
            except ValueError:
                pass
                
        if sugar_triggered:
            alerts_to_create.append({
                "severity": "High",
                "reason": "Dangerously elevated blood sugar",
                "message": "Dangerously elevated blood sugar (>250)",
                "recommendation": "Consult doctor immediately, limit sugar/carbs, check hydration level, and verify insulin dose."
            })
            risk_level = "high"
            
        # Rule 3: High Blood Pressure Alert
        bp_triggered = False
        bp_match = re.search(r'bp\s+(?:is|of)?\s*(\d{2,3})', raw_text)
        if bp_match:
            try:
                bp_val = int(bp_match.group(1))
                if bp_val > 180:
                    bp_triggered = True
            except ValueError:
                pass
                
        for metric_name, details in metrics.items():
            if isinstance(details, dict) and ("bp" in metric_name.lower() or "blood pressure" in metric_name.lower() or "systolic" in metric_name.lower()):
                val = details.get("value")
                if val:
                    try:
                        if "/" in str(val):
                            systolic = int(str(val).split("/")[0])
                        else:
                            systolic = int(float(val))
                        if systolic > 180:
                            bp_triggered = True
                    except Exception:
                        pass
                        
        if bp_triggered:
            alerts_to_create.append({
                "severity": "High",
                "reason": "Dangerously elevated blood pressure",
                "message": "Dangerously elevated blood pressure (Systolic BP >180)",
                "recommendation": "Rest in a quiet place, recheck BP in 5 minutes, seek immediate medical attention, and take prescribed BP medication."
            })
            risk_level = "high"
            
        # Rule 4: Repeated Severe Symptoms
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        severe_logs = db.query(SymptomLog).filter(
            SymptomLog.patient_id == patient_id,
            SymptomLog.created_at >= seven_days_ago,
            SymptomLog.severity.in_(["Medium", "High"])
        ).all()
        curr_severity = state.get("extracted_data", {}).get("severity", "Low")
        
        # Occurs at least 2 times in the previous 7 days (including current check-in if type is checkin)
        severe_count = len(severe_logs)
        if (severe_count >= 2) or (state.get("input_type") == "checkin" and curr_severity in ["Medium", "High"] and severe_count >= 1):
            alerts_to_create.append({
                "severity": "High",
                "reason": "Repeated severe symptom reports",
                "message": "Repeated severe symptom reports (Medium/High severity in last 7 days)",
                "recommendation": "Arrange home visit by assigned healthcare worker (HCW) within 24 hours."
            })
            risk_level = "high"
            
        # Rule 5: Abnormal Biomarker Alerts
        biomarker_triggered = False
        for metric_name, details in metrics.items():
            if isinstance(details, dict) and details.get("status") in ["high", "low"]:
                biomarker_triggered = True
                
        if biomarker_triggered:
            alerts_to_create.append({
                "severity": "High",
                "reason": "Critical abnormal lab values detected",
                "message": "Critical abnormal lab values detected in lab diagnostics report",
                "recommendation": "Review abnormal metrics with doctor during next follow-up for medication/lifestyle adjustments."
            })
            risk_level = "high"
            
        # Fallback / General Severity Check
        severity_score = state.get("extracted_data", {}).get("severity_score", 0)
        if severity_score >= 8:
            risk_level = "critical"
            if not alerts_to_create:
                alerts_to_create.append({
                    "severity": "High",
                    "reason": f"Critical symptoms reported: score {severity_score}/10",
                    "message": f"Critical symptoms reported: severity score {severity_score}/10",
                    "recommendation": "Urgent physician consultation and close observation required."
                })
        elif severity_score >= 5 and risk_level == "low":
            risk_level = "high"
            if not alerts_to_create:
                alerts_to_create.append({
                    "severity": "High",
                    "reason": f"High-concern symptoms reported: score {severity_score}/10",
                    "message": f"High-concern symptoms reported: severity score {severity_score}/10",
                    "recommendation": "Consult the healthcare worker or doctor for symptom evaluation."
                })
                
        # Raise Alerts & write to Activity Log
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        patient_name = patient.full_name if patient else "Patient"
        
        for alert_data in alerts_to_create:
            db_alert = RiskAlert(
                patient_id=patient_id,
                risk_level=risk_level,
                severity=alert_data["severity"],
                reason=alert_data["reason"],
                source="ai_orchestrator",
                alert_message=alert_data["message"],
                recommendation=alert_data.get("recommendation"),
                status="raised"
            )
            db.add(db_alert)
            db.commit()
            logger.info(f"RISK ALERT CREATED: {alert_data['reason']}")
            
            # Log Activity
            act_msg = f"⚠️ High-risk alert generated ({alert_data['reason']}) for {patient_name}"
            create_activity_log(db, patient_id, "RISK_ALERT_CREATED", act_msg)
            
        if patient:
            calculate_predictive_risk_score(db, patient)
            
        if alerts_to_create:
            risk_msg = " & ".join([a["reason"] for a in alerts_to_create])
            
    except Exception as e:
        logger.error(f"Error checking risks: {str(e)}")
        db.rollback()
    finally:
        db.close()
        
    return {
        "risk_level": risk_level,
        "risk_message": risk_msg if 'risk_msg' in locals() and risk_msg else None
    }


def responder_node(state: AgentState) -> Dict[str, Any]:
    """Translates response into patient's local dialect and handles TTS audio outputs."""
    logger.info("Responder Node: Finalizing translation and voice logs")
    local_lang = state["preferred_language"]
    
    # Add risk alerts warning to patient's message if critical
    resp_eng = state["response_english"]
    if state["risk_level"] in ["high", "critical"] and state.get("risk_message"):
        resp_eng += "\n\n⚠️ IMPORTANT: I have detected some concerning health indicators. I have immediately alerted your assigned health worker to visit you. Please stay calm."

    # Translate
    translated = translation_service.translate_from_english(resp_eng, local_lang)
    
    # Save conversation log
    db = SessionLocal()
    try:
        # Save user message
        if state["raw_input_text"]:
            db.add(ChatHistory(
                patient_id=state["patient_id"],
                sender="patient",
                message=state["raw_input_text"],
                local_language=local_lang
            ))
        # Save bot response
        db.add(ChatHistory(
            patient_id=state["patient_id"],
            sender="bot",
            message=resp_eng,
            local_language=local_lang
        ))
        db.commit()
    except Exception as e:
        logger.error(f"Error writing chat histories: {str(e)}")
        db.rollback()
    finally:
        db.close()

    # Generate speech synthesis bytes if input type was voice
    audio_bytes = None
    if state["input_type"] == "voice" or (state["raw_input_bytes"] is not None and state["input_type"] == "checkin"):
        audio_bytes = voice_service.synthesize_speech(translated, local_lang)

    return {
        "response_translated": translated,
        "response_audio_bytes": audio_bytes
    }


# --- LangGraph Setup & Router ---

def route_input(state: AgentState) -> str:
    """Routes state processing based on input classifications."""
    inp = state["input_type"]
    if inp == "prescription":
        return "prescription_reader"
    elif inp == "report":
        return "report_explainer"
    elif inp == "checkin":
        return "symptom_monitor"
    else:
        return "chat_flow"

# Create StateGraph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("classifier", classifier_node)
workflow.add_node("mcp_router", mcp_router_node)
workflow.add_node("prescription_reader", prescription_reader_node)
workflow.add_node("report_explainer", report_explainer_node)
workflow.add_node("symptom_monitor", symptom_monitor_node)
workflow.add_node("chat_flow", chat_flow_node)
workflow.add_node("risk_detector", risk_detector_node)
workflow.add_node("responder", responder_node)

# Set Entry Point
workflow.set_entry_point("classifier")

# Classifier → MCP Router (always runs first to check for MCP-eligible queries)
workflow.add_edge("classifier", "mcp_router")

# MCP Router → conditional routing based on original input type
workflow.add_conditional_edges(
    "mcp_router",
    route_input,
    {
        "prescription_reader": "prescription_reader",
        "report_explainer": "report_explainer",
        "symptom_monitor": "symptom_monitor",
        "chat_flow": "chat_flow"
    }
)

# Route medical analysis through risk detector
workflow.add_edge("prescription_reader", "risk_detector")
workflow.add_edge("report_explainer", "risk_detector")
workflow.add_edge("symptom_monitor", "risk_detector")
workflow.add_edge("chat_flow", "risk_detector")

# Finalize response logic
workflow.add_edge("risk_detector", "responder")
workflow.add_edge("responder", END)

# Compile Agent Orchestrator Graph
compiled_aarogya_agent = workflow.compile()
