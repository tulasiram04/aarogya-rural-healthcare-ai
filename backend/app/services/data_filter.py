"""Shared data-filter utilities for demo/real record isolation."""
from typing import Optional
from sqlalchemy.orm import Query
from sqlalchemy import Column, or_, and_


def apply_demo_filter(query: Query, model, data_filter: Optional[str] = "all") -> Query:
    """
    Filter query by is_demo column on models that support it.
    data_filter: 'real' | 'demo' | 'all'
    """
    if not hasattr(model, "is_demo"):
        return query
    col: Column = model.is_demo
    if data_filter == "real":
        return query.filter(col == False)  # noqa: E712
    if data_filter == "demo":
        return query.filter(col == True)  # noqa: E712
    return query


def apply_telegram_patient_filter(query: Query, data_filter: Optional[str] = "real") -> Query:
    """
    Portal patient filter — only Telegram-bot registrations appear in real/all views.

    - real: is_demo=False AND telegram_id IS NOT NULL (true bot registrations)
    - demo: is_demo=True (hackathon demo dataset only)
    - all:  real telegram patients OR demo patients (never manual/API-only rows)
    """
    from app.models.patient import Patient

    if data_filter == "demo":
        return query.filter(Patient.is_demo == True)  # noqa: E712

    telegram_registered = and_(
        Patient.is_demo == False,  # noqa: E712
        Patient.telegram_id.isnot(None),
    )

    if data_filter == "real":
        return query.filter(telegram_registered)

    # all = telegram-registered real patients + optional demo dataset
    return query.filter(
        or_(telegram_registered, Patient.is_demo == True)  # noqa: E712
    )


def telegram_patient_ids_subquery(db, data_filter: str = "real"):
    """Return list of patient UUIDs visible in the portal for the given filter."""
    from app.models.patient import Patient

    q = apply_telegram_patient_filter(db.query(Patient.id), data_filter)
    return [row[0] for row in q.all()]


def get_portal_patient_ids(db, data_filter: str, current_user=None) -> list:
    """Patient IDs visible in the portal (Telegram-only for real data), with optional role filter."""
    from app.models.patient import Patient

    q = apply_telegram_patient_filter(db.query(Patient), data_filter)
    if current_user is not None:
        if current_user.role == "doctor":
            q = q.filter(Patient.assigned_doctor_id == current_user.id)
        elif current_user.role == "hcw":
            q = q.filter(Patient.assigned_hcw_id == current_user.id)
    return [p.id for p in q.all()]
