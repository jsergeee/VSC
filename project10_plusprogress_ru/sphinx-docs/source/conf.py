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