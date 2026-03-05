# Используем официальный образ Python 3.10 (стабильная версия)
FROM python:3.10-slim

# Отключаем буферизацию вывода (чтобы логи сразу появлялись)
ENV PYTHONUNBUFFERED=1

# ⚡ КРИТИЧЕСКИ ВАЖНО: ограничиваем OpenBLAS одним потоком
# Это навсегда решит проблему с "Resource temporarily unavailable"
ENV OPENBLAS_NUM_THREADS=1
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV NUMEXPR_NUM_THREADS=1

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Копируем весь проект внутрь контейнера
COPY . .

# Собираем статические файлы (чтобы админка работала)
RUN python manage.py collectstatic --noinput

# Открываем порт, на котором будет работать приложение
EXPOSE 8000

# Команда для запуска (используем Gunicorn вместо runserver)
CMD ["gunicorn", "plusprogress.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]