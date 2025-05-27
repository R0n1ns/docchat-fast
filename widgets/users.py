from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QLineEdit, QPushButton, QHBoxLayout, QComboBox, QMessageBox
)

from api_client import APIError


class UserManager(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self.setWindowTitle("User Management (Admin)")
        self.setMinimumSize(600, 400)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f9fafc;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                color: #444;
            }
            QLabel#titleLabel {
                font-size: 24px;
                font-weight: 700;
                margin-bottom: 20px;
                color: #222;
            }
            QLabel {
                font-size: 14px;
            }
            QTableWidget {
                background-color: #fff;
                border: none;
                font-size: 14px;
                border-radius: 8px;
                padding: 10px;
                gridline-color: #e1e4e8;
                selection-background-color: #1a73e8;
                selection-color: white;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            QHeaderView::section {
                background-color: #f0f3f7;
                padding: 8px;
                border: none;
                font-weight: 600;
                color: #555;
            }
            QTableWidget::item {
                padding: 8px 10px;
            }
            QTableWidget::item:selected {
                background-color: #1a73e8;
                color: white;
                border-radius: 4px;
            }
            QPushButton {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #4a90e2, stop:1 #357abd);
                color: white;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 15px;
                font-weight: 600;
                transition: background-color 0.3s ease;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: #2a62b9;
            }
            QPushButton:pressed {
                background-color: #244f91;
            }
            QLineEdit, QComboBox {
                background-color: white;
                border: 1.5px solid #cdd4e0;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 14px;
                color: #333;
                min-width: 150px;
                transition: border-color 0.3s ease;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #4a90e2;
                outline: none;
            }
            QComboBox {
                padding-right: 24px;
            }
        """)

        layout = QVBoxLayout()

        title = QLabel("User Management")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        # Таблица пользователей
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Email", "Role"])
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(self.table.SelectionMode.SingleSelection)
        layout.addWidget(self.table)

        # Форма добавления пользователя
        form_layout = QHBoxLayout()

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        form_layout.addWidget(self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(self.password_input)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["user", "admin"])
        form_layout.addWidget(self.role_combo)

        self.add_button = QPushButton("Add User")
        self.add_button.clicked.connect(self.add_user)
        form_layout.addWidget(self.add_button)

        layout.addLayout(form_layout)

        # Кнопки для обновления и удаления выбранного пользователя
        button_layout = QHBoxLayout()

        self.update_role_button = QPushButton("Update Role")
        self.update_role_button.clicked.connect(self.update_role)
        button_layout.addWidget(self.update_role_button)

        self.delete_button = QPushButton("Delete User")
        self.delete_button.clicked.connect(self.delete_user)
        button_layout.addWidget(self.delete_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.load_users()

    def load_users(self):
        try:
            users = self.api.get_users()
            self.table.setRowCount(len(users))
            for i, user in enumerate(users):
                self.table.setItem(i, 0, QTableWidgetItem(user.get("email", "")))
                self.table.setItem(i, 1, QTableWidgetItem(user.get("role", "")))
        except APIError as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def add_user(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_combo.currentText()

        if not email or not password:
            QMessageBox.warning(self, "Ошибка", "Введите email и пароль")
            return

        try:
            self.api.create_user(email, password, role)
            self.load_users()
        except APIError as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def update_role(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя в таблице")
            return
        email = selected[0].text()
        role = self.role_combo.currentText()
        try:
            self.api.update_user_role(email, role)
            QMessageBox.information(self, "Успех", f"Роль пользователя {email} изменена на {role}.")
            self.load_users()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка при обновлении роли", str(e))

    def delete_user(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя в таблице")
            return
        email = selected[0].text()
        confirm = QMessageBox.question(
            self, "Подтверждение", f"Удалить пользователя {email}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.api.delete_user(email)
                QMessageBox.information(self, "Успех", f"Пользователь {email} удалён.")
                self.load_users()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка при удалении пользователя", str(e))
