"""Export utilities for Excel and PDF output."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


HEADERS = [
    "ID",
    "First Name",
    "Last Name",
    "Phone",
    "Birth Year",
    "Sector",
    "Temir Daftar",
    "Low Income",
]


def export_students_excel(rows: Iterable[dict], out_path: str) -> str:
    wb = Workbook()
    ws = wb.active
    ws.title = "Students"
    ws.append(HEADERS)
    for row in rows:
        ws.append(
            [
                row.get("id"),
                row.get("first_name"),
                row.get("last_name"),
                row.get("phone"),
                row.get("birth_year"),
                row.get("sector"),
                "Yes" if row.get("temir_daftar") else "No",
                "Yes" if row.get("low_income") else "No",
            ]
        )
    dst = Path(out_path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    wb.save(dst)
    return str(dst)


def export_students_pdf(rows: Iterable[dict], out_path: str) -> str:
    dst = Path(out_path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(dst), pagesize=A4)
    width, height = A4

    y = height - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Student Report")
    y -= 30

    c.setFont("Helvetica", 9)
    c.drawString(40, y, "ID")
    c.drawString(70, y, "Name")
    c.drawString(220, y, "Phone")
    c.drawString(320, y, "Sector")
    c.drawString(420, y, "Flags")
    y -= 15

    for row in rows:
        name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
        flags = []
        if row.get("temir_daftar"):
            flags.append("Temir")
        if row.get("low_income"):
            flags.append("Low")
        c.drawString(40, y, str(row.get("id", "")))
        c.drawString(70, y, name[:26])
        c.drawString(220, y, str(row.get("phone", ""))[:15])
        c.drawString(320, y, str(row.get("sector", ""))[:15])
        c.drawString(420, y, ", ".join(flags) or "-")
        y -= 14
        if y < 40:
            c.showPage()
            y = height - 40
            c.setFont("Helvetica", 9)

    c.save()
    return str(dst)
