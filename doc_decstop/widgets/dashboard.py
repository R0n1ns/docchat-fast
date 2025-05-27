from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QGroupBox, QFormLayout, QHBoxLayout, QTextEdit, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from api_client import APIError


class DashboardWindow(QMainWindow):
    def __init__(self, api):
        super().__init__()
        self.api = api
        self.init_ui()
        self.load_documents()

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

        title = QLabel("EDI System Dashboard")
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

        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по документам...")
        self.search_input.textChanged.connect(self.filter_documents)
        filter_layout.addWidget(self.search_input)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["Все", "Approved", "Pending", "Rejected"])
        self.status_filter.currentIndexChanged.connect(self.filter_documents)
        filter_layout.addWidget(self.status_filter)

        layout.addLayout(filter_layout)

        self.doc_table = QTableWidget()
        self.doc_table.setColumnCount(6)
        self.doc_table.setHorizontalHeaderLabels([
            "ID", "Отправитель", "Получатель", "Дата", "Статус", "Версия"
        ])
        self.doc_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.doc_table.itemSelectionChanged.connect(self.document_selected)
        self.doc_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.doc_table)

        buttons_layout = QHBoxLayout()
        self.upload_btn = QPushButton("Загрузить файл")
        self.upload_btn.clicked.connect(self.upload_document)
        buttons_layout.addWidget(self.upload_btn)

        self.encrypt_btn = QPushButton("Зашифровать")
        self.encrypt_btn.clicked.connect(self.encrypt_document)
        buttons_layout.addWidget(self.encrypt_btn)

        self.download_btn = QPushButton("Скачать и расшифровать")
        self.download_btn.clicked.connect(self.download_document)
        buttons_layout.addWidget(self.download_btn)

        self.sign_btn = QPushButton("Подписать")
        self.sign_btn.clicked.connect(self.sign_document)
        buttons_layout.addWidget(self.sign_btn)

        self.edit_meta_btn = QPushButton("Редактировать метаданные")
        self.edit_meta_btn.clicked.connect(self.edit_metadata)
        buttons_layout.addWidget(self.edit_meta_btn)

        layout.addLayout(buttons_layout)

        meta_group = QGroupBox("Метаданные документа")
        meta_layout = QFormLayout()
        self.meta_sender = QLineEdit()
        self.meta_recipient = QLineEdit()
        self.meta_date = QLineEdit()
        self.meta_status = QLineEdit()
        self.meta_version = QLineEdit()
        meta_layout.addRow("Отправитель:", self.meta_sender)
        meta_layout.addRow("Получатель:", self.meta_recipient)
        meta_layout.addRow("Дата:", self.meta_date)
        meta_layout.addRow("Статус:", self.meta_status)
        meta_layout.addRow("Версия:", self.meta_version)
        meta_group.setLayout(meta_layout)
        layout.addWidget(meta_group)

    def init_log_tab(self):
        layout = QVBoxLayout(self.tab_log)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

    def init_settings_tab(self):
        layout = QVBoxLayout(self.tab_settings)
        form = QFormLayout()

        self.api_url_input = QLineEdit()
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

    # --- Методы для документов ---
    def load_documents(self):
        try:
            self.documents = self.api.get_documents()
            self.display_documents(self.documents)
        except APIError as e:
            self.show_error(f"Ошибка загрузки документов: {e.message}")

    def display_documents(self, docs):
        self.doc_table.setRowCount(len(docs))
        for i, doc in enumerate(docs):
            self.doc_table.setItem(i, 0, QTableWidgetItem(str(doc.get("id", ""))))
            self.doc_table.setItem(i, 1, QTableWidgetItem(doc.get("sender", "")))
            self.doc_table.setItem(i, 2, QTableWidgetItem(doc.get("recipient", "")))
            self.doc_table.setItem(i, 3, QTableWidgetItem(doc.get("date", "")))
            self.doc_table.setItem(i, 4, QTableWidgetItem(doc.get("status", "")))
            self.doc_table.setItem(i, 5, QTableWidgetItem(str(doc.get("version", ""))))

    def filter_documents(self):
        text = self.search_input.text().lower()
        status = self.status_filter.currentText()
        filtered = []
        for doc in self.documents:
            if (text in str(doc.get("id", "")).lower()
                    or text in doc.get("sender", "").lower()
                    or text in doc.get("recipient", "").lower()):
                if status == "Все" or doc.get("status", "") == status:
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
        self.meta_sender.setText(self.current_doc.get("sender", ""))
        self.meta_recipient.setText(self.current_doc.get("recipient", ""))
        self.meta_date.setText(self.current_doc.get("date", ""))
        self.meta_status.setText(self.current_doc.get("status", ""))
        self.meta_version.setText(str(self.current_doc.get("version", "")))

    def clear_metadata_fields(self):
        self.meta_sender.clear()
        self.meta_recipient.clear()
        self.meta_date.clear()
        self.meta_status.clear()
        self.meta_version.clear()

    def upload_document(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл")
        if not file_path:
            return

        title = QInputDialog.getText(self, "Название документа", "Введите название:")[0]
        if not title:
            return

        try:
            self.api.upload_document(file_path, title)
            self.load_documents()
            self.show_notification("Документ успешно загружен")
        except APIError as e:
            self.show_error(f"Ошибка загрузки: {e.message}")

    def download_document(self):
        if not self.current_doc:
            self.show_error("Выберите документ для скачивания.")
            return
        try:
            doc_id = self.current_doc.get("id")
            data = self.api.download_document(doc_id)
            if not data:
                raise Exception("Пустые данные файла.")
            save_path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл как", f"document_{doc_id}")
            if save_path:
                with open(save_path, "wb") as f:
                    f.write(data)
                self.log_event(f"Документ ID {doc_id} скачан и сохранён в {save_path}")
                self.show_notification("Документ успешно скачан и сохранён.")
        except Exception as e:
            self.show_error(f"Ошибка скачивания документа: {e}")

    def encrypt_document(self):
        if not self.current_doc:
            self.show_error("Выберите документ для шифрования.")
            return
        try:
            doc_id = self.current_doc.get("id")
            self.api.encrypt_document(doc_id)
            self.log_event(f"Документ ID {doc_id} зашифрован.")
            self.show_notification("Документ успешно зашифрован.")
            self.load_documents()
        except Exception as e:
            self.show_error(f"Ошибка шифрования: {e}")

    def sign_document(self):
        if not self.current_doc:
            self.show_error("Выберите документ для подписания.")
            return
        try:
            doc_id = self.current_doc.get("id")
            self.api.sign_document(doc_id)
            self.log_event(f"Документ ID {doc_id} подписан.")
            self.show_notification("Документ успешно подписан.")
            self.load_documents()
        except Exception as e:
            self.show_error(f"Ошибка подписания: {e}")

    def edit_metadata(self):
        if not self.current_doc:
            self.show_error("Выберите документ для редактирования метаданных.")
            return
        try:
            doc_id = self.current_doc.get("id")
            metadata = {
                "sender": self.meta_sender.text(),
                "recipient": self.meta_recipient.text(),
                "date": self.meta_date.text(),
                "status": self.meta_status.text(),
                "version": self.meta_version.text(),
            }
            self.api.update_metadata(doc_id, metadata)
            self.log_event(f"Метаданные документа ID {doc_id} обновлены.")
            self.show_notification("Метаданные документа обновлены.")
            self.load_documents()
        except Exception as e:
            self.show_error(f"Ошибка обновления метаданных: {e}")

    # --- Журнал действий ---
    def load_action_log(self):
        try:
            self.action_log = self.api.get_action_log()
        except AttributeError:
            self.action_log = []
        self.update_log_text()

    def log_event(self, message: str):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        self.action_log.append(full_message)
        self.update_log_text()

    def update_log_text(self):
        self.log_text.clear()
        self.log_text.append("\n".join(self.action_log))

    # --- Пример заготовок для оставшихся методов ---
    def browse_cert_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите сертификат")
        if file_path:
            self.cert_file_input.setText(file_path)

    def save_settings(self):
        api_url = self.api_url_input.text()
        cert_path = self.cert_file_input.text()
        sync_enabled = self.sync_checkbox.isChecked()
        # Тут логика сохранения настроек, например в файл или в api
        self.log_event("Настройки сохранены.")
        self.show_notification("Настройки успешно сохранены.")

    def handle_logout(self):
        self.log_event("Пользователь был автоматически выведен из системы из-за бездействия.")
        self.show_notification("Время сессии истекло. Пожалуйста, войдите снова.")
        self.close()  # или вызови окно логина

    def sync_offline_changes(self):
        # Здесь синхронизация офлайн изменений с сервером
        self.log_event("Офлайн изменения синхронизированы.")

    def show_error(self, message):
        QMessageBox.critical(self, "Ошибка", message)

    def show_notification(self, message):
        QMessageBox.information(self, "Информация", message)
