📋 ИТОГ: Полная инструкция по настройке Sphinx
Шаг 1: Установка
powershell
pip install sphinx sphinx-rtd-theme
Шаг 2: Создание структуры
powershell
cd F:\VSC\project10_plusprogress_ru
mkdir sphinx-docs
cd sphinx-docs
sphinx-quickstart
# При запросе: разделить source и build? → Yes
# Название проекта: Plusprogress.ru
# Автор: Yakovenko Sergey
# Остальное по умолчанию
Шаг 3: Настройка source/conf.py ✅ (ваш правильный шаблон)
python
# Configuration file for the Sphinx documentation builder.

import os
import sys
import django

# Добавляем путь к корню проекта
sys.path.insert(0, os.path.abspath('../../'))

# Настраиваем Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'plusprogress.settings'
django.setup()

# -- Project information -----------------------------------------------------
project = 'Plusprogress.ru'
copyright = '2026, Yakovenko Sergey'
author = 'Yakovenko Sergey'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',      # автодокументация из кода
    'sphinx.ext.viewcode',     # ссылки на исходный код
    'sphinx.ext.napoleon',     # поддержка Google-style docstrings
    'sphinx.ext.todo',         # TODO заметки
]

templates_path = ['_templates']
exclude_patterns = []
language = 'ru'

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'  # красивая тема Read the Docs
html_static_path = ['_static']
Шаг 4: Генерация документации из кода
powershell
# Из папки sphinx-docs
cd F:\VSC\project10_plusprogress_ru\sphinx-docs

# Удалить старые файлы (если есть)
Remove-Item source\*.rst -Force -ErrorAction SilentlyContinue

# Создать новые .rst файлы из всего приложения school
sphinx-apidoc -o source ../school -f -e -M

# Собрать HTML
.\make.bat html
Шаг 5: Просмотр результата
powershell
start build\html\index.html
🎯 Что теперь у вас есть:
Инструмент	Назначение	Адрес
Swagger UI	Документация API	http://127.0.0.1:8000/api/docs/
Sphinx	Документация кода	file:///F:/.../build/html/index.html
📝 Бонус: Правила написания docstring'ов
Чтобы Sphinx красиво всё отображал, используйте такой формат:

Для модуля (в начале файла):
python
"""
Краткое описание модуля.

Подробное описание, что делает этот модуль,
какие классы содержит и для чего нужен.
"""
Для класса:
python
class MyClass:
    """
    Описание класса.
    
    :param param1: Описание параметра
    :type param1: str
    
    .. note:: Важное примечание
    """
Для метода/функции:
python
def my_function(arg1, arg2):
    """
    Краткое описание функции.
    
    :param arg1: Описание первого аргумента
    :type arg1: int
    :param arg2: Описание второго аргумента
    :type arg2: str
    :returns: Описание возвращаемого значения
    :rtype: bool
    
    Пример:
        >>> my_function(1, "test")
        True
    """
🏆 Поздравляю!
Теперь у вас профессиональная документация для Django проекта:

✅ Swagger — для API

✅ Sphinx — для всего кода

✅ Оба инструмента работают автоматически

Сохраните этот шаблон conf.py в свою библиотеку — он идеально подходит для Django проектов!

