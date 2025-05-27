from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QTextEdit,
    QPushButton, QLabel, QHBoxLayout, QListWidgetItem,
    QMessageBox
)
from PyQt6.QtGui import QFont
from api_client import APIError


class DocumentSendWindow(QWidget):
    def __init__(self, api, doc_id):
        super().__init__()
        self.api = api
        self.doc_id = doc_id
        self.init_ui()
        self.load_data()

    def init_ui(self):
        self.setWindowTitle("Send Document")
        self.setFixedSize(800, 600)
        self.setStyleSheet("background-color: #f4f6f9;")

        layout = QVBoxLayout()

        title = QLabel("Select Recipients and Add a Message")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 15px;")
        layout.addWidget(title)

        self.recipient_list = QListWidget()
        self.recipient_list.setStyleSheet("background-color: white; border-radius: 8px;")
        layout.addWidget(self.recipient_list)

        self.message_box = QTextEdit()
        self.message_box.setPlaceholderText("Enter optional message here...")
        self.message_box.setStyleSheet("background-color: white; border-radius: 8px; padding: 10px;")
        layout.addWidget(self.message_box)

        self.send_btn = QPushButton("Send Document")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #005BAC;
                color: white;
                padding: 10px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #004080;
            }
        """)
        self.send_btn.clicked.connect(self.send_document)

        layout.addWidget(self.send_btn)
        self.setLayout(layout)

    def load_data(self):
        try:
            recipients = self.api.get_users()
            for user in recipients:
                item = QListWidgetItem(f"{user['name']} ({user['email']})")
                item.setData(Qt.ItemDataRole.UserRole, user["id"])
                item.setCheckState(Qt.CheckState.Unchecked)
                self.recipient_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def send_document(self):
        selected = []
        for i in range(self.recipient_list.count()):
            item = self.recipient_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.data(Qt.ItemDataRole.UserRole))

        message = self.message_box.toPlainText()

        try:
            self.api.send_document(self.doc_id, selected, message)
            QMessageBox.information(self, "Success", "Document sent successfully!")
            self.close()
        except APIError as e:
            QMessageBox.critical(self, "Send Failed", str(e))