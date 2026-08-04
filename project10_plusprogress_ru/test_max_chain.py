#!/usr/bin/env python
# test_max_chain.py - пошаговая проверка цепочки уведомлений MAX

import os
import sys
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plusprogress.settings')
django.setup()

from decimal import Decimal
from school.models import User, Teacher, Student, Subject, Lesson, LessonAttendance, BotSubscriber
from school.bot_service import MaxBotService
from school.max_notifier import notify_new_lesson_max

print("=" * 60)
print("🔍 ТЕСТ ЦЕПОЧКИ УВЕДОМЛЕНИЙ MAX")
print("=" * 60)

# ============================================================
# ШАГ 1: Проверка бота
# ============================================================
print("\n📌 ШАГ 1: Проверка MaxBotService")
try:
    service = MaxBotService()
    bot = service.get_active_bot()
    if bot:
        print(f"   ✅ Бот найден: {bot.bot_name} (ID: {bot.bot_id})")
        print(f"   ✅ Токен: {bot.api_key[:20]}...")
        print(f"   ✅ Активен: {bot.is_active}")
    else:
        print("   ❌ Бот НЕ найден!")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    sys.exit(1)

# ============================================================
# ШАГ 2: Проверка chat_id пользователя
# ============================================================
print("\n📌 ШАГ 2: Проверка chat_id пользователя")
try:
    # Используем вашего пользователя (admin)
    user = User.objects.get(username='admin')
    print(f"   👤 Пользователь: {user.get_full_name()} (ID: {user.id})")
    print(f"   📱 max_chat_id: {user.max_chat_id}")
    print(f"   🔔 max_notifications: {user.max_notifications}")
    
    if not user.max_chat_id:
        print("   ⚠️ max_chat_id не установлен! Устанавливаем...")
        user.max_chat_id = "394353540"  # Ваш chat_id
        user.max_notifications = True
        user.save()
        print(f"   ✅ Установлен max_chat_id: {user.max_chat_id}")
    if not user.max_notifications:
        print("   ⚠️ max_notifications выключены! Включаем...")
        user.max_notifications = True
        user.save()
        print("   ✅ max_notifications включены")
except User.DoesNotExist:
    print("   ❌ Пользователь admin не найден!")
    sys.exit(1)

# ============================================================
# ШАГ 3: Создание тестовых данных
# ============================================================
print("\n📌 ШАГ 3: Создание тестовых данных")

# Учитель
teacher_user, _ = User.objects.get_or_create(
    username='teacher_test',
    defaults={
        'first_name': 'Тестовый',
        'last_name': 'Учитель',
        'role': 'teacher',
        'email': 'teacher@test.ru'
    }
)
if not teacher_user.max_chat_id:
    teacher_user.max_chat_id = "394353540"
    teacher_user.max_notifications = True
    teacher_user.save()

teacher, _ = Teacher.objects.get_or_create(user=teacher_user)

# Ученик
student_user, _ = User.objects.get_or_create(
    username='student_test',
    defaults={
        'first_name': 'Тестовый',
        'last_name': 'Ученик',
        'role': 'student',
        'email': 'student@test.ru'
    }
)
if not student_user.max_chat_id:
    student_user.max_chat_id = "394353540"
    student_user.max_notifications = True
    student_user.save()

student, _ = Student.objects.get_or_create(user=student_user)
student.teachers.add(teacher)

# Предмет
subject, _ = Subject.objects.get_or_create(
    name='Тестовый предмет',
    defaults={'description': 'Для теста уведомлений'}
)

# Подписчик MAX
subscriber, _ = BotSubscriber.objects.get_or_create(
    chat_id="394353540",
    defaults={
        'user': student_user,
        'first_name': student_user.first_name,
        'last_name': student_user.last_name,
        'username': student_user.username,
        'is_active': True
    }
)
if subscriber.user is None:
    subscriber.user = student_user
    subscriber.save()

print(f"   ✅ Учитель: {teacher_user.get_full_name()}")
print(f"   ✅ Ученик: {student_user.get_full_name()}")
print(f"   ✅ Предмет: {subject.name}")
print(f"   ✅ Подписчик: {subscriber.first_name} ({subscriber.chat_id})")

# ============================================================
# ШАГ 4: Прямая отправка сообщения через MaxBotService
# ============================================================
print("\n📌 ШАГ 4: Прямая отправка через MaxBotService")
try:
    result = service.send_message(
        chat_id=user.max_chat_id,
        message="🧪 Тест 1: Прямая отправка из скрипта! 🚀"
    )
    if result and result.status == 'sent':
        print(f"   ✅ Сообщение отправлено! (ID: {result.id})")
    else:
        print(f"   ❌ Ошибка отправки: {result.response if result else 'None'}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

# ============================================================
# ШАГ 5: Создание тестового урока
# ============================================================
print("\n📌 ШАГ 5: Создание тестового урока")
lesson = Lesson.objects.create(
    teacher=teacher,
    subject=subject,
    date=datetime.now().date() + timedelta(days=1),
    start_time=datetime.now().time().replace(hour=10, minute=0),
    end_time=datetime.now().time().replace(hour=11, minute=0),
    base_cost=Decimal('1000'),
    base_teacher_payment=Decimal('700'),
    status='scheduled'
)

LessonAttendance.objects.create(
    lesson=lesson,
    student=student,
    cost=Decimal('1000'),
    teacher_payment_share=Decimal('700'),
    status='registered'
)

print(f"   ✅ Урок создан: ID {lesson.id}")

# ============================================================
# ШАГ 6: Вызов notify_new_lesson_max
# ============================================================
print("\n📌 ШАГ 6: Вызов notify_new_lesson_max()")
try:
    print(f"   🔍 Вызываем notify_new_lesson_max(lesson={lesson.id})...")
    result = notify_new_lesson_max(lesson)
    print(f"   📊 Результат: {result}")
    
    if result:
        print("   ✅ Уведомление отправлено!")
    else:
        print("   ⚠️ Уведомление не отправлено (результат False)")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

# ============================================================
# ШАГ 7: Проверка подписчиков
# ============================================================
print("\n📌 ШАГ 7: Проверка подписчиков")
subscribers = BotSubscriber.objects.all()
print(f"   Всего подписчиков: {subscribers.count()}")
for sub in subscribers:
    print(f"   - {sub.first_name} (chat_id: {sub.chat_id}, user: {sub.user})")

# ============================================================
# ШАГ 8: Проверка настроек MAX в settings.py
# ============================================================
print("\n📌 ШАГ 8: Проверка настроек MAX")
from django.conf import settings
print(f"   MAX_BOT_API_URL: {getattr(settings, 'MAX_BOT_API_URL', 'НЕ НАСТРОЕН')}")
print(f"   MAX_BOT_TOKEN: {'УСТАНОВЛЕН' if getattr(settings, 'MAX_BOT_TOKEN', None) else 'НЕ НАСТРОЕН'}")
print(f"   MAX_BOT_ADMIN_CHAT_ID: {getattr(settings, 'MAX_BOT_ADMIN_CHAT_ID', 'НЕ НАСТРОЕН')}")
print(f"   MAX_BOT_ENABLED: {getattr(settings, 'MAX_BOT_ENABLED', False)}")

print("\n" + "=" * 60)
print("✅ ТЕСТ ЗАВЕРШЕН!")
print(f"📋 ID урока: {lesson.id}")
print("=" * 60)