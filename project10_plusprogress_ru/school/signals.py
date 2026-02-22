
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Lesson, Notification, User, LessonAttendance


@receiver(post_save, sender=LessonAttendance)
def attendance_created(sender, instance, created, **kwargs):
    """Создает уведомление когда ученик добавлен к уроку"""
    if created:
        print("=" * 50)
        print(f"✅ Ученик добавлен к уроку {instance.lesson.id}")
        print(f"   Ученик: {instance.student.user.get_full_name()}")

        lesson = instance.lesson

        # Уведомление ученику
        Notification.objects.create(
            user=instance.student.user,
            title='📚 Новое занятие',
            message=f'Запланировано занятие по {lesson.subject.name} с {lesson.teacher.user.get_full_name()} на {lesson.date.strftime("%d.%m.%Y")} в {lesson.start_time.strftime("%H:%M")}',
            notification_type='lesson_reminder',
            link=f'/student/lesson/{lesson.id}/'
        )
        print(f"✅ Уведомление ученику создано")

        # Проверяем, нужно ли отправить уведомление учителю (первый ученик)
        if lesson.attendance.count() == 1:
            Notification.objects.create(
                user=lesson.teacher.user,
                title='📚 Новое занятие',
                message=f'Запланировано занятие по {lesson.subject.name} с учеником {instance.student.user.get_full_name()} на {lesson.date.strftime("%d.%m.%Y")} в {lesson.start_time.strftime("%H:%M")}',
                notification_type='lesson_reminder',
                link=f'/teacher/lesson/{lesson.id}/'
            )
            print(f"✅ Уведомление учителю создано")
        print("=" * 50)


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