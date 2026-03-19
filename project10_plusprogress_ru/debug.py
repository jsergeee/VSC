# debug.py
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plusprogress.settings')

print("1. Импортируем django...")
print("2. Вызываем django.setup()...")

try:
    django.setup()
    print("3. Django.setup() выполнен успешно!")
    
    from django.apps import apps
    print("4. Загруженные приложения:")
    for app in apps.get_app_configs():
        print(f"   - {app.name}")
except Exception as e:
    print(f"ОШИБКА: {e}")
    import traceback
    traceback.print_exc()