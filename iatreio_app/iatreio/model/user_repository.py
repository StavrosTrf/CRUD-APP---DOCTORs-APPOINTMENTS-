"""DAO χρηστών (users) — καθαρό CRUD χωρίς επιχειρησιακή λογική."""
from __future__ import annotations

import sqlite3

from .database import Database
from .entities import User


def _row_to_user(row: sqlite3.Row) -> User:
    return User(
        id=row["id"],
        username=row["username"],
        password_hash=row["password_hash"],
        salt=row["salt"],
        role=row["role"],
        full_name=row["full_name"],
        patient_id=row["patient_id"],
        active=bool(row["active"]),
        failed_attempts=row["failed_attempts"],
        locked=bool(row["locked"]),
    )


class UserRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, user: User) -> User:
        cur = self.db.cursor()
        cur.execute(
            """INSERT INTO users
               (username, password_hash, salt, role, full_name, patient_id,
                active, failed_attempts, locked)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                user.username, user.password_hash, user.salt, user.role,
                user.full_name, user.patient_id, int(user.active),
                user.failed_attempts, int(user.locked),
            ),
        )
        self.db.commit()
        user.id = cur.lastrowid
        return user

    def get_by_username(self, username: str) -> User | None:
        cur = self.db.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        return _row_to_user(row) if row else None

    def get_by_id(self, user_id: int) -> User | None:
        cur = self.db.cursor()
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        return _row_to_user(row) if row else None

    def list_by_role(self, role: str) -> list[User]:
        cur = self.db.cursor()
        cur.execute(
            "SELECT * FROM users WHERE role = ? ORDER BY full_name", (role,)
        )
        return [_row_to_user(r) for r in cur.fetchall()]

    def update_security(self, user: User) -> None:
        """Ενημερώνει μόνο τα πεδία ασφαλείας (failed_attempts, locked)."""
        cur = self.db.cursor()
        cur.execute(
            "UPDATE users SET failed_attempts = ?, locked = ? WHERE id = ?",
            (user.failed_attempts, int(user.locked), user.id),
        )
        self.db.commit()
