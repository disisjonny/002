"""SQLite database access layer for student management."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class DatabaseManager:
    """Handles SQLite connection and CRUD operations."""

    def __init__(self, db_path: str = "data/students.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    middle_name TEXT,
                    birth_year INTEGER,
                    nationality TEXT,
                    phone TEXT,
                    address TEXT,
                    mahalla TEXT,
                    street TEXT,
                    photo_path TEXT,
                    father_name TEXT,
                    father_phone TEXT,
                    father_birth_year INTEGER,
                    mother_name TEXT,
                    mother_phone TEXT,
                    mother_birth_year INTEGER,
                    marital_status TEXT,
                    temir_daftar INTEGER DEFAULT 0,
                    low_income INTEGER DEFAULT 0,
                    sector TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def add_student(self, payload: dict[str, Any]) -> int:
        cols = ", ".join(payload.keys())
        placeholders = ", ".join("?" for _ in payload)
        query = f"INSERT INTO students ({cols}) VALUES ({placeholders})"
        with self.conn:
            cur = self.conn.execute(query, tuple(payload.values()))
            return int(cur.lastrowid)

    def update_student(self, student_id: int, payload: dict[str, Any]) -> None:
        assignments = ", ".join(f"{key} = ?" for key in payload.keys())
        query = f"UPDATE students SET {assignments} WHERE id = ?"
        with self.conn:
            self.conn.execute(query, tuple(payload.values()) + (student_id,))

    def delete_student(self, student_id: int) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM students WHERE id = ?", (student_id,))

    def get_student(self, student_id: int) -> sqlite3.Row | None:
        cur = self.conn.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        return cur.fetchone()

    def list_students(self, search: str = "", filter_mode: str = "All") -> list[sqlite3.Row]:
        query = "SELECT * FROM students WHERE 1=1"
        args: list[Any] = []

        if search:
            query += " AND (first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? OR sector LIKE ?)"
            like = f"%{search}%"
            args.extend([like, like, like, like])

        if filter_mode == "Temir Daftar":
            query += " AND temir_daftar = 1"
        elif filter_mode == "Low Income":
            query += " AND low_income = 1"

        query += " ORDER BY created_at DESC"
        cur = self.conn.execute(query, args)
        return cur.fetchall()

    def stats(self) -> dict[str, int]:
        total = self.conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        temir = self.conn.execute("SELECT COUNT(*) FROM students WHERE temir_daftar = 1").fetchone()[0]
        low = self.conn.execute("SELECT COUNT(*) FROM students WHERE low_income = 1").fetchone()[0]
        return {"total": total, "temir": temir, "low": low}

    def close(self) -> None:
        self.conn.close()
