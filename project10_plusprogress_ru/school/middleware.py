# school/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages
from .models import Student
from django.shortcuts import redirect
from django.urls import reverse
import logging
from .models import User
from django.utils import timezone
from .models import Lesson
from .models import UserActionLog
from .utils import get_client_ip


class StudentProfileMiddleware(MiddlewareMixin):
    """Проверяет наличие профиля ученика при каждом запросе"""

    def process_request(self, request):
        if request.user.is_authenticated and request.user.role == 'student':
            try:
                profile = request.user.student_profile
            except:
                Student.objects.create(user=request.user)
                request.session['profile_recreated'] = True


logger = logging.getLogger(__name__)


class EmailVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
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
        now = timezone.now()

        if self.last_check is None or (now - self.last_check).seconds > 3600:
            today = now.date()
            current_time = now.time()

            past_lessons = Lesson.objects.filter(
                status='scheduled',
                date__lt=today
            )

            today_past = Lesson.objects.filter(
                status='scheduled',
                date=today,
                start_time__lt=current_time
            )

            if past_lessons.exists():
                past_lessons.update(status='overdue')

            if today_past.exists():
                today_past.update(status='overdue')

            self.last_check = now

        return self.get_response(request)


import threading

class UserActionLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._current_user = threading.local()

    def __call__(self, request):
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
        return None


class PageViewLoggingMiddleware(MiddlewareMixin):
    """Логирование просмотров страниц"""

    def process_response(self, request, response):
        # Игнорируем статику, админку, API
        if request.path.startswith(('/static/', '/admin/', '/api/')):
            return response

        # Игнорируем файлы и медиа
        if request.path.startswith('/media/'):
            return response

        # Логируем всех (включая гостей)
        try:
            UserActionLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action_type='page_view',
                description=f'Просмотр страницы: {request.path}',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                url=request.path,
                additional_data={
                    'method': request.method,
                    'referer': request.META.get('HTTP_REFERER', ''),
                    'is_authenticated': request.user.is_authenticated
                }
            )
        except Exception as e:
            print(f"Ошибка логирования: {e}")

        return response
