from django.db import models

# Create your models here.
from django.db import models

class Event(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Запланировано'),
        ('completed', 'Проведено'),
        ('overdue', 'Просрочено'),
        ('cancelled', 'Отменено'),
    )
    
    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    date = models.DateField('Дата')
    start_time = models.TimeField('Время начала')
    end_time = models.TimeField('Время окончания')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-start_time']
    
    def __str__(self):
        return f"{self.title} - {self.date} {self.start_time}"