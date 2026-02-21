from .models import Lesson
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Lesson, Notification, User
from django.core.mail import send_mail
from django.conf import settings

@receiver(post_save, sender=Lesson)
def check_lesson_status(sender, instance, created, **kwargs):
    """Проверяет статус занятия при сохранении"""
    if instance.status == 'scheduled':
        instance.check_overdue()

# ✅ ВОТ ЭТОТ ДЕКОРАТОР БЫЛ ПРОПУЩЕН!
@receiver(post_save, sender=Lesson)
def create_lesson_notifications(sender, instance, created, **kwargs):
    """Создание уведомлений при создании/изменении занятия"""
    
    # При создании нового занятия
    if created:
        print(f"🔔 Сигнал сработал! Создано занятие {instance.id}")  # Для отладки
        
        # Уведомление ученику
        Notification.objects.create(
            user=instance.student.user,
            title='📚 Новое занятие',
            message=f'Запланировано занятие по {instance.subject.name} с {instance.teacher.user.get_full_name()} на {instance.date.strftime("%d.%m.%Y")} в {instance.start_time.strftime("%H:%M")}',
            notification_type='lesson_reminder',
            link=f'/student/dashboard/#schedule'
        )
        
        # Уведомление учителю
        Notification.objects.create(
            user=instance.teacher.user,
            title='📚 Новое занятие',
            message=f'Запланировано занятие с {instance.student.user.get_full_name()} по {instance.subject.name} на {instance.date.strftime("%d.%m.%Y")} в {instance.start_time.strftime("%H:%M")}',
            notification_type='lesson_reminder',
            link=f'/teacher/dashboard/'
        )
        
        print(f"✅ Уведомления созданы для ученика и учителя")
    
    # При изменении статуса (добавим обработку)
    else:
        if instance.status == 'canceled':
            # Уведомление об отмене
            for user in [instance.student.user, instance.teacher.user]:
                Notification.objects.create(
                    user=user,
                    title='❌ Занятие отменено',
                    message=f'Занятие по {instance.subject.name} на {instance.date.strftime("%d.%m.%Y")} в {instance.start_time.strftime("%H:%M")} отменено',
                    notification_type='lesson_canceled'
                )
            print(f"✅ Уведомления об отмене созданы")
        
        elif instance.status == 'completed':
            # Уведомление о проведенном занятии
            Notification.objects.create(
                user=instance.student.user,
                title='✅ Занятие проведено',
                message=f'Занятие по {instance.subject.name} с {instance.teacher.user.get_full_name()} успешно проведено. Отчет доступен в истории.',
                notification_type='lesson_completed',
                link=f'/student/dashboard/#history'
            )
            print(f"✅ Уведомление о проведении создано")

@receiver(post_save, sender=User)
def send_welcome_notification(sender, instance, created, **kwargs):
    """Приветственное уведомление для новых пользователей"""
    if created:
        Notification.objects.create(
            user=instance,
            title='👋 Добро пожаловать!',
            message='Рады видеть вас в школе "Плюс Прогресс". Здесь вы будете получать уведомления о занятиях и важных событиях.',
            notification_type='system',
            expires_at=timezone.now() + timedelta(days=30)
        )