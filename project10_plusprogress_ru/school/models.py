# school/models.py
import uuid
from decimal import Decimal
from datetime import datetime, date, time, timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Avg, Sum, Count
from datetime import timedelta, date
import uuid
from datetime import timedelta
from django.db.models import Sum


class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Ученик'),
        ('teacher', 'Учитель'),
        ('admin', 'Администратор'),
    )

    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField('Телефон', max_length=20, null=True)
    photo = models.ImageField('Фото', upload_to='users/', null=True, blank=True)
    patronymic = models.CharField('Отчество', max_length=50, blank=True)

    # ✅ РАСКОММЕНТИРУЕМ поле баланса
    balance = models.DecimalField('Баланс', max_digits=10, decimal_places=2, default=0)

    # ✅ Добавляем значение по умолчанию
    is_email_verified = models.BooleanField(default=False)
    email_verification_sent = models.DateTimeField(null=True, blank=True)

    # ✅ ИСПРАВЛЕННЫЕ related_name для групп и разрешений
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
            self.last_name = parts[0]
        if len(parts) >= 2:
            self.first_name = parts[1]
        if len(parts) >= 3:
            self.patronymic = ' '.join(parts[2:])

    def get_full_name(self):
        """Возвращает полное имя с отчеством"""
        full_name = super().get_full_name()
        if self.patronymic:
            return f"{full_name} {self.patronymic}".strip()
        return full_name


class EmailVerificationToken(models.Model):
    """Токен для подтверждения email"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='email_verification_token'
    )
    token = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = 'Токен подтверждения email'
        verbose_name_plural = 'Токены подтверждения email'

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Токен действует 48 часов
            self.expires_at = timezone.now() + timedelta(hours=48)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Проверяет, действителен ли токен"""
        return timezone.now() <= self.expires_at

    def __str__(self):
        return f"Токен для {self.user.email}"


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

    def get_full_name(self):
        """Возвращает полное имя учителя"""
        return self.user.get_full_name()

    def get_available_slots(self, date):
        """Возвращает доступные временные слоты учителя на указанную дату"""
        schedules = Schedule.objects.filter(
            teacher=self,
            date=date,  # Фильтруем по конкретной дате
            is_active=True
        )

        available_slots = []
        for schedule in schedules:
            existing_lessons = Lesson.objects.filter(
                teacher=self,
                date=date,
                start_time=schedule.start_time,
                status__in=['scheduled', 'completed']
            )

            if not existing_lessons.exists():
                available_slots.append({
                    'start': schedule.start_time,
                    'end': schedule.end_time,
                    'schedule_id': schedule.id
                })

        return available_slots

    def get_teacher_earnings(self, start_date=None, end_date=None):
        """ отладка """
        print(f"\n🔍 get_teacher_earnings для {self.user.get_full_name()}")
        print(f"   Период: {start_date} - {end_date}")

        lessons = Lesson.objects.filter(
            teacher=self,
            status='completed',
            date__gte=start_date,
            date__lte=end_date
        )

        print(f"   Найдено уроков: {lessons.count()}")
        for lesson in lessons:
            print(f"   - {lesson.date}: {lesson.subject.name}")
            for attendance in lesson.attendance.filter(status='attended'):
                print(
                    f" * {attendance.student.user.get_full_name()}: cost={attendance.cost}, teacher_payment={attendance.teacher_payment_share}")

        """Возвращает статистику по заработку учителя за период"""
        from django.db.models import Sum
        from .models import Payment

        payments = Payment.objects.filter(
            user=self.user,
            payment_type='teacher_payment'
        )

        salaries = Payment.objects.filter(
            user=self.user,
            payment_type='teacher_salary'
        )

        if start_date:
            payments = payments.filter(created_at__date__gte=start_date)
            salaries = salaries.filter(created_at__date__gte=start_date)
        if end_date:
            payments = payments.filter(created_at__date__lte=end_date)
            salaries = salaries.filter(created_at__date__lte=end_date)

        total_payments = payments.aggregate(Sum('amount'))['amount__sum'] or 0
        total_salaries = salaries.aggregate(Sum('amount'))['amount__sum'] or 0

        return {
            'total_payments': float(total_payments),
            'total_salaries': float(total_salaries),
            'net_income': float(total_payments - total_salaries),  # Чистый доход
            'payments_count': payments.count(),
            'salaries_count': salaries.count(),
        }

    def get_teacher_earnings(self, start_date, end_date):
        """
        Возвращает статистику выплат учителю за период
        """
        print(f"\n{'─' * 40}")
        print(f"🔍 get_teacher_earnings для {self.user.get_full_name()}")
        print(f"   Период: {start_date} - {end_date}")

        from .models import Lesson

        # Получаем все проведенные уроки учителя за период
        lessons = Lesson.objects.filter(
            teacher=self,
            status='completed',
            date__gte=start_date,
            date__lte=end_date
        ).prefetch_related('attendance__student__user')

        print(f"   Найдено уроков: {lessons.count()}")

        total_payments = 0  # Стоимость уроков
        total_salaries = 0  # Выплаты учителю
        total_attended = 0  # Счетчик attended
        total_debt = 0  # Счетчик debt

        if lessons.count() > 0:
            print(f"   📋 Детализация уроков:")
            for lesson in lessons:
                print(f"      📅 {lesson.date} (ID: {lesson.id}): {lesson.subject.name}")
                print(f"         Статус урока: {lesson.status}")

                attendances = lesson.attendance.all()
                print(f"         Всего записей: {attendances.count()}")

                for attendance in attendances:
                    # Считаем все, у кого есть teacher_payment_share
                    if attendance.teacher_payment_share > 0:
                        status_symbol = '✅' if attendance.status == 'attended' else '⚠️'
                        print(f"         {status_symbol} {attendance.student.user.get_full_name()}:")
                        print(
                            f"            status={attendance.status}, cost={attendance.cost}, teacher_payment={attendance.teacher_payment_share}")

                        if attendance.status == 'attended':
                            total_attended += 1
                        elif attendance.status == 'debt':
                            total_debt += 1

                        total_payments += float(attendance.cost)
                        total_salaries += float(attendance.teacher_payment_share)
        else:
            print(f"   ❌ Нет проведенных уроков за период")

        net_income = total_payments - total_salaries

        result = {
            'total_payments': total_payments,
            'total_salaries': total_salaries,
            'net_income': net_income,
            'payments_count': lessons.count(),
            'salaries_count': lessons.count(),
            'stats': {
                'attended': total_attended,
                'debt': total_debt,
                'total': total_attended + total_debt
            }
        }

        print(f"\n   📊 СТАТИСТИКА ПО СТАТУСАМ:")
        print(f"      ✅ Присутствовало: {total_attended}")
        print(f"      ⚠️ Задолженность: {total_debt}")
        print(f"      📊 Всего записей: {total_attended + total_debt}")
        print(f"   ✅ РЕЗУЛЬТАТ: {result}")
        print(f"{'─' * 40}\n")

        return result


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

    # ===== БАЛАНС (опционально, можете удалить если не нужен) =====
    def get_balance(self):
        """Возвращает текущий баланс ученика из связанного пользователя"""
        return self.user.balance

    @property
    def balance(self):
        """Текущий баланс ученика (property для доступа как student.balance)"""
        return self.user.balance

    # ===== ДЕПОЗИТЫ =====
    @property
    def total_deposits(self):
        """Сумма всех депозитов ученика"""
        from django.db.models import Sum
        return self.deposits.aggregate(Sum('amount'))['amount__sum'] or 0

    @property
    def deposits_count(self):
        """Количество депозитов"""
        return self.deposits.count()

    # ===== СТАТИСТИКА ПО УРОКАМ =====
    @property
    def total_attended_cost(self):
        """Сумма всех оплаченных уроков"""
        from django.db.models import Sum
        return self.lesson_attendance.filter(
            status='attended'
        ).aggregate(Sum('cost'))['cost__sum'] or 0

    @property
    def total_debt_cost(self):
        """Сумма всех уроков в долг"""
        from django.db.models import Sum
        return self.lesson_attendance.filter(
            status='debt'
        ).aggregate(Sum('cost'))['cost__sum'] or 0

    @property
    def total_lessons_cost(self):
        """Общая стоимость всех уроков (оплаченные + долги)"""
        return self.total_attended_cost + self.total_debt_cost

    @property
    def attended_lessons_count(self):
        """Количество оплаченных уроков"""
        return self.lesson_attendance.filter(status='attended').count()

    @property
    def debt_lessons_count(self):
        """Количество уроков в долг"""
        return self.lesson_attendance.filter(status='debt').count()

    @property
    def total_lessons_count(self):
        """Общее количество уроков"""
        return self.lesson_attendance.count()

    # ===== СТАТИСТИКА ПО ДАТАМ =====
    def get_lessons_by_period(self, start_date=None, end_date=None):
        """Возвращает уроки за период"""
        queryset = self.lesson_attendance.all()

        if start_date:
            queryset = queryset.filter(lesson__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(lesson__date__lte=end_date)

        return queryset

    def get_stats_by_period(self, start_date=None, end_date=None):
        """Статистика за период"""
        lessons = self.get_lessons_by_period(start_date, end_date)

        from django.db.models import Sum
        return {
            'total': lessons.count(),
            'attended': lessons.filter(status='attended').count(),
            'debt': lessons.filter(status='debt').count(),
            'attended_cost': lessons.filter(status='attended').aggregate(Sum('cost'))['cost__sum'] or 0,
            'debt_cost': lessons.filter(status='debt').aggregate(Sum('cost'))['cost__sum'] or 0,
            'total_cost': lessons.aggregate(Sum('cost'))['cost__sum'] or 0,
        }

    # ===== УЧИТЕЛЯ И ЗАМЕТКИ =====
    def get_teachers_list(self):
        """Список учителей ученика"""
        return ", ".join([t.user.get_full_name() for t in self.teachers.all()])

    def get_teacher_notes(self):
        """Возвращает заметки учителей об этом ученике"""
        return self.teacher_notes.all()

    # ===== ПОЛНОЕ ИМЯ =====
    def get_full_name(self):
        """Возвращает полное имя ученика"""
        return self.user.get_full_name()

    # ===== ИНФОРМАЦИЯ ДЛЯ АДМИНКИ =====
    @property
    def last_lesson_date(self):
        """Дата последнего урока"""
        last = self.lesson_attendance.order_by('-lesson__date').first()
        return last.lesson.date if last else None

    @property
    def last_lesson_subject(self):
        """Предмет последнего урока"""
        last = self.lesson_attendance.order_by('-lesson__date').first()
        return last.lesson.subject.name if last else None


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
    date = models.DateField('Дата', null=True, blank=True)
    start_time = models.TimeField('Время начала')
    end_time = models.TimeField('Время окончания')
    is_active = models.BooleanField('Активно', default=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписания'
        ordering = ['date', 'start_time']
        unique_together = ['teacher', 'date', 'start_time']  # Защита от дубликатов

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

    # ===== ВАЖНО: ВМЕСТО ОДНОГО УЧЕНИКА ТЕПЕРЬ МНОГИЕ =====
    students = models.ManyToManyField(
        Student,
        through='LessonAttendance',
        related_name='lessons',
        verbose_name='Ученики'
    )

    # Временное поле для совместимости (удалим позже)
    student_old = models.ForeignKey(
        Student,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lessons_old',
        verbose_name='Ученик (старое поле)'
    )
    # =======================================================

    # Поля для отслеживания переносов
    rescheduled_from = models.DateTimeField('Перенесено с', null=True, blank=True)
    rescheduled_to = models.DateTimeField('Перенесено на', null=True, blank=True)
    rescheduled_reason = models.TextField('Причина переноса', blank=True)

    date = models.DateField('Дата')
    start_time = models.TimeField('Время начала')
    end_time = models.TimeField('Время окончания')
    duration = models.IntegerField('Длительность (минут)', default=60)

    # Базовые финансовые поля (для удобства, могут переопределяться в LessonAttendance)
    base_cost = models.DecimalField('Базовая стоимость', max_digits=10, decimal_places=2, default=0)
    base_teacher_payment = models.DecimalField('Базовая выплата учителю', max_digits=10, decimal_places=2, default=0)

    # Поле для типа расчета
    price_type = models.CharField(
        'Тип оплаты',
        max_length=20,
        choices=[
            ('fixed', 'Фиксированная за всех'),
            ('per_student', 'За каждого ученика'),
            ('individual', 'Индивидуальная для каждого'),
        ],
        default='per_student'
    )

    meeting_link = models.URLField('Ссылка на занятие', blank=True)
    meeting_platform = models.CharField('Платформа', max_length=50, blank=True)

    # Поле для видео
    video_room = models.CharField(
        'Комната для видео',
        max_length=100,
        blank=True,
        null=True,
        help_text='Уникальный идентификатор комнаты для Jitsi Meet'
    )

    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField('Заметки', blank=True)

    # Пометка, что урок групповой (для быстрых фильтров)
    is_group = models.BooleanField('Групповой урок', default=False)

    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Занятие'
        verbose_name_plural = 'Занятия'
        ordering = ['-date', '-start_time']

    def __str__(self):
        students_count = self.students.count()
        if students_count == 0:
            return f"{self.subject} - {self.date} {self.start_time} (нет учеников)"
        elif students_count == 1:
            student = self.students.first()
            return f"{self.subject} - {self.date} {self.start_time} ({student.user.get_full_name()})"
        else:
            return f"{self.subject} - {self.date} {self.start_time} (группа {students_count} чел.)"

    def save(self, *args, **kwargs):
        # Автоматически вычисляем длительность
        if self.start_time and self.end_time:
            try:
                from datetime import datetime
                # Используем date из самого урока, если есть
                if self.date:
                    start = datetime.combine(self.date, self.start_time)
                    end = datetime.combine(self.date, self.end_time)
                else:
                    # Если даты нет, используем сегодня
                    start = datetime.combine(datetime.today(), self.start_time)
                    end = datetime.combine(datetime.today(), self.end_time)

                self.duration = int((end - start).total_seconds() / 60)
            except (TypeError, ValueError) as e:
                # Если ошибка - оставляем длительность по умолчанию
                print(f"Ошибка при вычислении длительности урока {self.id}: {e}")
                pass

        # Автоматически генерируем комнату для видео при создании
        if not self.video_room and not self.pk:
            import uuid
            self.video_room = f"lesson-{uuid.uuid4().hex[:8]}"

        # Автоматически ставим пометку группового урока
        if self.pk:
            if self.students.count() > 1:
                self.is_group = True
            else:
                self.is_group = False

        super().save(*args, **kwargs)

    def get_total_cost(self):
        """Общая стоимость урока для всех учеников"""
        if self.price_type == 'fixed':
            return self.base_cost
        elif self.price_type == 'per_student':
            return self.base_cost * self.students.count()
        else:
            # Индивидуальная - суммируем из записей посещаемости
            return sum(a.cost for a in self.attendance.all())

    def get_total_teacher_payment(self):
        """Общая выплата учителю за урок"""
        if self.price_type == 'individual':
            return sum(a.teacher_payment_share for a in self.attendance.all())
        else:
            return self.base_teacher_payment

    def mark_as_completed(self, report_data=None, attended_students=None):
        """
        Отмечает занятие как проведенное и создает отчет с учетом явки

        Args:
            report_data: словарь с данными отчета
            attended_students: список ID attendance присутствующих учеников

        Returns:
            LessonReport: созданный отчет или None
        """
        from .models import LessonReport, Payment, LessonAttendance

        self.status = 'completed'
        self.save()

        # ✅ НЕ МЕНЯЕМ СТАТУСЫ - они уже установлены в view!
        # Просто обрабатываем платежи и выплаты

        total_teacher_payment = 0
        attended_count = 0

        for attendance in self.attendance.filter(status='attended'):  # Берем уже отмеченных
            attended_count += 1
            total_teacher_payment += attendance.teacher_payment_share

            # Проверяем баланс ученика
            if attendance.student.user.balance >= attendance.cost:
                attendance.student.user.balance -= attendance.cost
                attendance.student.user.save()

                Payment.objects.create(
                    user=attendance.student.user,
                    amount=attendance.cost,
                    payment_type='expense',
                    description=f'Оплата занятия {self.date} ({self.subject.name})',
                    lesson=self
                )
            else:
                # Не хватает денег - создаем уведомление
                from .models import Notification
                Notification.objects.create(
                    user=attendance.student.user,
                    title='⚠️ Недостаточно средств',
                    message=f'На вашем балансе недостаточно средств для оплаты урока {self.date}. Пополните баланс.',
                    notification_type='system'
                )
                # Статус оставляем 'attended' - ученик был, но должен деньги

        # Начисляем выплату учителю (за всех присутствующих)
        self.teacher.wallet_balance += total_teacher_payment
        self.teacher.save()

        print(f"✅ Урок {self.id} завершен. Присутствовало: {attended_count}, выплата: {total_teacher_payment}")

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
        import uuid

        # Сохраняем информацию о переносе
        self.rescheduled_from = datetime.combine(self.date, self.start_time)
        self.status = 'rescheduled'
        self.save()

        # Создаем новое занятие
        new_lesson = Lesson.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            format=self.format,
            schedule=self.schedule,
            date=new_date,
            start_time=new_start_time,
            end_time=new_end_time,
            base_cost=self.base_cost,
            base_teacher_payment=self.base_teacher_payment,
            price_type=self.price_type,
            meeting_link=self.meeting_link,
            meeting_platform=self.meeting_platform,
            video_room=f"lesson-{uuid.uuid4().hex[:8]}",
            status='scheduled',
            notes=f"Перенесено с {self.date} {self.start_time}. Причина: {reason}",
            rescheduled_from=datetime.combine(self.date, self.start_time),
            rescheduled_reason=reason
        )

        # Копируем учеников
        for attendance in self.attendance.all():
            LessonAttendance.objects.create(
                lesson=new_lesson,
                student=attendance.student,
                cost=attendance.cost,
                discount=attendance.discount,
                teacher_payment_share=attendance.teacher_payment_share,
                status='registered'
            )

        return new_lesson

    def get_finance_stats(self):
        """Возвращает финансовую статистику урока (для совместимости с helper-классами)"""
        from django.db.models import Sum

        stats = {
            'total_cost': self.attendance.aggregate(Sum('cost'))['cost__sum'] or 0,
            'teacher_payment': self.attendance.aggregate(Sum('teacher_payment_share'))[
                                   'teacher_payment_share__sum'] or 0,
            'students_total': self.attendance.count(),
            'students_attended': self.attendance.filter(status='attended').count(),
            'students_debt': self.attendance.filter(status='debt').count(),
            'students_absent': self.attendance.filter(status='absent').count(),
            'students_registered': self.attendance.filter(status='registered').count(),
        }
        return stats


class LessonAttendance(models.Model):
    """Посещаемость и оплата ученика на уроке"""
    STATUS_CHOICES = [
        ('registered', 'Зарегистрирован'),
        ('attended', 'Присутствовал'),
        ('absent', 'Отсутствовал'),
        ('debt', 'Задолженность'),
    ]

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='attendance', verbose_name='Урок')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='lesson_attendance',
                                verbose_name='Ученик')

    # Индивидуальные настройки для этого ученика
    cost = models.DecimalField('Стоимость для ученика', max_digits=10, decimal_places=2)
    discount = models.DecimalField('Скидка %', max_digits=5, decimal_places=2, default=0)
    teacher_payment_share = models.DecimalField(
        'Доля выплаты учителю',
        max_digits=10,
        decimal_places=2,
        help_text='Сколько учитель получает за этого ученика'
    )

    # Статусы
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='registered')
    attendance_confirmed = models.BooleanField('Посещение подтверждено', default=False)
    registered_at = models.DateTimeField('Зарегистрирован', auto_now_add=True)

    class Meta:
        unique_together = ['lesson', 'student']
        verbose_name = 'Посещаемость урока'
        verbose_name_plural = 'Посещаемость уроков'

    def __str__(self):
        return f"{self.student} - {self.lesson} [{self.status}]"

    def save(self, *args, **kwargs):
        # Автоматически рассчитываем стоимость, если не указана
        if not self.cost:
            if self.lesson.price_type == 'fixed':
                total_students = self.lesson.attendance.count() or 1
                self.cost = self.lesson.base_cost / total_students
            elif self.lesson.price_type == 'per_student':
                self.cost = self.lesson.base_cost
            # Для individual оставляем как есть

        # Автоматически рассчитываем долю учителя, если не указана
        if not self.teacher_payment_share:
            if self.lesson.price_type == 'individual':
                # По умолчанию учитель получает 70% от стоимости урока
                self.teacher_payment_share = self.cost * Decimal('0.7')
            else:
                total_students = self.lesson.attendance.count() or 1
                self.teacher_payment_share = self.lesson.base_teacher_payment / total_students

        super().save(*args, **kwargs)


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
        ('teacher_payment', 'Начисление учителю', 'Зарплата учителя'),
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


class Payment(models.Model):
    PAYMENT_TYPE_CHOICES = (
        ('income', 'Пополнение'),
        ('expense', 'Списание'),
        ('teacher_payment', 'Начисление учителю'),  # ← Убрал второе значение
        ('teacher_salary', 'Зарплата учителя'),  # ← Добавил отдельную строку
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


class Notification(models.Model):
    """Система уведомлений для пользователей"""
    NOTIFICATION_TYPES = (
        ('lesson_reminder', '🔔 Напоминание о занятии'),
        ('lesson_canceled', '❌ Занятие отменено'),
        ('lesson_completed', '✅ Занятие проведено'),
        ('payment_received', '💰 Поступление средств'),
        ('payment_withdrawn', '💸 Списание средств'),
        ('material_added', '📚 Новый материал'),
        ('homework_assigned', '📝 Новое задание'),
        ('feedback_received', '⭐ Новая оценка'),
        ('system', '⚙ Системное уведомление'),
        ('homework_assigned', '📝 Новое задание'),
        ('homework_submitted', '📤 Задание сдано'),
        ('homework_checked', '✅ Задание проверено'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Пользователь'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок'
    )
    message = models.TextField(
        verbose_name='Сообщение'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='system',
        verbose_name='Тип уведомления'
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Прочитано'
    )
    link = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Ссылка'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Истекает'
    )
    payment = models.ForeignKey(
        'Payment', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='notifications'
    )
    

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.title}"

    def mark_as_read(self):
        """Отметить как прочитанное"""
        self.is_read = True
        self.save()

    @classmethod
    def get_unread_count(cls, user):
        """Количество непрочитанных уведомлений для пользователя"""
        return cls.objects.filter(user=user, is_read=False).count()


class LessonFeedback(models.Model):
    """Обратная связь по уроку от ученика"""
    RATING_CHOICES = [
        (1, '⭐ Ужасно'),
        (2, '⭐⭐ Плохо'),
        (3, '⭐⭐⭐ Нормально'),
        (4, '⭐⭐⭐⭐ Хорошо'),
        (5, '⭐⭐⭐⭐⭐ Отлично'),
    ]

    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.CASCADE,
        related_name='feedback',
        verbose_name='Урок'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        verbose_name='Ученик'
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        verbose_name='Учитель'
    )
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        verbose_name='Оценка'
    )
    comment = models.TextField(
        verbose_name='Комментарий',
        blank=True,
        help_text='Что понравилось? Что можно улучшить?'
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name='Публичный отзыв',
        help_text='Показывать на сайте?'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата оценки'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Оценка урока'
        verbose_name_plural = 'Оценки уроков'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['teacher', '-created_at']),
            models.Index(fields=['student', '-created_at']),
            models.Index(fields=['rating']),
        ]

    def __str__(self):
        return f"{self.student} оценил {self.teacher} на {self.rating}⭐"

    def save(self, *args, **kwargs):
        # При создании оценки создаем уведомление
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            self.create_notifications()

    def create_notifications(self):
        """Создает уведомления для учителя и админа"""
        from .models import Notification

        # Уведомление учителю
        Notification.objects.create(
            user=self.teacher.user,
            title=f'⭐ Новая оценка: {self.rating}/5',
            message=f'Ученик {self.student.user.get_full_name()} оценил урок по {self.lesson.subject.name}. Комментарий: {self.comment[:50]}...',
            notification_type='feedback_received',
            link=f'/teacher/feedbacks/#feedback-{self.id}'
        )

        # Уведомление админам
        admin_users = User.objects.filter(role='admin')
        for admin in admin_users:
            Notification.objects.create(
                user=admin,
                title=f'⭐ Новая оценка: {self.rating}/5',
                message=f'Учитель: {self.teacher.user.get_full_name()}, Ученик: {self.student.user.get_full_name()}, Предмет: {self.lesson.subject.name}',
                notification_type='feedback_received',
                link=f'/admin/school/lessonfeedback/{self.id}/change/'
            )


class TeacherRating(models.Model):
    """Агрегированный рейтинг учителя"""
    teacher = models.OneToOneField(
        Teacher,
        on_delete=models.CASCADE,
        related_name='rating_stats',
        verbose_name='Учитель'
    )
    average_rating = models.FloatField(
        default=0,
        verbose_name='Средний балл'
    )
    total_feedbacks = models.IntegerField(
        default=0,
        verbose_name='Всего оценок'
    )
    rating_5_count = models.IntegerField(default=0, verbose_name='5⭐')
    rating_4_count = models.IntegerField(default=0, verbose_name='4⭐')
    rating_3_count = models.IntegerField(default=0, verbose_name='3⭐')
    rating_2_count = models.IntegerField(default=0, verbose_name='2⭐')
    rating_1_count = models.IntegerField(default=0, verbose_name='1⭐')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Рейтинг учителя'
        verbose_name_plural = 'Рейтинги учителей'

    def __str__(self):
        return f"{self.teacher}: {self.average_rating:.1f}⭐ ({self.total_feedbacks} оценок)"

    def update_stats(self):
        """Обновляет статистику из всех оценок"""
        feedbacks = LessonFeedback.objects.filter(teacher=self.teacher)
        self.total_feedbacks = feedbacks.count()

        if self.total_feedbacks > 0:
            self.average_rating = feedbacks.aggregate(Avg('rating'))['rating__avg'] or 0
            self.rating_5_count = feedbacks.filter(rating=5).count()
            self.rating_4_count = feedbacks.filter(rating=4).count()
            self.rating_3_count = feedbacks.filter(rating=3).count()
            self.rating_2_count = feedbacks.filter(rating=2).count()
            self.rating_1_count = feedbacks.filter(rating=1).count()
        else:
            self.average_rating = 0
            self.rating_5_count = self.rating_4_count = self.rating_3_count = self.rating_2_count = self.rating_1_count = 0

        self.save()


class Homework(models.Model):
    """Домашнее задание"""
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='homeworks',
        verbose_name='Урок'
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='given_homeworks',
        verbose_name='Учитель'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='homeworks',
        verbose_name='Ученик'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        verbose_name='Предмет'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    description = models.TextField(
        verbose_name='Описание задания'
    )
    attachments = models.FileField(
        upload_to='homeworks/attachments/',
        blank=True,
        null=True,
        verbose_name='Файл с заданием'
    )
    deadline = models.DateTimeField(
        verbose_name='Срок сдачи'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата выдачи'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно'
    )

    class Meta:
        verbose_name = 'Домашнее задание'
        verbose_name_plural = 'Домашние задания'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'deadline']),
            models.Index(fields=['teacher', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.student.user.get_full_name()} ({self.deadline.strftime('%d.%m.%Y')})"

    def get_status(self):
        """Возвращает статус задания для ученика"""
        try:
            submission = self.submission
            if submission.status == 'submitted':
                return 'submitted'
            elif submission.status == 'checked':
                return 'checked'
        except HomeworkSubmission.DoesNotExist:
            pass

        if timezone.now() > self.deadline:
            return 'overdue'
        return 'pending'

    def get_status_display(self):
        status = self.get_status()
        statuses = {
            'pending': '⏳ Ожидает выполнения',
            'submitted': '📤 Выполнено, ожидает проверки',
            'checked': '✅ Проверено',
            'overdue': '⚠️ Просрочено',
        }
        return statuses.get(status, status)


class HomeworkSubmission(models.Model):
    """Выполненное домашнее задание"""
    STATUS_CHOICES = [
        ('submitted', 'Отправлено на проверку'),
        ('checked', 'Проверено'),
    ]

    homework = models.OneToOneField(
        Homework,
        on_delete=models.CASCADE,
        related_name='submission',
        verbose_name='Задание'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Ученик'
    )
    answer_text = models.TextField(
        verbose_name='Текст ответа',
        blank=True
    )
    file = models.FileField(
        upload_to='homeworks/submissions/',
        verbose_name='Файл с работой',
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='submitted',
        verbose_name='Статус'
    )
    grade = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Оценка'
    )
    teacher_comment = models.TextField(
        blank=True,
        verbose_name='Комментарий учителя'
    )
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата сдачи'
    )
    checked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата проверки'
    )

    class Meta:
        verbose_name = 'Выполненное задание'
        verbose_name_plural = 'Выполненные задания'

    def __str__(self):
        return f"Решение: {self.homework.title} - {self.student}"

    def save(self, *args, **kwargs):
        if self.pk is None:
            # Создание уведомления при сдаче
            self.create_notification()
        super().save(*args, **kwargs)

    def create_notification(self):
        """Уведомление учителю о сданном задании"""
        from .models import Notification
        Notification.objects.create(
            user=self.homework.teacher.user,
            title='📝 Сдано домашнее задание',
            message=f"{self.student.user.get_full_name()} сдал задание: {self.homework.title}",
            notification_type='homework_submitted',
            link=f'/teacher/homework/{self.homework.id}/'
        )


class GroupLesson(models.Model):
    """Групповое занятие"""
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='group_lessons', verbose_name='Учитель')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name='Предмет')
    format = models.ForeignKey(LessonFormat, on_delete=models.SET_NULL, null=True, verbose_name='Формат')

    date = models.DateField('Дата')
    start_time = models.TimeField('Время начала')
    end_time = models.TimeField('Время окончания')
    duration = models.IntegerField('Длительность (минут)', default=60)

    # Финансовая модель группы
    price_type = models.CharField(
        'Тип оплаты',
        max_length=20,
        choices=[
            ('fixed', 'Фиксированная за группу'),
            ('per_student', 'За каждого ученика'),
        ],
        default='per_student'
    )
    base_price = models.DecimalField('Базовая стоимость', max_digits=10, decimal_places=2,
                                     help_text='Для per_student: цена за одного, для fixed: цена за всю группу')
    teacher_payment = models.DecimalField('Начисление учителю', max_digits=10, decimal_places=2,
                                          help_text='Базовая выплата (может корректироваться в зависимости от числа учеников)')

    meeting_link = models.URLField('Ссылка на занятие', blank=True)
    meeting_platform = models.CharField('Платформа', max_length=50, blank=True)
    video_room = models.CharField('Комната для видео', max_length=100, blank=True, null=True)

    status = models.CharField('Статус', max_length=20, choices=Lesson.STATUS_CHOICES, default='scheduled')
    notes = models.TextField('Заметки', blank=True)

    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Групповое занятие'
        verbose_name_plural = 'Групповые занятия'
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"{self.subject.name} - {self.date} {self.start_time} ({self.students_count()} уч.)"

    def students_count(self):
        return self.enrollments.filter(status__in=['registered', 'attended']).count()

    def get_total_cost(self):
        """Общая стоимость занятия для всех учеников"""
        if self.price_type == 'fixed':
            return self.base_price
        else:
            return self.base_price * self.students_count()

    def get_teacher_payment(self):
        """Выплата учителю (может зависеть от числа учеников)"""
        # Здесь можно добавить логику: например, бонус за большее число учеников
        return self.teacher_payment

    def save(self, *args, **kwargs):
        # Автоматически вычисляем длительность
        if self.start_time and self.end_time:
            from datetime import datetime
            start = datetime.combine(datetime.today(), self.start_time)
            end = datetime.combine(datetime.today(), self.end_time)
            self.duration = int((end - start).total_seconds() / 60)
        super().save(*args, **kwargs)

    def mark_as_completed(self):
        """Завершить групповое занятие"""
        self.status = 'completed'
        self.save()

        # Списать деньги с учеников и начислить учителю
        from .models import Payment

        total_payment = 0
        for enrollment in self.enrollments.filter(status='attended'):
            # Списываем с ученика
            if enrollment.student.user.balance >= enrollment.cost_to_pay:
                enrollment.student.user.balance -= enrollment.cost_to_pay
                enrollment.student.user.save()

                Payment.objects.create(
                    user=enrollment.student.user,
                    amount=enrollment.cost_to_pay,
                    payment_type='expense',
                    description=f'Оплата группового занятия {self.date} ({self.subject.name})',
                )
                total_payment += enrollment.cost_to_pay
            else:
                enrollment.status = 'debt'
                enrollment.save()

        # Начисляем учителю (здесь можно определить процент от собранной суммы)
        teacher_income = total_payment * 0.7  # например, 70% от собранного
        self.teacher.wallet_balance += teacher_income
        self.teacher.save()


class GroupEnrollment(models.Model):
    """Запись ученика на групповое занятие"""
    STATUS_CHOICES = [
        ('registered', 'Зарегистрирован'),
        ('attended', 'Присутствовал'),
        ('absent', 'Отсутствовал'),
        ('debt', 'Задолженность'),
    ]

    group_lesson = models.ForeignKey(GroupLesson, on_delete=models.CASCADE, related_name='enrollments',
                                     verbose_name='Групповое занятие')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='group_enrollments',
                                verbose_name='Ученик')

    # Индивидуальные настройки для этого ученика
    cost_to_pay = models.DecimalField('Стоимость для ученика', max_digits=10, decimal_places=2,
                                      help_text='Может отличаться от базовой (скидка, акция)')
    discount = models.DecimalField('Скидка %', max_digits=5, decimal_places=2, default=0)

    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='registered')
    attendance_confirmed = models.BooleanField('Посещение подтверждено', default=False)

    registered_at = models.DateTimeField('Зарегистрирован', auto_now_add=True)

    class Meta:
        verbose_name = 'Запись на группу'
        verbose_name_plural = 'Записи на группы'
        unique_together = ['group_lesson', 'student']

    def __str__(self):
        return f"{self.student} - {self.group_lesson} [{self.status}]"

    def save(self, *args, **kwargs):
        # Если не указана индивидуальная стоимость, рассчитываем по правилам группы
        if not self.cost_to_pay:
            if self.group_lesson.price_type == 'fixed':
                # Фиксированная цена делится на всех зарегистрированных
                total_students = self.group_lesson.enrollments.count()
                self.cost_to_pay = self.group_lesson.base_price / max(total_students, 1)
            else:
                self.cost_to_pay = self.group_lesson.base_price
        super().save(*args, **kwargs)


# school/models.py

class ScheduleTemplate(models.Model):
    """Шаблон расписания для создания повторяющихся уроков"""
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='schedule_templates',
                                verbose_name='Учитель')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name='Предмет')
    format = models.ForeignKey(LessonFormat, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Формат')

    # Время урока
    start_time = models.TimeField('Время начала')
    end_time = models.TimeField('Время окончания')
    duration = models.IntegerField('Длительность (минут)', default=60, editable=False)

    # Повторение
    repeat_type = models.CharField(
        'Тип повторения',
        max_length=20,
        choices=[
            ('single', 'Разовый урок'),
            ('daily', 'Каждый день'),
            ('weekly', 'Каждую неделю'),
            ('biweekly', 'Раз в две недели'),
            ('monthly', 'Каждый месяц'),
        ],
        default='single'
    )

    # Дни недели (для повторяющихся)
    monday = models.BooleanField('Понедельник', default=False)
    tuesday = models.BooleanField('Вторник', default=False)
    wednesday = models.BooleanField('Среда', default=False)
    thursday = models.BooleanField('Четверг', default=False)
    friday = models.BooleanField('Пятница', default=False)
    saturday = models.BooleanField('Суббота', default=False)
    sunday = models.BooleanField('Воскресенье', default=False)

    # Дата для разового урока / период для повторяющихся
    start_date = models.DateField('Дата начала', null=True, blank=True)
    end_date = models.DateField('Дата окончания', null=True, blank=True)
    max_occurrences = models.PositiveIntegerField('Максимальное количество занятий', null=True, blank=True)

    # Ученики
    students = models.ManyToManyField(Student, through='ScheduleTemplateStudent', blank=True, verbose_name='Ученики')

    # Финансы (опционально)
    base_cost = models.DecimalField('Базовая стоимость', max_digits=10, decimal_places=2, null=True, blank=True)
    base_teacher_payment = models.DecimalField('Базовая выплата учителю', max_digits=10, decimal_places=2, null=True,
                                               blank=True)

    meeting_link = models.URLField('Ссылка на занятие', blank=True)
    meeting_platform = models.CharField('Платформа', max_length=50, blank=True)

    notes = models.TextField('Заметки', blank=True)

    is_active = models.BooleanField('Активно', default=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Шаблон расписания'
        verbose_name_plural = 'Шаблоны расписания'

    def __str__(self):
        if self.repeat_type == 'single':
            date_str = self.start_date.strftime('%d.%m.%Y') if self.start_date else 'без даты'
            return f"{self.subject.name} - {date_str} {self.start_time}"
        else:
            days = []
            if self.monday: days.append('Пн')
            if self.tuesday: days.append('Вт')
            if self.wednesday: days.append('Ср')
            if self.thursday: days.append('Чт')
            if self.friday: days.append('Пт')
            if self.saturday: days.append('Сб')
            if self.sunday: days.append('Вс')
            days_str = ', '.join(days) if days else 'Все дни'
            return f"{self.subject.name} - {self.start_time} ({days_str})"

    # school/models.py - замените метод save() в классе ScheduleTemplate

    def save(self, *args, **kwargs):
        # ПРОВЕРЯЕМ, ЧТО ВРЕМЯ ЗАДАНО
        if self.start_time and self.end_time:
            # Конвертируем время в минуты
            start_minutes = self.start_time.hour * 60 + self.start_time.minute
            end_minutes = self.end_time.hour * 60 + self.end_time.minute

            # Вычисляем разницу
            diff = end_minutes - start_minutes

            # Если отрицательная (переход через полночь), добавляем 24 часа
            if diff < 0:
                diff += 24 * 60

            self.duration = diff
        else:
            # Если время не задано, ставим длительность по умолчанию
            self.duration = 60

        super().save(*args, **kwargs)

    def generate_lessons(self):
        """Генерирует уроки по шаблону"""
        if self.repeat_type == 'single':
            return self._create_single_lesson()
        else:
            return self._create_recurring_lessons()

    def _create_single_lesson(self):
        """Создает разовый урок"""
        from .models import Lesson, LessonAttendance

        if not self.start_date:
            return []

        lesson = Lesson.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            format=self.format,
            date=self.start_date,
            start_time=self.start_time,
            end_time=self.end_time,
            base_cost=self.base_cost or 0,
            base_teacher_payment=self.base_teacher_payment or 0,
            meeting_link=self.meeting_link,
            meeting_platform=self.meeting_platform,
            status='scheduled',
            notes=self.notes
        )

        # Добавляем учеников
        for student in self.students.all():
            LessonAttendance.objects.create(
                lesson=lesson,
                student=student,
                cost=self.base_cost or 0,
                teacher_payment_share=self.base_teacher_payment or 0
            )

        return [lesson]

    def _create_recurring_lessons(self):
        """Создает серию уроков по расписанию"""
        from datetime import timedelta, date
        from .models import Lesson, LessonAttendance

        if not self.start_date:
            return []

        generated = []
        current_date = self.start_date

        # Определяем дату окончания
        if self.end_date:
            end_date = self.end_date
        else:
            # Если дата окончания не указана - создаем на 3 месяца вперед
            end_date = self.start_date + timedelta(days=90)
            print(f"⚠️ end_date не указан, создаем уроки на 3 месяца до {end_date}")

        # Максимальное количество уроков
        max_lessons = self.max_occurrences or 20  # максимум 20 уроков по умолчанию

        count = 0
        safety_counter = 0
        MAX_SAFETY = 500  # защита от бесконечного цикла

        print(f"🔍 Генерация уроков с {current_date} по {end_date}, макс={max_lessons}")

        while current_date <= end_date and count < max_lessons and safety_counter < MAX_SAFETY:
            safety_counter += 1

            if self._should_create_lesson(current_date):
                # Проверяем, нет ли уже урока на эту дату
                existing_lesson = Lesson.objects.filter(
                    teacher=self.teacher,
                    date=current_date,
                    start_time=self.start_time
                ).first()

                if not existing_lesson:
                    lesson = Lesson.objects.create(
                        teacher=self.teacher,
                        subject=self.subject,
                        format=self.format,
                        date=current_date,
                        start_time=self.start_time,
                        end_time=self.end_time,
                        base_cost=self.base_cost or 0,
                        base_teacher_payment=self.base_teacher_payment or 0,
                        meeting_link=self.meeting_link,
                        meeting_platform=self.meeting_platform,
                        status='scheduled',
                        notes=f'Создано из шаблона #{self.id}: {self.notes}'
                    )

                    for student in self.students.all():
                        LessonAttendance.objects.create(
                            lesson=lesson,
                            student=student,
                            cost=self.base_cost or 0,
                            teacher_payment_share=self.base_teacher_payment or 0
                        )

                    generated.append(lesson)
                    count += 1
                    print(f"✅ Создан урок {count}: {current_date}")

            current_date += timedelta(days=1)

        if safety_counter >= MAX_SAFETY:
            print(f"⚠️ Достигнут лимит безопасности ({MAX_SAFETY} итераций)")

        print(f"✅ Всего создано {len(generated)} уроков")
        return generated

    def _should_create_lesson(self, date):
        """Проверяет, нужно ли создавать урок в эту дату"""
        weekday = date.weekday()

        if self.repeat_type == 'daily':
            return True
        elif self.repeat_type == 'weekly':
            return ((weekday == 0 and self.monday) or
                    (weekday == 1 and self.tuesday) or
                    (weekday == 2 and self.wednesday) or
                    (weekday == 3 and self.thursday) or
                    (weekday == 4 and self.friday) or
                    (weekday == 5 and self.saturday) or
                    (weekday == 6 and self.sunday))
        elif self.repeat_type == 'biweekly':
            weeks_diff = (date - self.start_date).days // 7
            if weeks_diff % 2 == 0:
                return ((weekday == 0 and self.monday) or
                        (weekday == 1 and self.tuesday) or
                        (weekday == 2 and self.wednesday) or
                        (weekday == 3 and self.thursday) or
                        (weekday == 4 and self.friday) or
                        (weekday == 5 and self.saturday) or
                        (weekday == 6 and self.sunday))
        elif self.repeat_type == 'monthly':
            if self.start_date:
                return date.day == self.start_date.day

        return False


class ScheduleTemplateStudent(models.Model):
    """Связь шаблона с учеником (с возможностью индивидуальных настроек)"""
    template = models.ForeignKey(ScheduleTemplate, on_delete=models.CASCADE, related_name='student_settings')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='schedule_templates')

    # Индивидуальные настройки для ученика
    individual_cost = models.DecimalField('Индивидуальная стоимость', max_digits=10, decimal_places=2, null=True,
                                          blank=True)
    individual_payment = models.DecimalField('Индивидуальная выплата', max_digits=10, decimal_places=2, null=True,
                                             blank=True)

    class Meta:
        unique_together = ['template', 'student']
        verbose_name = 'Настройка ученика в шаблоне'
        verbose_name_plural = 'Настройки учеников в шаблоне'


class StudentSubjectPrice(models.Model):
    """Индивидуальная стоимость предмета для ученика"""
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='subject_prices',
        verbose_name='Ученик'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        verbose_name='Предмет'
    )

    # Цены
    cost = models.DecimalField(
        'Стоимость урока',
        max_digits=10,
        decimal_places=2,
        help_text='Сколько платит ученик'
    )
    teacher_payment = models.DecimalField(
        'Начисление учителю',
        max_digits=10,
        decimal_places=2,
        help_text='Сколько получает учитель'
    )

    # Настройки
    discount = models.DecimalField(
        'Скидка %',
        max_digits=5,
        decimal_places=2,
        default=0,
        blank=True
    )
    valid_from = models.DateField(
        'Действует с',
        null=True, blank=True
    )
    valid_to = models.DateField(
        'Действует по',
        null=True, blank=True
    )
    is_active = models.BooleanField(
        'Активно',
        default=True
    )

    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Цена для ученика'
        verbose_name_plural = 'Цены для учеников'
        unique_together = ['student', 'subject']  # Одна цена на пару ученик+предмет
        ordering = ['student', 'subject']

    def __str__(self):
        return f"{self.student} - {self.subject}: {self.cost}₽ (выплата {self.teacher_payment}₽)"

    @classmethod
    def get_price_for(cls, student, subject):
        """Получить цену для ученика и предмета"""
        try:
            price = cls.objects.get(
                student=student,
                subject=subject,
                is_active=True
            )
            return price.cost, price.teacher_payment
        except cls.DoesNotExist:
            return None, None


class TrialRequest(models.Model):
    """Заявка на пробный урок"""
    name = models.CharField('Имя', max_length=100)
    email = models.EmailField('Email')
    phone = models.CharField('Телефон', max_length=20)
    subject = models.CharField('Предмет', max_length=50)
    created_at = models.DateTimeField('Дата заявки', auto_now_add=True)
    is_processed = models.BooleanField('Обработано', default=False)

    class Meta:
        verbose_name = 'Заявка на пробный урок'
        verbose_name_plural = 'Заявки на пробный урок'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"
