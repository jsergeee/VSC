# school/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages
from .models import Student
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
import logging
from .models import User
from django.utils import timezone
from .models import Lesson


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


logger = logging.getLogger(__name__)


class EmailVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Список разрешенных URL для неподтвержденных пользователей
        allowed_paths = [
            '/logout/',
            '/login/',
            '/register/',
            '/resend-verification/',
            '/verify-email/',
            '/admin/',
        ]

        if request.user.is_authenticated:
            if not request.user.is_email_verified:
                current_path = request.path
                allowed = any(current_path.startswith(path) for path in allowed_paths)

                if not allowed:
                    messages.warning(
                        request,
                        'Пожалуйста, подтвердите ваш email для доступа к личному кабинету'
                    )
                    return redirect('resend_verification')

        return self.get_response(request)


class OverdueLessonsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.last_check = None

    def __call__(self, request):
        from datetime import datetime
        from django.utils import timezone
        from school.models import Lesson

        now = timezone.now()

        # Проверяем раз в час
        if self.last_check is None or (now - self.last_check).seconds > 3600:
            today = now.date()
            current_time = now.time()

            # Уроки с прошедшей датой
            past_lessons = Lesson.objects.filter(
                status='scheduled',
                date__lt=today
            )

            # Уроки сегодня, но время уже прошло
            today_past = Lesson.objects.filter(
                status='scheduled',
                date=today,
                start_time__lt=current_time
            )

            # Обновляем статусы
            if past_lessons.exists():
                past_lessons.update(status='overdue')

            if today_past.exists():
                today_past.update(status='overdue')

            self.last_check = now

        return self.get_response(request)




# school/middleware.py - добавьте новый класс
import threading
from .models import UserActionLog

class UserActionLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Сохраняем информацию о входе/выходе в потоке
        self._current_user = threading.local()

    def __call__(self, request):
        # Сохраняем информацию о запросе
        if request.user.is_authenticated:
            request.user_action_log = {
                'user': request.user,
                'ip': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'url': request.build_absolute_uri(),
            }
        else:
            request.user_action_log = None

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Логирование входа/выхода"""
        if request.path.endswith('/login/') and request.method == 'POST':
            # Логирование входа будет в views.py после успешной аутентификации
            pass
        return None