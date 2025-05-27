from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt, QSettings

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("YourCompany", "EDI_System")
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 200)
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        # Server URL input
        self.server_url_input = QLineEdit()
        self.server_url_input.setPlaceholderText("https://api.example.com")
        form.addRow("Server URL:", self.server_url_input)

        # Test connection button
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        form.addRow(self.test_btn)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(form)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_settings(self):
        url = self.settings.value("server_url", "")
        self.server_url_input.setText(url)

    def save_settings(self):
        url = self.server_url_input.text().strip()
        if not url.startswith(("http://", "https://")):
            QMessageBox.warning(self, "Error", "Invalid URL format")
            return

        self.settings.setValue("server_url", url)
        self.accept()

    def test_connection(self):
        from api_client import APIClient  # Импорт здесь чтобы избежать циклических зависимостей
        url = self.server_url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Server URL is not set")
            return

        try:
            client = APIClient(url)
            if client.check_health():
                QMessageBox.information(self, "Success", "Connection successful!")
            else:
                QMessageBox.critical(self, "Error", "Server is not responding")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection failed: {str(e)}")