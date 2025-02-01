#!/bin/bash

# Проверка наличия переменной в .env
check_env_var() {
    if [ -z "$1" ]; then
        echo "Переменная $2 не найдена в .env файле"
        exit 1
    fi
}

# Проверяем, существует ли файл .env
if [ ! -f .env ]; then
    echo ".env файл не найден. Завершаем выполнение."
    exit 1
fi

# Загружаем переменные окружения из файла .env, исключая комментарии и пустые строки
set -a  # Автоматически экспортировать все переменные
source <(grep -v '^\s*#' .env | grep -v '^\s*$')
set +a  # Отключить автоматический экспорт

check_env_var "$VPS_SERVER_IP" "VPS_SERVER_IP"
check_env_var "$VPS_SSH_PORT" "VPS_SSH_PORT"
check_env_var "$VPS_USER" "VPS_USER"

# Установим флаг для завершения при любой ошибке
set -e

# Создаем временную копию .env
cp .env .env.temp

# Меняем ENVIRONMENT=dev на ENVIRONMENT=prod только в временном файле
sed -i 's/^ENVIRONMENT=dev$/ENVIRONMENT=prod/' .env.temp

# Копируем временный .env файл на сервер
scp -P $VPS_SSH_PORT .env.temp $VPS_USER@$VPS_SERVER_IP:ChatGPT_Telegram_Bot/.env
if [ $? -ne 0 ]; then
    echo "Ошибка при копировании .env файла на сервер"
    exit 1
fi

# Удаляем временный файл
rm .env.temp

echo ".env файл успешно скопирован на сервер"
