#!/bin/bash

# Проверка наличия директории
check_dir() {
    if [ ! -d "$1" ]; then
        echo "Директория $2 не найдена в проекте"
        exit 1
    fi
}

# Определяем корень проекта
PROJECT_ROOT=$(git rev-parse --show-toplevel)

# Путь к папке dashboards
DASHBOARDS_DIR="$PROJECT_ROOT/grafana/dashboards"

# Проверяем, существует ли папка dashboards
check_dir "$DASHBOARDS_DIR" "grafana/dashboards"

# Установим флаг для завершения при любой ошибке
set -e

# Копируем папку dashboards на сервер
scp -P $VPS_SSH_PORT -r "$DASHBOARDS_DIR" $VPS_USER@$VPS_SERVER_IP:ChatGPT_Telegram_Bot/
if [ $? -ne 0 ]; then
    echo "Ошибка при копировании папки dashboards на сервер"
    exit 1
fi

echo "Папка dashboards успешно скопирована на сервер"
