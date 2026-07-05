"""DAO ιατρικού ιστορικού (medical_records) — CRUD."""
from __future__ import annotations

import sqlite3

from .database import Database
from .entities import MedicalRecord

_SELECT_JOINED = """
SELECT m.*, u.full_name AS doctor_name
FROM medical_records m
JOIN users u ON u.id = m.doctor_id
"""


def _row_to_record(row: sqlite3.Row) -> MedicalRecord:
    keys = row.keys()
    return MedicalRecord(
        id=row["id"],
        patient_id=row["patient_id"],
        appointment_id=row["appointment_id"],
        doctor_id=row["doctor_id"],
        symptoms=row["symptoms"],
        diagnosis=row["diagnosis"],
        observations=row["observations"],
        prescription=row["prescription"],
        created_at=row["created_at"],
        doctor_name=row["doctor_name"] if "doctor_name" in keys else "",
    )


class MedicalRecordRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    # --- Create ---
    def add(self, r: MedicalRecord) -> MedicalRecord:
        cur = self.db.cursor()
        cur.execute(
            """INSERT INTO medical_records
               (patient_id, appointment_id, doctor_id, symptoms, diagnosis,
                observations, prescription, created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (r.patient_id, r.appointment_id, r.doctor_id, r.symptoms,
             r.diagnosis, r.observations, r.prescription, r.created_at),
        )
        self.db.commit()
        r.id = cur.lastrowid
        return r

    # --- Read ---
    def get_by_id(self, record_id: int) -> MedicalRecord | None:
        cur = self.db.cursor()
        cur.execute(_SELECT_JOINED + " WHERE m.id = ?", (record_id,))
        row = cur.fetchone()
        return _row_to_record(row) if row else None

    def list_for_patient(self, patient_id: int) -> list[MedicalRecord]:
        cur = self.db.cursor()
        cur.execute(
            _SELECT_JOINED + " WHERE m.patient_id = ? ORDER BY m.created_at DESC",
            (patient_id,),
        )
        return [_row_to_record(r) for r in cur.fetchall()]

    # --- Update ---
    def update(self, r: MedicalRecord) -> None:
        cur = self.db.cursor()
        cur.execute(
            """UPDATE medical_records SET
               symptoms = ?, diagnosis = ?, observations = ?, prescription = ?
               WHERE id = ?""",
            (r.symptoms, r.diagnosis, r.observations, r.prescription, r.id),
        )
        self.db.commit()

    # --- Delete ---
    def delete(self, record_id: int) -> None:
        cur = self.db.cursor()
        cur.execute("DELETE FROM medical_records WHERE id = ?", (record_id,))
        self.db.commit()
