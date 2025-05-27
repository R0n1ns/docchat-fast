from typing import Dict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QFrame, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from SettingsDialog import SettingsDialog
from api_client import APIError

class LoginWindow(QWidget):
    login_success = pyqtSignal(dict)

    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self.init_ui()
        self.current_email = None

    def init_ui(self):
        self.setWindowTitle("Corporate Login Portal")
        self.setFixedSize(500, 400)
        self.setStyleSheet("""
            QWidget {
                background-color: #f4f6f9;
                color: #000000;
            }
            QLabel, QLineEdit, QPushButton {
                color: #000000;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #ccc;
                padding: 5px;
                border-radius: 4px;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                padding: 30px;
            }
        """)
        frame_layout = QVBoxLayout(frame)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Welcome to EDI System")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                font-size: 16px;
            }
            QPushButton:hover { color: #005BAC; }
        """)
        self.settings_btn.clicked.connect(self.open_settings)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.settings_btn)
        frame_layout.addLayout(header_layout)

        # Форма входа
        self.form = QFormLayout()
        self.form.setSpacing(15)

        # Поля ввода
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        self.email_input.setMinimumHeight(35)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setMinimumHeight(35)

        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText("Enter OTP code")
        self.otp_input.setMinimumHeight(35)
        self.otp_input.hide()

        self.form.addRow("Email:", self.email_input)
        self.form.addRow("Password:", self.password_input)
        self.form.addRow("OTP:", self.otp_input)

        # Кнопки
        self.btn_send_code = QPushButton("Send Code")
        self.btn_send_code.setStyleSheet("""
            QPushButton {
                background-color: #005BAC;
                color: white;
                padding: 10px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #004080; }
        """)
        self.btn_send_code.clicked.connect(self.send_code)

        self.btn_confirm = QPushButton("Confirm OTP")
        self.btn_confirm.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        self.btn_confirm.clicked.connect(self.confirm_otp)
        self.btn_confirm.hide()

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.btn_send_code)
        button_layout.addWidget(self.btn_confirm)

        frame_layout.addLayout(self.form)
        frame_layout.addLayout(button_layout)
        main_layout.addWidget(frame)
        self.setLayout(main_layout)

    def send_code(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()

        if not email or "@" not in email:
            self.show_error("Please enter a valid email address")
            return
        if not password:
            self.show_error("Please enter your password")
            return

        try:
            self.api.login_init(email, password)
            self.current_email = email
            self.otp_input.show()
            self.btn_confirm.show()
            self.btn_send_code.hide()
            self.show_info("OTP code has been sent to your email")
        except APIError as e:
            self.show_error(f"Error: {e.message}")

    def confirm_otp(self):
        otp = self.otp_input.text().strip()
        if len(otp) != 6 or not otp.isdigit():
            self.show_error("Please enter a valid 6-digit OTP code")
            return

        try:
            token_data = self.api.login(self.current_email, otp)
            user_info = self.api.get_current_user()

            # Закрываем окно входа
            self.close()

            # Импорт главного окна через абсолютный путь
            from widgets.dashboard import DashboardWindow  # Исправленный импорт
            self.dashboard = DashboardWindow(self.api)
            self.dashboard.show()

        except APIError as e:
            self.show_error(f"Authentication failed: {e.message}")

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

    def show_info(self, message):
        QMessageBox.information(self, "Information", message)

    def open_settings(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec()

    def login_init(self, email: str, password: str) -> Dict:
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login-init",
            data={"username": email, "password": password}
        )
        return self._handle_response(response)