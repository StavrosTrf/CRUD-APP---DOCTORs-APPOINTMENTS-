"""DAO ασθενών (patients) — CRUD πάνω στον πίνακα patients."""
from __future__ import annotations

import sqlite3

from .database import Database
from .entities import Patient


def _row_to_patient(row: sqlite3.Row) -> Patient:
    return Patient(
        id=row["id"],
        amka=row["amka"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        phone=row["phone"],
        email=row["email"],
        date_of_birth=row["date_of_birth"],
        gdpr_consent=bool(row["gdpr_consent"]),
        created_at=row["created_at"],
    )


class PatientRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    # --- Create ---
    def add(self, p: Patient) -> Patient:
        cur = self.db.cursor()
        cur.execute(
            """INSERT INTO patients
               (amka, first_name, last_name, phone, email, date_of_birth,
                gdpr_consent, created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                p.amka, p.first_name, p.last_name, p.phone, p.email,
                p.date_of_birth, int(p.gdpr_consent), p.created_at,
            ),
        )
        self.db.commit()
        p.id = cur.lastrowid
        return p

    # --- Read ---
    def get_by_id(self, patient_id: int) -> Patient | None:
        cur = self.db.cursor()
        cur.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
        row = cur.fetchone()
        return _row_to_patient(row) if row else None

    def get_by_amka(self, amka: str) -> Patient | None:
        cur = self.db.cursor()
        cur.execute("SELECT * FROM patients WHERE amka = ?", (amka,))
        row = cur.fetchone()
        return _row_to_patient(row) if row else None

    def list_all(self) -> list[Patient]:
        cur = self.db.cursor()
        cur.execute("SELECT * FROM patients ORDER BY last_name, first_name")
        return [_row_to_patient(r) for r in cur.fetchall()]

    def search(self, term: str) -> list[Patient]:
        """Αναζήτηση κατά ΑΜΚΑ, όνομα ή επώνυμο."""
        like = f"%{term}%"
        cur = self.db.cursor()
        cur.execute(
            """SELECT * FROM patients
               WHERE amka LIKE ? OR first_name LIKE ? OR last_name LIKE ?
               ORDER BY last_name, first_name""",
            (like, like, like),
        )
        return [_row_to_patient(r) for r in cur.fetchall()]

    # --- Update ---
    def update(self, p: Patient) -> None:
        cur = self.db.cursor()
        cur.execute(
            """UPDATE patients SET
               amka = ?, first_name = ?, last_name = ?, phone = ?, email = ?,
               date_of_birth = ?, gdpr_consent = ?
               WHERE id = ?""",
            (
                p.amka, p.first_name, p.last_name, p.phone, p.email,
                p.date_of_birth, int(p.gdpr_consent), p.id,
            ),
        )
        self.db.commit()

    # --- Delete ---
    def delete(self, patient_id: int) -> None:
        cur = self.db.cursor()
        cur.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        self.db.commit()
