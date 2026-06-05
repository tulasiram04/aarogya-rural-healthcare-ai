"""
AAROGYA Demo Data Seeder
========================
Populates the database with realistic demo data for dashboard demonstration.
Clears existing records and seeds a comprehensive clinical dataset.
Run: python seed_demo_data.py
"""

import sys
import os
import uuid
import random
from datetime import datetime, timezone, timedelta, date, time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.patient import Patient
from app.models.medical import Prescription, Reminder, ComplianceLog, LabReport
from app.models.logs import RiskAlert, SymptomLog, ChatHistory, ActivityLog
from app.services.risk_score import calculate_predictive_risk_score
from app.services.activity import create_activity_log
from app.services.demo_data import delete_demo_records

def clear_demo_data(db):
    print("Removing old demo records (preserving real patient data)...")
    counts = delete_demo_records(db)
    print(f"  ✓ Demo cleanup complete: {counts}")

def seed():
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("  AAROGYA Hackathon Demo Seeder")
        print("=" * 60)
        
        # 0. Clear old data
        clear_demo_data(db)

        # ============================================================
        # 1. Create/Verify Medical Staff Users
        # ============================================================
        print("\n[1/7] Verification of medical staff users...")
        
        doctor = db.query(User).filter(User.phone == "9876543210").first()
        if not doctor:
            doctor = User(
                phone="9876543210",
                role="doctor",
                full_name="Dr. Dinesh Kumar",
                email="dinesh.kumar@aarogya.health",
                hashed_password=get_password_hash("doctor123"),
                is_active=True,
            )
            db.add(doctor)
            db.flush()
            print("  ✓ Created Doctor: Dr. Dinesh Kumar (9876543210)")
        else:
            doctor.hashed_password = get_password_hash("doctor123")
            db.add(doctor)
            db.flush()
            print(f"  ✓ Doctor verified: {doctor.full_name}")

        hcw = db.query(User).filter(User.phone == "9876543211").first()
        if not hcw:
            hcw = User(
                phone="9876543211",
                role="hcw",
                full_name="Kamla Devi",
                email="kamla.devi@aarogya.health",
                hashed_password=get_password_hash("hcw123"),
                is_active=True,
            )
            db.add(hcw)
            db.flush()
            print("  ✓ Created HCW: Kamla Devi (9876543211)")
        else:
            hcw.hashed_password = get_password_hash("hcw123")
            db.add(hcw)
            db.flush()
            print(f"  ✓ HCW verified: {hcw.full_name}")

        admin = db.query(User).filter(User.phone == "9876543200").first()
        if not admin:
            admin = User(
                phone="9876543200",
                role="admin",
                full_name="System Admin",
                email="admin@aarogya.health",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
            )
            db.add(admin)
            db.flush()
            print("  ✓ Created Admin: System Admin (9876543200)")
        else:
            admin.hashed_password = get_password_hash("admin123")
            db.add(admin)
            db.flush()
            
        db.commit()
        
        # ============================================================
        # 2. Create Patients
        # ============================================================
        print("\n[2/7] Creating 10 patient records...")
        
        patient_data = [
            {"full_name": "Ramesh Yadav", "age": 55, "gender": "Male", "village": "Hasanpur", "phone": "8001001001",
             "preferred_language": "hindi", "telegram_id": 100001, "sub_center": "Palwal PHC",
             "medical_history": {"diabetes_type_2": True, "hypertension": True, "bmi": 28.5}},
            {"full_name": "Sunita Devi", "age": 42, "gender": "Female", "village": "Hasanpur", "phone": "8001001002",
             "preferred_language": "hindi", "telegram_id": 100002, "sub_center": "Palwal PHC",
             "medical_history": {"anemia": True, "thyroid": "hypothyroid"}},
            {"full_name": "Lakshmi Narayan", "age": 67, "gender": "Male", "village": "Bhondsi", "phone": "8001001003",
             "preferred_language": "hindi", "telegram_id": 100003, "sub_center": "Sohna CHC",
             "medical_history": {"diabetes_type_2": True, "chronic_kidney_disease": "Stage 2", "bp_medication": True}},
            {"full_name": "Priya Sharma", "age": 28, "gender": "Female", "village": "Bhondsi", "phone": "8001001004",
             "preferred_language": "hindi", "telegram_id": 100004, "sub_center": "Sohna CHC",
             "medical_history": {"gestational_diabetes": True, "iron_deficiency": True}},
            {"full_name": "Mohan Das", "age": 60, "gender": "Male", "village": "Manesar", "phone": "8001001005",
             "preferred_language": "hindi", "telegram_id": 100005, "sub_center": "Manesar PHC",
             "medical_history": {"copd": True, "smoking_history": "30 pack years", "hypertension": True}},
            {"full_name": "Anita Kumari", "age": 35, "gender": "Female", "village": "Hasanpur", "phone": "8001001006",
             "preferred_language": "hindi", "telegram_id": 100006, "sub_center": "Palwal PHC",
             "medical_history": {"asthma": True, "vitamin_d_deficiency": True}},
            {"full_name": "Raju Meena", "age": 48, "gender": "Male", "village": "Manesar", "phone": "8001001007",
             "preferred_language": "hindi", "telegram_id": 100007, "sub_center": "Manesar PHC",
             "medical_history": {"diabetes_type_2": True, "neuropathy": "mild", "fatty_liver": True}},
            {"full_name": "Kavitha Selvam", "age": 52, "gender": "Female", "village": "Bhondsi", "phone": "8001001008",
             "preferred_language": "tamil", "telegram_id": 100008, "sub_center": "Sohna CHC",
             "medical_history": {"rheumatoid_arthritis": True, "osteoporosis": "mild"}},
            {"full_name": "Sanjay Gupta", "age": 44, "gender": "Male", "village": "Hasanpur", "phone": "8001001009",
             "preferred_language": "hindi", "telegram_id": 100009, "sub_center": "Palwal PHC",
             "medical_history": {"hypertension": True, "obesity": True, "sleep_apnea": True}},
            {"full_name": "Meera Bai", "age": 70, "gender": "Female", "village": "Manesar", "phone": "8001001010",
             "preferred_language": "hindi", "telegram_id": 100010, "sub_center": "Manesar PHC",
             "medical_history": {"diabetes_type_2": True, "cataract": "bilateral", "heart_disease": "stable angina"}},
        ]

        patients = []
        for pd in patient_data:
            p = Patient(
                telegram_id=pd["telegram_id"],
                phone=pd["phone"],
                full_name=pd["full_name"],
                age=pd["age"],
                gender=pd["gender"],
                village=pd["village"],
                sub_center=pd["sub_center"],
                assigned_hcw_id=hcw.id,
                assigned_doctor_id=doctor.id,
                preferred_language=pd["preferred_language"],
                medical_history=pd["medical_history"],
                is_active=True,
                is_demo=True,
                created_at=datetime.now(timezone.utc) - timedelta(days=15)
            )
            db.add(p)
            db.flush()
            patients.append(p)
            
            # Log registration in ActivityLog
            create_activity_log(db, p.id, "PATIENT_REGISTERED", f"👤 {p.full_name} registered as a new patient", is_demo=True)
            print(f"  ✓ Seeded patient: {p.full_name} ({p.village})")
        
        db.commit()
        
        # ============================================================
        # 3. Create Prescriptions + Reminders
        # ============================================================
        print("\n[3/7] Seeding prescriptions and active reminders...")
        
        prescription_configs = [
            {"patient_idx": 0, "diagnosis": "Type 2 Diabetes Mellitus", "medicines": [
                {"name": "Metformin 500mg", "dosage": "1 tablet", "frequency": "twice daily", "time": time(8, 0), "time2": time(20, 0)},
                {"name": "Amlodipine 5mg", "dosage": "1 tablet", "frequency": "once daily", "time": time(8, 0)},
            ]},
            {"patient_idx": 2, "diagnosis": "Uncontrolled Diabetes & stage II CKD", "medicines": [
                {"name": "Insulin Glargine 10U", "dosage": "10 units SC", "frequency": "once daily", "time": time(22, 0)},
                {"name": "Losartan 50mg", "dosage": "1 tablet", "frequency": "once daily", "time": time(8, 0)},
                {"name": "Atorvastatin 20mg", "dosage": "1 tablet", "frequency": "once daily", "time": time(20, 0)},
            ]},
            {"patient_idx": 4, "diagnosis": "COPD & Mild Hypertension", "medicines": [
                {"name": "Tiotropium Inhaler", "dosage": "1 puff", "frequency": "once daily", "time": time(7, 0)},
                {"name": "Telmisartan 40mg", "dosage": "1 tablet", "frequency": "once daily", "time": time(8, 0)},
            ]},
            {"patient_idx": 6, "diagnosis": "Diabetes Mellitus with Diabetic Neuropathy", "medicines": [
                {"name": "Glimepiride 2mg", "dosage": "1 tablet", "frequency": "once daily", "time": time(7, 30)},
                {"name": "Pregabalin 75mg", "dosage": "1 capsule", "frequency": "twice daily", "time": time(8, 0), "time2": time(20, 0)},
            ]},
            {"patient_idx": 9, "diagnosis": "Ischemic Heart Disease & Hyperlipidemia", "medicines": [
                {"name": "Metformin 1000mg", "dosage": "1 tablet", "frequency": "twice daily", "time": time(8, 0), "time2": time(20, 0)},
                {"name": "Isosorbide Mononitrate 30mg", "dosage": "1 tablet", "frequency": "once daily", "time": time(8, 0)},
                {"name": "Aspirin 75mg", "dosage": "1 tablet", "frequency": "once daily", "time": time(13, 0)},
            ]},
        ]
        
        all_reminders = []
        for rx_cfg in prescription_configs:
            patient = patients[rx_cfg["patient_idx"]]
            meds = rx_cfg["medicines"]
            
            structured = [{"name": m["name"], "dosage": m["dosage"], "frequency": m["frequency"],
                           "schedule_time": m["time"].strftime("%H:%M:%S")} for m in meds]
            
            rx = Prescription(
                patient_id=patient.id,
                raw_image_url=f"/uploads/prescriptions/sample_{patient.id}.jpg",
                raw_ocr_text=str(structured),
                structured_data=structured,
                diagnosis=rx_cfg["diagnosis"],
                issue_date=date.today() - timedelta(days=7),
                is_demo=True,
                created_at=datetime.now(timezone.utc) - timedelta(days=7),
            )
            db.add(rx)
            db.flush()
            
            # Log Activity
            create_activity_log(db, patient.id, "PRESCRIPTION_UPLOADED", f"🩺 {patient.full_name} uploaded prescription (Diagnosis: {rx.diagnosis})", is_demo=True)

            for med in meds:
                rem = Reminder(
                    patient_id=patient.id,
                    prescription_id=rx.id,
                    medicine_name=med["name"],
                    dosage=med["dosage"],
                    schedule_time=med["time"],
                    frequency=med["frequency"],
                    is_active=True,
                    start_date=date.today() - timedelta(days=7),
                    end_date=date.today() + timedelta(days=23),
                )
                db.add(rem)
                db.flush()
                all_reminders.append(rem)
                
                if "time2" in med:
                    rem2 = Reminder(
                        patient_id=patient.id,
                        prescription_id=rx.id,
                        medicine_name=med["name"],
                        dosage=med["dosage"],
                        schedule_time=med["time2"],
                        frequency=med["frequency"],
                        is_active=True,
                        start_date=date.today() - timedelta(days=7),
                        end_date=date.today() + timedelta(days=23),
                    )
                    db.add(rem2)
                    db.flush()
                    all_reminders.append(rem2)
            
            print(f"  ✓ Prescription for {patient.full_name}: {len(meds)} medicines")
        
        db.commit()
        
        # ============================================================
        # 4. Create Compliance Logs
        # ============================================================
        print("\n[4/7] Generating 7-day adherence history logs...")
        
        random.seed(42)
        compliance_count = 0
        for rem in all_reminders:
            # Generate 7 days of compliance logs
            for day_offset in range(7):
                log_date = datetime.now(timezone.utc) - timedelta(days=day_offset)
                status = random.choices(["taken", "missed", "pending"], weights=[72, 18, 10])[0]
                
                log = ComplianceLog(
                    reminder_id=rem.id,
                    scheduled_time=log_date.replace(hour=rem.schedule_time.hour, minute=rem.schedule_time.minute),
                    taken_time=log_date if status == "taken" else None,
                    status=status,
                )
                db.add(log)
                compliance_count += 1
        
        db.commit()
        print(f"  ✓ Created {compliance_count} compliance adherence logs")
        
        # ============================================================
        # 5. Create Lab Reports
        # ============================================================
        print("\n[5/7] Seeding lab reports & biomarker structures...")
        
        lab_reports_data = [
            {"patient_idx": 0, "report_type": "Diabetic Panel", "metrics": {
                "HbA1c": {"value": 8.1, "unit": "%", "reference_range": "4.0 - 5.6", "status": "high"},
                "Fasting Blood Sugar": {"value": 152, "unit": "mg/dL", "reference_range": "70 - 100", "status": "high"},
                "Post Prandial Sugar": {"value": 220, "unit": "mg/dL", "reference_range": "< 140", "status": "high"},
                "Creatinine": {"value": 0.9, "unit": "mg/dL", "reference_range": "0.6 - 1.2", "status": "normal"},
            }, "summary": "Uncontrolled type 2 diabetes. HbA1c 8.1% indicates poor glycemic control over 3 months. Immediate medication review recommended."},
            {"patient_idx": 2, "report_type": "Renal Function Test", "metrics": {
                "Creatinine": {"value": 2.3, "unit": "mg/dL", "reference_range": "0.6 - 1.2", "status": "high"},
                "BUN": {"value": 38, "unit": "mg/dL", "reference_range": "7 - 20", "status": "high"},
                "eGFR": {"value": 42, "unit": "mL/min", "reference_range": "> 90", "status": "low"},
                "Potassium": {"value": 5.2, "unit": "mEq/L", "reference_range": "3.5 - 5.0", "status": "high"},
            }, "summary": "Declining kidney function (Stage 3A CKD). Creatinine elevated at 2.3, eGFR 42. Requires nephrology referral and dose adjustment of medications."},
            {"patient_idx": 1, "report_type": "Complete Blood Count", "metrics": {
                "Hemoglobin": {"value": 8.2, "unit": "g/dL", "reference_range": "12.0 - 16.0", "status": "low"},
                "MCV": {"value": 68, "unit": "fL", "reference_range": "80 - 100", "status": "low"},
                "Ferritin": {"value": 8, "unit": "ng/mL", "reference_range": "12 - 150", "status": "low"},
                "WBC": {"value": 7.2, "unit": "×10³/µL", "reference_range": "4.0 - 11.0", "status": "normal"},
            }, "summary": "Severe iron deficiency anemia. Hemoglobin critically low at 8.2 g/dL. Iron supplementation and dietary counseling urgently needed."},
            {"patient_idx": 4, "report_type": "Pulmonary Function", "metrics": {
                "FEV1": {"value": 58, "unit": "%", "reference_range": "> 80", "status": "low"},
                "FVC": {"value": 72, "unit": "%", "reference_range": "> 80", "status": "low"},
                "SpO2": {"value": 93, "unit": "%", "reference_range": "95 - 100", "status": "low"},
            }, "summary": "Moderate COPD confirmed. FEV1 at 58% of predicted. Oxygen saturation borderline. Continue inhaler therapy and consider pulmonary rehabilitation."},
            {"patient_idx": 9, "report_type": "Cardiac Profile", "metrics": {
                "Troponin I": {"value": 0.02, "unit": "ng/mL", "reference_range": "< 0.04", "status": "normal"},
                "BNP": {"value": 180, "unit": "pg/mL", "reference_range": "< 100", "status": "high"},
                "Total Cholesterol": {"value": 245, "unit": "mg/dL", "reference_range": "< 200", "status": "high"},
                "LDL": {"value": 165, "unit": "mg/dL", "reference_range": "< 100", "status": "high"},
            }, "summary": "Elevated cardiac markers. BNP suggests early heart failure. Cholesterol significantly elevated — statin therapy adjustment needed."},
        ]
        
        for lr_data in lab_reports_data:
            patient = patients[lr_data["patient_idx"]]
            lr = LabReport(
                patient_id=patient.id,
                file_url=f"/uploads/reports/sample_{patient.id}.jpg",
                report_type=lr_data["report_type"],
                raw_ocr_text=lr_data["summary"],
                extracted_metrics=lr_data["metrics"],
                ai_explanation=f"AI Interpretation Summary: {lr_data['summary']}",
                summary_local_lang="",
                is_demo=True,
                uploaded_at=datetime.now(timezone.utc) - timedelta(days=4)
            )
            db.add(lr)
            db.flush()
            
            # Log Activity
            create_activity_log(db, patient.id, "LAB_REPORT_UPLOADED", f"🩸 {patient.full_name} uploaded lab report ({lr.report_type})", is_demo=True)
            print(f"  ✓ Lab report for {patient.full_name}: {lr_data['report_type']}")
        
        db.commit()
        
        # ============================================================
        # 6. Create Symptom Logs
        # ============================================================
        print("\n[6/7] Seeding symptom log entries...")
        
        symptom_configs = [
            {"patient_idx": 0, "answers": {"fatigue": "yes", "excessive_thirst": "yes", "blurred_vision": "mild"}, "symptoms": "Fatigue, Excessive Thirst", "severity": "Medium", "score": 5},
            {"patient_idx": 2, "answers": {"swelling_feet": "yes", "reduced_urine": "yes", "nausea": "yes", "fatigue": "severe"}, "symptoms": "Swelling in feet, Reduced Urine, Fatigue", "severity": "High", "score": 8},
            {"patient_idx": 4, "answers": {"shortness_of_breath": "yes", "chronic_cough": "yes", "wheezing": "moderate"}, "symptoms": "Shortness of breath, Cough, Wheezing", "severity": "Medium", "score": 6},
            {"patient_idx": 1, "answers": {"weakness": "severe", "dizziness": "yes", "pale_skin": "yes"}, "symptoms": "Weakness, Dizziness, Pale skin", "severity": "Medium", "score": 7},
            {"patient_idx": 9, "answers": {"chest_pain": "mild", "fatigue": "yes", "shortness_of_breath": "on_exertion"}, "symptoms": "Mild Chest pain, Shortness of breath", "severity": "Medium", "score": 7},
            {"patient_idx": 6, "answers": {"tingling_feet": "yes", "burning_sensation": "yes", "numbness": "moderate"}, "symptoms": "Tingling and numbness in feet", "severity": "Low", "score": 4},
            {"patient_idx": 3, "answers": {"fatigue": "mild", "frequent_urination": "yes"}, "symptoms": "Fatigue, Frequent urination", "severity": "Low", "score": 3},
        ]
        
        for sc in symptom_configs:
            patient = patients[sc["patient_idx"]]
            sl = SymptomLog(
                patient_id=patient.id,
                answers=sc["answers"],
                transcript=f"Patient reports symptoms: {', '.join(sc['answers'].keys())}",
                severity_score=sc["score"],
                symptoms=sc["symptoms"],
                severity=sc["severity"],
                recommendation="• Drink plenty of fluids.\n• Monitor BP hourly.\n• Arrange HCW visit.",
                created_at=datetime.now(timezone.utc) - timedelta(days=2)
            )
            db.add(sl)
            db.flush()
            
            # Log Activity
            if sc["severity"] in ["Medium", "High"]:
                act_msg = f"⚠️ {patient.full_name} reported {sc['symptoms']} (Severity: {sc['severity']})"
            else:
                act_msg = f"✅ {patient.full_name} completed daily check-in"
            create_activity_log(db, patient.id, "CHECKIN_SUBMITTED", act_msg, is_demo=True)
            print(f"  ✓ Symptom log for {patient.full_name}: severity {sc['severity']} ({sc['score']}/10)")
        
        db.commit()
        
        # ============================================================
        # 7. Create Risk Alerts
        # ============================================================
        print("\n[7/7] Seeding active risk alerts...")
        
        alert_configs = [
            {"patient_idx": 2, "level": "critical", "source": "report_reader",
             "message": "Kidney dysfunction warning: Creatinine is 2.3 mg/dL. eGFR dropped to 42.",
             "reason": "Dangerously elevated creatinine levels (2.3 mg/dL) & low eGFR",
             "recommendation": "Arrange urgent nephrology consultation, suspend nephrotoxic medicines, review blood biochemistry."},
            {"patient_idx": 2, "level": "high", "source": "symptom_monitor",
             "message": "Patient reporting feet swelling, reduced urine volume, and severe fatigue.",
             "reason": "Clinical symptoms indicative of severe fluid retention and worsening renal output",
             "recommendation": "Schedule physical home assessment by Assigned HCW Kamla Devi, restrict sodium and fluids."},
            {"patient_idx": 1, "level": "high", "source": "report_reader",
             "message": "Severe anemia: Hemoglobin 8.2 g/dL. Ferritin depleted at 8 ng/mL.",
             "reason": "Dangerously low Hb levels (8.2 g/dL) indicating severe iron depletion",
             "recommendation": "Prescribe iron supplementation, run stool test for occult blood, recommend high-iron diet."},
            {"patient_idx": 9, "level": "critical", "source": "ai_orchestrator",
             "message": "Cardiac risk: BNP 180 pg/mL with exertional dyspnea & chest pain.",
             "reason": "Elevated BNP biomarker and symptomatic cardiac distress",
             "recommendation": "Refer to cardiologist, check medication adherence (Aspirin), administer sublingual nitrates if acute."},
            {"patient_idx": 0, "level": "high", "source": "compliance_tracker",
             "message": "Non-compliance: Metformin adherence rate is low. HbA1c elevated (8.1%).",
             "reason": "Poor medication adherence triggering elevated blood glycemic biomarkers",
             "recommendation": "Conduct home compliance check-in, inspect tablet count, provide digital medication reminder box."}
        ]
        
        for ac in alert_configs:
            patient = patients[ac["patient_idx"]]
            ra = RiskAlert(
                patient_id=patient.id,
                risk_level=ac["level"],
                source=ac["source"],
                alert_message=ac["message"],
                reason=ac["reason"],
                recommendation=ac["recommendation"],
                severity=ac["level"].capitalize(),
                status="raised",
                is_demo=True,
                created_at=datetime.now(timezone.utc) - timedelta(hours=12)
            )
            db.add(ra)
            db.flush()
            
            # Log Activity
            create_activity_log(db, patient.id, "RISK_ALERT_CREATED", f"⚠️ High-risk alert generated ({ac['reason']}) for {patient.full_name}", is_demo=True)
            print(f"  ✓ {ac['level'].upper()} alert for {patient.full_name}")
        
        db.commit()

        # ============================================================
        # 8. Recalculate Risk Scores for all Patients
        # ============================================================
        print("\nRecalculating predictive risk scores for all patients...")
        for patient in patients:
            calculate_predictive_risk_score(db, patient)
        db.commit()

        # Summary
        print("\n" + "=" * 60)
        print("  SEEDING COMPLETE!")
        print("=" * 60)
        print(f"\n  📊 Summary:")
        print(f"     Users:            3 (1 doctor, 1 HCW, 1 admin)")
        print(f"     Patients:         {len(patients)}")
        print(f"     Prescriptions:    {len(prescription_configs)}")
        print(f"     Reminders:        {len(all_reminders)}")
        print(f"     Compliance Logs:  {compliance_count}")
        print(f"     Lab Reports:      {len(lab_reports_data)}")
        print(f"     Symptom Logs:     {len(symptom_configs)}")
        print(f"     Risk Alerts:      {len(alert_configs)}")
        print(f"\n  🔐 Login Credentials:")
        print(f"     Doctor:  9876543210 / doctor123")
        print(f"     HCW:     9876543211 / hcw123")
        print(f"     Admin:   9876543200 / admin123")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ SEEDING FAILED: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
