# check_lessons.py
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plusprogress.settings')
django.setup()

from school.models import Student, LessonAttendance, Payment

student = Student.objects.get(id=2)

print(f"\n{'='*60}")
print(f"ПРОВЕРКА УРОКОВ УЧЕНИКА: {student.user.get_full_name()}")
print(f"{'='*60}")

# Все посещения уроков
attendances = LessonAttendance.objects.filter(student=student)
print(f"\n1. Всего записей о посещении: {attendances.count()}")
for a in attendances:
    status_icon = {
        'attended': '✅',
        'debt': '⚠️',
        'absent': '❌',
        'registered': '📝'
    }.get(a.status, '❓')
    
    print(f"   {status_icon} Урок {a.lesson.date}: {a.cost}₽ - статус: {a.status}")
    
    # Проверяем, есть ли платеж за этот урок
    payment = Payment.objects.filter(
        user=student.user,
        lesson=a.lesson,
        payment_type='expense'
    ).first()
    
    if payment:
        print(f"      💰 Платеж найден: {payment.amount}₽")
    else:
        print(f"      ❌ Платеж НЕ найден!")

# Все платежи ученика
payments = Payment.objects.filter(user=student.user).order_by('-created_at')
print(f"\n2. Все платежи ученика (всего: {payments.count()}):")
for p in payments:
    lesson_info = f" (урок {p.lesson.id})" if p.lesson else ""
    print(f"   {p.created_at.strftime('%d.%m.%Y')}: {p.amount}₽ - {p.payment_type}{lesson_info}")

print(f"\n{'='*60}")
