# create_missing_payments.py
from school.models import Lesson, LessonAttendance, Payment
from django.db import transaction


def create_missing_payments():
    """Создает недостающие платежи за проведенные уроки"""

    print("🔍 Поиск уроков без платежей...")

    # Находим все проведенные уроки с присутствовавшими учениками
    attended_attendances = LessonAttendance.objects.filter(
        status='attended',
        lesson__status='completed'
    ).select_related('lesson', 'student__user', 'lesson__subject')

    print(f"✅ Найдено записей о посещаемости: {attended_attendances.count()}")

    created_count = 0
    skipped_count = 0

    with transaction.atomic():
        for attendance in attended_attendances:
            # Проверяем, есть ли уже платеж
            existing_payment = Payment.objects.filter(
                user=attendance.student.user,
                lesson=attendance.lesson,
                payment_type='expense'
            ).exists()

            if not existing_payment:
                # Создаем платеж
                Payment.objects.create(
                    user=attendance.student.user,
                    amount=attendance.cost,
                    payment_type='expense',
                    description=f'Оплата занятия {attendance.lesson.date} ({attendance.lesson.subject.name})',
                    lesson=attendance.lesson
                )
                created_count += 1
                print(f"✅ Создан платеж для {attendance.student.user.username} - {attendance.cost}₽")
            else:
                skipped_count += 1

    print(f"\n{'=' * 50}")
    print(f"✅ Создано платежей: {created_count}")
    print(f"⏭️ Пропущено (уже были): {skipped_count}")
    print(f"{'=' * 50}")


if __name__ == '__main__':
    create_missing_payments()