@echo off
cd /d "D:\VSC\project6"
echo Запуск мониторинга из планировщика: %date% %time%
python "D:\VSC\project6\ping_scheduler.py"
echo Завершено: %date% %time%