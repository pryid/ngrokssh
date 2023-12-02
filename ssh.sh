#!/bin/bash

# Запуск ngrok для туннелирования порта 22
ngrok tcp 22 --authtoken YOUR_TOKEN &

# Получаем PID ngrok
NGROK_PID=$!

# Переход в директорию Python-скрипта
cd $HOME/ngrokfetch

# Запуск Python-скрипта
python ngrok_fetch.py &

# Получаем PID Python скрипта
PYTHON_PID=$!

# Ожидаем завершения этих процессов
wait $NGROK_PID
wait $PYTHON_PID
