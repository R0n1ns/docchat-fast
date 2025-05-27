
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox, QHeaderView
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from api_client import APIError


class QWebEngineView:
    pass


class DocumentViewWindow(QWidget):
    def __init__(self, api, doc_id):
        super().__init__()
        self.api = api
        self.doc_id = doc_id
        self.init_ui()
        self.load_data()

    def init_ui(self):
        self.setWindowTitle("Document Viewer")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet("background-color: #f4f6f9;")

        layout = QVBoxLayout(self)

        title = QLabel("Document Content and History")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 15px;")
        layout.addWidget(title)

        self.web_view = QWebEngineView()
        self.web_view.setStyleSheet("border: 1px solid #ccc; border-radius: 6px;")
        layout.addWidget(self.web_view, stretch=3)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(["User", "Action", "Timestamp"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border-radius: 6px;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #005BAC;
                color: white;
                padding: 6px;
            }
        """)
        layout.addWidget(self.history_table, stretch=1)

    def load_data(self):
        try:
            html = self.api.get_document_html(self.doc_id)
            self.web_view.setHtml(html)

            history = self.api.get_document_history(self.doc_id)
            self.history_table.setRowCount(len(history))
            for i, h in enumerate(history):
                self.history_table.setItem(i, 0, QTableWidgetItem(h["user"]))
                self.history_table.setItem(i, 1, QTableWidgetItem(h["action"]))
                self.history_table.setItem(i, 2, QTableWidgetItem(h["timestamp"]))

        except APIError as e:
            QMessageBox.critical(self, "Error", str(e))