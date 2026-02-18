from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Lesson

@receiver(post_save, sender=Lesson)
def check_lesson_status(sender, instance, created, **kwargs):
    """Проверяет статус занятия при сохранении"""
    if instance.status == 'scheduled':
        instance.check_overdue()