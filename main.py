import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QSettings

from SettingsDialog import SettingsDialog
from api_client import APIClient
from widgets.login import LoginWindow
from widgets.dashboard import DashboardWindow


def check_server_connection(api_client: APIClient) -> bool:
    """Проверка соединения с сервером"""
    try:
        return api_client.check_health()
    except Exception as e:
        QMessageBox.critical(None, "Ошибка соединения",
                             f"Не удалось подключиться к серверу:\n{str(e)}")
        return False


def main():
    app = QApplication(sys.argv)

    # Настройки приложения
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    settings = QSettings("YourCompany", "EDI_System")

    # Основной цикл подключения
    while True:
        # Инициализация API клиента
        api_client = APIClient()

        # Первичная проверка соединения
        if check_server_connection(api_client):
            break

        # Если соединение не установлено - показываем настройки
        settings_dialog = SettingsDialog()
        result = settings_dialog.exec()

        if result != SettingsDialog.DialogCode.Accepted:
            # Пользователь отменил настройки - выход
            sys.exit(0)

        # Обновляем URL в клиенте
        api_client.update_base_url(settings.value("server_url"))

    # Инициализация окна входа
    login_window = LoginWindow(api_client)

    def handle_login_success(user_data: dict):
        """Обработчик успешного входа"""
        login_window.close()

        # Создаем и показываем главное окно
        dashboard = DashboardWindow(api_client, user_data)
        dashboard.show()

    # Подключаем сигнал успешного входа
    login_window.login_success.connect(handle_login_success)

    # Показываем окно входа
    login_window.show()

    # Запуск основного цикла приложения
    sys.exit(app.exec())


if __name__ == "__main__":
    main()