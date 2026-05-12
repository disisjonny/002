"""Business logic services for students."""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from database.db_manager import DatabaseManager


class StudentService:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db
        self.photo_dir = Path("data/photos")
        self.photo_dir.mkdir(parents=True, exist_ok=True)

    def _save_photo(self, source_path: str | None) -> str:
        if not source_path:
            return ""
        src = Path(source_path)
        if not src.exists():
            return ""
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}{src.suffix}"
        dst = self.photo_dir / filename
        shutil.copy2(src, dst)
        return str(dst)

    def create_student(self, payload: dict[str, Any]) -> int:
        photo_source = payload.pop("photo_source", "")
        payload["photo_path"] = self._save_photo(photo_source)
        return self.db.add_student(payload)

    def update_student(self, student_id: int, payload: dict[str, Any]) -> None:
        photo_source = payload.pop("photo_source", "")
        if photo_source:
            payload["photo_path"] = self._save_photo(photo_source)
        self.db.update_student(student_id, payload)

    def backup_database(self, destination_dir: str) -> str:
        dst_dir = Path(destination_dir)
        dst_dir.mkdir(parents=True, exist_ok=True)
        backup_name = f"students_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = dst_dir / backup_name
        shutil.copy2(self.db.db_path, backup_path)
        return str(backup_path)
