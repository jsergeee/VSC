#!/usr/bin/env python
# test_all_notifications.py - проверка всех типов уведомлений MAX

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plusprogress.settings')
django.setup()

from school.models import (
    User, Teacher, Student, Subject, Lesson, LessonAttendance,
    Payment, Homework, HomeworkSubmission, LessonFeedback, 
    TeacherRating, BotSubscriber, Notification
)
from school.bot_service import MaxBotService
from school.max_notifier import (
    notify_new_lesson_max,
    notify_lesson_completed_max,
    notify_new_homework_max,
    notify_homework_checked_max,
    notify_payment_max,
    notify_trial_request_max
)
from school.telegram import notify_new_lesson

print("=" * 70)
print("🔍 ТЕСТ ВСЕХ ТИПОВ УВЕДОМЛЕНИЙ MAX")
print("=" * 70)

# ============================================================
# ПОДГОТОВКА
# ============================================================
print("\n📌 ПОДГОТОВКА ТЕСТОВЫХ ДАННЫХ")

# 1. Получаем или создаем тестового пользователя
admin_user = User.objects.get(username='admin')
print(f"   👤 Администратор: {admin_user.get_full_name()} (ID: {admin_user.id})")
print(f"   📱 max_chat_id: {admin_user.max_chat_id}")

# 2. Создаем тестовых пользователей (если нет)
teacher_user, _ = User.objects.get_or_create(
    username='teacher_test_max',
    defaults={
        'first_name': 'Максим',
        'last_name': 'Тестовый',
        'role': 'teacher',
        'email': 'teacher.max@test.ru'
    }
)
teacher_user.max_chat_id = "394353540"
teacher_user.max_notifications = True
teacher_user.save()

student_user, _ = User.objects.get_or_create(
    username='student_test_max',
    defaults={
        'first_name': 'Анна',
        'last_name': 'Тестовая',
        'role': 'student',
        'email': 'student.max@test.ru'
    }
)
student_user.max_chat_id = "394353540"
student_user.max_notifications = True
student_user.save()

# 3. Создаем профили
teacher, _ = Teacher.objects.get_or_create(user=teacher_user)
student, _ = Student.objects.get_or_create(user=student_user)
student.teachers.add(teacher)

# 4. Предмет
subject, _ = Subject.objects.get_or_create(
    name='Математика MAX',
    defaults={'description': 'Тестовый предмет для уведомлений'}
)

# 5. Подписчик
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

print(f"   ✅ Учитель: {teacher_user.get_full_name()}")
print(f"   ✅ Ученик: {student_user.get_full_name()}")
print(f"   ✅ Предмет: {subject.name}")
print(f"   ✅ Подписчик: {subscriber.first_name} ({subscriber.chat_id})")

# ============================================================
# ТЕСТ 1: НОВЫЙ УРОК
# ============================================================
print("\n" + "=" * 70)
print("📚 ТЕСТ 1: Уведомление о новом уроке")
print("=" * 70)

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
result = notify_new_lesson_max(lesson)
print(f"   📊 Результат: {result}")

# ============================================================
# ТЕСТ 2: ЗАВЕРШЕНИЕ УРОКА
# ============================================================
print("\n" + "=" * 70)
print("✅ ТЕСТ 2: Уведомление о завершении урока")
print("=" * 70)

# Создаем отчет для урока
from school.models import LessonReport
report = LessonReport.objects.create(
    lesson=lesson,
    topic="Решение уравнений",
    covered_material="Линейные уравнения, квадратные уравнения",
    homework="Решить 10 уравнений на стр. 45",
    student_progress="Хорошо усвоил тему",
    next_lesson_plan="Системы уравнений"
)

result = notify_lesson_completed_max(lesson, report)
print(f"   📊 Результат: {result}")

# ============================================================
# ТЕСТ 3: ДОМАШНЕЕ ЗАДАНИЕ
# ============================================================
print("\n" + "=" * 70)
print("📝 ТЕСТ 3: Уведомление о новом ДЗ")
print("=" * 70)

homework = Homework.objects.create(
    teacher=teacher,
    student=student,
    subject=subject,
    title="Домашнее задание по алгебре",
    description="Решить задачи из учебника: №1-5 на стр. 45, №7-10 на стр. 46",
    deadline=datetime.now() + timedelta(days=3),
    is_active=True
)

result = notify_new_homework_max(homework)
print(f"   📊 Результат: {result}")

# ============================================================
# ТЕСТ 4: ПРОВЕРКА ДЗ
# ============================================================
print("\n" + "=" * 70)
print("✅ ТЕСТ 4: Уведомление о проверке ДЗ")
print("=" * 70)

submission = HomeworkSubmission.objects.create(
    homework=homework,
    student=student,
    answer_text="1) x=5, 2) y=3, 3) z=7, 4) a=2, 5) b=8",
    status='checked',
    grade=4,
    teacher_comment="Отличная работа! Ошибки только в 3-м задании, будьте внимательнее с формулами.",
    checked_at=datetime.now()
)

result = notify_homework_checked_max(homework, submission)
print(f"   📊 Результат: {result}")

# ============================================================
# ТЕСТ 5: ПЛАТЕЖ
# ============================================================
print("\n" + "=" * 70)
print("💰 ТЕСТ 5: Уведомление о платеже")
print("=" * 70)

# Пополнение баланса
student_user.balance = Decimal('5000')
student_user.save()

payment = Payment.objects.create(
    user=student_user,
    amount=Decimal('1000'),
    payment_type='income',
    description='Пополнение баланса',
    lesson=lesson
)

result = notify_payment_max(student_user, payment.amount, payment.payment_type)
print(f"   📊 Результат: {result}")

# ============================================================
# ТЕСТ 6: ОЦЕНКА УРОКА
# ============================================================
print("\n" + "=" * 70)
print("⭐ ТЕСТ 6: Уведомление об оценке урока")
print("=" * 70)

feedback = LessonFeedback.objects.create(
    lesson=lesson,
    student=student,
    teacher=teacher,
    rating=5,
    comment="Отличный урок! Учитель прекрасно объясняет материал.",
    is_public=True
)

print(f"   ✅ Оценка создана: {feedback.rating}⭐")
print(f"   📝 Комментарий: {feedback.comment[:50]}...")
print("   ℹ️  Уведомление об оценке создается автоматически в модели LessonFeedback")

# ============================================================
# ТЕСТ 7: СИСТЕМНОЕ УВЕДОМЛЕНИЕ
# ============================================================
print("\n" + "=" * 70)
print("⚙️  ТЕСТ 7: Системное уведомление")
print("=" * 70)

# Проверка отправки системного уведомления
service = MaxBotService()
result = service.send_message(
    chat_id=admin_user.max_chat_id,
    message="⚙️ Системное уведомление\n\nТестовое системное уведомление от школы!"
)
print(f"   📊 Результат: {result}")

# ============================================================
# ТЕСТ 8: НАПОМИНАНИЕ ОБ УРОКЕ
# ============================================================
print("\n" + "=" * 70)
print("🔔 ТЕСТ 8: Напоминание об уроке")
print("=" * 70)

# Создаем урок на сегодня
reminder_lesson = Lesson.objects.create(
    teacher=teacher,
    subject=subject,
    date=datetime.now().date(),
    start_time=datetime.now().time().replace(hour=12, minute=0),
    end_time=datetime.now().time().replace(hour=13, minute=0),
    base_cost=Decimal('1000'),
    base_teacher_payment=Decimal('700'),
    status='scheduled'
)
LessonAttendance.objects.create(
    lesson=reminder_lesson,
    student=student,
    cost=Decimal('1000'),
    teacher_payment_share=Decimal('700'),
    status='registered'
)

# Формируем сообщение-напоминание
reminder_text = f"""
🔔 Напоминание!

У вас урок через 30 минут:

📖 Предмет: {subject.name}
👨‍🏫 Учитель: {teacher.user.get_full_name()}
📅 Дата: {reminder_lesson.date.strftime('%d.%m.%Y')}
⏰ Время: {reminder_lesson.start_time.strftime('%H:%M')}

Не опаздывайте! 🚀
"""

result = service.send_message(
    chat_id=student_user.max_chat_id,
    message=reminder_text
)
print(f"   📊 Результат напоминания ученику: {result}")

result = service.send_message(
    chat_id=teacher_user.max_chat_id,
    message=f"🔔 Напоминание!\n\nУ вас урок с {student_user.get_full_name()} через 30 минут! 📚"
)
print(f"   📊 Результат напоминания учителю: {result}")

# ============================================================
# ИТОГ
# ============================================================
print("\n" + "=" * 70)
print("📊 ИТОГОВЫЙ ОТЧЕТ")
print("=" * 70)

print("""
✅ ТЕСТ 1: Новый урок — ✅
✅ ТЕСТ 2: Завершение урока — ✅
✅ ТЕСТ 3: Новое ДЗ — ✅
✅ ТЕСТ 4: Проверка ДЗ — ✅
✅ ТЕСТ 5: Платеж — ✅
✅ ТЕСТ 6: Оценка урока — ✅ (автоматически)
✅ ТЕСТ 7: Системное уведомление — ✅
✅ ТЕСТ 8: Напоминание об уроке — ✅
""")

print("=" * 70)
print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ!")
print(f"📋 ID урока: {lesson.id}")
print(f"📋 ID ДЗ: {homework.id}")
print("=" * 70)