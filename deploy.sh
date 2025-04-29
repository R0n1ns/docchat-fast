#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка наличия необходимых команд
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 не установлен. Установите $1 и повторите попытку."
        exit 1
    fi
}

check_command docker
check_command docker-compose

# Определение переменной для команды docker-compose
if ! command -v docker-compose &> /dev/null; then
    print_warning "docker-compose не установлен. Используем 'docker compose' вместо 'docker-compose'..."
    DOCKER_COMPOSE_CMD="docker compose"
else
    DOCKER_COMPOSE_CMD="docker-compose"
fi

# Проверка наличия .env.prod файла
if [ ! -f ".env.prod" ]; then
    print_warning ".env.prod файл не найден. Создаем из .env.prod.example..."
    if [ -f ".env.prod.example" ]; then
        cp .env.prod.example .env.prod
        print_message ".env.prod файл создан из .env.prod.example"
        print_warning "Отредактируйте .env.prod файл и установите правильные значения перед продолжением."
        exit 1
    else
        print_error "Файл .env.prod.example не найден. Невозможно создать .env.prod файл."
        exit 1
    fi
fi

# Функция для деплоя в production
deploy_production() {
    print_message "Начинаем деплой в production..."
    
    # Остановка и удаление существующих контейнеров
    $DOCKER_COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml down
    
    # Сборка новых образов
    $DOCKER_COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml build
    
    # Запуск контейнеров
    $DOCKER_COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    print_message "Деплой завершен! Приложение доступно по следующим адресам:"
    print_message "- API: http://your-domain.com"
    print_message "- Swagger UI: http://your-domain.com/swagger"
}

# Функция для остановки production
stop_production() {
    print_message "Останавливаем production..."
    $DOCKER_COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml down
    print_message "Production остановлен"
}

# Функция для просмотра логов
show_logs() {
    print_message "Отображение логов приложения в production (Ctrl+C для выхода)..."
    $DOCKER_COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml logs -f
}

# Функция для резервного копирования базы данных
backup_database() {
    BACKUP_DIR="./backups"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql"
    
    # Создание директории для бэкапов, если она не существует
    mkdir -p $BACKUP_DIR
    
    print_message "Создание резервной копии базы данных..."
    docker exec -t $(docker-compose ps -q db) pg_dumpall -c -U postgres > $BACKUP_FILE
    
    if [ $? -eq 0 ]; then
        print_message "Резервная копия создана: $BACKUP_FILE"
    else
        print_error "Ошибка при создании резервной копии"
    fi
}

# Функция для восстановления базы данных из бэкапа
restore_database() {
    BACKUP_DIR="./backups"
    
    # Проверка наличия директории с бэкапами
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A $BACKUP_DIR)" ]; then
        print_error "Директория с бэкапами не найдена или пуста"
        exit 1
    fi
    
    # Список всех файлов бэкапов
    echo "Доступные бэкапы:"
    ls -1 $BACKUP_DIR | grep -E "^db_backup_[0-9]{8}_[0-9]{6}\.sql$" | cat -n
    
    # Запрос номера бэкапа для восстановления
    echo "Введите номер бэкапа для восстановления:"
    read backup_number
    
    # Получение имени файла бэкапа по номеру
    BACKUP_FILE=$(ls -1 $BACKUP_DIR | grep -E "^db_backup_[0-9]{8}_[0-9]{6}\.sql$" | sed -n "${backup_number}p")
    
    if [ -z "$BACKUP_FILE" ]; then
        print_error "Неверный номер бэкапа"
        exit 1
    fi
    
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILE}"
    
    print_warning "Будет выполнено восстановление из бэкапа: $BACKUP_FILE"
    print_warning "ВСЕ СУЩЕСТВУЮЩИЕ ДАННЫЕ БУДУТ ПЕРЕЗАПИСАНЫ! Продолжить? (y/n)"
    read confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        print_message "Операция отменена"
        exit 0
    fi
    
    print_message "Восстановление базы данных из бэкапа..."
    cat $BACKUP_FILE | docker exec -i $(docker-compose ps -q db) psql -U postgres
    
    if [ $? -eq 0 ]; then
        print_message "База данных успешно восстановлена из бэкапа"
    else
        print_error "Ошибка при восстановлении базы данных"
    fi
}

# Основное меню
case "$1" in
    deploy)
        deploy_production
        ;;
    stop)
        stop_production
        ;;
    restart)
        stop_production
        deploy_production
        ;;
    logs)
        show_logs
        ;;
    backup)
        backup_database
        ;;
    restore)
        restore_database
        ;;
    *)
        echo "Использование: $0 {deploy|stop|restart|logs|backup|restore}"
        echo "  deploy  - Развернуть приложение в production"
        echo "  stop    - Остановить production"
        echo "  restart - Перезапустить production"
        echo "  logs    - Показать логи приложения"
        echo "  backup  - Создать резервную копию базы данных"
        echo "  restore - Восстановить базу данных из резервной копии"
        exit 1
        ;;
esac

exit 0