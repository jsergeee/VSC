from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Получить значение из словаря по ключу"""
    # Пробуем получить по ключу как есть
    try:
        return dictionary.get(key, 0)
    except (AttributeError, TypeError):
        # Если словарь некорректный
        return 0