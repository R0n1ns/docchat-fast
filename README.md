<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Проект защищенного ЭДО</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 40px;
            background-color: #f9f9f9;
        }
        h1, h2, h3 {
            color: #333366;
        }
        h1 {
            border-bottom: 2px solid #333366;
            padding-bottom: 10px;
        }
        ul {
            margin-left: 20px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            background-color: #fff;
            margin-bottom: 30px;
        }
        table, th, td {
            border: 1px solid #aaa;
        }
        th, td {
            padding: 10px;
            text-align: left;
        }
        .section {
            margin-bottom: 40px;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>

    <h1>Проект защищенного электронного документооборота (ЭДО)</h1>

    <div class="section">
        <h2>1. Цель проекта</h2>
        <p>Создание приложения для защищенного электронного документооборота (ЭДО), позволяющего пользователям безопасно обмениваться документами, обрабатывать их и хранить без необходимости подключения к сети Интернет.</p>
    </div>

    <div class="section">
        <h2>2. Технический результат проекта</h2>
        <p>Разработка приложения для защищенного ЭДО в рамках закрытого информационного контура, обеспечивающего сбор, хранение, обработку, обмен и предоставление конфиденциальной информации.</p>
    </div>

    <div class="section">
        <h2>3. Архитектура</h2>
        <h3>Технологический стек проекта:</h3>
        <table>
            <thead>
                <tr>
                    <th>Компонент</th>
                    <th>Технология / Решение</th>
                </tr>
            </thead>
            <tbody>
                <tr><td>Язык</td><td>Python 3.10+ (типизация, async/await)</td></tr>
                <tr><td>API framework</td><td>FastAPI (+ Uvicorn / Gunicorn)</td></tr>
                <tr><td>ORM</td><td>SQLAlchemy core + Alembic (миграции)</td></tr>
                <tr><td>БД (реляционная)</td><td>PostgreSQL</td></tr>
                <tr><td>Хранилище файлов</td><td>MinIO (S3 совместимое)</td></tr>
                <tr><td>Криптография</td><td>PyCA Cryptography (AES 256 GCM)</td></tr>
                <tr><td>Auth / SSO</td><td>FastAPI OAuth2PasswordBearer + JWT (access/refresh)</td></tr>
                <tr><td>Контейнеризация</td><td>Docker</td></tr>
                <tr><td>Оркестрация</td><td>Kubernetes</td></tr>
                <tr><td>API Gateway</td><td>FastAPI</td></tr>
                <tr><td>Логирование</td><td>EFK-stack (Elasticsearch + Fluentd + Kibana)</td></tr>
                <tr><td>Метрики / Tracing</td><td>Prometheus + Grafana + Jaeger</td></tr>
                <tr><td>Desktop-клиент (опционально)</td><td>PyQt</td></tr>
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>4. Ключевые модули и алгоритмы</h2>
        <ul>
            <li><strong>API Gateway (FastAPI):</strong> Единая точка входа, роутинг на downstream сервисы, валидация JWT, rate limiting, сбор метрик.</li>
            <li><strong>Модуль аутентификации пользователей:</strong>
                <ul>
                    <li>Форма ввода логина и пароля через корпоративную почту.</li>
                    <li>Одноразовый шестизначный код на почту.</li>
                    <li>Интеграция с LDAP.</li>
                </ul>
            </li>
            <li><strong>Модуль управления доступом:</strong>
                <ul>
                    <li>Три уровня доступа: пользователь, руководитель, администратор.</li>
                    <li>Настройка ролей через веб-интерфейс.</li>
                </ul>
            </li>
            <li><strong>Модуль безопасности передачи данных:</strong>
                <ul>
                    <li>Шифрование AES-256.</li>
                    <li>Использование TLS для защиты каналов.</li>
                </ul>
            </li>
            <li><strong>Модуль проверки целостности документов:</strong>
                <ul>
                    <li>Блокчейн или другой механизм контроля целостности.</li>
                    <li>Валидация подписей цифровыми сертификатами.</li>
                </ul>
            </li>
            <li><strong>Модуль управления журналом и статусом документов:</strong>
                <ul>
                    <li>Просмотр истории действий и отчетов.</li>
                </ul>
            </li>
            <li><strong>Модуль аналитики и мониторинга:</strong>
                <ul>
                    <li>Интеграция с Prometheus, Grafana.</li>
                    <li>Анализ активности пользователей.</li>
                </ul>
            </li>
        </ul>
    </div>

    <div class="section">
        <h2>5. Описание Desktop-приложения</h2>
        <ol>
            <li><strong>Аутентификация пользователя:</strong>
                <ul>
                    <li>Форма логина и пароля.</li>
                    <li>Запрос одноразового кода на корпоративную почту.</li>
                    <li>Хранение JWT-токенов.</li>
                    <li>Работа с электронными ключами доступа.</li>
                </ul>
            </li>
            <li><strong>Работа с документами:</strong>
                <ul>
                    <li>Загрузка и шифрование документов.</li>
                    <li>Скачивание и дешифрование.</li>
                    <li>Просмотр и редактирование метаданных.</li>
                    <li>Подписание и проверка документов.</li>
                </ul>
            </li>
            <li><strong>Управление документами:</strong>
                <ul>
                    <li>Фильтрация, поиск, версия документов.</li>
                </ul>
            </li>
            <li><strong>Журнал действий:</strong>
                <ul>
                    <li>История событий: загрузка, скачивание, ошибки и др.</li>
                </ul>
            </li>
            <li><strong>Уведомления:</strong> Локальные всплывающие уведомления о событиях.</li>
            <li><strong>Настройки приложения:</strong> Управление API-сервером, сертификатами и синхронизацией.</li>
            <li><strong>Безопасность:</strong> Шифрование, защита токенов, таймер выхода.</li>
            <li><strong>Офлайн-режим:</strong> Работа без интернета с последующей синхронизацией.</li>
            <li><strong>Обновление:</strong> Автоматическое или полуавтоматическое обновление клиента.</li>
        </ol>
    </div>

    <div class="section">
        <h2>6. План работ</h2>
        <ol>
            <li><strong>Обсуждение технологий и архитектуры:</strong>
                <ul>
                    <li>Выбор стека: Python, FastAPI, PostgreSQL, MinIO, gRPC и др.</li>
                    <li>Проектирование микросервисной архитектуры.</li>
                    <li>Определение сервисов: API Gateway, Auth Service, User Management и др.</li>
                </ul>
            </li>
            <li><strong>Разработка API сервисов:</strong>
                <ul>
                    <li>Аутентификация, работа с документами, управление пользователями.</li>
                    <li>Спецификация через OpenAPI/Swagger.</li>
                </ul>
            </li>
            <li><strong>Разработка API Gateway:</strong> JWT-проверка, rate limiting, сбор метрик.</li>
            <li><strong>Разработка мониторинга и аналитики:</strong> Интеграция Prometheus, Grafana, Loki.</li>
            <li><strong>Тестирование и автоматизация:</strong>
                <ul>
                    <li>Smoke, модульные, интеграционные тесты.</li>
                    <li>Тестирование безопасности.</li>
                </ul>
            </li>
            <li><strong>Разработка десктоп-приложения:</strong> Выбор технологии (PyQt6, Tauri, Electron), реализация ключевых функций.</li>
            <li><strong>Интеграция и тестирование:</strong> Проверка совместной работы клиента и API.</li>
            <li><strong>Нагрузочное тестирование:</strong> Тестирование устойчивости системы.</li>
            <li><strong>Документирование проекта:</strong> Техническая документация, руководства пользователей.</li>
        </ol>
    </div>

</body>
</html>
