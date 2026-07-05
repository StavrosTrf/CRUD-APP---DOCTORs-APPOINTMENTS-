"""DAO ραντεβού (appointments) — CRUD με προαιρετικά joins σε ονόματα."""
from __future__ import annotations

import sqlite3

from .database import Database
from .entities import Appointment

# SELECT με joins ώστε να επιστρέφονται και τα ονόματα ασθενούς/ιατρού.
_SELECT_JOINED = """
SELECT a.*,
       (p.last_name || ' ' || p.first_name) AS patient_name,
       u.full_name AS doctor_name
FROM appointments a
JOIN patients p ON p.id = a.patient_id
JOIN users    u ON u.id = a.doctor_id
"""


def _row_to_appt(row: sqlite3.Row) -> Appointment:
    keys = row.keys()
    return Appointment(
        id=row["id"],
        patient_id=row["patient_id"],
        doctor_id=row["doctor_id"],
        category=row["category"],
        scheduled_at=row["scheduled_at"],
        status=row["status"],
        notes=row["notes"],
        patient_name=row["patient_name"] if "patient_name" in keys else "",
        doctor_name=row["doctor_name"] if "doctor_name" in keys else "",
    )


class AppointmentRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    # --- Create ---
    def add(self, a: Appointment) -> Appointment:
        cur = self.db.cursor()
        cur.execute(
            """INSERT INTO appointments
               (patient_id, doctor_id, category, scheduled_at, status, notes)
               VALUES (?,?,?,?,?,?)""",
            (a.patient_id, a.doctor_id, a.category, a.scheduled_at,
             a.status, a.notes),
        )
        self.db.commit()
        a.id = cur.lastrowid
        return a

    # --- Read ---
    def get_by_id(self, appt_id: int) -> Appointment | None:
        cur = self.db.cursor()
        cur.execute(_SELECT_JOINED + " WHERE a.id = ?", (appt_id,))
        row = cur.fetchone()
        return _row_to_appt(row) if row else None

    def list_all(self) -> list[Appointment]:
        cur = self.db.cursor()
        cur.execute(_SELECT_JOINED + " ORDER BY a.scheduled_at")
        return [_row_to_appt(r) for r in cur.fetchall()]

    def list_for_patient(self, patient_id: int) -> list[Appointment]:
        cur = self.db.cursor()
        cur.execute(
            _SELECT_JOINED + " WHERE a.patient_id = ? ORDER BY a.scheduled_at",
            (patient_id,),
        )
        return [_row_to_appt(r) for r in cur.fetchall()]

    def list_for_doctor(self, doctor_id: int) -> list[Appointment]:
        cur = self.db.cursor()
        cur.execute(
            _SELECT_JOINED + " WHERE a.doctor_id = ? ORDER BY a.scheduled_at",
            (doctor_id,),
        )
        return [_row_to_appt(r) for r in cur.fetchall()]

    def find_conflict(self, doctor_id: int, scheduled_at: str,
                      exclude_id: int | None = None) -> Appointment | None:
        """Βρίσκει υπάρχον ενεργό ραντεβού του ιατρού στην ίδια ώρα (double-booking)."""
        cur = self.db.cursor()
        sql = (
            "SELECT * FROM appointments "
            "WHERE doctor_id = ? AND scheduled_at = ? AND status != 'CANCELLED'"
        )
        params: list = [doctor_id, scheduled_at]
        if exclude_id is not None:
            sql += " AND id != ?"
            params.append(exclude_id)
        cur.execute(sql, params)
        row = cur.fetchone()
        return _row_to_appt(row) if row else None

    # --- Update ---
    def update(self, a: Appointment) -> None:
        cur = self.db.cursor()
        cur.execute(
            """UPDATE appointments SET
               patient_id = ?, doctor_id = ?, category = ?, scheduled_at = ?,
               status = ?, notes = ?
               WHERE id = ?""",
            (a.patient_id, a.doctor_id, a.category, a.scheduled_at,
             a.status, a.notes, a.id),
        )
        self.db.commit()

    # --- Delete ---
    def delete(self, appt_id: int) -> None:
        cur = self.db.cursor()
        cur.execute("DELETE FROM appointments WHERE id = ?", (appt_id,))
        self.db.commit()
