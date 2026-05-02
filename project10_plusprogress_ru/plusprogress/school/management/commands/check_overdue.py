# school/management/commands/check_overdue.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from school.models import Lesson

class Command(BaseCommand):
    help = 'Проверяет и обновляет статус просроченных занятий'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Начинаем проверку просроченных занятий...'))
        
        now = timezone.now()
        today = now.date()
        current_time = now.time()
        
        # Находим просроченные занятия (статус scheduled, дата в прошлом)
        overdue_past = Lesson.objects.filter(
            status='scheduled',
            date__lt=today
        )
        
        # Находим просроченные занятия (сегодня, но время уже прошло)
        overdue_today = Lesson.objects.filter(
            status='scheduled',
            date=today,
            start_time__lt=current_time
        )
        
        # Объединяем и обновляем
        overdue_lessons = overdue_past | overdue_today
        count = 0
        
        for lesson in overdue_lessons:
            lesson.status = 'overdue'
            lesson.save()
            count += 1
            self.stdout.write(f"  - Просрочено: {lesson.subject.name} ({lesson.date} {lesson.start_time})")
        
        self.stdout.write(self.style.SUCCESS(f'✅ Обновлено {count} просроченных занятий'))