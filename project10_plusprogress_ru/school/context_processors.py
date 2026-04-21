# school/context_processors.py
from django.urls import resolve

def lk_admin_processor(request):
    """
    Определяет, находится ли пользователь в ЛК или админке
    """
    context = {
        'is_lk': False,
        'is_admin': False,
    }
    
    path = request.path
    
    # Проверяем админку
    if path.startswith('/admin/'):
        context['is_admin'] = True
        return context
    
    if not request.user.is_authenticated:
        return context
    
    # Список путей личного кабинета
    lk_paths = [
        '/dashboard/',
        '/profile/',
        '/teacher/',
        '/student/',
        '/materials/',
        '/lessons/',
        '/schedule/',
        '/calendar/',
        '/payments/',
    ]
    
    for lk_path in lk_paths:
        if path.startswith(lk_path):
            context['is_lk'] = True
            break
    
    return context