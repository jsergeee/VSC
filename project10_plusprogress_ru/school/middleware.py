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
        print("🔥🔥🔥 MIDDLEWARE ПРОСРОЧКИ ЗАГРУЖЕН 🔥🔥🔥")

    def __call__(self, request):
        from datetime import datetime
        from django.utils import timezone
        from school.models import Lesson
        
        now = timezone.now()
        print(f"\n🔍 ПРОВЕРКА ПРОСРОЧЕННЫХ УРОКОВ: {now}")
        print(f"   Путь запроса: {request.path}")
        
        # Проверяем раз в час
        if self.last_check is None or (now - self.last_check).seconds > 3600:
            print("⏰ НАЧИНАЕМ ПРОВЕРКУ (прошло больше часа)")
            
            today = now.date()
            current_time = now.time()
            
            print(f"📅 Сегодня: {today}, время: {current_time}")
            
            # Все запланированные уроки
            all_scheduled = Lesson.objects.filter(status='scheduled')
            print(f"📊 Всего запланированных уроков: {all_scheduled.count()}")
            
            # Уроки с прошедшей датой
            past_lessons = Lesson.objects.filter(
                status='scheduled',
                date__lt=today
            )
            past_count = past_lessons.count()
            print(f"📅 Уроков с прошедшей датой: {past_count}")
            
            # Уроки сегодня, но время уже прошло
            today_past = Lesson.objects.filter(
                status='scheduled',
                date=today,
                start_time__lt=current_time
            )
            today_count = today_past.count()
            print(f"⏰ Уроков сегодня с прошедшим временем: {today_count}")
            
            # Обновляем статусы
            if past_count > 0:
                past_lessons.update(status='overdue')
                print(f"   ✅ Обновлено {past_count} уроков с прошлыми датами")
            
            if today_count > 0:
                today_past.update(status='overdue')
                print(f"   ✅ Обновлено {today_count} сегодняшних уроков")
            
            total = past_count + today_count
            if total > 0:
                print(f"🎉 ВСЕГО ОБНОВЛЕНО: {total} уроков")
            else:
                print("✅ Просроченных уроков нет")
            
            self.last_check = now
        else:
            print(f"⏳ Пропускаем проверку, прошло {(now - self.last_check).seconds} секунд")
        
        return self.get_response(request)