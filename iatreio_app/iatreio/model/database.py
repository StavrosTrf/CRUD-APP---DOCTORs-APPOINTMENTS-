"""Επίπεδο πρόσβασης δεδομένων — διαχείριση σύνδεσης SQLite3 & σχήματος.

Η κλάση Database κρατά μία σύνδεση sqlite3 και δημιουργεί το σχήμα.
Υποστηρίζει βάση σε αρχείο (εφαρμογή) ή στη μνήμη ":memory:" (unit tests).
"""
from __future__ import annotations

import sqlite3


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    salt            TEXT NOT NULL,
    role            TEXT NOT NULL,
    full_name       TEXT NOT NULL DEFAULT '',
    patient_id      INTEGER,
    active          INTEGER NOT NULL DEFAULT 1,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked          INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS patients (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    amka          TEXT NOT NULL UNIQUE,
    first_name    TEXT NOT NULL,
    last_name     TEXT NOT NULL,
    phone         TEXT NOT NULL DEFAULT '',
    email         TEXT NOT NULL DEFAULT '',
    date_of_birth TEXT NOT NULL DEFAULT '',
    gdpr_consent  INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS appointments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id   INTEGER NOT NULL,
    doctor_id    INTEGER NOT NULL,
    category     TEXT NOT NULL DEFAULT '',
    scheduled_at TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'SCHEDULED',
    notes        TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id)  REFERENCES users(id)   ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS medical_records (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id     INTEGER NOT NULL,
    appointment_id INTEGER,
    doctor_id      INTEGER NOT NULL,
    symptoms       TEXT NOT NULL DEFAULT '',
    diagnosis      TEXT NOT NULL DEFAULT '',
    observations   TEXT NOT NULL DEFAULT '',
    prescription   TEXT NOT NULL DEFAULT '',
    created_at     TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (patient_id)     REFERENCES patients(id)     ON DELETE CASCADE,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE SET NULL,
    FOREIGN KEY (doctor_id)      REFERENCES users(id)        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_appt_doctor_time
    ON appointments(doctor_id, scheduled_at);
CREATE INDEX IF NOT EXISTS idx_record_patient
    ON medical_records(patient_id);
"""


class Database:
    """Λεπτό wrapper πάνω από τη σύνδεση sqlite3."""

    def __init__(self, path: str = "iatreio.db") -> None:
        self.path = path
        # check_same_thread=False ώστε η Tkinter (main thread) να λειτουργεί ομαλά.
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_schema()

    def create_schema(self) -> None:
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def cursor(self) -> sqlite3.Cursor:
        return self.conn.cursor()

    def commit(self) -> None:
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
