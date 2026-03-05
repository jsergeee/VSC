import os
import sys

# ===== НАСТРОЙКИ ПУТЕЙ =====
# Путь к вашему проекту (где лежит manage.py)
project_path = '/home/c/cy51482/plusprogress'
# Путь к виртуальному окружению
venv_path = '/home/c/cy51482/plusprogress/venv'

# ===== АКТИВАЦИЯ ВИРТУАЛЬНОГО ОКРУЖЕНИЯ =====
activate_this = os.path.join(venv_path, 'bin/activate_this.py')
if os.path.exists(activate_this):
    with open(activate_this) as f:
        exec(f.read(), {'__file__': activate_this})
else:
    print("WARNING: activate_this.py not found")

# ===== ПУТЬ К ПРОЕКТУ =====
sys.path.insert(0, project_path)

# ===== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ИЗ .ENV =====
env_path = os.path.join(project_path, '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ.setdefault(key, value)

# ===== ЗАПУСК DJANGO =====
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plusprogress.settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()