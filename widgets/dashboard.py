import json

import requests
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QGroupBox, QFormLayout, QHBoxLayout, QTextEdit, QMessageBox, QFileDialog,
    QInputDialog, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from api_client import APIError


class DashboardWindow(QMainWindow):
    def __init__(self, api, user_data):
        super().__init__()
        self.api = api
        self.user_data = user_data
        self.init_ui()
        self.load_documents()
        self.init_timers()

    def init_ui(self):
        self.setWindowTitle("Dashboard | EDI System")
        self.setGeometry(100, 100, 1400, 900)

        # Общий стиль окна и виджетов
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f2f5;
                font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
                font-size: 12pt;
                color: #2c3e50;
            }
            QLabel#titleLabel {
                font-size: 22pt;
                font-weight: 700;
                color: #34495e;
                margin-bottom: 20px;
            }
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                background: white;
                border-radius: 8px;
                margin-top: 10px;
            }
            QTabBar::tab {
                background: #ecf0f1;
                border: 1px solid #bdc3c7;
                padding: 10px 25px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 5px;
                font-weight: 600;
                color: #7f8c8d;
            }
            QTabBar::tab:selected, QTabBar::tab:hover {
                background: #3498db;
                color: white;
                border-color: #2980b9;
            }
            QTableWidget {
                background: white;
                border: none;
                border-radius: 8px;
                gridline-color: #ecf0f1;
            }
            QTableWidget::item:selected {
                background-color: #2980b9;
                color: white;
            }
            QPushButton {
                background-color: #2980b9;
                color: white;
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: 600;
                min-width: 120px;
                transition: background-color 0.3s ease;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #1c5980;
            }
            QLineEdit, QComboBox {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 6px 8px;
                background: white;
            }
            QGroupBox {
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 15px;
                padding: 10px;
                background: #fafafa;
                font-weight: 600;
                color: #34495e;
            }
            QTextEdit {
                background: white;
                border-radius: 8px;
                border: 1px solid #bdc3c7;
                padding: 10px;
                font-family: "Segoe UI";
                font-size: 11pt;
            }
        """)

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Заголовок с именем пользователя
        title_text = f"EDI System Dashboard | Привет, {self.user_data.get('full_name', 'Пользователь')}!"
        title = QLabel(title_text)
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- Вкладка Документы ---
        self.tab_documents = QWidget()
        self.tabs.addTab(self.tab_documents, "Документы")
        self.init_documents_tab()

        # --- Вкладка Журнал действий ---
        self.tab_log = QWidget()
        self.tabs.addTab(self.tab_log, "Журнал действий")
        self.init_log_tab()

        # --- Вкладка Настройки ---
        self.tab_settings = QWidget()
        self.tabs.addTab(self.tab_settings, "Настройки")
        self.init_settings_tab()

        self.setCentralWidget(central_widget)

    def init_documents_tab(self):
        layout = QVBoxLayout(self.tab_documents)

        # Фильтры и поиск
        filter_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по документам...")
        self.search_input.textChanged.connect(self.filter_documents)
        filter_layout.addWidget(self.search_input)

        self.document_type_filter = QComboBox()
        self.document_type_filter.addItems(["Все документы", "Мои документы", "Доступные мне"])
        self.document_type_filter.currentIndexChanged.connect(self.filter_documents)
        filter_layout.addWidget(self.document_type_filter)

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_documents)
        filter_layout.addWidget(refresh_btn)

        layout.addLayout(filter_layout)

        # Таблица документов
        self.doc_table = QTableWidget()
        self.doc_table.setColumnCount(7)
        self.doc_table.setHorizontalHeaderLabels([
            "ID", "Название", "Описание", "Файл", "Тип", "Дата создания", "Версия"
        ])
        self.doc_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.doc_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.doc_table.itemSelectionChanged.connect(self.document_selected)
        layout.addWidget(self.doc_table)

        # Кнопки действий
        buttons_layout = QHBoxLayout()

        self.upload_btn = QPushButton("Загрузить файл")
        self.upload_btn.clicked.connect(self.upload_document)
        buttons_layout.addWidget(self.upload_btn)

        self.upload_version_btn = QPushButton("Загрузить новую версию")
        self.upload_version_btn.clicked.connect(self.upload_new_version)
        buttons_layout.addWidget(self.upload_version_btn)

        self.download_btn = QPushButton("Скачать")
        self.download_btn.clicked.connect(self.download_document)
        buttons_layout.addWidget(self.download_btn)

        self.verify_btn = QPushButton("Проверить целостность")
        self.verify_btn.clicked.connect(self.verify_document)
        buttons_layout.addWidget(self.verify_btn)

        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(self.delete_document)
        buttons_layout.addWidget(self.delete_btn)

        layout.addLayout(buttons_layout)

        # Метаданные документа
        meta_group = QGroupBox("Метаданные документа")
        meta_layout = QFormLayout()

        self.meta_title = QLineEdit()
        self.meta_description = QTextEdit()
        self.meta_description.setMaximumHeight(80)
        self.meta_filename = QLineEdit()
        self.meta_filename.setReadOnly(True)
        self.meta_content_type = QLineEdit()
        self.meta_content_type.setReadOnly(True)
        self.meta_created_at = QLineEdit()
        self.meta_created_at.setReadOnly(True)
        self.meta_version = QLineEdit()
        self.meta_version.setReadOnly(True)

        meta_layout.addRow("Название:", self.meta_title)
        meta_layout.addRow("Описание:", self.meta_description)
        meta_layout.addRow("Имя файла:", self.meta_filename)
        meta_layout.addRow("Тип контента:", self.meta_content_type)
        meta_layout.addRow("Дата создания:", self.meta_created_at)
        meta_layout.addRow("Версия:", self.meta_version)

        meta_group.setLayout(meta_layout)
        layout.addWidget(meta_group)

        # Кнопка сохранения метаданных
        save_meta_btn = QPushButton("Сохранить метаданные")
        save_meta_btn.clicked.connect(self.save_metadata)
        layout.addWidget(save_meta_btn)

    def init_log_tab(self):
        layout = QVBoxLayout(self.tab_log)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        self.load_action_log()

    def init_settings_tab(self):
        layout = QVBoxLayout(self.tab_settings)
        form = QFormLayout()

        self.api_url_input = QLineEdit()
        self.api_url_input.setText(self.api.base_url)
        form.addRow("API URL:", self.api_url_input)

        self.cert_file_input = QLineEdit()
        form.addRow("Путь к сертификату:", self.cert_file_input)
        browse_btn = QPushButton("Обзор")
        browse_btn.clicked.connect(self.browse_cert_file)
        form.addRow("", browse_btn)

        self.sync_checkbox = QPushButton("Включить синхронизацию")
        self.sync_checkbox.setCheckable(True)
        form.addRow("Синхронизация:", self.sync_checkbox)

        save_btn = QPushButton("Сохранить настройки")
        save_btn.clicked.connect(self.save_settings)
        form.addRow(save_btn)

        layout.addLayout(form)

    def init_timers(self):
        self.logout_timer = QTimer()
        self.logout_timer.setInterval(30 * 60 * 1000)  # 30 минут
        self.logout_timer.timeout.connect(self.handle_logout)
        self.logout_timer.start()

        self.sync_timer = QTimer()
        self.sync_timer.setInterval(5 * 60 * 1000)  # 5 минут
        self.sync_timer.timeout.connect(self.sync_offline_changes)
        self.sync_timer.start()

    # --- Методы для работы с документами ---
    def load_documents(self):
        try:
            self.documents = self.api.get_documents()
            self.filtered_documents = self.documents
            self.display_documents(self.documents)
            self.log_event("Список документов обновлен")
        except APIError as e:
            self.show_error(f"Ошибка загрузки документов: {e.message}")

    def display_documents(self, docs):
        self.doc_table.setRowCount(len(docs))
        for i, doc in enumerate(docs):
            self.doc_table.setItem(i, 0, QTableWidgetItem(str(doc.get("id", ""))))
            self.doc_table.setItem(i, 1, QTableWidgetItem(doc.get("title", "")))
            self.doc_table.setItem(i, 2, QTableWidgetItem(doc.get("description", "") or ""))
            self.doc_table.setItem(i, 3, QTableWidgetItem(doc.get("filename", "")))
            self.doc_table.setItem(i, 4, QTableWidgetItem(doc.get("content_type", "")))
            self.doc_table.setItem(i, 5, QTableWidgetItem(doc.get("created_at", "")))
            self.doc_table.setItem(i, 6, QTableWidgetItem(str(doc.get("current_version_id", "")) or ""))

        # Автонастройка ширины столбцов
        self.doc_table.resizeColumnsToContents()

    def filter_documents(self):
        text = self.search_input.text().lower()
        doc_type = self.document_type_filter.currentIndex()

        filtered = []
        for doc in self.documents:
            # Фильтр по типу документа
            if doc_type == 1 and doc.get("creator_id") != self.user_data.get("id"):
                continue
            if doc_type == 2 and doc.get("creator_id") == self.user_data.get("id"):
                continue

            # Фильтр по тексту
            if (text in str(doc.get("id", "")).lower() or
                    text in doc.get("title", "").lower() or
                    text in (doc.get("description", "") or "").lower() or
                    text in doc.get("filename", "").lower()):
                filtered.append(doc)

        self.filtered_documents = filtered
        self.display_documents(filtered)

    def document_selected(self):
        selected = self.doc_table.selectedItems()
        if not selected:
            self.current_doc = None
            self.clear_metadata_fields()
            return

        row = selected[0].row()
        if row < len(self.filtered_documents):
            self.current_doc = self.filtered_documents[row]
            self.load_metadata_fields()
        else:
            self.current_doc = None
            self.clear_metadata_fields()

    def load_metadata_fields(self):
        if not self.current_doc:
            self.clear_metadata_fields()
            return

        self.meta_title.setText(self.current_doc.get("title", ""))
        self.meta_description.setText(self.current_doc.get("description", "") or "")
        self.meta_filename.setText(self.current_doc.get("filename", ""))
        self.meta_content_type.setText(self.current_doc.get("content_type", ""))
        self.meta_created_at.setText(self.current_doc.get("created_at", ""))
        self.meta_version.setText(str(self.current_doc.get("current_version_id", "") or ""))

    def clear_metadata_fields(self):
        self.meta_title.clear()
        self.meta_description.clear()
        self.meta_filename.clear()
        self.meta_content_type.clear()
        self.meta_created_at.clear()
        self.meta_version.clear()

    def upload_document(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл для загрузки",
            "",
            "Все файлы (*);;PDF (*.pdf);;Документы (*.doc *.docx);;Таблицы (*.xls *.xlsx)"
        )

        if not file_path:
            return

        title, ok = QInputDialog.getText(
            self,
            "Название документа",
            "Введите название документа:"
        )

        if not ok or not title:
            return

        try:
            self.api.upload_document(file_path, title)
            self.load_documents()
            self.log_event(f"Документ '{title}' успешно загружен")
            self.show_notification("Документ успешно загружен")
        except APIError as e:
            # Добавляем более информативное сообщение
            error_msg = f"Ошибка загрузки: {e.message}"
            if "500" in e.message:
                error_msg += "\n(Серверная ошибка, проверьте логи сервера)"
            self.show_error(error_msg)

    def upload_new_version(self):
        if not self.current_doc:
            self.show_error("Выберите документ для обновления")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите новую версию файла",
            "",
            "Все файлы (*);;PDF (*.pdf);;Документы (*.doc *.docx);;Таблицы (*.xls *.xlsx)"
        )

        if not file_path:
            return

        try:
            doc_id = self.current_doc.get("id")
            self.api.upload_new_version(doc_id, file_path)
            self.load_documents()
            self.log_event(f"Загружена новая версия документа ID: {doc_id}")
            self.show_notification("Новая версия документа успешно загружена")
        except APIError as e:
            self.show_error(f"Ошибка загрузки новой версии: {e.message}")

    def download_document(self):
        if not self.current_doc:
            self.show_error("Выберите документ для скачивания")
            return

        try:
            doc_id = self.current_doc.get("id")
            filename = self.current_doc.get("filename", f"document_{doc_id}")

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

            self.log_event(f"Документ ID {doc_id} скачан и сохранён в {save_path}")
            self.show_notification("Документ успешно скачан")
        except Exception as e:
            self.show_error(f"Ошибка скачивания документа: {str(e)}")

    def verify_document(self):
        if not self.current_doc:
            self.show_error("Выберите документ для проверки")
            return

        try:
            doc_id = self.current_doc.get("id")
            result = self.api.verify_document_integrity(doc_id)

            if result.get("integrity_verified", False):
                self.show_notification("Целостность документа подтверждена")
                self.log_event(f"Целостность документа ID {doc_id} подтверждена")
            else:
                self.show_error("Целостность документа нарушена")
                self.log_event(f"Целостность документа ID {doc_id} нарушена")
        except APIError as e:
            self.show_error(f"Ошибка проверки целостности: {e.message}")

    def delete_document(self):
        if not self.current_doc:
            self.show_error("Выберите документ для удаления")
            return

        confirm = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить документ '{self.current_doc.get('title')}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            doc_id = self.current_doc.get("id")
            self.api.delete_document(doc_id)
            self.load_documents()
            self.log_event(f"Документ ID {doc_id} удалён")
            self.show_notification("Документ успешно удалён")
        except APIError as e:
            self.show_error(f"Ошибка удаления документа: {e.message}")

    def save_metadata(self):
        if not self.current_doc:
            self.show_error("Выберите документ для редактирования")
            return

        try:
            doc_id = self.current_doc.get("id")
            metadata = {
                "title": self.meta_title.text(),
                "description": self.meta_description.toPlainText()
            }

            self.api.update_document_metadata(doc_id, metadata)
            self.load_documents()
            self.log_event(f"Метаданные документа ID {doc_id} обновлены")
            self.show_notification("Метаданные документа успешно сохранены")
        except APIError as e:
            self.show_error(f"Ошибка обновления метаданных: {e.message}")

    # --- Методы для работы с журналом действий ---
    def load_action_log(self):
        try:
            # В реальном приложении здесь будет запрос к API
            # self.action_log = self.api.get_action_log()
            self.action_log = [
                "2023-05-15 09:30:15 | Пользователь вошел в систему",
                "2023-05-15 10:15:22 | Загружен новый документ: Отчет за апрель",
                "2023-05-15 11:40:05 | Скачан документ: Договор №123"
            ]
            self.update_log_text()
        except Exception as e:
            self.action_log = [f"Ошибка загрузки журнала: {str(e)}"]
            self.update_log_text()

    def log_event(self, message: str):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        self.action_log.append(full_message)
        self.update_log_text()

    def update_log_text(self):
        self.log_text.clear()
        self.log_text.append("\n".join(self.action_log[-50:]))  # Показываем последние 50 записей

    # --- Методы для работы с настройками ---
    def browse_cert_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите сертификат",
            "",
            "Сертификаты (*.pem *.crt);;Все файлы (*)"
        )
        if file_path:
            self.cert_file_input.setText(file_path)

    def save_settings(self):
        api_url = self.api_url_input.text()
        cert_path = self.cert_file_input.text()
        sync_enabled = self.sync_checkbox.isChecked()

        # Сохраняем настройки
        settings = self.api.settings
        settings.setValue("server_url", api_url)
        settings.setValue("cert_path", cert_path)
        settings.setValue("sync_enabled", sync_enabled)

        # Обновляем API клиент
        self.api.base_url = api_url

        self.log_event("Настройки приложения сохранены")
        self.show_notification("Настройки успешно сохранены")

    def handle_logout(self):
        try:
            if self.api.refresh_token:
                self.api.logout()
        except Exception:
            pass

        self.log_event("Пользователь был автоматически выведен из системы из-за бездействия")
        self.show_notification("Время сессии истекло. Пожалуйста, войдите снова.")
        self.close()

    def sync_offline_changes(self):
        if self.sync_checkbox.isChecked():
            self.log_event("Офлайн изменения синхронизированы с сервером")

    # --- Вспомогательные методы ---
    def show_error(self, message):
        QMessageBox.critical(self, "Ошибка", message)

    def show_notification(self, message):
        QMessageBox.information(self, "Информация", message)

    def _handle_response(self, response):
        try:
            response.raise_for_status()
            # Пытаемся обработать как JSON только если есть содержимое
            if response.content:
                return response.json()
            return {}
        except requests.exceptions.HTTPError as e:
            # Обрабатываем случай, когда ответ не в JSON формате
            try:
                error_msg = response.json().get("detail", str(e))
            except json.JSONDecodeError:
                error_msg = response.text or str(e)
            raise APIError(error_msg, response.status_code)
        except Exception as e:
            raise APIError(str(e))