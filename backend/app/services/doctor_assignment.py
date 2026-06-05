import logging
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.patient import Patient

logger = logging.getLogger("aarogya.doctor_assignment")

def assign_doctor_to_patient(db: Session, patient: Patient) -> None:
    """
    Assigns a doctor to the patient based on assignment rules:
    - If only one active doctor exists, assign them automatically.
    - If multiple active doctors exist, assign the doctor with the least assigned patients.
    """
    try:
        doctors = db.query(User).filter(User.role == "doctor", User.is_active == True).all()
        if not doctors:
            logger.warning("No active doctors found to assign patient.")
            return

        if len(doctors) == 1:
            patient.assigned_doctor_id = doctors[0].id
            logger.info(f"Auto-assigned patient {patient.full_name} to the only doctor: {doctors[0].full_name}")
            try:
                from app.services.activity import create_activity_log
                create_activity_log(db, patient.id, "DOCTOR_ASSIGNED", f"👤 Doctor {doctors[0].full_name} assigned to patient {patient.full_name}")
            except Exception as act_err:
                logger.error(f"Failed to log doctor assignment activity: {str(act_err)}")
        else:
            # Count assigned patients for each doctor
            doctor_counts = []
            for doc in doctors:
                count = db.query(Patient).filter(Patient.assigned_doctor_id == doc.id).count()
                doctor_counts.append((doc, count))
            
            # Sort by count and pick the least one
            doctor_counts.sort(key=lambda x: x[1])
            assigned_doc, least_count = doctor_counts[0]
            patient.assigned_doctor_id = assigned_doc.id
            logger.info(f"Auto-assigned patient {patient.full_name} to doctor {assigned_doc.full_name} with least patients ({least_count}).")
            try:
                from app.services.activity import create_activity_log
                create_activity_log(db, patient.id, "DOCTOR_ASSIGNED", f"👤 Doctor {assigned_doc.full_name} assigned to patient {patient.full_name}")
            except Exception as act_err:
                logger.error(f"Failed to log doctor assignment activity: {str(act_err)}")
    except Exception as e:
        logger.error(f"Doctor assignment failed: {str(e)}")
