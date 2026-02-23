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
    """
    Проверяет, подтвержден ли email пользователя.
    Не пускает неподтвержденных пользователей в личный кабинет.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Список разрешенных URL для неподтвержденных пользователей
        try:
            allowed_paths = [
                reverse('logout'),
                reverse('login'),
                reverse('register'),
                reverse('resend_verification'),
                '/admin/',
            ]

            # Добавляем verify_email с любым токеном
            verify_email_url = reverse('verify_email', args=['dummy'])
            verify_email_base = verify_email_url.replace('dummy', '')
            allowed_paths.append(verify_email_base)

        except Exception as e:
            # Если ошибка при построении URL, используем строки
            logger.error(f"Ошибка при построении URL в middleware: {e}")
            allowed_paths = [
                '/logout/',
                '/login/',
                '/register/',
                '/resend-verification/',
                '/verify-email/',
                '/admin/',
            ]

        # Для отладки
        if request.user.is_authenticated:
            print(f"\n📋 Middleware check for path: {request.path}")
            print(f"   User: {request.user.username}")
            print(f"   is_email_verified: {request.user.is_email_verified}")
            print(f"   Allowed paths: {allowed_paths}")

        if request.user.is_authenticated and not request.user.is_email_verified:
            # Проверяем, находится ли пользователь на разрешенном пути
            current_path = request.path
            allowed = False

            for path in allowed_paths:
                if current_path.startswith(path):
                    allowed = True
                    break

            print(f"   Current path: {current_path}")
            print(f"   Allowed: {allowed}")

            if not allowed:
                print(f"   ⚠️ Blocking access, redirecting to resend_verification")
                messages.warning(
                    request,
                    'Пожалуйста, подтвердите ваш email для доступа к личному кабинету. '
                    'Проверьте вашу почту (включая папку "Спам").'
                )
                return redirect('resend_verification')
            else:
                print(f"   ✅ Path allowed for unverified user")
        else:
            if request.user.is_authenticated:
                print(f"   ✅ User verified, no restrictions")

        return self.get_response(request)