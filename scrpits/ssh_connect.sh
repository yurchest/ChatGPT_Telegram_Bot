#!/bin/bash

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

# Проверяем, существует ли файл .env
if [ ! -f "$ENV_FILE" ]; then
    echo "$ENV_FILE файл не найден. Завершаем выполнение."
    exit 1
fi

# Загружаем переменные окружения из файла .env, исключая комментарии и пустые строки
set -a  # Автоматически экспортировать все переменные
source <(grep -v '^\s*#' "$ENV_FILE" | grep -v '^\s*$')
set +a  # Отключить автоматический экспорт

check_env_var "$VPS_SERVER_IP" "VPS_SERVER_IP"
check_env_var "$VPS_SSH_PORT" "VPS_SSH_PORT"
check_env_var "$VPS_USER" "VPS_USER"

# Установим флаг для завершения при любой ошибке
set -e

# Подключаемся по SSH
ssh -p $VPS_SSH_PORT $VPS_USER@$VPS_SERVER_IP