@echo off
chcp 65001 >nul
echo ========================================
echo Автоматический сканер сети
echo Запуск: %date% %time%
echo ========================================

REM Переход в директорию скрипта
cd /d "D:\VSC\project3"

REM Запуск Python скрипта
python scan-net.py

REM Сохраняем код возврата
set EXIT_CODE=%errorlevel%

if %EXIT_CODE% equ 0 (
    echo.
    echo Сканирование успешно завершено!
) else (
    echo.
    echo Сканирование завершено с ошибкой (код: %EXIT_CODE%)
)

REM Пауза только при ручном запуске
REM pause