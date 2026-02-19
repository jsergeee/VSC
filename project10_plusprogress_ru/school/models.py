# school/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta, datetime


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
    
    # Добавьте эти строки для решения конфликта
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
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
    
    def get_full_name(self):
        """Возвращает полное имя с отчеством"""
        full_name = super().get_full_name()
        if self.patronymic:
            return f"{full_name} {self.patronymic}".strip()
        return full_name


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
        return self.user.get_full_name() or self.user.username
    
    def get_available_slots(self, date):
        """Возвращает доступные временные слоты учителя на указанную дату"""
        day = date.weekday()
        schedules = Schedule.objects.filter(
            teacher=self,
            day_of_week=day,
            is_active=True
        )
        
        available_slots = []
        for schedule in schedules:
            # Проверяем, не занято ли это время
            existing_lessons = Lesson.objects.filter(
                teacher=self,
                date=date,
                start_time__gte=schedule.start_time,
                end_time__lte=schedule.end_time,
                status__in=['scheduled', 'completed']
            )
            
            if not existing_lessons.exists():
                available_slots.append({
                    'start': schedule.start_time,
                    'end': schedule.end_time,
                    'schedule_id': schedule.id
                })
        
        return available_slots


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

   
    def get_balance(self):
        """Возвращает текущий баланс ученика (депозиты - списания за занятия)"""
        from django.db.models import Sum
        from .models import Lesson  # Импортируем внутри метода
        
        # Сумма всех депозитов
        total_deposits = self.deposits.aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Сумма всех проведенных занятий
        total_lessons = Lesson.objects.filter(
            student=self,
            status='completed'
        ).aggregate(Sum('cost'))['cost__sum'] or 0
        
        return total_deposits - total_lessons
    
    def get_teacher_notes(self):
        """Возвращает заметки учителей об этом ученике"""
        return self.teacher_notes.all()
class LessonFormat(models.Model):
    name = models.CharField('Название', max_length=100)
    description = models.TextField('Описание', blank=True)
    
    class Meta:
        verbose_name = 'Формат занятия'
        verbose_name_plural = 'Форматы занятий'
    
    def __str__(self):
        return self.name
    
    def get_balance(self):
        """Возвращает текущий баланс ученика (депозиты - списания за занятия)"""
        from django.db.models import Sum
        
        total_deposits = self.deposits.aggregate(Sum('amount'))['amount__sum'] or 0
        
        total_lessons = Lesson.objects.filter(
            student=self,
            status='completed'
        ).aggregate(Sum('cost'))['cost__sum'] or 0
        
        return total_deposits - total_lessons
    
    def get_teacher_notes(self):
        """Возвращает заметки учителей об этом ученике"""
        return self.notes.all()


class Schedule(models.Model):
    DAY_CHOICES = [
        (0, 'Понедельник'), (1, 'Вторник'), (2, 'Среда'), (3, 'Четверг'),
        (4, 'Пятница'), (5, 'Суббота'), (6, 'Воскресенье')
    ]
    
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='schedules', verbose_name='Учитель')
    day_of_week = models.IntegerField('День недели', choices=DAY_CHOICES)
    start_time = models.TimeField('Время начала')
    end_time = models.TimeField('Время окончания')
    is_active = models.BooleanField('Активно', default=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписания'
        ordering = ['day_of_week', 'start_time']
        unique_together = ['teacher', 'day_of_week', 'start_time']  # Защита от дубликатов
    
    def __str__(self):
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        return f"{self.teacher} - {days[self.day_of_week]} {self.start_time}-{self.end_time}"
    
    def generate_lessons(self, start_date, end_date, student=None, subject=None, cost=None):
        """
        Генерирует занятия из расписания на указанный период
        
        Args:
            start_date: дата начала периода
            end_date: дата окончания периода
            student: ученик (если None, то занятие создается без ученика)
            subject: предмет (если None, берется первый предмет учителя)
            cost: стоимость (если None, берется дефолтная)
        
        Returns:
            list: список созданных занятий
        """
        from datetime import timedelta
        
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if not subject:
            subject = self.teacher.subjects.first()
        
        lessons = []
        current_date = start_date
        
        while current_date <= end_date:
            if current_date.weekday() == self.day_of_week:
                # Проверяем, нет ли уже занятия на это время
                existing = Lesson.objects.filter(
                    teacher=self.teacher,
                    date=current_date,
                    start_time=self.start_time,
                    schedule=self
                ).exists()
                
                if not existing:
                    lesson = Lesson(
                        teacher=self.teacher,
                        student=student,
                        subject=subject,
                        format=LessonFormat.objects.first(),  # или нужный формат
                        date=current_date,
                        start_time=self.start_time,
                        end_time=self.end_time,
                        duration=self.get_duration_minutes(),
                        cost=cost or self.get_default_cost(),
                        teacher_payment=self.get_teacher_payment(cost),
                        status='scheduled',
                        schedule=self  # связываем с расписанием
                    )
                    lessons.append(lesson)
            
            current_date += timedelta(days=1)
        
        # Массовое создание
        if lessons:
            return Lesson.objects.bulk_create(lessons)
        return []
    
    def get_duration_minutes(self):
        """Возвращает длительность занятия в минутах"""
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        return int((end - start).total_seconds() / 60)
    
    def get_default_cost(self):
        """Возвращает стоимость по умолчанию (можно настроить под свои нужды)"""
        # Здесь можно добавить логику расчета стоимости
        return 1000
    
    def get_teacher_payment(self, cost=None):
        """Возвращает выплату учителю"""
        if cost is None:
            cost = self.get_default_cost()
        # Например, учитель получает 70% от стоимости
        return cost * 0.7


class Lesson(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Запланировано'),
        ('completed', 'Проведено'),
        ('cancelled', 'Отменено'),
        ('no_show', 'Ученик не явился'),
        ('overdue', 'Просрочено'),
        ('rescheduled', 'Перенесено'),
    )
    
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='lessons', verbose_name='Учитель')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='lessons', verbose_name='Ученик', null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name='Предмет')
    format = models.ForeignKey(LessonFormat, on_delete=models.SET_NULL, null=True, verbose_name='Формат')
    schedule = models.ForeignKey(
        Schedule, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='lessons',
        verbose_name='Создано из расписания'
    )
        # Поля для отслеживания переносов
    rescheduled_from = models.DateTimeField('Перенесено с', null=True, blank=True)
    rescheduled_to = models.DateTimeField('Перенесено на', null=True, blank=True)
    rescheduled_reason = models.TextField('Причина переноса', blank=True)
    
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
        student_name = self.student.user.get_full_name() if self.student else 'Не назначен'
        return f"{self.subject} - {self.date} {self.start_time} ({student_name})"
    
    def save(self, *args, **kwargs):
        # Автоматически вычисляем длительность
        if self.start_time and self.end_time:
            from datetime import datetime
            start = datetime.combine(datetime.today(), self.start_time)
            end = datetime.combine(datetime.today(), self.end_time)
            self.duration = int((end - start).total_seconds() / 60)
        super().save(*args, **kwargs)
    
    def mark_as_completed(self, report_data=None):
        """
        Отмечает занятие как проведенное и создает отчет
        
        Args:
            report_data: словарь с данными отчета (topic, covered_material, homework, student_progress, next_lesson_plan)
        
        Returns:
            LessonReport: созданный отчет или None
        """
        from .models import LessonReport, Payment
        
        self.status = 'completed'
        self.save()
        
        # Создаем отчет, если переданы данные
        if report_data:
            report = LessonReport.objects.create(
                lesson=self,
                topic=report_data.get('topic', ''),
                covered_material=report_data.get('covered_material', ''),
                homework=report_data.get('homework', ''),
                student_progress=report_data.get('student_progress', ''),
                next_lesson_plan=report_data.get('next_lesson_plan', '')
            )
            
            # Начисляем выплату учителю
            self.teacher.wallet_balance += self.teacher_payment
            self.teacher.save()
            
            # Списание с баланса ученика
            if self.student:
                self.student.user.balance -= self.cost
                self.student.user.save()
                
                # Создаем запись о платеже
                Payment.objects.create(
                    user=self.student.user,
                    amount=self.cost,
                    payment_type='expense',
                    description=f'Оплата занятия {self.date} ({self.subject.name})',
                    lesson=self
                )
            
            return report
        return None
    
    def check_overdue(self):
        """
        Проверяет, просрочено ли занятие
        Возвращает True, если статус изменен на 'overdue'
        """
        from datetime import datetime
        
        if self.status != 'scheduled':
            return False
        
        lesson_datetime = datetime.combine(self.date, self.start_time)
        now = datetime.now()
        
        if lesson_datetime < now:
            self.status = 'overdue'
            self.save()
            return True
        return False
    
    def reschedule(self, new_date, new_start_time, new_end_time, reason=''):
        """Перенос занятия на новое время"""
        from datetime import datetime
        
        # Сохраняем информацию о переносе
        self.rescheduled_from = datetime.combine(self.date, self.start_time)
        self.status = 'rescheduled'
        self.save()
        
        # Создаем новое занятие
        new_lesson = Lesson.objects.create(
            teacher=self.teacher,
            student=self.student,
            subject=self.subject,
            format=self.format,
            schedule=self.schedule,
            date=new_date,
            start_time=new_start_time,
            end_time=new_end_time,
            cost=self.cost,
            teacher_payment=self.teacher_payment,
            meeting_link=self.meeting_link,
            meeting_platform=self.meeting_platform,
            status='scheduled',
            notes=f"Перенесено с {self.date} {self.start_time}. Причина: {reason}",
            rescheduled_from=datetime.combine(self.date, self.start_time),
            rescheduled_reason=reason
        )
        
        return new_lesson
    
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
    
class Material(models.Model):
    """Методические материалы"""
    MATERIAL_TYPES = (
        ('file', 'Файл'),
        ('link', 'Ссылка'),
    )
    
    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    material_type = models.CharField('Тип', max_length=10, choices=MATERIAL_TYPES, default='file')
    file = models.FileField('Файл', upload_to='materials/', null=True, blank=True)
    link = models.URLField('Ссылка', blank=True)
    
    # Кто добавил
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_materials')
    
    # Для кого (связь многие-ко-многим)
    teachers = models.ManyToManyField(Teacher, blank=True, verbose_name='Учителя')
    students = models.ManyToManyField(Student, blank=True, verbose_name='Ученики')
    subjects = models.ManyToManyField(Subject, blank=True, verbose_name='Предметы')
    
    # Для всех или нет
    is_public = models.BooleanField('Публичный', default=False)
    
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'Методический материал'
        verbose_name_plural = 'Методические материалы'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return f"/media/{self.file}" if self.file else self.link


class Deposit(models.Model):
    """Депозиты учеников (пополнения счета)"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='deposits')
    amount = models.DecimalField('Сумма', max_digits=10, decimal_places=2)
    description = models.CharField('Описание', max_length=200, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_deposits')
    created_at = models.DateTimeField('Дата', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Депозит'
        verbose_name_plural = 'Депозиты'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.amount} руб."


class StudentNote(models.Model):
    """Заметки учителя об ученике"""
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='student_notes')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='teacher_notes')
    text = models.TextField('Заметка')
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'Заметка об ученике'
        verbose_name_plural = 'Заметки об учениках'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.teacher.user.get_full_name} -> {self.student.user.get_full_name}: {self.text[:50]}"    