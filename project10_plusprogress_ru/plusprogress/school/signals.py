# school/signals.py
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Lesson, Notification, User, LessonAttendance, Payment, LessonReport
from django.db.models.signals import post_save, m2m_changed, post_delete

# ИМПОРТИРУЕМ ФУНКЦИИ ИЗ TELEGRAM
from .telegram import notify_new_lesson, notify_lesson_completed, notify_payment


@receiver(m2m_changed, sender=Lesson.students.through)
def lesson_students_added(sender, instance, action, **kwargs):
    """Отправляет Telegram уведомление когда ученики добавлены к уроку"""
    if action == 'post_add':
        print("\n" + "=" * 50)
        print(f"📱 ОТПРАВКА TELEGRAM УВЕДОМЛЕНИЯ о новом уроке {instance.id}")
        print(f"   Ученики добавлены, отправляем уведомление")
        print("=" * 50 + "\n")

        # Принудительно обновляем объект из базы
        instance.refresh_from_db()

        # Отправляем Telegram уведомление
        notify_new_lesson(instance)


@receiver(post_save, sender=LessonAttendance)
def attendance_created(sender, instance, created, **kwargs):
    """Создает уведомление когда ученик добавлен к уроку"""
    if created:
        print("=" * 50)
        print(f"✅ Ученик добавлен к уроку {instance.lesson.id}")
        print(f"   Ученик: {instance.student.user.get_full_name()}")

        lesson = instance.lesson

        # Внутреннее уведомление ученику (в базе данных)
        Notification.objects.create(
            user=instance.student.user,
            title='📚 Новое занятие',
            message=f'Запланировано занятие по {lesson.subject.name} с {lesson.teacher.user.get_full_name()} на {lesson.date.strftime("%d.%m.%Y")} в {lesson.start_time.strftime("%H:%M")}',
            notification_type='lesson_reminder',
            link=f'/student/lesson/{lesson.id}/'
        )
        print(f"✅ Внутреннее уведомление ученику создано")

        # Внутреннее уведомление учителю (если первый ученик)
        if lesson.attendance.count() == 1:
            Notification.objects.create(
                user=lesson.teacher.user,
                title='📚 Новое занятие',
                message=f'Запланировано занятие по {lesson.subject.name} с учеником {instance.student.user.get_full_name()} на {lesson.date.strftime("%d.%m.%Y")} в {lesson.start_time.strftime("%H:%M")}',
                notification_type='lesson_reminder',
                link=f'/teacher/lesson/{lesson.id}/'
            )
            print(f"✅ Внутреннее уведомление учителю создано")
        print("=" * 50)


@receiver(post_save, sender=LessonReport)
def lesson_completed_notifications(sender, instance, created, **kwargs):
    """
    Сигнал для создания уведомлений при завершении урока
    """
    if created:
        lesson = instance.lesson

        print("\n" + "🔥" * 60)
        print("🔥 ЗАВЕРШЕНИЕ УРОКА - ОТПРАВКА УВЕДОМЛЕНИЙ")
        print(f"🔥 Урок ID: {lesson.id}")

        # Отправляем Telegram уведомление о завершении урока
        notify_lesson_completed(lesson, instance)

        # Внутренние уведомления
        attended_ids = []
        for a in lesson.attendance.all():
            if a.status == 'attended':
                attended_ids.append(a.id)

        if attended_ids:
            teacher_payment = sum(float(a.teacher_payment_share) for a in lesson.attendance.filter(id__in=attended_ids))

            # Внутреннее уведомление учителю
            Notification.objects.create(
                user=lesson.teacher.user,
                title='✅ Занятие проведено',
                message=f'Урок "{lesson.subject.name}" от {lesson.date} завершен. Присутствовало: {len(attended_ids)} учеников. Выплата: {teacher_payment:.0f} ₽',
                notification_type='lesson_completed',
            )

            # Внутренние уведомления ученикам
            for attendance in lesson.attendance.filter(id__in=attended_ids):
                Notification.objects.create(
                    user=attendance.student.user,
                    title='✅ Занятие проведено',
                    message=f'Урок "{lesson.subject.name}" от {lesson.date} завершен. Отчет доступен в дневнике.',
                    notification_type='lesson_completed',
                )
        else:
            print("⚠️ Нет присутствовавших - внутренние уведомления не созданы")

        print("🔥" * 60 + "\n")


@receiver(post_save, sender=Payment)
def payment_created_notification(sender, instance, created, **kwargs):
    """Отправляет уведомление о платеже"""
    if created:
        print(f"\n💰 Создан платеж: {instance.amount} ₽ ({instance.payment_type})")

        # Отправляем Telegram уведомление о платеже
        notify_payment(instance.user, instance.amount, instance.payment_type)


@receiver(post_save, sender=User)
def send_welcome_notification(sender, instance, created, **kwargs):
    """Приветственное уведомление для новых пользователей"""
    if created:
        Notification.objects.create(
            user=instance,
            title='👋 Добро пожаловать!',
            message='Рады видеть вас в школе "Плюс Прогресс"',
            notification_type='system',
            expires_at=timezone.now() + timedelta(days=30)
        )
        print(f"✅ Приветственное уведомление для {instance.username}")


@receiver(post_delete, sender=Payment)
def delete_payment_notifications(sender, instance, **kwargs):
    """Удаляет все уведомления, связанные с платежом, при его удалении"""
    print(f"\n{'💰' * 30}")
    print(f"💰 Сигнал: удаление платежа #{instance.id}")

    notifications = Notification.objects.filter(payment=instance)
    count = notifications.count()
    if count > 0:
        notifications.delete()
        print(f"   ✅ Удалено уведомлений: {count}")
    else:
        print(f"   ⚠️ Связанных уведомлений не найдено")
    print(f"{'💰' * 30}\n")