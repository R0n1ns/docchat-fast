import json
import os
import mimetypes

import requests
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QGroupBox, QFormLayout, QHBoxLayout, QTextEdit, QMessageBox, QFileDialog,
    QInputDialog, QHeaderView, QDialog, QDialogButtonBox, QListWidgetItem, QListWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QColor

from api_client import APIError
from widgets.document_view import DocumentViewWindow


class DashboardWindow(QMainWindow):
    def __init__(self, api, user_data):
        super().__init__()
        self.api = api
        self.user_data = user_data
        self.is_admin = user_data.get('role') == 'admin'  # Проверяем роль пользователя
        # print(user_data)
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
        # self.tab_log = QWidget()
        # self.tabs.addTab(self.tab_log, "Журнал действий")
        # self.init_log_tab()

        # --- Вкладка Пользователи (только для админа) ---
        if self.is_admin:
            self.tab_users = QWidget()
            self.tabs.addTab(self.tab_users, "Пользователи")
            self.init_users_tab()

            self.tab_groups = QWidget()
            self.tabs.addTab(self.tab_groups, "Группы")
            self.init_groups_tab()
        # --- Вкладка Настройки ---
        self.tab_settings = QWidget()
        self.tabs.addTab(self.tab_settings, "Настройки")
        self.init_settings_tab()

        self.setCentralWidget(central_widget)

    def init_users_tab(self):
        layout = QVBoxLayout(self.tab_users)

        # Панель инструментов
        toolbar_layout = QHBoxLayout()

        self.user_search = QLineEdit()
        self.user_search.setPlaceholderText("Поиск пользователей...")
        self.user_search.textChanged.connect(self.filter_users)
        toolbar_layout.addWidget(self.user_search)

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_users)
        toolbar_layout.addWidget(refresh_btn)

        add_user_btn = QPushButton("Добавить пользователя")
        add_user_btn.clicked.connect(self.add_user_dialog)
        toolbar_layout.addWidget(add_user_btn)

        layout.addLayout(toolbar_layout)

        # Таблица пользователей
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(7)  # Увеличили количество столбцов
        self.users_table.setHorizontalHeaderLabels([
            "ID", "ФИО", "Email", "Должность", "Роль", "Статус", "Действия"
        ])
        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.users_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.users_table)

        self.load_users()

    def init_groups_tab(self):
        layout = QVBoxLayout(self.tab_groups)

        # Панель инструментов
        toolbar_layout = QHBoxLayout()

        self.group_search = QLineEdit()
        self.group_search.setPlaceholderText("Поиск групп...")
        self.group_search.textChanged.connect(self.filter_groups)
        toolbar_layout.addWidget(self.group_search)

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_groups)
        toolbar_layout.addWidget(refresh_btn)

        add_group_btn = QPushButton("Добавить группу")
        add_group_btn.clicked.connect(self.add_group_dialog)
        toolbar_layout.addWidget(add_group_btn)

        layout.addLayout(toolbar_layout)

        # Таблица групп
        self.groups_table = QTableWidget()
        self.groups_table.setColumnCount(5)
        self.groups_table.setHorizontalHeaderLabels([
            "ID", "Название", "Руководитель", "Участников", "Действия"
        ])
        self.groups_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.groups_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.groups_table)

        self.load_groups()

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
        self.doc_table.setColumnCount(8)  # Добавили столбец для действий
        self.doc_table.setHorizontalHeaderLabels([
            "ID", "Название", "Описание", "Файл", "Тип", "Дата создания", "Версия", "Действия"
        ])
        self.doc_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.doc_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.doc_table)

        # Кнопки действий
        buttons_layout = QHBoxLayout()

        self.upload_btn = QPushButton("Загрузить файл")
        self.upload_btn.clicked.connect(self.upload_document)
        buttons_layout.addWidget(self.upload_btn)

        layout.addLayout(buttons_layout)

    # def init_log_tab(self):
    #     layout = QVBoxLayout(self.tab_log)
    #     self.log_text = QTextEdit()
    #     self.log_text.setReadOnly(True)
    #     layout.addWidget(self.log_text)
    #     self.load_action_log()

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
        # self.sync_timer.timeout.connect(self.sync_offline_changes)
        self.sync_timer.start()

    # --- Методы для работы с документами ---
    def load_documents(self):
        try:
            self.documents = self.api.get_documents()
            self.filtered_documents = self.documents
            self.display_documents(self.documents)
            # self.log_event("Список документов обновлен")
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

            # Кнопка "Просмотр"
            view_btn = QPushButton("Просмотр")
            view_btn.setProperty("doc_id", doc["id"])
            view_btn.clicked.connect(self.open_document_view)
            self.doc_table.setCellWidget(i, 7, view_btn)

        # Автонастройка ширины столбцов
        self.doc_table.resizeColumnsToContents()

    def open_document_view(self):
        btn = self.sender()
        doc_id = btn.property("doc_id")

        # Найти документ по ID
        doc = next((d for d in self.documents if d["id"] == doc_id), None)

        if doc:
            view_dialog = DocumentViewWindow(self.api, doc, self)
            view_dialog.exec()

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
            # self.log_event(f"Документ '{title}' успешно загружен")
            self.show_notification("Документ успешно загружен")
        except APIError as e:
            # Добавляем более информативное сообщение
            error_msg = f"Ошибка загрузки: {e.message}"
            if "500" in e.message:
                error_msg += "\n(Серверная ошибка, проверьте логи сервера)"
            self.show_error(error_msg)

    # # --- Методы для работы с журналом действий ---
    # def load_action_log(self):
    #     try:
    #         # В реальном приложении здесь будет запрос к API
    #         # self.action_log = self.api.get_action_log()
    #         self.action_log = [
    #             "2023-05-15 09:30:15 | Пользователь вошел в систему",
    #             "2023-05-15 10:15:22 | Загружен новый документ: Отчет за апрель",
    #             "2023-05-15 11:40:05 | Скачан документ: Договор №123"
    #         ]
    #         self.update_log_text()
    #     except Exception as e:
    #         self.action_log = [f"Ошибка загрузки журнала: {str(e)}"]
    #         self.update_log_text()

    # def log_event(self, message: str):
    #     from datetime import datetime
    #     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #     full_message = f"[{timestamp}] {message}"
    #     self.action_log.append(full_message)
    #     self.update_log_text()

    # def update_log_text(self):
    #     self.log_text.clear()
    #     self.log_text.append("\n".join(self.action_log[-50:]))  # Показываем последние 50 записей

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

        # self.log_event("Настройки приложения сохранены")
        self.show_notification("Настройки успешно сохранены")

    def handle_logout(self):
        try:
            if self.api.refresh_token:
                self.api.logout()
        except Exception:
            pass

        # self.log_event("Пользователь был автоматически выведен из системы из-за бездействия")
        self.show_notification("Время сессии истекло. Пожалуйста, войдите снова.")
        self.close()

    # def sync_offline_changes(self):
    #     if self.sync_checkbox.isChecked():
    #         self.log_event("Офлайн изменения синхронизированы с сервером")

    # --- Вспомогательные методы ---
    def show_error(self, message):
        QMessageBox.critical(self, "Ошибка", message)

    def show_notification(self, message):
        QMessageBox.information(self, "Информация", message)
        # === Методы для работы с пользователями ===

    def load_users(self):
        try:
            self.users = self.api.get_users()
            self.filtered_users = self.users
            self.display_users(self.users)
        except APIError as e:
            self.show_error(f"Ошибка загрузки пользователей: {e.message}")

    def display_users(self, users):
        self.users_table.setRowCount(len(users))
        for i, user in enumerate(users):
            self.users_table.setItem(i, 0, QTableWidgetItem(str(user.get("id", ""))))
            self.users_table.setItem(i, 1, QTableWidgetItem(user.get("full_name", "")))
            self.users_table.setItem(i, 2, QTableWidgetItem(user.get("email", "")))
            self.users_table.setItem(i, 3, QTableWidgetItem(user.get("job_title", "")))
            self.users_table.setItem(i, 4, QTableWidgetItem(user.get("role", "")))

            # Статус пользователя
            status_item = QTableWidgetItem()
            status_item.setData(Qt.ItemDataRole.DisplayRole,
                                "Активен" if user.get("is_active", True) else "Заблокирован")
            status_item.setForeground(QColor("green") if user.get("is_active", True) else QColor("red"))
            self.users_table.setItem(i, 5, status_item)

            # Кнопки действий
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(5, 2, 5, 2)
            btn_layout.setSpacing(5)

            # Кнопка блокировки/разблокировки
            toggle_btn = QPushButton("Заблокировать" if user.get("is_active", True) else "Разблокировать")
            toggle_btn.setProperty("user_id", user["id"])
            toggle_btn.setProperty("current_status", user.get("is_active", True))
            toggle_btn.setStyleSheet(
                "background-color: #e67e22;" if user.get("is_active", True) else "background-color: #27ae60;")
            toggle_btn.clicked.connect(self.toggle_user_status)
            btn_layout.addWidget(toggle_btn)

            # Кнопка редактирования
            edit_btn = QPushButton("Редактировать")
            edit_btn.setProperty("user_id", user["id"])
            edit_btn.setStyleSheet("background-color: #3498db;")
            edit_btn.clicked.connect(self.edit_user_dialog)
            btn_layout.addWidget(edit_btn)

            # Кнопка удаления
            delete_btn = QPushButton("Удалить")
            delete_btn.setProperty("user_id", user["id"])
            delete_btn.setStyleSheet("background-color: #e74c3c;")
            delete_btn.clicked.connect(self.delete_user)
            btn_layout.addWidget(delete_btn)

            widget = QWidget()
            widget.setLayout(btn_layout)
            self.users_table.setCellWidget(i, 6, widget)

        self.users_table.resizeColumnsToContents()
        self.users_table.setColumnWidth(6, 300)  # Фиксируем ширину столбца с кнопками

    def toggle_user_status(self):
        btn = self.sender()
        user_id = btn.property("user_id")
        current_status = btn.property("current_status")

        user = next((u for u in self.users if u["id"] == user_id), None)
        if not user:
            return

        new_status = not current_status
        action = "разблокировать" if new_status else "заблокировать"

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы уверены, что хотите {action} пользователя {user.get('full_name', '')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Обновляем статус пользователя через API
                self.api.update_user(
                    user_id=user_id,
                    is_active=new_status
                )

                # Обновляем кнопку и статус в таблице
                btn.setText("Заблокировать" if new_status else "Разблокировать")
                btn.setProperty("current_status", new_status)
                btn.setStyleSheet("background-color: #e67e22;" if new_status else "background-color: #27ae60;")

                # Обновляем статус в таблице
                row = self.find_table_row_by_user_id(user_id)
                if row >= 0:
                    status_item = self.users_table.item(row, 5)
                    status_item.setText("Активен" if new_status else "Заблокирован")
                    status_item.setForeground(QColor("green") if new_status else QColor("red"))

                self.show_notification(f"Статус пользователя успешно изменен")
            except APIError as e:
                self.show_error(f"Ошибка изменения статуса: {e.message}")

    def find_table_row_by_user_id(self, user_id):
        for row in range(self.users_table.rowCount()):
            if int(self.users_table.item(row, 0).text()) == user_id:
                return row
        return -1
    def filter_users(self):
        text = self.user_search.text().lower()
        filtered = [user for user in self.users
                    if text in str(user.get("id", "")).lower()
                    or text in user.get("full_name", "").lower()
                    or text in user.get("email", "").lower()
                    or text in user.get("job_title", "").lower()]
        self.filtered_users = filtered
        self.display_users(filtered)

    def add_user_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить пользователя")
        layout = QFormLayout(dialog)

        email_edit = QLineEdit()
        full_name_edit = QLineEdit()
        password_edit = QLineEdit()
        password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        role_combo = QComboBox()
        role_combo.addItems(["user", "admin"])

        layout.addRow("Email:", email_edit)
        layout.addRow("ФИО:", full_name_edit)
        layout.addRow("Пароль:", password_edit)
        layout.addRow("Роль:", role_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self.api.create_user(
                    email=email_edit.text(),
                    password=password_edit.text(),
                    role=role_combo.currentText(),
                    full_name=full_name_edit.text()
                )
                self.load_users()
                self.show_notification("Пользователь успешно создан")
            except APIError as e:
                self.show_error(f"Ошибка создания пользователя: {e.message}")

    def edit_user_dialog(self):
        user_id = self.sender().property("user_id")
        user = next((u for u in self.users if u["id"] == user_id), None)

        if not user:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать пользователя")
        dialog.setMinimumWidth(400)
        layout = QFormLayout(dialog)

        email_edit = QLineEdit(user.get("email", ""))
        full_name_edit = QLineEdit(user.get("full_name", ""))
        job_title_edit = QLineEdit(user.get("job_title", ""))

        role_combo = QComboBox()
        role_combo.addItems(["user", "admin"])
        role_combo.setCurrentText(user.get("role", "user"))

        status_combo = QComboBox()
        status_combo.addItems(["Активен", "Заблокирован"])
        status_combo.setCurrentIndex(0 if user.get("is_active", True) else 1)

        layout.addRow("Email:", email_edit)
        layout.addRow("ФИО:", full_name_edit)
        layout.addRow("Должность:", job_title_edit)
        layout.addRow("Роль:", role_combo)
        layout.addRow("Статус:", status_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self.api.update_user(
                    user_id=user_id,
                    email=email_edit.text(),
                    full_name=full_name_edit.text(),
                    job_title=job_title_edit.text(),
                    role=role_combo.currentText(),
                    is_active=(status_combo.currentIndex() == 0)
                )
                self.load_users()
                self.show_notification("Данные пользователя обновлены")
            except APIError as e:
                self.show_error(f"Ошибка обновления пользователя: {e.message}")

    def delete_user(self):
        user_id = self.sender().property("user_id")
        user = next((u for u in self.users if u["id"] == user_id), None)

        if not user:
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить пользователя {user.get('full_name', '')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.api.delete_user(user_id)
                self.load_users()
                self.show_notification("Пользователь удален")
            except APIError as e:
                self.show_error(f"Ошибка удаления пользователя: {e.message}")

        # === Методы для работы с группами ===

    def load_groups(self):
        try:
            # Предположим, что у нас есть метод get_groups в API
            self.groups = self.api.get_groups()  # Этот метод нужно реализовать в api_client.py
            self.filtered_groups = self.groups
            self.display_groups(self.groups)
        except APIError as e:
            self.show_error(f"Ошибка загрузки групп: {e.message}")

    def display_groups(self, groups):
        self.groups_table.setRowCount(len(groups))
        for i, group in enumerate(groups):
            self.groups_table.setItem(i, 0, QTableWidgetItem(str(group.get("id", ""))))
            self.groups_table.setItem(i, 1, QTableWidgetItem(group.get("name", "")))
            self.groups_table.setItem(i, 2, QTableWidgetItem(group.get("leader_name", "")))
            self.groups_table.setItem(i, 3, QTableWidgetItem(str(len(group.get("members", [])))))

            # Кнопки действий
            btn_layout = QHBoxLayout()

            edit_btn = QPushButton("Редактировать")
            edit_btn.setProperty("group_id", group["id"])
            edit_btn.clicked.connect(self.edit_group_dialog)
            btn_layout.addWidget(edit_btn)

            delete_btn = QPushButton("Удалить")
            delete_btn.setProperty("group_id", group["id"])
            delete_btn.clicked.connect(self.delete_group)
            btn_layout.addWidget(delete_btn)

            widget = QWidget()
            widget.setLayout(btn_layout)
            self.groups_table.setCellWidget(i, 4, widget)

        self.groups_table.resizeColumnsToContents()

    def filter_groups(self):
        text = self.group_search.text().lower()
        filtered = [group for group in self.groups
                    if text in str(group.get("id", "")).lower()
                    or text in group.get("name", "").lower()
                    or text in group.get("leader_name", "").lower()]
        self.filtered_groups = filtered
        self.display_groups(filtered)

    def add_group_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить группу")
        layout = QFormLayout(dialog)

        name_edit = QLineEdit()
        leader_combo = QComboBox()

        # Заполняем комбобокс пользователями
        try:
            users = self.api.get_users()
            for user in users:
                leader_combo.addItem(user.get("full_name", ""), user["id"])
        except APIError as e:
            self.show_error(f"Ошибка загрузки пользователей: {e.message}")

        layout.addRow("Название группы:", name_edit)
        layout.addRow("Руководитель:", leader_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                # Предположим, что у нас есть метод create_group в API
                self.api.create_group(
                    name=name_edit.text(),
                    leader_id=leader_combo.currentData()
                )
                self.load_groups()
                self.show_notification("Группа успешно создана")
            except APIError as e:
                self.show_error(f"Ошибка создания группы: {e.message}")

    def edit_group_dialog(self):
        group_id = self.sender().property("group_id")
        group = next((g for g in self.groups if g["id"] == group_id), None)

        if not group:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать группу")
        layout = QFormLayout(dialog)

        name_edit = QLineEdit(group.get("name", ""))
        leader_combo = QComboBox()

        # Заполняем комбобокс пользователями
        try:
            users = self.api.get_users()
            current_leader = group.get("leader_id")
            for user in users:
                leader_combo.addItem(user.get("full_name", ""), user["id"])
                if user["id"] == current_leader:
                    leader_combo.setCurrentIndex(leader_combo.count() - 1)
        except APIError as e:
            self.show_error(f"Ошибка загрузки пользователей: {e.message}")

        layout.addRow("Название группы:", name_edit)
        layout.addRow("Руководитель:", leader_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                # Предположим, что у нас есть метод update_group в API
                self.api.update_group(
                    group_id=group_id,
                    name=name_edit.text(),
                    leader_id=leader_combo.currentData()
                )
                self.load_groups()
                self.show_notification("Данные группы обновлены")
            except APIError as e:
                self.show_error(f"Ошибка обновления группы: {e.message}")

    def delete_group(self):
        group_id = self.sender().property("group_id")
        group = next((g for g in self.groups if g["id"] == group_id), None)

        if not group:
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить группу {group.get('name', '')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Предположим, что у нас есть метод delete_group в API
                self.api.delete_group(group_id)
                self.load_groups()
                self.show_notification("Группа удалена")
            except APIError as e:
                self.show_error(f"Ошибка удаления группы: {e.message}")