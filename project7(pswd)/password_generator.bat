@echo off
chcp 65001 >nul
cd /d "D:\VSC\project7(pswd)"
echo Запуск генератора паролей...
echo.
python password_generator.py
echo.
pause