# school/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages
from .models import Student

class StudentProfileMiddleware(MiddlewareMixin):
    """Проверяет наличие профиля ученика при каждом запросе"""
    
    def process_request(self, request):
        if request.user.is_authenticated and request.user.role == 'student':
            # Проверяем наличие профиля ученика
            try:
                # Просто проверяем существование
                profile = request.user.student_profile
            except:
                # Если профиля нет, создаем его
                Student.objects.create(user=request.user)
                # Добавляем сообщение в сессию, чтобы показать при следующем запросе
                request.session['profile_recreated'] = True