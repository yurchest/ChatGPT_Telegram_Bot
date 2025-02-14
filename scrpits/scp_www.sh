#!/bin/bash

# Проверка наличия директории
check_dir() {
    if [ ! -d "$1" ]; then
        echo "Директория $2 не найдена в проекте"
        exit 1
    fi
}
# Проверка наличия переменной в .env
check_env_var() {
    if [ -z "$1" ]; then
        echo "Переменная $2 не найдена в .env файле"
        exit 1
    fi
}

# Определяем корень проекта
PROJECT_ROOT=$(git rev-parse --show-toplevel)
# Путь к .env файлу
ENV_FILE="$PROJECT_ROOT/.env"
# Путь к папке www
WWW_DIR="$PROJECT_ROOT/www"

# Проверяем, существует ли папка dashboards
check_dir "$WWW_DIR" "grafana/dashboards"

# Загружаем переменные окружения из файла .env, исключая комментарии и пустые строки
set -a  # Автоматически экспортировать все переменные
source <(grep -v '^\s*#' "$ENV_FILE" | grep -v '^\s*$')
set +a  # Отключить автоматический экспорт

check_env_var "$VPS_SERVER_IP" "VPS_SERVER_IP"
check_env_var "$VPS_SSH_PORT" "VPS_SSH_PORT"
check_env_var "$VPS_USER" "VPS_USER"

# Установим флаг для завершения при любой ошибке
set -e

# Копируем папку WWW на сервер
scp -P $VPS_SSH_PORT -r "$WWW_DIR" $VPS_USER@$VPS_SERVER_IP:/var/www/html
if [ $? -ne 0 ]; then
    echo "Ошибка при копировании папки www на сервер"
    exit 1
fi

echo "Папка www успешно скопирована на сервер $VPS_SERVER_IP"