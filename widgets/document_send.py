from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QTextEdit,
    QPushButton, QLabel, QHBoxLayout, QListWidgetItem,
    QMessageBox, QDialog, QGroupBox
)
from PyQt6.QtGui import QFont, QIcon
from api_client import APIError


class DocumentSendDialog(QDialog):
    def __init__(self, api, document_id, parent=None):
        super().__init__(parent)
        self.api = api
        self.document_id = document_id
        self.setWindowTitle("Отправить документ")
        self.setGeometry(400, 400, 600, 500)
        self.init_ui()
        self.load_users_and_groups()

    def init_ui(self):
        layout = QVBoxLayout()

        # Заголовок
        title = QLabel("Выберите получателей для этого документа")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # Пользователи
        users_group = QGroupBox("Отправить пользователям")
        users_layout = QVBoxLayout()
        self.users_list = QListWidget()
        self.users_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        users_layout.addWidget(self.users_list)
        users_group.setLayout(users_layout)
        layout.addWidget(users_group)

        # Группы
        groups_group = QGroupBox("Отправить группам")
        groups_layout = QVBoxLayout()
        self.groups_list = QListWidget()
        self.groups_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        groups_layout.addWidget(self.groups_list)
        groups_group.setLayout(groups_layout)
        layout.addWidget(groups_group)

        # Заметки
        notes_group = QGroupBox("Заметки (необязательно)")
        notes_layout = QVBoxLayout()
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        notes_layout.addWidget(self.notes_edit)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)

        # Кнопки
        buttons_layout = QHBoxLayout()
        back_btn = QPushButton("Назад")
        back_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(back_btn)

        send_btn = QPushButton("Отправить документ")
        send_btn.setIcon(QIcon.fromTheme("mail-send"))
        send_btn.clicked.connect(self.send_document)
        buttons_layout.addWidget(send_btn)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def load_users_and_groups(self):
        try:
            # Загрузка пользователей
            users = self.api.get_users()
            for user in users:
                display_text = f"{user.get('full_name', '')} ({user.get('email', '')})"
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, user["id"])
                self.users_list.addItem(item)

            # Загрузка групп (если доступно в API)
            # groups = self.api.get_groups()
            # for group in groups:
            #     item = QListWidgetItem(group["name"])
            #     item.setData(Qt.ItemDataRole.UserRole, group["id"])
            #     self.groups_list.addItem(item)

            # Если группы не реализованы, скрываем секцию
            if self.groups_list.count() == 0:
                self.groups_list.parent().setVisible(False)

        except APIError as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {e.message}")

    def send_document(self):
        # Собираем выбранных пользователей
        selected_users = []
        for item in self.users_list.selectedItems():
            user_id = item.data(Qt.ItemDataRole.UserRole)
            selected_users.append(user_id)

        # Собираем выбранные группы
        selected_groups = []
        for item in self.groups_list.selectedItems():
            group_id = item.data(Qt.ItemDataRole.UserRole)
            selected_groups.append(group_id)

        notes = self.notes_edit.toPlainText()

        if not selected_users and not selected_groups:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одного получателя")
            return

        try:
            # Отправка документа
            self.api.share_document(
                self.document_id,
                selected_users,
                selected_groups,
                notes
            )

            QMessageBox.information(self, "Успех", "Документ успешно отправлен")
            self.accept()
        except APIError as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка отправки документа: {e.message}")

