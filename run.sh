#!/bin/bash

# Переменная для хранения цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для отображения сообщений
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка наличия Docker и Docker Compose
if ! command -v docker &> /dev/null; then
    print_error "Docker не установлен. Установите Docker и повторите попытку."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_warning "Docker Compose не установлен. Проверьте, что он установлен вместе с Docker или установите отдельно."
    print_warning "Пытаемся использовать 'docker compose' вместо 'docker-compose'..."
    DOCKER_COMPOSE_CMD="docker compose"
else
    DOCKER_COMPOSE_CMD="docker-compose"
fi

# Функция для создания .env файла, если он не существует
create_env_file() {
    if [ ! -f ".env" ]; then
        print_warning ".env файл не найден. Создаем из .env.example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_message ".env файл создан из .env.example"
        else
            print_error "Файл .env.example не найден. Невозможно создать .env файл."
            exit 1
        fi
    else
        print_message ".env файл уже существует"
    fi
}

# Функция для создания и запуска контейнеров
start_app() {
    print_message "Запуск приложения..."
    $DOCKER_COMPOSE_CMD up -d --build
    print_message "Приложение запущено! Доступно по адресу:"
    print_message "- API: http://localhost:5000"
    print_message "- Swagger UI: http://localhost:5000/swagger"
    print_message "- Админер (управление БД): http://localhost:8080"
    print_message "Данные для входа в Админер:"
    print_message "  Система: PostgreSQL"
    print_message "  Сервер: db"
    print_message "  Логин: postgres"
    print_message "  Пароль: postgres"
    print_message "  База данных: document_management"
}

# Функция для остановки контейнеров
stop_app() {
    print_message "Остановка приложения..."
    $DOCKER_COMPOSE_CMD down
    print_message "Приложение остановлено"
}

# Функция для просмотра логов
show_logs() {
    print_message "Отображение логов приложения (Ctrl+C для выхода)..."
    $DOCKER_COMPOSE_CMD logs -f
}

# Функция для просмотра статуса
show_status() {
    print_message "Статус контейнеров:"
    $DOCKER_COMPOSE_CMD ps
}

# Функция для удаления контейнеров и данных
cleanup() {
    print_warning "Эта команда удалит все контейнеры и данные. Продолжить? (y/n)"
    read -r answer
    if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
        print_message "Удаление всех контейнеров и данных..."
        $DOCKER_COMPOSE_CMD down -v
        print_message "Очистка выполнена"
    else
        print_message "Операция отменена"
    fi
}

# Основное меню
case "$1" in
    start)
        create_env_file
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        stop_app
        create_env_file
        start_app
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    cleanup)
        cleanup
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|logs|status|cleanup}"
        echo "  start   - Создать и запустить контейнеры"
        echo "  stop    - Остановить контейнеры"
        echo "  restart - Перезапустить контейнеры"
        echo "  logs    - Показать логи приложения"
        echo "  status  - Показать статус контейнеров"
        echo "  cleanup - Удалить все контейнеры и данные"
        exit 1
        ;;
esac

exit 0