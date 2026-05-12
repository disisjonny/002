# Student Management Desktop Application (PyQt6 + SQLite)

A modern dashboard-style desktop application for teachers to manage students, family status, social categories, and reports.

## Features

- Dashboard with statistic cards and chart
- Add/Edit/Delete students
- Student list with sorting, search, and filters
- Student profile (double-click row)
- Photo upload and local storage
- Export to Excel and PDF
- SQLite backup

## Project Structure

```
.
├── data/
│   ├── photos/
│   └── students.db
├── requirements.txt
├── README.md
└── src/
    ├── main.py
    ├── database/
    │   ├── __init__.py
    │   └── db_manager.py
    ├── services/
    │   ├── __init__.py
    │   ├── export_service.py
    │   └── student_service.py
    └── ui/
        ├── __init__.py
        ├── main_window.py
        └── style.qss
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

## Build single .exe with PyInstaller (Windows)

1. Install PyInstaller:

```bash
pip install pyinstaller
```

2. Build one-file executable:

```bash
pyinstaller --noconfirm --onefile --windowed \
  --name "StudentManagementApp" \
  --add-data "src/ui/style.qss;ui" \
  src/main.py
```

3. Find output:
- `dist/StudentManagementApp.exe`

> Note: On Windows CMD, use `^` for line continuation; on PowerShell use backtick (`` ` ``) or a single-line command.
