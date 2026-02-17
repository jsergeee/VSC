# school/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Ученик'),
        ('teacher', 'Учитель'),
        ('admin', 'Администратор'),
    )
    
    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField('Телефон', max_length=20, blank=True)
    photo = models.ImageField('Фото', upload_to='users/', null=True, blank=True)
    patronymic = models.CharField('Отчество', max_length=50, blank=True)
    balance = models.DecimalField('Баланс', max_digits=10, decimal_places=2, default=0)
    
        # Добавьте этот метод
    def __str__(self):
        full_name = self.get_full_name().strip()
        if full_name:
            return full_name
        return self.username
    
    def set_full_name(self, full_name):
        """Разделяет полное имя на фамилию, имя и отчество"""
        parts = full_name.strip().split()
        if len(parts) >= 1:
            self.first_name = parts[0]
        if len(parts) >= 2:
            self.last_name = parts[1]
        if len(parts) >= 3:
            self.patronymic = ' '.join(parts[2:])
    
    # Добавьте эти строки для решения конфликта
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',  # Изменено с user_set
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',  # Изменено с user_set
        related_query_name='custom_user',
    )
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return f"{self.last_name} {self.first_name}".strip() or self.username


# Остальные модели остаются без изменений
class Subject(models.Model):
    name = models.CharField('Название', max_length=100)
    description = models.TextField('Описание', blank=True)
    
    class Meta:
        verbose_name = 'Предмет'
        verbose_name_plural = 'Предметы'
    
    def __str__(self):
        return self.name


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    subjects = models.ManyToManyField(Subject, verbose_name='Предметы')
    bio = models.TextField('Биография', blank=True)
    education = models.TextField('Образование', blank=True)
    experience = models.IntegerField('Опыт работы (лет)', default=0)
    certificate = models.FileField('Сертификат', upload_to='certificates/', null=True, blank=True)
    payment_details = models.TextField('Данные для выплат', blank=True)
    wallet_balance = models.DecimalField('Баланс кошелька', max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = 'Учитель'
        verbose_name_plural = 'Учителя'
    
    def __str__(self):
        # Возвращаем полное имя пользователя
        return self.user.get_full_name() or self.user.username

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    teachers = models.ManyToManyField(Teacher, verbose_name='Учителя', blank=True)
    parent_name = models.CharField('Имя родителя', max_length=200, blank=True)
    parent_phone = models.CharField('Телефон родителя', max_length=20, blank=True)
    notes = models.TextField('Заметки', blank=True)
    
    class Meta:
        verbose_name = 'Ученик'
        verbose_name_plural = 'Ученики'
    
    def __str__(self):
        return self.user.get_full_name() or self.user.username


class LessonFormat(models.Model):
    name = models.CharField('Название', max_length=100)
    description = models.TextField('Описание', blank=True)
    
    class Meta:
        verbose_name = 'Формат занятия'
        verbose_name_plural = 'Форматы занятий'
    
    def __str__(self):
        return self.name


class Lesson(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Запланировано'),
        ('completed', 'Проведено'),
        ('cancelled', 'Отменено'),
        ('no_show', 'Ученик не явился'),
    )
    
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='lessons', verbose_name='Учитель')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='lessons', verbose_name='Ученик')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name='Предмет')
    format = models.ForeignKey(LessonFormat, on_delete=models.SET_NULL, null=True, verbose_name='Формат')
    
    date = models.DateField('Дата')
    start_time = models.TimeField('Время начала')
    end_time = models.TimeField('Время окончания')
    duration = models.IntegerField('Длительность (минут)', default=60)
    
    cost = models.DecimalField('Стоимость', max_digits=10, decimal_places=2)
    teacher_payment = models.DecimalField('Выплата учителю', max_digits=10, decimal_places=2)
    
    meeting_link = models.URLField('Ссылка на занятие', blank=True)
    meeting_platform = models.CharField('Платформа', max_length=50, blank=True)
    
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField('Заметки', blank=True)
    
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'Занятие'
        verbose_name_plural = 'Занятия'
        ordering = ['-date', '-start_time']
    
    def __str__(self):
        return f"{self.subject} - {self.date} {self.start_time}"


class LessonReport(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='report', verbose_name='Занятие')
    topic = models.CharField('Тема занятия', max_length=200)
    covered_material = models.TextField('Пройденный материал')
    homework = models.TextField('Домашнее задание')
    student_progress = models.TextField('Прогресс ученика')
    next_lesson_plan = models.TextField('План следующего занятия', blank=True)
    
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Отчет о занятии'
        verbose_name_plural = 'Отчеты о занятиях'
    
    def __str__(self):
        return f"Отчет: {self.lesson}"


class Payment(models.Model):
    PAYMENT_TYPE_CHOICES = (
        ('income', 'Пополнение'),
        ('expense', 'Списание'),
        ('teacher_payment', 'Выплата учителю'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments', verbose_name='Пользователь')
    amount = models.DecimalField('Сумма', max_digits=10, decimal_places=2)
    payment_type = models.CharField('Тип', max_length=20, choices=PAYMENT_TYPE_CHOICES)
    description = models.CharField('Описание', max_length=200)
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Занятие')
    
    created_at = models.DateTimeField('Дата', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_payment_type_display()} - {self.amount} руб."


class Schedule(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='schedule', verbose_name='Учитель')
    day_of_week = models.IntegerField('День недели', choices=[
        (0, 'Понедельник'), (1, 'Вторник'), (2, 'Среда'), (3, 'Четверг'),
        (4, 'Пятница'), (5, 'Суббота'), (6, 'Воскресенье')
    ])
    start_time = models.TimeField('Время начала')
    end_time = models.TimeField('Время окончания')
    is_active = models.BooleanField('Активно', default=True)
    
    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписание'
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        return f"{self.teacher.user.get_full_name()} - {days[self.day_of_week]} {self.start_time}-{self.end_time}"


class TrialRequest(models.Model):
    name = models.CharField('Имя', max_length=100)
    email = models.EmailField('Email')
    phone = models.CharField('Телефон', max_length=20)
    subject = models.CharField('Предмет', max_length=50)
    created_at = models.DateTimeField('Дата заявки', auto_now_add=True)
    is_processed = models.BooleanField('Обработано', default=False)
    
    class Meta:
        verbose_name = 'Заявка на пробный урок'
        verbose_name_plural = 'Заявки на пробный урок'
    
    def __str__(self):
        return f"{self.name} - {self.subject}"