from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from school.models import Lesson, Notification
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Отправляет напоминания о предстоящих занятиях'
    
    def handle(self, *args, **options):
        # Находим занятия, которые начнутся через 1 час (+- 5 минут)
        now = timezone.now()
        reminder_time = now + timedelta(hours=1)
        time_window_start = reminder_time - timedelta(minutes=5)
        time_window_end = reminder_time + timedelta(minutes=5)
        
        # Ищем занятия со статусом 'scheduled', которые начинаются через час
        lessons = Lesson.objects.filter(
            status='scheduled',
            date=now.date(),
            start_time__gte=time_window_start.time(),
            start_time__lte=time_window_end.time()
        )
        
        reminders_sent = 0
        for lesson in lessons:
            # Проверяем, не отправляли ли уже напоминание
            existing = Notification.objects.filter(
                user=lesson.student.user,
                notification_type='lesson_reminder',
                created_at__date=now.date(),
                message__contains=f"через 1 час"
            ).exists()
            
            if not existing:
                # Уведомление ученику
                Notification.objects.create(
                    user=lesson.student.user,
                    title='🔔 Через 1 час занятие!',
                    message=f'Через 1 час начинается занятие по {lesson.subject.name} с {lesson.teacher.user.get_full_name()}. Ссылка для подключения: {lesson.meeting_link}',
                    notification_type='lesson_reminder',
                    link=lesson.meeting_link
                )
                
                # Отправляем email, если есть адрес
                if lesson.student.user.email:
                    send_mail(
                        subject=f'Напоминание: занятие через 1 час',
                        message=f'Здравствуйте, {lesson.student.user.first_name}!\n\nЧерез 1 час начинается занятие по {lesson.subject.name} с {lesson.teacher.user.get_full_name()}.\n\nСсылка для подключения: {lesson.meeting_link}\n\nХорошего занятия!',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[lesson.student.user.email],
                        fail_silently=True,
                    )
                
                reminders_sent += 1
                self.stdout.write(f"Напоминание отправлено {lesson.student.user.get_full_name()} о занятии в {lesson.start_time}")
        
        self.stdout.write(self.style.SUCCESS(f'Отправлено {reminders_sent} напоминаний'))