"""Main GUI for the Student Management dashboard app."""
from __future__ import annotations

from pathlib import Path

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from database.db_manager import DatabaseManager
from services.export_service import export_students_excel, export_students_pdf
from services.student_service import StudentService


class StudentProfileDialog(QMessageBox):
    def __init__(self, student: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Student Profile - {student.get('first_name','')}")
        text = (
            f"Name: {student.get('first_name','')} {student.get('last_name','')}\n"
            f"Phone: {student.get('phone','')}\n"
            f"Address: {student.get('address','')}\n"
            f"Father: {student.get('father_name','')} ({student.get('father_phone','')})\n"
            f"Mother: {student.get('mother_name','')} ({student.get('mother_phone','')})\n"
            f"Temir Daftar: {'Yes' if student.get('temir_daftar') else 'No'}\n"
            f"Low Income: {'Yes' if student.get('low_income') else 'No'}"
        )
        self.setText(text)
        self.setStandardButtons(QMessageBox.StandardButton.Ok)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Student Management Dashboard")
        self.resize(1400, 860)

        self.db = DatabaseManager()
        self.service = StudentService(self.db)
        self.current_photo_source = ""
        self.editing_student_id: int | None = None

        root = QWidget(objectName="root")
        self.setCentralWidget(root)
        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addWidget(self._build_sidebar(), 0)
        right = QVBoxLayout()
        right.setContentsMargins(16, 16, 16, 16)
        right.setSpacing(12)
        right.addWidget(self._build_topbar())

        self.pages = QStackedWidget()
        self.dashboard_page = self._build_dashboard_page()
        self.add_student_page = self._build_add_student_page()
        self.student_list_page = self._build_student_list_page()
        self.reports_page = self._build_reports_page()
        self.settings_page = self._build_settings_page()

        for p in [
            self.dashboard_page,
            self.add_student_page,
            self.student_list_page,
            self.reports_page,
            self.settings_page,
        ]:
            self.pages.addWidget(p)
        right.addWidget(self.pages, 1)
        main_layout.addLayout(right, 1)

        self.refresh_dashboard()
        self.load_student_table()

    def _build_sidebar(self) -> QWidget:
        frame = QFrame(objectName="sidebar")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 16, 10, 16)
        title = QLabel("🎓 School Admin")
        title.setStyleSheet("font-size: 18px; font-weight: 700; padding: 8px;")
        layout.addWidget(title)

        items = [
            ("📊 Dashboard", 0),
            ("➕ Add Student", 1),
            ("👥 Student List", 2),
            ("📁 Reports", 3),
            ("⚙️ Settings", 4),
        ]
        self.nav_buttons: list[QPushButton] = []
        for idx, (label, page_idx) in enumerate(items):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("class", "nav")
            btn.setObjectName(f"nav_{page_idx}")
            btn.setStyleSheet("")
            btn.clicked.connect(lambda _, pi=page_idx: self.set_page(pi))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)
            if idx == 0:
                btn.setChecked(True)

        layout.addStretch(1)
        return frame

    def _build_topbar(self) -> QWidget:
        frame = QFrame(objectName="topbar")
        layout = QHBoxLayout(frame)
        title = QLabel("Student Management")
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
        self.global_search = QLineEdit()
        self.global_search.setPlaceholderText("Search student...")
        self.global_search.textChanged.connect(self.on_global_search)
        user = QToolButton()
        user.setText("👤")
        user.setStyleSheet("font-size: 18px;")

        layout.addWidget(title)
        layout.addStretch(1)
        layout.addWidget(self.global_search, 0)
        layout.addWidget(user)
        return frame

    def _stat_card(self, label: str, value: str) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        l = QVBoxLayout(card)
        l.addWidget(QLabel(label))
        val = QLabel(value)
        val.setStyleSheet("font-size: 28px; font-weight: 800;")
        l.addWidget(val)
        l.addStretch(1)
        card.value_label = val  # type: ignore[attr-defined]
        return card

    def _build_dashboard_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        stats_layout = QGridLayout()
        self.card_total = self._stat_card("Total Students", "0")
        self.card_temir = self._stat_card("Students in Temir Daftar", "0")
        self.card_low = self._stat_card("Low-income Students", "0")
        stats_layout.addWidget(self.card_total, 0, 0)
        stats_layout.addWidget(self.card_temir, 0, 1)
        stats_layout.addWidget(self.card_low, 0, 2)
        layout.addLayout(stats_layout)

        chart_card = QFrame()
        chart_card.setProperty("class", "card")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.addWidget(QLabel("Distribution"))
        self.fig = Figure(figsize=(5, 3), facecolor="none")
        self.canvas = FigureCanvas(self.fig)
        chart_layout.addWidget(self.canvas)
        layout.addWidget(chart_card, 1)
        return page

    def _group_box(self, title: str) -> tuple[QGroupBox, QFormLayout]:
        box = QGroupBox(title)
        box.setStyleSheet(
            "QGroupBox {font-size: 14px; font-weight: 700; border: 1px solid #e6ebf4; "
            "border-radius: 12px; margin-top: 8px; padding: 12px;}"
        )
        form = QFormLayout(box)
        return box, form

    def _build_add_student_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)

        info_box, info_form = self._group_box("Student Information")
        self.first_name = QLineEdit(); info_form.addRow("First Name", self.first_name)
        self.last_name = QLineEdit(); info_form.addRow("Last Name", self.last_name)
        self.middle_name = QLineEdit(); info_form.addRow("Middle Name", self.middle_name)
        self.birth_year = QSpinBox(); self.birth_year.setRange(1980, 2030); info_form.addRow("Birth Year", self.birth_year)
        self.nationality = QLineEdit(); info_form.addRow("Nationality", self.nationality)
        self.phone = QLineEdit(); info_form.addRow("Phone Number", self.phone)
        self.address = QTextEdit(); self.address.setFixedHeight(60); info_form.addRow("Address", self.address)
        self.mahalla = QLineEdit(); info_form.addRow("Mahalla", self.mahalla)
        self.street = QLineEdit(); info_form.addRow("Street", self.street)

        self.photo_preview = QLabel("No photo")
        self.photo_preview.setFixedSize(120, 120)
        self.photo_preview.setStyleSheet("border:1px dashed #b8c6e2; border-radius: 10px;")
        self.photo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_btn = QPushButton("Upload Photo")
        upload_btn.setProperty("class", "secondary")
        upload_btn.clicked.connect(self.upload_photo)
        photo_row = QHBoxLayout(); photo_row.addWidget(self.photo_preview); photo_row.addWidget(upload_btn); photo_row.addStretch(1)
        info_form.addRow("Photo", photo_row)

        father_box, father_form = self._group_box("Father Information")
        self.father_name = QLineEdit(); father_form.addRow("Full Name", self.father_name)
        self.father_phone = QLineEdit(); father_form.addRow("Phone", self.father_phone)
        self.father_birth = QSpinBox(); self.father_birth.setRange(1940, 2030); father_form.addRow("Birth Year", self.father_birth)

        mother_box, mother_form = self._group_box("Mother Information")
        self.mother_name = QLineEdit(); mother_form.addRow("Full Name", self.mother_name)
        self.mother_phone = QLineEdit(); mother_form.addRow("Phone", self.mother_phone)
        self.mother_birth = QSpinBox(); self.mother_birth.setRange(1940, 2030); mother_form.addRow("Birth Year", self.mother_birth)

        family_box, family_form = self._group_box("Family Information")
        self.marital_status = QComboBox(); self.marital_status.addItems(["Married", "Divorced", "Single Parent", "Other"])
        family_form.addRow("Marital Status", self.marital_status)
        self.temir = QComboBox(); self.temir.addItems(["No", "Yes"]); family_form.addRow("Temir Daftar", self.temir)
        self.low_income = QComboBox(); self.low_income.addItems(["No", "Yes"]); family_form.addRow("Low Income", self.low_income)
        self.sector = QLineEdit(); family_form.addRow("Sector", self.sector)

        inner_layout.addWidget(info_box)
        inner_layout.addWidget(father_box)
        inner_layout.addWidget(mother_box)
        inner_layout.addWidget(family_box)

        actions = QHBoxLayout()
        save_btn = QPushButton("Save Student")
        save_btn.setProperty("class", "primary")
        save_btn.clicked.connect(self.save_student)
        clear_btn = QPushButton("Clear")
        clear_btn.setProperty("class", "secondary")
        clear_btn.clicked.connect(self.clear_form)
        actions.addStretch(1)
        actions.addWidget(clear_btn)
        actions.addWidget(save_btn)
        inner_layout.addLayout(actions)

        scroll.setWidget(inner)
        layout.addWidget(scroll)
        return page

    def _build_student_list_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        bar = QHBoxLayout()
        self.list_search = QLineEdit(); self.list_search.setPlaceholderText("Search by name, phone, sector")
        self.list_search.textChanged.connect(self.load_student_table)
        self.filter_combo = QComboBox(); self.filter_combo.addItems(["All", "Temir Daftar", "Low Income"])
        self.filter_combo.currentTextChanged.connect(self.load_student_table)

        edit_btn = QPushButton("Edit")
        edit_btn.setProperty("class", "secondary")
        edit_btn.clicked.connect(self.edit_selected_student)
        delete_btn = QPushButton("Delete")
        delete_btn.setProperty("class", "secondary")
        delete_btn.clicked.connect(self.delete_selected_student)

        bar.addWidget(self.list_search, 1)
        bar.addWidget(self.filter_combo)
        bar.addWidget(edit_btn)
        bar.addWidget(delete_btn)
        layout.addLayout(bar)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["ID", "First Name", "Last Name", "Phone", "Birth Year", "Sector", "Temir", "Low"])
        self.table.setSortingEnabled(True)
        self.table.cellDoubleClicked.connect(self.show_profile_from_row)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)
        return page

    def _build_reports_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        card = QFrame(); card.setProperty("class", "card")
        cl = QVBoxLayout(card)
        cl.addWidget(QLabel("Export & Reports"))

        excel_btn = QPushButton("Export to Excel")
        excel_btn.setProperty("class", "primary")
        excel_btn.clicked.connect(self.export_excel)
        pdf_btn = QPushButton("Export to PDF")
        pdf_btn.setProperty("class", "secondary")
        pdf_btn.clicked.connect(self.export_pdf)
        cl.addWidget(excel_btn)
        cl.addWidget(pdf_btn)
        cl.addStretch(1)
        layout.addWidget(card)
        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        card = QFrame(); card.setProperty("class", "card")
        cl = QVBoxLayout(card)
        cl.addWidget(QLabel("Settings & Backup"))
        backup_btn = QPushButton("Backup Database")
        backup_btn.setProperty("class", "primary")
        backup_btn.clicked.connect(self.backup_database)
        cl.addWidget(backup_btn)
        cl.addStretch(1)
        layout.addWidget(card)
        return page

    def set_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        for i, b in enumerate(self.nav_buttons):
            b.setChecked(i == index)

    def upload_photo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Photo", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.current_photo_source = path
            pix = QPixmap(path).scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.photo_preview.setPixmap(pix)

    def form_payload(self) -> dict:
        return {
            "first_name": self.first_name.text().strip(),
            "last_name": self.last_name.text().strip(),
            "middle_name": self.middle_name.text().strip(),
            "birth_year": self.birth_year.value(),
            "nationality": self.nationality.text().strip(),
            "phone": self.phone.text().strip(),
            "address": self.address.toPlainText().strip(),
            "mahalla": self.mahalla.text().strip(),
            "street": self.street.text().strip(),
            "father_name": self.father_name.text().strip(),
            "father_phone": self.father_phone.text().strip(),
            "father_birth_year": self.father_birth.value(),
            "mother_name": self.mother_name.text().strip(),
            "mother_phone": self.mother_phone.text().strip(),
            "mother_birth_year": self.mother_birth.value(),
            "marital_status": self.marital_status.currentText(),
            "temir_daftar": 1 if self.temir.currentText() == "Yes" else 0,
            "low_income": 1 if self.low_income.currentText() == "Yes" else 0,
            "sector": self.sector.text().strip(),
            "photo_source": self.current_photo_source,
        }

    def save_student(self) -> None:
        payload = self.form_payload()
        if not payload["first_name"] or not payload["last_name"]:
            QMessageBox.warning(self, "Validation", "First Name and Last Name are required.")
            return

        if self.editing_student_id:
            self.service.update_student(self.editing_student_id, payload)
            QMessageBox.information(self, "Updated", "Student updated successfully.")
            self.editing_student_id = None
        else:
            self.service.create_student(payload)
            QMessageBox.information(self, "Saved", "Student saved successfully.")

        self.clear_form()
        self.load_student_table()
        self.refresh_dashboard()

    def clear_form(self) -> None:
        for widget in [
            self.first_name,
            self.last_name,
            self.middle_name,
            self.nationality,
            self.phone,
            self.mahalla,
            self.street,
            self.father_name,
            self.father_phone,
            self.mother_name,
            self.mother_phone,
            self.sector,
        ]:
            widget.clear()
        self.birth_year.setValue(2008)
        self.father_birth.setValue(1980)
        self.mother_birth.setValue(1980)
        self.address.clear()
        self.temir.setCurrentIndex(0)
        self.low_income.setCurrentIndex(0)
        self.current_photo_source = ""
        self.photo_preview.setPixmap(QPixmap())
        self.photo_preview.setText("No photo")

    def load_student_table(self) -> None:
        rows = self.db.list_students(self.list_search.text(), self.filter_combo.currentText()) if hasattr(self, "list_search") else self.db.list_students()
        self.table.setRowCount(0)
        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            vals = [
                row_data["id"],
                row_data["first_name"],
                row_data["last_name"],
                row_data["phone"],
                row_data["birth_year"],
                row_data["sector"],
                "Yes" if row_data["temir_daftar"] else "No",
                "Yes" if row_data["low_income"] else "No",
            ]
            for col, val in enumerate(vals):
                self.table.setItem(row, col, QTableWidgetItem(str(val if val is not None else "")))

    def selected_student_id(self) -> int | None:
        items = self.table.selectedItems()
        if not items:
            return None
        return int(self.table.item(items[0].row(), 0).text())

    def edit_selected_student(self) -> None:
        student_id = self.selected_student_id()
        if not student_id:
            QMessageBox.warning(self, "Select", "Please select a student row.")
            return
        row = self.db.get_student(student_id)
        if not row:
            return

        # Reset pending upload state so an old unsaved file path is never reused
        # when opening another student in edit mode.
        self.current_photo_source = ""

        self.editing_student_id = student_id
        self.set_page(1)
        self.first_name.setText(row["first_name"] or "")
        self.last_name.setText(row["last_name"] or "")
        self.middle_name.setText(row["middle_name"] or "")
        self.birth_year.setValue(row["birth_year"] or 2008)
        self.nationality.setText(row["nationality"] or "")
        self.phone.setText(row["phone"] or "")
        self.address.setText(row["address"] or "")
        self.mahalla.setText(row["mahalla"] or "")
        self.street.setText(row["street"] or "")
        self.father_name.setText(row["father_name"] or "")
        self.father_phone.setText(row["father_phone"] or "")
        self.father_birth.setValue(row["father_birth_year"] or 1980)
        self.mother_name.setText(row["mother_name"] or "")
        self.mother_phone.setText(row["mother_phone"] or "")
        self.mother_birth.setValue(row["mother_birth_year"] or 1980)
        self.marital_status.setCurrentText(row["marital_status"] or "Married")
        self.temir.setCurrentIndex(1 if row["temir_daftar"] else 0)
        self.low_income.setCurrentIndex(1 if row["low_income"] else 0)
        self.sector.setText(row["sector"] or "")
        if row["photo_path"] and Path(row["photo_path"]).exists():
            pix = QPixmap(row["photo_path"]).scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.photo_preview.setPixmap(pix)
            self.photo_preview.setText("")
        else:
            self.photo_preview.setPixmap(QPixmap())
            self.photo_preview.setText("No photo")

    def delete_selected_student(self) -> None:
        student_id = self.selected_student_id()
        if not student_id:
            QMessageBox.warning(self, "Select", "Please select a student row.")
            return
        if QMessageBox.question(self, "Confirm", "Delete selected student?") == QMessageBox.StandardButton.Yes:
            self.db.delete_student(student_id)
            self.load_student_table()
            self.refresh_dashboard()

    def show_profile_from_row(self, row: int, _col: int) -> None:
        student_id = int(self.table.item(row, 0).text())
        student = self.db.get_student(student_id)
        if student:
            StudentProfileDialog(dict(student), self).exec()

    def refresh_dashboard(self) -> None:
        stats = self.db.stats()
        self.card_total.value_label.setText(str(stats["total"]))
        self.card_temir.value_label.setText(str(stats["temir"]))
        self.card_low.value_label.setText(str(stats["low"]))

        self.fig.clear()
        ax = self.fig.add_subplot(111)
        labels = ["Temir Daftar", "Low Income", "Other"]
        other = max(stats["total"] - stats["temir"] - stats["low"], 0)
        values = [stats["temir"], stats["low"], other]
        ax.bar(labels, values, color=["#3f7cff", "#7ec8ff", "#c7d7f9"])
        ax.set_facecolor("#ffffff")
        ax.set_title("Student Categories")
        self.canvas.draw()

    def current_rows(self) -> list[dict]:
        rows = self.db.list_students(self.list_search.text(), self.filter_combo.currentText())
        return [dict(r) for r in rows]

    def export_excel(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export Excel", "students.xlsx", "Excel Files (*.xlsx)")
        if path:
            out = export_students_excel(self.current_rows(), path)
            QMessageBox.information(self, "Exported", f"Excel exported to:\n{out}")

    def export_pdf(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "students.pdf", "PDF Files (*.pdf)")
        if path:
            out = export_students_pdf(self.current_rows(), path)
            QMessageBox.information(self, "Exported", f"PDF exported to:\n{out}")

    def backup_database(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose Backup Folder")
        if folder:
            out = self.service.backup_database(folder)
            QMessageBox.information(self, "Backup Complete", f"Backup saved to:\n{out}")

    def on_global_search(self, text: str) -> None:
        if hasattr(self, "list_search"):
            self.list_search.setText(text)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.db.close()
        super().closeEvent(event)
