
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox, QHeaderView, QFileDialog, QDialogButtonBox, QLineEdit,
    QGroupBox, QFormLayout, QTextEdit, QDialog
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt

from api_client import APIError
from widgets.document_send import DocumentSendDialog


class QWebEngineView:
    pass


class DocumentViewWindow(QDialog):
    def __init__(self, api, document_data, parent=None):
        super().__init__(parent)
        self.api = api
        self.document_data = document_data
        self.setWindowTitle(f"Просмотр документа: {document_data.get('title', '')}")
        self.setGeometry(300, 300, 800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Заголовок
        title = QLabel(f"Документ: {self.document_data.get('title', '')}")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # Метаданные документа
        meta_group = QGroupBox("Метаданные документа")
        meta_layout = QFormLayout()

        self.meta_title = QLineEdit(self.document_data.get("title", ""))
        self.meta_description = QTextEdit(self.document_data.get("description", "") or "")
        self.meta_description.setMaximumHeight(80)

        # Только для чтения
        self.meta_id = QLineEdit(str(self.document_data.get("id", "")))
        self.meta_id.setReadOnly(True)
        self.meta_filename = QLineEdit(self.document_data.get("filename", ""))
        self.meta_filename.setReadOnly(True)
        self.meta_content_type = QLineEdit(self.document_data.get("content_type", ""))
        self.meta_content_type.setReadOnly(True)
        self.meta_created_at = QLineEdit(self.document_data.get("created_at", ""))
        self.meta_created_at.setReadOnly(True)
        self.meta_version = QLineEdit(str(self.document_data.get("current_version_id", "") or ""))
        self.meta_version.setReadOnly(True)
        self.meta_creator = QLineEdit(str(self.document_data.get("creator_id", "")))
        self.meta_creator.setReadOnly(True)

        meta_layout.addRow("ID:", self.meta_id)
        meta_layout.addRow("Название:", self.meta_title)
        meta_layout.addRow("Описание:", self.meta_description)
        meta_layout.addRow("Имя файла:", self.meta_filename)
        meta_layout.addRow("Тип контента:", self.meta_content_type)
        meta_layout.addRow("Дата создания:", self.meta_created_at)
        meta_layout.addRow("Версия:", self.meta_version)
        meta_layout.addRow("Создатель:", self.meta_creator)

        meta_group.setLayout(meta_layout)
        layout.addWidget(meta_group)

        # Кнопки действий
        buttons_layout = QHBoxLayout()

        self.download_btn = QPushButton("Скачать")
        self.download_btn.setIcon(QIcon.fromTheme("document-save"))
        self.download_btn.clicked.connect(self.download_document)
        buttons_layout.addWidget(self.download_btn)

        self.verify_btn = QPushButton("Проверить целостность")
        self.verify_btn.setIcon(QIcon.fromTheme("document-edit-verify"))
        self.verify_btn.clicked.connect(self.verify_document)
        buttons_layout.addWidget(self.verify_btn)

        # НОВАЯ КНОПКА: Отправить документ
        self.send_btn = QPushButton("Отправить")
        self.send_btn.setIcon(QIcon.fromTheme("document-send"))
        self.send_btn.clicked.connect(self.open_send_dialog)
        buttons_layout.addWidget(self.send_btn)

        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.setIcon(QIcon.fromTheme("edit-delete"))
        self.delete_btn.clicked.connect(self.delete_document)
        buttons_layout.addWidget(self.delete_btn)

        self.upload_version_btn = QPushButton("Загрузить новую версию")
        self.upload_version_btn.setIcon(QIcon.fromTheme("document-send"))
        self.upload_version_btn.clicked.connect(self.upload_new_version)
        buttons_layout.addWidget(self.upload_version_btn)

        layout.addLayout(buttons_layout)

        # Кнопки сохранения/закрытия
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Close)
        button_box.accepted.connect(self.save_metadata)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    # Новый метод для открытия диалога отправки
    def open_send_dialog(self):
        send_dialog = DocumentSendDialog(self.api, self.document_data["id"], self)
        send_dialog.exec()

    def download_document(self):
        try:
            doc_id = self.document_data.get("id")
            filename = self.document_data.get("filename", f"document_{doc_id}")

            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить документ",
                filename,
                "Все файлы (*);;PDF (*.pdf);;Документы (*.doc *.docx);;Таблицы (*.xls *.xlsx)"
            )

            if not save_path:
                return

            file_data = self.api.download_document(doc_id)

            if not file_data:
                raise Exception("Пустые данные файла")

            with open(save_path, "wb") as f:
                f.write(file_data)

            QMessageBox.information(self, "Успех", "Документ успешно скачан")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка скачивания документа: {str(e)}")

    def verify_document(self):
        try:
            doc_id = self.document_data.get("id")
            result = self.api.verify_document_integrity(doc_id)

            if result.get("integrity_verified", False):
                QMessageBox.information(self, "Проверка целостности", "Целостность документа подтверждена")
            else:
                QMessageBox.warning(self, "Проверка целостности", "Целостность документа нарушена")
        except APIError as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка проверки целостности: {e.message}")

    def delete_document(self):
        confirm = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить документ '{self.document_data.get('title')}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            doc_id = self.document_data.get("id")
            self.api.delete_document(doc_id)
            QMessageBox.information(self, "Успех", "Документ успешно удалён")
            self.accept()  # Закрываем окно после удаления
        except APIError as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка удаления документа: {e.message}")

    def upload_new_version(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите новую версию файла",
            "",
            "Все файлы (*);;PDF (*.pdf);;Документы (*.doc *.docx);;Таблицы (*.xls *.xlsx)"
        )

        if not file_path:
            return

        try:
            doc_id = self.document_data.get("id")
            self.api.upload_new_version(doc_id, file_path)
            QMessageBox.information(self, "Успех", "Новая версия документа успешно загружена")
        except APIError as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки новой версии: {e.message}")

    def save_metadata(self):
        try:
            doc_id = self.document_data.get("id")
            metadata = {
                "title": self.meta_title.text(),
                "description": self.meta_description.toPlainText()
            }

            self.api.update_document_metadata(doc_id, metadata)
            QMessageBox.information(self, "Успех", "Метаданные документа успешно обновлены")
        except APIError as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка обновления метаданных: {e.message}")
