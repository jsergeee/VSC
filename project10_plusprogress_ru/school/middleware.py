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

        print(f"\n📋 MIDDLEWARE CHECK:")
        print(f"   Path: {request.path}")
        print(f"   User authenticated: {request.user.is_authenticated}")

        if request.user.is_authenticated:
            print(f"   User: {request.user.username}")
            print(f"   is_email_verified: {request.user.is_email_verified}")
            print(f"   From DB: {User.objects.get(id=request.user.id).is_email_verified}")

            if not request.user.is_email_verified:
                print(f"   ❌ Email not verified")
                current_path = request.path
                allowed = any(current_path.startswith(path) for path in allowed_paths)
                print(f"   Path allowed: {allowed}")

                if not allowed:
                    print(f"   🚫 Redirecting to resend_verification")
                    messages.warning(
                        request,
                        'Пожалуйста, подтвердите ваш email для доступа к личному кабинету'
                    )
                    return redirect('resend_verification')
            else:
                print(f"   ✅ Email verified")

        return self.get_response(request)