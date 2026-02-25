from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, Prefetch, Avg
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.urls import reverse
from django.template.loader import render_to_string
from django.db import connection, transaction
from decimal import Decimal
from datetime import datetime, date, timedelta
import json
import csv
import uuid
import io
import os
import tempfile
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from weasyprint import HTML
import logging
import traceback

# Импорты моделей
from .models import (
    User, Teacher, Student, Subject, LessonFormat, Lesson,
    LessonAttendance, LessonReport, Payment, Schedule, TrialRequest,
    Material, Deposit, StudentNote, GroupLesson, GroupEnrollment,
    Notification, LessonFeedback, TeacherRating, Homework,
    HomeworkSubmission, ScheduleTemplate, ScheduleTemplateStudent,
    StudentSubjectPrice, EmailVerificationToken
)

from .forms import (
    UserRegistrationForm, UserLoginForm, TrialRequestForm,
    LessonReportForm, ProfileUpdateForm, LessonFeedbackForm,
    HomeworkForm, HomeworkSubmissionForm, HomeworkCheckForm,
    ScheduleTemplateForm
)

from .utils import send_verification_email, send_verification_success_email

logger = logging.getLogger(__name__)


# ============================================
# ЧАСТЬ 1: HELPER-КЛАССЫ ДЛЯ ФИНАНСОВЫХ РАСЧЕТОВ
# ============================================

class LessonFinanceCalculator:
    """
    ЕДИНЫЙ КАЛЬКУЛЯТОР ФИНАНСОВ ДЛЯ УРОКА
    """

    def __init__(self, lesson):
        self.lesson = lesson
        self.attendances = lesson.attendance.all()

    @property
    def total_cost(self) -> Decimal:
        """Общая стоимость урока для всех учеников"""
        return sum((a.cost for a in self.attendances), Decimal('0'))

    @property
    def teacher_payment(self) -> Decimal:
        """Общая выплата учителю за урок"""
        return sum((a.teacher_payment_share for a in self.attendances), Decimal('0'))

    @property
    def attended_cost(self) -> Decimal:
        """Стоимость только для присутствовавших"""
        return sum((a.cost for a in self.attendances if a.status == 'attended'), Decimal('0'))

    @property
    def attended_payment(self) -> Decimal:
        """Выплата учителю только за присутствовавших"""
        return sum((a.teacher_payment_share for a in self.attendances if a.status == 'attended'), Decimal('0'))

    @property
    def debt_cost(self) -> Decimal:
        """Стоимость уроков в долг"""
        return sum((a.cost for a in self.attendances if a.status == 'debt'), Decimal('0'))

    @property
    def stats(self) -> dict:
        """Полная статистика по уроку"""
        return {
            # Денежные показатели
            'total_cost': float(self.total_cost),
            'teacher_payment': float(self.teacher_payment),
            'attended_cost': float(self.attended_cost),
            'attended_payment': float(self.attended_payment),
            'debt_cost': float(self.debt_cost),

            # Количественные показатели
            'students_total': self.attendances.count(),
            'students_attended': self.attendances.filter(status='attended').count(),
            'students_debt': self.attendances.filter(status='debt').count(),
            'students_absent': self.attendances.filter(status='absent').count(),
            'students_registered': self.attendances.filter(status='registered').count(),
        }

    def get_attendance_details(self) -> list:
        """Детализация по ученикам"""
        return [
            {
                'student_id': a.student.id,
                'student_name': a.student.user.get_full_name(),
                'cost': float(a.cost),
                'teacher_payment': float(a.teacher_payment_share),
                'status': a.status,
                # УБРАЛИ balance_before и balance_after
            }
            for a in self.attendances
        ]


class PeriodFinanceCalculator:
    """
    КАЛЬКУЛЯТОР ФИНАНСОВ ЗА ПЕРИОД
    Использовать для отчетов и дашбордов
    """

    def __init__(self, lessons_queryset, payments_queryset=None):
        self.lessons = lessons_queryset
        self.payments = payments_queryset if payments_queryset is not None else Payment.objects.none()

    @property
    def lessons_stats(self) -> dict:
        """Статистика по урокам за период"""
        completed = self.lessons.filter(status='completed')

        total_cost = Decimal('0')
        total_payment = Decimal('0')

        for lesson in completed:
            calc = LessonFinanceCalculator(lesson)
            total_cost += calc.total_cost
            total_payment += calc.teacher_payment

        return {
            'total': self.lessons.count(),
            'completed': completed.count(),
            'cancelled': self.lessons.filter(status='cancelled').count(),
            'overdue': self.lessons.filter(status='overdue').count(),
            'scheduled': self.lessons.filter(status='scheduled').count(),
            'total_cost': float(total_cost),
            'teacher_payment': float(total_payment),
        }

    @property
    def payments_stats(self) -> dict:
        """Статистика по платежам за период"""
        return {
            'income': float(self.payments.filter(payment_type='income').aggregate(Sum('amount'))['amount__sum'] or 0),
            'expense': float(self.payments.filter(payment_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0),
            'teacher_payments': float(
                self.payments.filter(payment_type='teacher_payment').aggregate(Sum('amount'))['amount__sum'] or 0),
            'total': float(self.payments.aggregate(Sum('amount'))['amount__sum'] or 0),
            'count': self.payments.count(),
        }

    @property
    def school_finances(self) -> dict:
        """Финансовые показатели школы"""
        payments = self.payments_stats

        return {
            'income': payments['expense'],
            'expense': payments['teacher_payments'],
            'profit': payments['expense'] - payments['teacher_payments'],
            'profit_margin': ((payments['expense'] - payments['teacher_payments']) / payments['expense'] * 100) if
            payments['expense'] > 0 else 0
        }


class StudentFinanceHelper:
    """
    ПОМОЩНИК ПО СТАТИСТИКЕ УЧЕНИКА
    """

    def __init__(self, student):
        self.student = student
        self.user = student.user

    # УДАЛЯЕМ методы balance и debt

    def get_lessons_stats(self, days=30) -> dict:
        """Статистика по урокам за последние N дней"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        attendances = LessonAttendance.objects.filter(
            student=self.student,
            lesson__date__gte=start_date,
            lesson__date__lte=end_date
        )

        total_cost = attendances.aggregate(Sum('cost'))['cost__sum'] or 0

        return {
            'period_days': days,
            'total': attendances.count(),
            'attended': attendances.filter(status='attended').count(),
            'debt': attendances.filter(status='debt').count(),
            'total_cost': float(total_cost),
            'average_cost': float(total_cost / attendances.count()) if attendances.exists() else 0
        }

    def get_lessons_stats_by_period(self, start_date=None, end_date=None):
        """Статистика по урокам за указанный период"""
        attendances = LessonAttendance.objects.filter(
            student=self.student
        )

        if start_date:
            attendances = attendances.filter(lesson__date__gte=start_date)
        if end_date:
            attendances = attendances.filter(lesson__date__lte=end_date)

        total_cost = attendances.aggregate(Sum('cost'))['cost__sum'] or 0

        return {
            'total': attendances.count(),
            'attended': attendances.filter(status='attended').count(),
            'debt': attendances.filter(status='debt').count(),
            'total_cost': float(total_cost),
            'average_cost': float(total_cost / attendances.count()) if attendances.exists() else 0
        }


class TeacherFinanceHelper:
    """
    ПОМОЩНИК ПО ФИНАНСАМ УЧИТЕЛЯ
    """

    def __init__(self, teacher):
        self.teacher = teacher
        self.user = teacher.user

    @property
    def wallet_balance(self) -> Decimal:
        """Текущий баланс кошелька"""
        return self.teacher.wallet_balance

    def get_payment_stats(self, days=30) -> dict:
        """Статистика выплат"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        payments = Payment.objects.filter(
            user=self.user,
            payment_type='teacher_payment',
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )

        return {
            'period_days': days,
            'total': payments.aggregate(Sum('amount'))['amount__sum'] or 0,
            'count': payments.count(),
            'average': (payments.aggregate(Sum('amount'))[
                            'amount__sum'] or 0) / payments.count() if payments.exists() else 0
        }


# ============================================
# ЧАСТЬ 2: ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ПОИСКА
# ============================================

def find_teacher_by_full_name(name):
    """Поиск учителя по полному имени"""
    if not name:
        return None

    name = str(name).strip()
    if not name:
        return None

    name_parts = name.split()
    if not name_parts:
        return None

    last_name = name_parts[0]
    teachers = Teacher.objects.filter(user__last_name__icontains=last_name)

    if teachers.exists():
        if teachers.count() == 1:
            return teachers.first()

        if len(name_parts) > 1:
            first_name = name_parts[1]
            teachers = teachers.filter(user__first_name__icontains=first_name)
            if teachers.exists():
                return teachers.first()

    for teacher in Teacher.objects.all():
        full_name = teacher.user.get_full_name().lower()
        if name.lower() in full_name:
            return teacher

    return None


def find_student_by_full_name(name):
    """Поиск ученика по полному имени"""
    if not name:
        return None

    name = str(name).strip()
    if not name:
        return None

    name_parts = name.split()
    if not name_parts:
        return None

    last_name = name_parts[0]
    students = Student.objects.filter(user__last_name__icontains=last_name)

    if students.exists():
        if students.count() == 1:
            return students.first()

        if len(name_parts) > 1:
            first_name = name_parts[1]
            students = students.filter(user__first_name__icontains=first_name)
            if students.exists():
                return students.first()

    for student in Student.objects.all():
        full_name = student.user.get_full_name().lower()
        if name.lower() in full_name:
            return student

    return None


def find_teacher_by_id(teacher_id):
    """Поиск учителя по ID"""
    try:
        return Teacher.objects.get(id=int(teacher_id))
    except (ValueError, Teacher.DoesNotExist):
        return None


def find_student_by_id(student_id):
    """Поиск ученика по ID"""
    try:
        return Student.objects.get(id=int(student_id))
    except (ValueError, Student.DoesNotExist):
        return None


def create_lesson_with_prices(teacher, student, subject, date, start_time, end_time):
    """Создание урока с автоматической подстановкой цен"""

    cost, teacher_payment = StudentSubjectPrice.get_price_for(student, subject)

    if cost is None:
        cost = Decimal('1000')
    if teacher_payment is None:
        teacher_payment = cost * Decimal('0.7')

    lesson = Lesson.objects.create(
        teacher=teacher,
        subject=subject,
        date=date,
        start_time=start_time,
        end_time=end_time,
        base_cost=cost,
        base_teacher_payment=teacher_payment
    )

    LessonAttendance.objects.create(
        lesson=lesson,
        student=student,
        cost=cost,
        teacher_payment_share=teacher_payment,
        status='registered'
    )

    return lesson


# ============================================
# ЧАСТЬ 3: ОСНОВНЫЕ VIEWS (рефакторинг ключевых функций)
# ============================================

def home(request):
    """Главная страница"""
    trial_form = TrialRequestForm()
    if request.method == 'POST':
        trial_form = TrialRequestForm(request.POST)
        if trial_form.is_valid():
            trial_form.save()
            messages.success(request, 'Заявка успешно отправлена! Мы свяжемся с вами в ближайшее время.')
            return redirect('home')

    context = {
        'trial_form': trial_form,
        'subjects': Subject.objects.all(),
    }
    return render(request, 'school/home.html', context)


def register(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()

                if send_verification_email(user, request):
                    messages.success(
                        request,
                        'Регистрация прошла успешно! На ваш email отправлено письмо с подтверждением.'
                    )
                else:
                    messages.warning(
                        request,
                        'Регистрация прошла успешно, но не удалось отправить письмо подтверждения.'
                    )

                return redirect('login')

            except Exception as e:
                messages.error(request, f'Ошибка при регистрации: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        form = UserRegistrationForm()

    return render(request, 'school/register.html', {'form': form})


def user_login(request):
    """Вход в систему"""
    if request.method == 'POST':
        form = UserLoginForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(username=username, password=password)

            if user:
                if not user.is_email_verified:
                    messages.warning(
                        request,
                        'Пожалуйста, подтвердите ваш email перед входом в систему. '
                        '<a href="{}" class="alert-link">Отправить письмо повторно</a>'.format(
                            reverse('resend_verification')
                        )
                    )
                    return redirect('login')

                login(request, user)

                if user.role == 'student':
                    return redirect('student_dashboard')
                elif user.role == 'teacher':
                    return redirect('teacher_dashboard')
                else:
                    return redirect('admin:index')
            else:
                messages.error(request, 'Неверное имя пользователя или пароль')
    else:
        form = UserLoginForm()

    return render(request, 'school/login.html', {'form': form})


@login_required
def user_logout(request):
    """Выход из системы"""
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    """Редирект на соответствующий дашборд"""
    user = request.user

    if user.role == 'student':
        return redirect('student_dashboard')
    elif user.role == 'teacher':
        return redirect('teacher_dashboard')
    else:
        return redirect('admin:index')


@login_required
def student_dashboard(request):
    """Личный кабинет ученика"""
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    user = User.objects.get(pk=request.user.pk)

    try:
        student = user.student_profile
    except:
        student = Student.objects.create(user=user)
        messages.info(request, 'Профиль ученика был создан')

    student.refresh_from_db()

    # ✅ Баланс
    balance = float(user.balance)

    # Статистика по урокам
    attended_lessons = LessonAttendance.objects.filter(
        student=student,
        status='attended'
    ).count()

    attended_cost = LessonAttendance.objects.filter(
        student=student,
        status='attended'
    ).aggregate(Sum('cost'))['cost__sum'] or 0

    debt_lessons = LessonAttendance.objects.filter(
        student=student,
        status='debt'
    ).count()

    debt_cost = LessonAttendance.objects.filter(
        student=student,
        status='debt'
    ).aggregate(Sum('cost'))['cost__sum'] or 0

    teachers = student.teachers.all()
    recent_deposits = student.deposits.all()[:5]

    # ✅ ДЛЯ КАЛЕНДАРЯ: ВСЕ уроки (без ограничений)
    all_lessons = Lesson.objects.filter(
        attendance__student=student
    ).select_related('teacher__user', 'subject', 'format').distinct().order_by('date', 'start_time')

    # ⚡⚡⚡ ИСПРАВЛЕНИЕ 1: Проверка просроченных уроков ⚡⚡⚡
    from datetime import datetime
    updated_count = 0
    for lesson in all_lessons:
        if lesson.status == 'scheduled':
            lesson_datetime = datetime.combine(lesson.date, lesson.start_time)
            if lesson_datetime < datetime.now():
                lesson.status = 'overdue'
                lesson.save()
                updated_count += 1
                print(f"⚠️ Урок {lesson.id} автоматически помечен как просроченный (из дашборда)")

    if updated_count > 0:
        print(f"✅ Обновлено {updated_count} просроченных уроков")
        # ⚡⚡⚡ ИСПРАВЛЕНИЕ 2: Обновляем queryset после изменений ⚡⚡⚡
        all_lessons = Lesson.objects.filter(
            attendance__student=student
        ).select_related('teacher__user', 'subject', 'format').distinct().order_by('date', 'start_time')

    # ✅ ДЛЯ СПИСКА: ближайшие 10 уроков (только запланированные)
    upcoming_lessons_list = Lesson.objects.filter(
        attendance__student=student,
        date__gte=date.today(),
        status='scheduled'
    ).select_related('teacher__user', 'subject', 'format').distinct().order_by('date', 'start_time')[:10]

    past_lessons = Lesson.objects.filter(
        attendance__student=student,
        status='completed'
    ).select_related('teacher__user', 'subject').distinct().order_by('-date')[:10]

    materials = Material.objects.filter(
        Q(students=student) | Q(is_public=True) | Q(teachers__in=teachers)
    ).distinct()[:20]

    recent_homeworks = Homework.objects.filter(
        student=student,
        is_active=True
    ).exclude(
        submission__status='checked'
    ).select_related('teacher__user', 'subject').order_by('deadline')[:4]

    # ✅ Групповые уроки ВСЕ (без фильтра по статусу)
    group_lessons = GroupLesson.objects.filter(
        enrollments__student=student
    ).select_related('teacher__user', 'subject')

    # Календарь - цвета в зависимости от статуса
    calendar_events = []

    # Цвета для разных статусов
    status_colors = {
        'scheduled': '#007bff',  # синий
        'completed': '#28a745',  # зеленый
        'cancelled': '#dc3545',  # красный
        'overdue': '#fd7e14',  # оранжевый
        'rescheduled': '#ffc107',  # желтый
        'no_show': '#6c757d',  # серый
    }

    # ✅ Добавляем ВСЕ обычные уроки
    for lesson in all_lessons:
        color = status_colors.get(lesson.status, '#6c757d')
        calendar_events.append({
            'title': f"{lesson.subject.name} - {lesson.teacher.user.last_name}",
            'start': f"{lesson.date}T{lesson.start_time}",
            'end': f"{lesson.date}T{lesson.end_time}",
            'url': f"/lesson/{lesson.id}/",
            'backgroundColor': color,
            'borderColor': color,
            'textColor': 'white'
        })
        print(f"✅ Добавлен урок: {lesson.date} - {lesson.subject.name} (статус: {lesson.status})")

    # ✅ Добавляем ВСЕ групповые уроки
    for lesson in group_lessons:
        color = status_colors.get(lesson.status, '#6c757d')
        calendar_events.append({
            'title': f"👥 {lesson.subject.name} (группа)",
            'start': f"{lesson.date}T{lesson.start_time}",
            'end': f"{lesson.date}T{lesson.end_time}",
            'url': f"/student/group-lesson/{lesson.id}/",
            'backgroundColor': color,
            'borderColor': color,
            'textColor': 'white'
        })
        print(f"✅ Добавлен групповой урок: {lesson.date} - {lesson.subject.name} (статус: {lesson.status})")

    # ✅ Отладка
    print(f"\n📊 ВСЕГО ОБЫЧНЫХ УРОКОВ: {all_lessons.count()}")
    print(f"📊 ВСЕГО ГРУППОВЫХ УРОКОВ: {group_lessons.count()}")
    print(f"📅 СОЗДАНО СОБЫТИЙ КАЛЕНДАРЯ: {len(calendar_events)}")

    context = {
        'student': student,
        'balance': balance,
        'attended_lessons': attended_lessons,
        'attended_cost': float(attended_cost),
        'debt_lessons': debt_lessons,
        'debt_cost': float(debt_cost),
        'recent_deposits': recent_deposits,
        'upcoming_lessons': upcoming_lessons_list,  # Для списка
        'past_lessons': past_lessons,
        'teachers': teachers,
        'materials': materials,
        'recent_homeworks': recent_homeworks,
        'calendar_events': calendar_events,  # Для календаря
    }

    return render(request, 'school/student/dashboard.html', context)


@login_required
def teacher_dashboard(request):
    """Личный кабинет учителя - РЕФАКТОРИНГ"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    teacher = request.user.teacher_profile
    today = timezone.now().date()

    # ИСПОЛЬЗУЕМ TeacherFinanceHelper
    finance_helper = TeacherFinanceHelper(teacher)

    students = teacher.student_set.all().select_related('user')

    upcoming_lessons = Lesson.objects.filter(
        teacher=teacher,
        date__gte=today,
        status='scheduled'
    ).select_related('subject').order_by('date', 'start_time')[:20]

    today_lessons = Lesson.objects.filter(
        teacher=teacher,
        date=today,
        status='scheduled'
    ).select_related('subject').order_by('start_time')

    past_lessons = Lesson.objects.filter(
        teacher=teacher,
        status='completed'
    ).select_related('subject').order_by('-date')[:20]

    all_lessons = Lesson.objects.filter(
        teacher=teacher
    ).select_related(
        'subject'
    ).prefetch_related(
        Prefetch(
            'attendance',
            queryset=LessonAttendance.objects.select_related('student__user')
        )
    ).order_by('date', 'start_time')

    materials = Material.objects.filter(
        Q(teachers=teacher) | Q(created_by=request.user)
    ).distinct().order_by('-created_at')[:20]

    recent_payments = Payment.objects.filter(
        user=request.user,
        payment_type='teacher_payment'
    ).order_by('-created_at')[:10]

    # Календарь с ИСПОЛЬЗОВАНИЕМ LessonFinanceCalculator
    calendar_events = []

    for lesson in all_lessons:
        calc = LessonFinanceCalculator(lesson)
        stats = calc.stats

        if lesson.status == 'completed':
            bg_color = '#28a745'
        elif lesson.status == 'cancelled':
            bg_color = '#dc3545'
        elif lesson.status == 'overdue':
            bg_color = '#fd7e14'
        elif lesson.date < today and lesson.status == 'scheduled':
            bg_color = '#ffc107'
        elif lesson.date == today:
            bg_color = '#007bff'
        else:
            bg_color = '#6c757d'

        if stats['students_total'] == 0:
            title = "Нет учеников"
        elif stats['students_total'] == 1:
            student = lesson.attendance.first().student
            title = student.user.get_full_name()
        else:
            title = f"{stats['students_total']} учеников"

        calendar_events.append({
            'title': title,
            'start': f"{lesson.date}T{lesson.start_time}",
            'end': f"{lesson.date}T{lesson.end_time}",
            'url': f"/teacher/lesson/{lesson.id}/",
            'backgroundColor': bg_color,
            'borderColor': bg_color,
            'textColor': 'white',
            'finance': {  # Добавляем финансы в событие
                'total_cost': stats['total_cost'],
                'teacher_payment': stats['teacher_payment']
            }
        })

    context = {
        'teacher': teacher,
        'finance': {
            'wallet_balance': float(finance_helper.wallet_balance),
            'payment_stats': finance_helper.get_payment_stats(30)
        },
        'students': students,
        'upcoming_lessons': upcoming_lessons,
        'today_lessons': today_lessons,
        'past_lessons': past_lessons,
        'all_lessons': all_lessons,
        'materials': materials,
        'recent_payments': recent_payments,
        'calendar_events': calendar_events,
    }

    return render(request, 'school/teacher/dashboard.html', context)


@login_required
def teacher_lesson_detail(request, lesson_id):
    """Детальная страница урока для учителя - РЕФАКТОРИНГ"""
    lesson = get_object_or_404(Lesson, id=lesson_id)

    if request.user.role != 'teacher' or lesson.teacher.user != request.user:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    # ИСПОЛЬЗУЕМ LessonFinanceCalculator
    calculator = LessonFinanceCalculator(lesson)
    stats = calculator.stats

    attendances = lesson.attendance.all().select_related('student__user')

    report = None
    if hasattr(lesson, 'report'):
        report = lesson.report

    form = None
    if lesson.status == 'scheduled':
        form = LessonReportForm()

    previous_lessons = Lesson.objects.filter(
        teacher=lesson.teacher,
        attendance__student__in=[a.student for a in attendances],
        date__lt=lesson.date,
        status='completed'
    ).distinct().order_by('-date')[:5]

    homeworks = Homework.objects.filter(lesson=lesson).order_by('-created_at')

    context = {
        'lesson': lesson,
        'attendances': calculator.get_attendance_details(),  # Детализация с балансами
        'finance': {  # УНИФИЦИРОВАННЫЕ финансы
            'total_cost': stats['total_cost'],
            'teacher_payment': stats['teacher_payment'],
            'attended_cost': stats['attended_cost'],
            'attended_payment': stats['attended_payment'],
            'debt_cost': stats['debt_cost'],
            'students_total': stats['students_total'],
            'students_attended': stats['students_attended'],
            'students_debt': stats['students_debt']
        },
        'report': report,
        'form': form,
        'previous_lessons': previous_lessons,
        'homeworks': homeworks,
    }

    return render(request, 'school/teacher/lesson_detail.html', context)


@login_required
def lesson_detail(request, lesson_id):
    """Детальная страница урока для ученика - РЕФАКТОРИНГ"""

    """Детальная страница урока для ученика - РЕФАКТОРИНГ"""

    lesson = get_object_or_404(Lesson, id=lesson_id)

    # ✅ ПРОВЕРКА НА ПРОСРОЧКУ
    from datetime import datetime
    if lesson.status == 'scheduled':
        lesson_datetime = datetime.combine(lesson.date, lesson.start_time)
        now = datetime.now()

        print(f"\n📅 ПРОВЕРКА УРОКА {lesson.id}:")
        print(f"   Статус: {lesson.status}")
        print(f"   Дата/время урока: {lesson_datetime}")
        print(f"   Текущее время: {now}")
        print(f"   Урок прошел? {lesson_datetime < now}")

        if lesson_datetime < now:
            lesson.status = 'overdue'
            lesson.save()
            print(f"   ✅ СТАТУС ИЗМЕНЕН НА: {lesson.status}")
        else:
            print(f"   ❌ Урок еще не прошел")

    user = request.user

    if user.role == 'student':
        try:
            attendance = lesson.attendance.get(student__user=user)
        except LessonAttendance.DoesNotExist:
            messages.error(request, 'Доступ запрещен')
            return redirect('dashboard')

        attendances = lesson.attendance.all().select_related('student__user')

    elif user.role == 'teacher' and lesson.teacher.user != user:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')
    else:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    # ИСПОЛЬЗУЕМ LessonFinanceCalculator
    calculator = LessonFinanceCalculator(lesson)

    previous_lessons = []
    if user.role == 'student':
        previous_lessons = Lesson.objects.filter(
            teacher=lesson.teacher,
            attendance__student=attendance.student,
            date__lt=lesson.date
        ).distinct().order_by('-date', '-start_time')[:5]

    report = None
    if hasattr(lesson, 'report'):
        report = lesson.report

    # Обработка оценки урока
    if request.method == 'POST' and user.role == 'student' and lesson.status == 'completed' and not hasattr(lesson,
                                                                                                            'feedback'):
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')
        is_public = request.POST.get('is_public') == 'on'

        if rating and rating.isdigit():
            feedback = LessonFeedback.objects.create(
                lesson=lesson,
                student=attendance.student,
                teacher=lesson.teacher,
                rating=int(rating),
                comment=comment,
                is_public=is_public
            )

            teacher_rating, created = TeacherRating.objects.get_or_create(teacher=lesson.teacher)
            teacher_rating.update_stats()

            messages.success(request, 'Спасибо за вашу оценку!')
            return redirect('lesson_detail', lesson_id=lesson.id)
        else:
            messages.error(request, 'Пожалуйста, поставьте оценку')

    context = {
        'lesson': lesson,
        'attendance': attendance,
        'attendances': calculator.get_attendance_details(),  # Детализация
        'finance': {  # Финансовая информация для ученика
            'student_cost': float(attendance.cost),
            'total_cost': calculator.stats['total_cost'],
            'students_total': calculator.stats['students_total']
        },
        'report': report,
        'previous_lessons': previous_lessons,
    }

    return render(request, 'school/student/lesson_detail.html', context)


@staff_member_required
@require_POST
def admin_complete_lesson(request, lesson_id):
    """Завершает занятие из админ-панели - ПОЛНЫЙ РЕФАКТОРИНГ"""
    print(f"REQUEST METHOD: {request.method}")
    print(f"REQUEST POST: {request.POST}")
    print(f"LESSON ID: {lesson_id}")
    print(f"\n{'🔥' * 30}")
    print(f"🔥🔥🔥 ЗАВЕРШЕНИЕ УРОКА #{lesson_id} 🔥🔥🔥")
    print(f"{'🔥' * 30}\n")

    try:
        lesson = Lesson.objects.select_related('teacher__user', 'subject').get(pk=lesson_id)

        if lesson.status == 'completed':
            messages.error(request, 'Занятие уже завершено')
            return redirect('admin:school_lesson_change', lesson_id)

        # ИСПОЛЬЗУЕМ LessonFinanceCalculator
        calculator = LessonFinanceCalculator(lesson)
        stats = calculator.stats

        if stats['students_total'] == 0:
            messages.error(request, 'Нет учеников на уроке')
            return redirect('admin:school_lesson_change', lesson_id)

        # Проверяем POST данные
        report_data = {
            'topic': request.POST.get('topic', '').strip(),
            'covered_material': request.POST.get('covered_material', '').strip(),
            'homework': request.POST.get('homework', '').strip(),
            'student_progress': request.POST.get('student_progress', '').strip(),
            'next_lesson_plan': request.POST.get('next_lesson_plan', '').strip()
        }

        required_fields = ['topic', 'covered_material', 'homework', 'student_progress']
        missing = [f for f in required_fields if not report_data[f]]
        if missing:
            messages.error(request, f'Заполните обязательные поля: {", ".join(missing)}')
            return redirect('admin:school_lesson_change', lesson_id)

        with transaction.atomic():
            processed_students = []

            for attendance in calculator.attendances:
                student = attendance.student
                user = student.user

                # ✅ ЗАПОМИНАЕМ БАЛАНС ДО СПИСАНИЯ
                old_balance = float(user.balance)

                # ✅ СПИСЫВАЕМ ДЕНЬГИ С БАЛАНСА УЧЕНИКА
                user.balance -= attendance.cost
                user.save()

                # УРОК СЧИТАЕТСЯ ПРОВЕДЕННЫМ
                attendance.status = 'attended'
                attendance.save()

                # СОЗДАЕМ ЗАПИСЬ О ПЛАТЕЖЕ
                Payment.objects.create(
                    user=user,
                    amount=attendance.cost,
                    payment_type='expense',
                    description=f'Оплата занятия {lesson.date} ({lesson.subject.name})',
                    lesson=lesson
                )

                student_data = {
                    'name': user.get_full_name(),
                    'cost': float(attendance.cost),
                    'teacher_payment': float(attendance.teacher_payment_share),
                    'old_balance': old_balance,
                    'new_balance': float(user.balance),
                    'debt': False
                }
                processed_students.append(student_data)

                print(f"💰 Баланс ученика {user.username}: {old_balance} → {user.balance} (списано {attendance.cost})")

            # НАЧИСЛЯЕМ УЧИТЕЛЮ
            old_teacher_balance = lesson.teacher.wallet_balance
            lesson.teacher.wallet_balance += calculator.teacher_payment
            lesson.teacher.save()

            if calculator.teacher_payment > 0:
                Payment.objects.create(
                    user=lesson.teacher.user,
                    amount=calculator.teacher_payment,
                    payment_type='teacher_payment',
                    description=f'Выплата за урок {lesson.date} ({lesson.subject.name})',
                    lesson=lesson
                )

            # МЕНЯЕМ СТАТУС УРОКА
            lesson.status = 'completed'
            lesson.save()

            # ✅ СОЗДАЕМ ИЛИ ОБНОВЛЯЕМ ОТЧЕТ (ВНУТРИ ТРАНЗАКЦИИ)
            report, created = LessonReport.objects.update_or_create(
                lesson=lesson,
                defaults={
                    'topic': report_data['topic'],
                    'covered_material': report_data['covered_material'],
                    'homework': report_data['homework'],
                    'student_progress': report_data['student_progress'],
                    'next_lesson_plan': report_data['next_lesson_plan']
                }
            )

            if created:
                print(f"✅ Создан новый отчет #{report.id}")
            else:
                print(f"✅ Обновлен существующий отчет #{report.id}")

        messages.success(request, f'✅ Урок успешно завершен! Отчет #{report.id} создан.')
        return redirect('admin:school_lesson_change', lesson_id)

    except Lesson.DoesNotExist:
        messages.error(request, 'Занятие не найдено')
        return redirect('admin:school_lesson_changelist')
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        traceback.print_exc()
        messages.error(request, f'Ошибка: {str(e)}')
        return redirect('admin:school_lesson_change', lesson_id)

@staff_member_required
def admin_finance_dashboard(request):
    """Финансовый дашборд для администратора - ПОЛНЫЙ РЕФАКТОРИНГ"""

    today = timezone.now().date()
    start_date = request.GET.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', today.strftime('%Y-%m-%d'))

    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Получаем данные за период
    lessons = Lesson.objects.filter(date__gte=start, date__lte=end)
    payments = Payment.objects.filter(created_at__date__gte=start, created_at__date__lte=end)

    # ИСПОЛЬЗУЕМ PeriodFinanceCalculator
    period_calc = PeriodFinanceCalculator(lessons, payments)

    # Статистика по ученикам
    students_with_debt = Student.objects.filter(user__balance__lt=0).count()
    total_debt = abs(
        Student.objects.filter(user__balance__lt=0).aggregate(Sum('user__balance'))['user__balance__sum'] or 0)

    students_with_balance = Student.objects.filter(user__balance__gt=0).count()
    total_balance = Student.objects.filter(user__balance__gt=0).aggregate(Sum('user__balance'))[
                        'user__balance__sum'] or 0

    # Топ-10 учеников
    top_students = Student.objects.select_related('user').order_by('-user__balance')[:10]
    top_debtors = Student.objects.filter(user__balance__lt=0).select_related('user').order_by('user__balance')[:10]

    # Статистика по учителям
    teachers_total_balance = Teacher.objects.aggregate(Sum('wallet_balance'))['wallet_balance__sum'] or 0

    context = {
        'period': {
            'start': start_date,
            'end': end_date,
            'start_formatted': start.strftime('%d.%m.%Y'),
            'end_formatted': end.strftime('%d.%m.%Y'),
        },
        'lessons_stats': period_calc.lessons_stats,
        'payments_stats': period_calc.payments_stats,
        'school_finances': period_calc.school_finances,
        'daily_stats': period_calc.get_daily_stats(start, end),
        'students': {
            'with_debt': students_with_debt,
            'total_debt': float(total_debt),
            'with_balance': students_with_balance,
            'total_balance': float(total_balance),
            'top_students': [
                {
                    'name': s.user.get_full_name(),
                    'balance': float(s.user.balance)
                } for s in top_students
            ],
            'top_debtors': [
                {
                    'name': s.user.get_full_name(),
                    'debt': float(s.user.balance)
                } for s in top_debtors
            ]
        },
        'teachers': {
            'total_balance': float(teachers_total_balance)
        }
    }

    return render(request, 'admin/finance/dashboard.html', context)


# Остальные views с аналогичным рефакторингом...
# (здесь идут все остальные функции, но я их пропускаю для краткости,
# так как принцип везде одинаковый - использовать созданные helper-классы)

@login_required
def student_deposit(request):
    """Пополнение баланса ученика"""
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    if request.method == 'POST':
        amount = request.POST.get('amount')
        description = request.POST.get('description', 'Пополнение счета')

        try:
            amount = Decimal(amount)
            if amount <= 0:
                messages.error(request, 'Сумма должна быть положительной')
                return redirect('student_dashboard')

            student = request.user.student_profile

            deposit = Deposit.objects.create(
                student=student,
                amount=amount,
                description=description,
                created_by=request.user
            )

            request.user.balance += amount
            request.user.save()

            messages.success(request, f'Счет пополнен на {amount} ₽')

        except (ValueError, TypeError, Decimal.InvalidOperation):
            messages.error(request, 'Неверная сумма')

        return redirect('student_dashboard')

    return redirect('student_dashboard')


# ============================================
# ЧАСТЬ 4: ФУНКЦИИ ЭКСПОРТА
# ============================================

@staff_member_required
def export_teacher_payment(request, format, teacher_id, start_date, end_date):
    """Экспорт отчета в разных форматах"""
    teacher = get_object_or_404(Teacher, id=teacher_id)
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()

    lessons = Lesson.objects.filter(
        teacher=teacher,
        status='completed',
        date__gte=start,
        date__lte=end
    ).prefetch_related('attendance__student__user', 'subject').order_by('date')

    # ИСПОЛЬЗУЕМ PeriodFinanceCalculator
    period_calc = PeriodFinanceCalculator(lessons)
    stats = period_calc.lessons_stats

    if format == 'excel':
        return export_to_excel(teacher, lessons, start, end, stats['teacher_payment'])
    elif format == 'word':
        return export_to_word(teacher, lessons, start, end, stats['teacher_payment'])
    elif format == 'pdf':
        return export_to_pdf(teacher, lessons, start, end, stats['teacher_payment'])
    else:
        return HttpResponse('Неподдерживаемый формат', status=400)


def export_to_excel(teacher, lessons, start, end, total_payment):
    """Экспорт в Excel"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Расчет выплат"

    title_font = Font(name='Arial', size=14, bold=True)
    header_font = Font(name='Arial', size=11, bold=True)
    normal_font = Font(name='Arial', size=10)
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font_white = Font(name='Arial', size=11, bold=True, color="FFFFFF")
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'),
                         bottom=Side(style='thin'))

    ws.merge_cells('A1:F1')
    cell = ws['A1']
    cell.value = f"Расчет выплат учителю: {teacher.user.get_full_name()}"
    cell.font = title_font
    cell.alignment = Alignment(horizontal='center')

    ws.merge_cells('A2:F2')
    cell = ws['A2']
    cell.value = f"Период: {start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}"
    cell.font = normal_font
    cell.alignment = Alignment(horizontal='center')

    ws.append([])

    headers = ['Дата', 'Ученик', 'Предмет', 'Стоимость урока', 'Выплата учителю', 'Статус']
    ws.append(headers)

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col)
        cell.value = header
        cell.font = header_font_white
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border

    row = 5
    for lesson in lessons:
        # ИСПОЛЬЗУЕМ LessonFinanceCalculator для детализации
        calculator = LessonFinanceCalculator(lesson)
        for attendance in calculator.get_attendance_details():
            ws.cell(row=row, column=1, value=lesson.date.strftime('%d.%m.%Y')).border = thin_border
            ws.cell(row=row, column=2, value=attendance['student_name']).border = thin_border
            ws.cell(row=row, column=3, value=lesson.subject.name).border = thin_border
            ws.cell(row=row, column=4, value=attendance['cost']).border = thin_border
            ws.cell(row=row, column=5, value=attendance['teacher_payment']).border = thin_border
            ws.cell(row=row, column=6, value=lesson.get_status_display()).border = thin_border

            ws.cell(row=row, column=4).number_format = '#,##0.00 ₽'
            ws.cell(row=row, column=5).number_format = '#,##0.00 ₽'
            row += 1

    row += 1
    ws.cell(row=row, column=4, value="ИТОГО:").font = header_font
    ws.cell(row=row, column=5, value=float(total_payment)).font = header_font
    ws.cell(row=row, column=5).number_format = '#,##0.00 ₽'

    column_widths = [12, 30, 20, 15, 15, 15]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"teacher_payment_{teacher.id}_{start}_{end}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    wb.save(response)
    return response


def export_to_word(teacher, lessons, start, end, total_payment):
    """Экспорт в Word"""
    doc = Document()

    title = doc.add_heading('Расчет выплат учителю', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_heading('Информация об учителе:', level=1)
    doc.add_paragraph(f'ФИО: {teacher.user.get_full_name()}')
    doc.add_paragraph(f'Email: {teacher.user.email}')
    doc.add_paragraph(f'Телефон: {teacher.user.phone}')

    doc.add_heading('Период расчета:', level=1)
    doc.add_paragraph(f'с {start.strftime("%d.%m.%Y")} по {end.strftime("%d.%m.%Y")}')

    doc.add_heading('Детализация уроков:', level=1)

    table = doc.add_table(rows=1, cols=5)
    table.style = 'Table Grid'

    header_cells = table.rows[0].cells
    headers = ['Дата', 'Ученик', 'Предмет', 'Стоимость', 'Выплата']
    for i, header in enumerate(headers):
        header_cells[i].text = header
        header_cells[i].paragraphs[0].runs[0].font.bold = True

    for lesson in lessons:
        calculator = LessonFinanceCalculator(lesson)
        for attendance in calculator.get_attendance_details():
            row_cells = table.add_row().cells
            row_cells[0].text = lesson.date.strftime('%d.%m.%Y')
            row_cells[1].text = attendance['student_name']
            row_cells[2].text = lesson.subject.name
            row_cells[3].text = f"{attendance['cost']:.2f} ₽"
            row_cells[4].text = f"{attendance['teacher_payment']:.2f} ₽"

    doc.add_paragraph()
    total_para = doc.add_paragraph()
    total_para.add_run('ИТОГО К ВЫПЛАТЕ: ').bold = True
    total_para.add_run(f'{total_payment:.2f} ₽').bold = True

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="teacher_payment_{teacher.id}_{start}_{end}.docx"'

    doc.save(response)
    return response


def export_to_pdf(teacher, lessons, start, end, total_payment):
    """Экспорт в PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    title = Paragraph(f"Расчет выплат учителю", styles['Title'])
    elements.append(title)
    elements.append(Paragraph(f"<b>{teacher.user.get_full_name()}</b>", styles['Normal']))
    elements.append(Paragraph(f"Период: {start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}", styles['Normal']))
    elements.append(Paragraph("<br/>", styles['Normal']))

    data = [['Дата', 'Ученик', 'Предмет', 'Стоимость', 'Выплата']]

    for lesson in lessons:
        calculator = LessonFinanceCalculator(lesson)
        for attendance in calculator.get_attendance_details():
            data.append([
                lesson.date.strftime('%d.%m.%Y'),
                attendance['student_name'],
                lesson.subject.name,
                f"{attendance['cost']:.2f} ₽",
                f"{attendance['teacher_payment']:.2f} ₽"
            ])

    data.append(['', '', '', 'ИТОГО:', f"{total_payment:.2f} ₽"])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -2), 1, colors.black),
        ('GRID', (0, -1), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="teacher_payment_{teacher.id}_{start}_{end}.pdf"'

    return response


@staff_member_required
def admin_lesson_export(request, format):
    """Экспорт уроков из админки"""
    lessons = Lesson.objects.all().select_related(
        'teacher__user', 'subject', 'format'
    ).prefetch_related('attendance__student__user').order_by('-date', 'start_time')

    teacher_id = request.GET.get('teacher__id__exact')
    student_id = request.GET.get('student__id__exact')
    subject_id = request.GET.get('subject__id__exact')
    status = request.GET.get('status__exact')
    date_from = request.GET.get('date__gte')
    date_to = request.GET.get('date__lte')

    if teacher_id:
        lessons = lessons.filter(teacher_id=teacher_id)
    if student_id:
        lessons = lessons.filter(attendance__student_id=student_id)
    if subject_id:
        lessons = lessons.filter(subject_id=subject_id)
    if status:
        lessons = lessons.filter(status=status)
    if date_from:
        lessons = lessons.filter(date__gte=date_from)
    if date_to:
        lessons = lessons.filter(date__lte=date_to)

    # ИСПОЛЬЗУЕМ PeriodFinanceCalculator
    period_calc = PeriodFinanceCalculator(lessons)
    stats = period_calc.lessons_stats

    title = f"Экспорт уроков"

    if format == 'excel':
        return export_lessons_excel(lessons, title, stats['completed'], stats['cancelled'],
                                    stats['overdue'], stats['total_cost'], stats['teacher_payment'])
    elif format == 'csv':
        return export_lessons_csv(lessons, title, stats['completed'], stats['cancelled'],
                                  stats['overdue'], stats['total_cost'], stats['teacher_payment'])
    elif format == 'html':
        return export_lessons_html(lessons, title, stats['completed'], stats['cancelled'],
                                   stats['overdue'], stats['total_cost'], stats['teacher_payment'])
    elif format == 'pdf':
        return export_lessons_pdf(lessons, title, stats['completed'], stats['cancelled'],
                                  stats['overdue'], stats['total_cost'], stats['teacher_payment'])
    else:
        messages.error(request, 'Неподдерживаемый формат')
        return redirect(request.META.get('HTTP_REFERER', 'admin:school_lesson_changelist'))


def export_lessons_excel(lessons, title, completed_count, cancelled_count, overdue_count, total_cost, total_payment):
    """Экспорт уроков в Excel"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Уроки"

    title_font = Font(name='Arial', size=16, bold=True)
    header_font = Font(name='Arial', size=12, bold=True)
    header_fill = PatternFill(start_color="417690", end_color="417690", fill_type="solid")
    header_font_white = Font(name='Arial', size=12, bold=True, color="FFFFFF")
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'),
                         bottom=Side(style='thin'))

    ws.merge_cells('A1:I1')
    cell = ws['A1']
    cell.value = title
    cell.font = title_font
    cell.alignment = Alignment(horizontal='center')

    ws.merge_cells('A2:I2')
    cell = ws['A2']
    cell.value = f"Дата экспорта: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    cell.font = Font(italic=True)
    cell.alignment = Alignment(horizontal='center')

    ws.merge_cells('A3:I3')
    cell = ws['A3']
    cell.value = f"Всего: {lessons.count()} | Проведено: {completed_count} | Отменено: {cancelled_count} | Просрочено: {overdue_count} | Сумма: {total_cost:,.2f} ₽ | Выплаты: {total_payment:,.2f} ₽"
    cell.font = Font(bold=True)
    cell.alignment = Alignment(horizontal='center')

    ws.append([])

    headers = ['ID урока', 'Дата', 'Время', 'Учитель', 'Ученик', 'Предмет', 'Стоимость', 'Выплата учителю', 'Статус']

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=5, column=col)
        cell.value = header
        cell.font = header_font_white
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border

    row = 6
    for lesson in lessons:
        calculator = LessonFinanceCalculator(lesson)
        for attendance in calculator.get_attendance_details():
            ws.cell(row=row, column=1, value=lesson.id).border = thin_border
            ws.cell(row=row, column=2, value=lesson.date.strftime('%d.%m.%Y')).border = thin_border
            ws.cell(row=row, column=3,
                    value=f"{lesson.start_time.strftime('%H:%M')}-{lesson.end_time.strftime('%H:%M')}").border = thin_border
            ws.cell(row=row, column=4, value=lesson.teacher.user.get_full_name()).border = thin_border
            ws.cell(row=row, column=5, value=attendance['student_name']).border = thin_border
            ws.cell(row=row, column=6, value=lesson.subject.name).border = thin_border
            ws.cell(row=row, column=7, value=attendance['cost']).border = thin_border
            ws.cell(row=row, column=8, value=attendance['teacher_payment']).border = thin_border
            ws.cell(row=row, column=9, value=lesson.get_status_display()).border = thin_border

            ws.cell(row=row, column=7).number_format = '#,##0.00 ₽'
            ws.cell(row=row, column=8).number_format = '#,##0.00 ₽'

            status_cell = ws.cell(row=row, column=9)
            if lesson.status == 'completed':
                status_cell.font = Font(color="28A745", bold=True)
            elif lesson.status == 'cancelled':
                status_cell.font = Font(color="DC3545", bold=True)
            elif lesson.status == 'overdue':
                status_cell.font = Font(color="FFC107", bold=True)
            elif lesson.status == 'scheduled':
                status_cell.font = Font(color="007BFF", bold=True)

            row += 1

    row += 1
    ws.cell(row=row, column=6, value="ИТОГО:").font = Font(bold=True)
    ws.cell(row=row, column=7, value=float(total_cost)).font = Font(bold=True)
    ws.cell(row=row, column=7).number_format = '#,##0.00 ₽'
    ws.cell(row=row, column=8, value=float(total_payment)).font = Font(bold=True)
    ws.cell(row=row, column=8).number_format = '#,##0.00 ₽'

    column_widths = [8, 12, 15, 25, 25, 20, 15, 18, 15]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"lessons_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    wb.save(response)
    return response


def export_lessons_csv(lessons, title, completed_count, cancelled_count, overdue_count, total_cost, total_payment):
    """Экспорт уроков в CSV"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    filename = f"lessons_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    response.write('\ufeff')
    writer = csv.writer(response, delimiter=';')

    writer.writerow([title])
    writer.writerow([f"Дата экспорта: {datetime.now().strftime('%d.%m.%Y %H:%M')}"])
    writer.writerow([
                        f"Всего: {lessons.count()} | Проведено: {completed_count} | Отменено: {cancelled_count} | Просрочено: {overdue_count}"])
    writer.writerow([f"Общая стоимость: {total_cost:.2f} ₽ | Общая сумма выплат: {total_payment:.2f} ₽"])
    writer.writerow([])

    writer.writerow(['ID', 'Дата', 'Время', 'Учитель', 'Ученик', 'Предмет', 'Стоимость', 'Выплата учителю', 'Статус'])

    for lesson in lessons:
        calculator = LessonFinanceCalculator(lesson)
        for attendance in calculator.get_attendance_details():
            writer.writerow([
                lesson.id,
                lesson.date.strftime('%d.%m.%Y'),
                f"{lesson.start_time.strftime('%H:%M')}-{lesson.end_time.strftime('%H:%M')}",
                lesson.teacher.user.get_full_name(),
                attendance['student_name'],
                lesson.subject.name,
                f"{attendance['cost']:.2f}",
                f"{attendance['teacher_payment']:.2f}",
                lesson.get_status_display(),
            ])

    return response


def export_lessons_html(lessons, title, completed_count, cancelled_count, overdue_count, total_cost, total_payment):
    """Экспорт уроков в HTML"""
    context = {
        'title': title,
        'lessons': lessons,
        'export_date': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'overdue_count': overdue_count,
        'total_cost': total_cost,
        'total_payment': total_payment,
    }

    html_content = render_to_string('admin/school/lesson/export.html', context)

    response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
    filename = f"lessons_export_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


def export_lessons_pdf(lessons, title, completed_count, cancelled_count, overdue_count, total_cost, total_payment):
    """Экспорт уроков в PDF"""
    context = {
        'title': title,
        'lessons': lessons,
        'export_date': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'overdue_count': overdue_count,
        'total_cost': total_cost,
        'total_payment': total_payment,
        'pdf_mode': True,
    }

    html_string = render_to_string('admin/school/lesson/export.html', context)

    response = HttpResponse(content_type='application/pdf')
    filename = f"lessons_export_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    HTML(string=html_string).write_pdf(response)

    return response


def download_import_template(request):
    """Скачать шаблон для импорта с поддержкой ID"""
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="import_lessons_template.xlsx"'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Импорт уроков"

    headers = [
        'Дата', 'Время начала', 'Время окончания',
        'ID учителя', 'Учитель (ФИО)',
        'ID учеников', 'Ученики (ФИО через ;)',
        'Предмет', 'Стоимость урока', 'Выплата учителю', 'Статус'
    ]

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
        cell.fill = openpyxl.styles.PatternFill(start_color="417690", end_color="417690", fill_type="solid")

    examples = [
        ['01.03.2026', '10:00', '11:00', '10', 'Иванов Иван', '13', 'Петров Петр', 'Математика', '1000', '500',
         'scheduled'],
        ['02.03.2026', '11:00', '12:00', '11', 'Петрова Анна', '14;15', 'Сидоров Сидор; Козлова Елена', 'Русский язык',
         '1500', '900', 'scheduled'],
        ['03.03.2026', '14:00', '15:00', '12', 'Смирнов Павел', '16;17;18',
         'Соколов Максим; Волкова Дарья; Морозов Алексей', 'Английский язык', '2400', '1500', 'scheduled'],
    ]

    for row_num, example in enumerate(examples, start=2):
        for col_num, value in enumerate(example, 1):
            ws.cell(row=row_num, column=col_num, value=value)

    column_widths = [12, 15, 15, 12, 25, 15, 30, 20, 15, 15, 15]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

    wb.save(response)
    return response


# ============================================
# ЧАСТЬ 5: ФУНКЦИИ ИМПОРТА
# ============================================

@staff_member_required
def import_students(request):
    """Импорт учеников из Excel"""
    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            messages.error(request, 'Выберите файл для импорта')
            return redirect('admin:school_student_changelist')

        try:
            wb = openpyxl.load_workbook(file)
            ws = wb.active

            success_count = 0
            error_count = 0
            errors = []

            for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if not any(row):
                    continue

                try:
                    student_id = row[0]
                    last_name = row[1]
                    first_name = row[2]
                    patronymic = row[3]
                    email = row[4]
                    phone = row[5]
                    parent_name = row[6]
                    parent_phone = row[7]

                    if student_id:
                        user = User.objects.get(id=student_id)
                    else:
                        username = f"student_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        user = User.objects.create_user(
                            username=username,
                            email=email,
                            password='default123'
                        )
                        user.role = 'student'

                    user.last_name = last_name
                    user.first_name = first_name
                    user.patronymic = patronymic
                    user.phone = phone
                    user.save()

                    student, created = Student.objects.get_or_create(user=user)
                    student.parent_name = parent_name
                    student.parent_phone = parent_phone
                    student.save()

                    success_count += 1

                except Exception as e:
                    error_count += 1
                    errors.append(f"Строка {row_num}: {str(e)}")

            if success_count > 0:
                messages.success(request, f'✅ Импортировано учеников: {success_count}')
            if error_count > 0:
                error_text = '\n'.join(errors[:5])
                if len(errors) > 5:
                    error_text += f'\n... и еще {len(errors) - 5} ошибок'
                messages.warning(request, f'⚠️ Ошибок: {error_count}\n{error_text}')

        except Exception as e:
            messages.error(request, f'Ошибка при импорте: {str(e)}')

        return redirect('admin:school_student_changelist')

    return render(request, 'admin/school/student/import.html')


@staff_member_required
def download_student_template(request):
    """Скачать шаблон для импорта учеников"""
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="import_students_template.xlsx"'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Импорт учеников"

    headers = ['ID (оставьте пустым для новых)', 'Фамилия', 'Имя', 'Отчество', 'Email', 'Телефон', 'Родитель',
               'Телефон родителя']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = openpyxl.styles.Font(bold=True)

    examples = [
        ['', 'Иванов', 'Иван', 'Иванович', 'ivanov@mail.ru', '+79001234567', 'Иванова М.И.', '+79007654321'],
        ['13', 'Петров', 'Петр', 'Петрович', 'petrov@mail.ru', '+79009876543', 'Петрова А.С.', '+79005432176'],
    ]

    for row_num, example in enumerate(examples, start=2):
        for col_num, value in enumerate(example, 1):
            ws.cell(row=row_num, column=col_num, value=value)

    wb.save(response)
    return response


@staff_member_required
def import_teachers(request):
    """Импорт учителей из Excel"""
    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            messages.error(request, 'Выберите файл для импорта')
            return redirect('admin:school_teacher_changelist')

        try:
            wb = openpyxl.load_workbook(file)
            ws = wb.active

            success_count = 0
            error_count = 0
            errors = []

            for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if not any(row):
                    continue

                try:
                    teacher_id = row[0]
                    last_name = row[1]
                    first_name = row[2]
                    patronymic = row[3]
                    email = row[4]
                    phone = row[5]
                    subjects_str = row[6]
                    experience = row[7]
                    education = row[8]

                    if teacher_id:
                        user = User.objects.get(id=teacher_id)
                    else:
                        username = f"teacher_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        user = User.objects.create_user(
                            username=username,
                            email=email,
                            password='default123'
                        )
                        user.role = 'teacher'

                    user.last_name = last_name
                    user.first_name = first_name
                    user.patronymic = patronymic
                    user.phone = phone
                    user.save()

                    teacher, created = Teacher.objects.get_or_create(user=user)
                    teacher.experience = experience or 0
                    teacher.education = education or ''
                    teacher.save()

                    if subjects_str:
                        subject_names = [s.strip() for s in str(subjects_str).split(';')]
                        for subject_name in subject_names:
                            subject, _ = Subject.objects.get_or_create(name=subject_name)
                            teacher.subjects.add(subject)

                    success_count += 1

                except Exception as e:
                    error_count += 1
                    errors.append(f"Строка {row_num}: {str(e)}")

            if success_count > 0:
                messages.success(request, f'✅ Импортировано учителей: {success_count}')
            if error_count > 0:
                error_text = '\n'.join(errors[:5])
                if len(errors) > 5:
                    error_text += f'\n... и еще {len(errors) - 5} ошибок'
                messages.warning(request, f'⚠️ Ошибок: {error_count}\n{error_text}')

        except Exception as e:
            messages.error(request, f'Ошибка при импорте: {str(e)}')

        return redirect('admin:school_teacher_changelist')

    return render(request, 'admin/school/teacher/import.html')


@staff_member_required
def download_teacher_template(request):
    """Скачать шаблон для импорта учителей"""
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="import_teachers_template.xlsx"'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Импорт учителей"

    headers = ['ID (пусто для новых)', 'Фамилия', 'Имя', 'Отчество', 'Email', 'Телефон', 'Предметы (через ;)',
               'Опыт (лет)', 'Образование']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = openpyxl.styles.Font(bold=True)

    examples = [
        ['', 'Соколов', 'Павел', 'Алексеевич', 'sokolov@mail.ru', '+79001112233', 'Математика;Физика', '5', 'МГУ'],
        ['10', 'Петрова', 'Анна', 'Игоревна', 'petrova@mail.ru', '+79002223344', 'Русский язык;Литература', '8',
         'МПГУ'],
    ]

    for row_num, example in enumerate(examples, start=2):
        for col_num, value in enumerate(example, 1):
            ws.cell(row=row_num, column=col_num, value=value)

    wb.save(response)
    return response


@staff_member_required
def import_lessons(request):
    """Импорт уроков из Excel или CSV"""
    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            messages.error(request, 'Выберите файл для импорта')
            return redirect('admin:school_lesson_changelist')

        if file.name.endswith('.csv'):
            return import_from_csv(file, request)
        elif file.name.endswith(('.xlsx', '.xls')):
            return import_from_excel(file, request)
        else:
            messages.error(request, 'Поддерживаются только файлы CSV и Excel (.xlsx, .xls)')
            return redirect('admin:school_lesson_changelist')

    return render(request, 'admin/school/lesson/import.html')


def import_from_csv(file, request):
    """Импорт из CSV"""
    try:
        decoded_file = file.read().decode('utf-8-sig').splitlines()
        reader = csv.DictReader(decoded_file, delimiter=';')

        success_count = 0
        error_count = 0
        errors = []

        for row_num, row in enumerate(reader, start=2):
            try:
                teacher_name = row.get('Учитель', '').strip()
                student_name = row.get('Ученик', '').strip()
                subject_name = row.get('Предмет', '').strip()

                teacher = find_teacher_by_full_name(teacher_name)
                if not teacher:
                    raise ValueError(f"Учитель '{teacher_name}' не найден")

                student = find_student_by_full_name(student_name)
                if not student:
                    raise ValueError(f"Ученик '{student_name}' не найден")

                subject = Subject.objects.filter(name__icontains=subject_name).first()
                if not subject:
                    raise ValueError(f"Предмет '{subject_name}' не найден")

                date_str = row.get('Дата', '').strip()
                if date_str:
                    date = datetime.strptime(date_str, '%d.%m.%Y').date()
                else:
                    raise ValueError("Дата не указана")

                start_time_str = row.get('Время начала', '').strip()
                end_time_str = row.get('Время окончания', '').strip()

                if start_time_str:
                    start_time = datetime.strptime(start_time_str, '%H:%M').time()
                else:
                    raise ValueError("Время начала не указано")

                if end_time_str:
                    end_time = datetime.strptime(end_time_str, '%H:%M').time()
                else:
                    from datetime import timedelta
                    start_dt = datetime.combine(date, start_time)
                    end_dt = start_dt + timedelta(hours=1)
                    end_time = end_dt.time()

                cost = Decimal(str(row.get('Стоимость', '1000')).replace(',', '.'))
                teacher_payment = Decimal(str(row.get('Выплата учителю', cost * Decimal('0.7'))).replace(',', '.'))

                status = row.get('Статус', 'scheduled').strip().lower()
                if status not in ['scheduled', 'completed', 'cancelled', 'overdue']:
                    status = 'scheduled'

                lesson = Lesson.objects.create(
                    teacher=teacher,
                    subject=subject,
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    base_cost=cost,
                    base_teacher_payment=teacher_payment,
                    status=status,
                )

                LessonAttendance.objects.create(
                    lesson=lesson,
                    student=student,
                    cost=cost,
                    teacher_payment_share=teacher_payment,
                    status='registered' if status == 'scheduled' else status
                )

                success_count += 1

            except Exception as e:
                error_count += 1
                errors.append(f"Строка {row_num}: {str(e)}")

        if success_count > 0:
            messages.success(request, f'✅ Импортировано уроков: {success_count}')
        if error_count > 0:
            error_text = '\n'.join(errors[:5])
            if len(errors) > 5:
                error_text += f'\n... и еще {len(errors) - 5} ошибок'
            messages.warning(request, f'⚠️ Ошибок: {error_count}\n{error_text}')

        return redirect('admin:school_lesson_changelist')

    except Exception as e:
        messages.error(request, f'Ошибка при импорте: {str(e)}')
        return redirect('admin:school_lesson_changelist')


def import_from_excel(file, request):
    """Импорт из Excel с поддержкой ID"""
    try:
        import tempfile
        import os
        from datetime import datetime, timedelta

        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            for chunk in file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        wb = openpyxl.load_workbook(tmp_path)
        ws = wb.active

        headers = [cell.value for cell in ws[1] if cell.value]

        success_count = 0
        error_count = 0
        errors = []

        for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if not any(row):
                continue

            try:
                row_dict = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        row_dict[header] = row[i]

                # Парсинг даты - поддерживаем оба формата
                date_str = str(row_dict.get('Дата', '')).strip()
                date = None

                # Пробуем разные форматы даты
                date_formats = [
                    '%Y-%m-%d %H:%M:%S',  # 2026-02-01 00:00:00
                    '%Y-%m-%d',  # 2026-02-01
                    '%d.%m.%Y',  # 01.02.2026
                    '%d.%m.%Y %H:%M:%S',  # 01.02.2026 00:00:00
                ]

                for fmt in date_formats:
                    try:
                        date = datetime.strptime(date_str, fmt).date()
                        break
                    except ValueError:
                        continue

                if not date:
                    raise ValueError(
                        f"Не удалось распознать дату '{date_str}'. Используйте формат ДД.ММ.ГГГГ или ГГГГ-ММ-ДД")

                # Парсинг времени
                start_time_str = str(row_dict.get('Время начала', '')).strip()
                end_time_str = str(row_dict.get('Время окончания', '')).strip()

                # Пробуем разные форматы времени
                time_formats = [
                    '%H:%M:%S',  # 10:00:00
                    '%H:%M',  # 10:00
                ]

                start_time = None
                for fmt in time_formats:
                    try:
                        start_time = datetime.strptime(start_time_str, fmt).time()
                        break
                    except ValueError:
                        continue

                if not start_time:
                    raise ValueError(f"Не удалось распознать время начала '{start_time_str}'")

                if end_time_str:
                    for fmt in time_formats:
                        try:
                            end_time = datetime.strptime(end_time_str, fmt).time()
                            break
                        except ValueError:
                            continue
                else:
                    # Если время окончания не указано, ставим +1 час
                    from datetime import timedelta, datetime
                    start_dt = datetime.combine(date, start_time)
                    end_dt = start_dt + timedelta(hours=1)
                    end_time = end_dt.time()

                # Поиск учителя по ID или ФИО
                teacher_id = row_dict.get('ID учителя')
                teacher = None

                if teacher_id:
                    teacher = find_teacher_by_id(teacher_id)
                    if not teacher:
                        raise ValueError(f"Учитель с ID '{teacher_id}' не найден")
                else:
                    teacher_name = str(row_dict.get('Учитель', '')).strip()
                    teacher = find_teacher_by_full_name(teacher_name)
                    if not teacher:
                        raise ValueError(f"Учитель '{teacher_name}' не найден")

                # Поиск учеников по ID или ФИО
                students = []

                student_ids_str = row_dict.get('ID учеников', '')
                if student_ids_str:
                    student_ids = [s.strip() for s in str(student_ids_str).split(';') if s.strip()]
                    for student_id in student_ids:
                        student = find_student_by_id(student_id)
                        if not student:
                            raise ValueError(f"Ученик с ID '{student_id}' не найден")
                        students.append(student)
                else:
                    students_str = str(row_dict.get('Ученики', '')).strip()
                    student_names = [s.strip() for s in students_str.split(';') if s.strip()]
                    for student_name in student_names:
                        student = find_student_by_full_name(student_name)
                        if not student:
                            raise ValueError(f"Ученик '{student_name}' не найден")
                        students.append(student)

                if not students:
                    raise ValueError("Не указаны ученики")

                # Поиск предмета
                subject_name = str(row_dict.get('Предмет', '')).strip()
                subject = Subject.objects.filter(name__icontains=subject_name).first()
                if not subject:
                    raise ValueError(f"Предмет '{subject_name}' не найден")

                # Стоимость
                cost_str = str(row_dict.get('Стоимость урока', '1000')).replace(',', '.')
                teacher_payment_str = str(row_dict.get('Выплата учителю', float(cost_str) * 0.7)).replace(',', '.')

                try:
                    cost = Decimal(cost_str)
                except:
                    raise ValueError(f"Неверный формат стоимости: {cost_str}")

                try:
                    teacher_payment = Decimal(teacher_payment_str)
                except:
                    teacher_payment = cost * Decimal('0.7')

                # Статус
                status = str(row_dict.get('Статус', 'scheduled')).strip().lower()
                if status not in ['scheduled', 'completed', 'cancelled', 'overdue']:
                    status = 'scheduled'

                # Создание урока
                lesson = Lesson.objects.create(
                    teacher=teacher,
                    subject=subject,
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    base_cost=cost,
                    base_teacher_payment=teacher_payment,
                    status=status,
                )

                # Создаем записи посещаемости для всех учеников
                for student in students:
                    LessonAttendance.objects.create(
                        lesson=lesson,
                        student=student,
                        cost=cost,
                        teacher_payment_share=teacher_payment,
                        status='registered' if status == 'scheduled' else status
                    )

                success_count += 1

            except Exception as e:
                error_count += 1
                errors.append(f"Строка {row_num}: {str(e)}")

        # Удаляем временный файл
        os.unlink(tmp_path)

        # Сообщаем результат
        if success_count > 0:
            messages.success(request, f'✅ Импортировано уроков: {success_count}')
        if error_count > 0:
            error_text = '\n'.join(errors[:5])
            if len(errors) > 5:
                error_text += f'\n... и еще {len(errors) - 5} ошибок'
            messages.warning(request, f'⚠️ Ошибок: {error_count}\n{error_text}')

        return redirect('admin:school_lesson_changelist')

    except Exception as e:
        messages.error(request, f'Ошибка при импорте: {str(e)}')
        return redirect('admin:school_lesson_changelist')

@staff_member_required
def download_user_template(request):
    """Скачать шаблон для импорта пользователей"""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from django.http import HttpResponse
    from datetime import datetime
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Импорт пользователей"
    
    headers = ['Username', 'Имя', 'Фамилия', 'Отчество', 'Email', 'Телефон', 'Роль', 'Пароль']
    
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="417690", end_color="417690", fill_type="solid")
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
    
    # Пример данных
    examples = [
        ['ivanov', 'Иван', 'Иванов', 'Иванович', 'ivan@mail.ru', '+79991234567', 'student', 'pass123'],
        ['petrova', 'Мария', 'Петрова', 'Сергеевна', 'maria@mail.ru', '+79997654321', 'teacher', 'pass123'],
    ]
    
    for row_num, example in enumerate(examples, start=2):
        for col_num, value in enumerate(example, 1):
            ws.cell(row=row_num, column=col_num, value=value)
    
    column_widths = [15, 15, 15, 15, 25, 15, 10, 15]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"user_import_template_{datetime.now().strftime('%Y%m%d')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib import messages
import openpyxl
from datetime import datetime
import traceback
from .models import User

@staff_member_required
def import_users_view(request):
    """Отдельное представление для импорта пользователей"""
    if request.method == 'POST' and request.FILES.get('import_file'):
        file = request.FILES['import_file']
        
        try:
            wb = openpyxl.load_workbook(file)
            ws = wb.active
            
            success_count = 0
            error_count = 0
            errors = []
            
            for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if not any(row):
                    continue
                
                try:
                    username = str(row[0]) if row[0] else None
                    first_name = str(row[1]) if row[1] else ''
                    last_name = str(row[2]) if row[2] else ''
                    patronymic = str(row[3]) if row[3] else ''
                    email = str(row[4]) if row[4] else ''
                    phone = str(row[5]) if row[5] else ''
                    role = str(row[6]) if row[6] else 'student'
                    password = str(row[7]) if row[7] else 'default123'
                    
                    if not username:
                        raise ValueError("Имя пользователя обязательно")
                    
                    if User.objects.filter(username=username).exists():
                        raise ValueError(f"Пользователь с username '{username}' уже существует")
                    
                    if email and User.objects.filter(email=email).exists():
                        raise ValueError(f"Пользователь с email '{email}' уже существует")
                    
                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        phone=phone,
                        role=role
                    )
                    user.patronymic = patronymic
                    user.save()
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"Строка {row_num}: {str(e)}")
            
            messages.success(request, f'✅ Импортировано пользователей: {success_count}')
            if error_count > 0:
                error_text = '\n'.join(errors[:5])
                if len(errors) > 5:
                    error_text += f'\n... и еще {len(errors) - 5} ошибок'
                messages.warning(request, f'⚠️ Ошибок: {error_count}\n{error_text}')
            
        except Exception as e:
            messages.error(request, f'Ошибка при импорте: {str(e)}')
        
        return redirect('admin:school_user_changelist')
    
    return render(request, 'admin/school/user/import.html')
# ============================================
# ЧАСТЬ 6: API И JSON ФУНКЦИИ
# ============================================

@require_GET
def api_schedules(request):
    """API для календаря расписаний"""
    schedules = Schedule.objects.filter(is_active=True).select_related('teacher__user')

    events = []
    today = date.today()

    for schedule in schedules:
        for i in range(30):
            event_date = today + timedelta(days=i)
            if event_date.weekday() == schedule.day_of_week:
                lesson = Lesson.objects.filter(
                    teacher=schedule.teacher,
                    date=event_date,
                    start_time=schedule.start_time
                ).first()

                start_dt = datetime.combine(event_date, schedule.start_time)
                end_dt = datetime.combine(event_date, schedule.end_time)

                event = {
                    'id': f"schedule_{schedule.id}_{event_date}",
                    'teacher_name': schedule.teacher.user.get_full_name(),
                    'subject': 'Расписание',
                    'start': start_dt.isoformat(),
                    'end': end_dt.isoformat(),
                    'color': '#28a745' if lesson else '#3788d8',
                }

                if lesson:
                    event['subject'] = lesson.subject.name
                    event['student_name'] = lesson.student.user.get_full_name()
                    event['status'] = lesson.status

                events.append(event)

    return JsonResponse(events, safe=False)


@staff_member_required
def schedule_calendar_data(request):
    """API для календаря расписаний"""
    schedules = Schedule.objects.filter(is_active=True).select_related('teacher__user')

    events = []
    today = date.today()

    for i in range(60):
        event_date = today + timedelta(days=i)
        day_schedules = schedules.filter(date=event_date)

        for schedule in day_schedules:
            lesson = Lesson.objects.filter(
                teacher=schedule.teacher,
                date=event_date,
                start_time=schedule.start_time
            ).first()

            start_dt = datetime.combine(event_date, schedule.start_time)
            end_dt = datetime.combine(event_date, schedule.end_time)

            color = '#79aec8'
            if lesson:
                if lesson.status == 'completed':
                    color = '#28a745'
                elif lesson.status == 'overdue':
                    color = '#dc3545'
                elif lesson.status == 'scheduled':
                    color = '#007bff'
                elif lesson.status == 'cancelled':
                    color = '#fd7e14'

            event = {
                'id': f"schedule_{schedule.id}_{event_date}",
                'schedule_id': schedule.id,
                'teacher_name': schedule.teacher.user.get_full_name(),
                'start': start_dt.isoformat(),
                'end': end_dt.isoformat(),
                'color': color,
            }

            if lesson:
                event['lesson_id'] = lesson.id
                event['title'] = f"{schedule.teacher.user.last_name} - {lesson.subject.name}"
                first_attendance = lesson.attendance.first()
                if first_attendance:
                    event['title'] += f" ({first_attendance.student.user.last_name})"
            else:
                event['title'] = f"{schedule.teacher.user.last_name} - свободно"

            events.append(event)

    return JsonResponse(events, safe=False)


@login_required
def get_notifications(request):
    """API для получения уведомлений"""
    try:
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:20]
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

        notifications_data = []
        for n in notifications:
            try:
                time_diff = timezone.now() - n.created_at
                if time_diff.days > 0:
                    created_ago = f"{time_diff.days} дн. назад"
                elif time_diff.seconds // 3600 > 0:
                    created_ago = f"{time_diff.seconds // 3600} ч. назад"
                elif time_diff.seconds // 60 > 0:
                    created_ago = f"{time_diff.seconds // 60} мин. назад"
                else:
                    created_ago = "только что"
            except:
                created_ago = n.created_at.strftime('%d.%m.%Y %H:%M')

            notifications_data.append({
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'type': n.notification_type,
                'is_read': n.is_read,
                'link': n.link if n.link else '',
                'created_at': n.created_at.strftime('%d.%m.%Y %H:%M'),
                'created_ago': created_ago,
            })

        return JsonResponse({
            'unread_count': unread_count,
            'notifications': notifications_data
        })

    except Exception as e:
        print(f"❌ Ошибка в get_notifications: {e}")
        return JsonResponse({'error': str(e), 'notifications': [], 'unread_count': 0}, status=500)


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Отметить уведомление как прочитанное"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()

        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

        return JsonResponse({
            'status': 'ok',
            'unread_count': unread_count,
            'message': 'Уведомление отмечено как прочитанное'
        })
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Уведомление не найдено'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def mark_all_notifications_read(request):
    """Отметить все уведомления как прочитанные"""
    try:
        count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({
            'status': 'ok',
            'count': count,
            'message': f'Отмечено {count} уведомлений'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def generate_video_room(request, lesson_id):
    """Генерирует комнату для видео"""
    lesson = get_object_or_404(Lesson, id=lesson_id)

    if not lesson.video_room:
        lesson.video_room = str(uuid.uuid4())[:8]
        lesson.save()

    return JsonResponse({
        'room': lesson.video_room,
        'url': f'https://meet.jit.si/plusprogress-{lesson.id}-{lesson.date}'
    })


@login_required
@require_POST
def create_video_room(request, lesson_id):
    """Учитель создает видео-комнату для урока"""
    try:
        lesson = get_object_or_404(Lesson, id=lesson_id)

        if request.user.role != 'teacher' or lesson.teacher.user != request.user:
            return JsonResponse({'error': 'Доступ запрещен'}, status=403)

        if lesson.status != 'scheduled':
            return JsonResponse({'error': 'Урок уже проведен или отменен'}, status=400)

        if not lesson.video_room:
            lesson.video_room = str(uuid.uuid4())[:8]
            lesson.save()

        return JsonResponse({
            'success': True,
            'room': lesson.video_room
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================
# ЧАСТЬ 7: ОТЧЕТЫ
# ============================================

@login_required
def overdue_report(request):
    """Отчет по просроченным занятиям"""
    if request.user.role not in ['admin', 'teacher']:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    now = timezone.now()
    overdue_lessons = Lesson.objects.filter(
        status='scheduled',
        date__lt=now.date()
    ) | Lesson.objects.filter(
        status='scheduled',
        date=now.date(),
        start_time__lt=now.time()
    )

    for lesson in overdue_lessons:
        lesson.check_overdue()

    teacher_id = request.GET.get('teacher')
    student_id = request.GET.get('student')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    lessons = Lesson.objects.filter(status='overdue').select_related(
        'teacher__user', 'subject'
    ).prefetch_related('attendance__student__user')

    if teacher_id:
        lessons = lessons.filter(teacher_id=teacher_id)
    if student_id:
        lessons = lessons.filter(attendance__student_id=student_id)
    if date_from:
        lessons = lessons.filter(date__gte=date_from)
    if date_to:
        lessons = lessons.filter(date__lte=date_to)

    # ИСПОЛЬЗУЕМ PeriodFinanceCalculator для статистики
    period_calc = PeriodFinanceCalculator(lessons)
    stats = period_calc.lessons_stats

    context = {
        'lessons': lessons.order_by('-date', '-start_time'),
        'stats': {
            'total': stats['total'],
            'by_teacher': lessons.values('teacher__user__last_name').annotate(count=Count('id')).order_by('-count'),
            'by_subject': lessons.values('subject__name').annotate(count=Count('id')).order_by('-count'),
        },
        'teachers': Teacher.objects.all(),
        'students': Student.objects.all(),
    }

    return render(request, 'school/reports/overdue.html', context)


@staff_member_required
def student_report(request, student_id):
    """Отчет по ученику"""
    student = get_object_or_404(Student, id=student_id)

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Преобразуем строки в даты
    start_date = None
    end_date = None
    if date_from:
        start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
    if date_to:
        end_date = datetime.strptime(date_to, '%Y-%m-%d').date()

    # Получаем ТОЛЬКО ПРОВЕДЕННЫЕ уроки (attended)
    attendances = LessonAttendance.objects.filter(
        student=student,
        status='attended'  # ← Только проведенные уроки
    ).select_related(
        'lesson', 'lesson__subject'
    ).order_by('lesson__date')

    if start_date:
        attendances = attendances.filter(lesson__date__gte=start_date)
    if end_date:
        attendances = attendances.filter(lesson__date__lte=end_date)

    # Получаем все уникальные даты
    dates = attendances.dates('lesson__date', 'day').order_by('lesson__date')

    # Получаем все уникальные предметы
    subjects = attendances.values_list('lesson__subject__name', flat=True).distinct()

    # Создаем словарь для хранения данных по предметам
    subjects_data_dict = {}
    daily_totals = {date: 0 for date in dates}

    # Инициализируем словарь для каждого предмета
    for subject_name in subjects:
        subjects_data_dict[subject_name] = {date: 0 for date in dates}

    # Заполняем данные
    for attendance in attendances:
        subject_name = attendance.lesson.subject.name
        lesson_date = attendance.lesson.date
        cost = attendance.cost

        subjects_data_dict[subject_name][lesson_date] += cost
        daily_totals[lesson_date] += cost

    # Формируем данные для таблицы
    subjects_data = []
    total_sum = 0

    for subject_name, daily_costs in subjects_data_dict.items():
        daily_costs_list = []
        subject_total = 0

        for date in dates:
            cost = daily_costs.get(date, 0)
            daily_costs_list.append(float(cost))
            subject_total += cost

        subjects_data.append({
            'name': subject_name,
            'daily_costs': daily_costs_list,
            'total': float(subject_total)
        })
        total_sum += subject_total

    # Статистика по ученику
    total_lessons = attendances.count()
    total_attended_cost = attendances.aggregate(Sum('cost'))['cost__sum'] or 0

    # Получаем отдельно уроки в долг (для статистики)
    debt_attendances = LessonAttendance.objects.filter(
        student=student,
        status='debt'
    )
    if start_date:
        debt_attendances = debt_attendances.filter(lesson__date__gte=start_date)
    if end_date:
        debt_attendances = debt_attendances.filter(lesson__date__lte=end_date)

    debt_lessons = debt_attendances.count()
    total_debt_cost = debt_attendances.aggregate(Sum('cost'))['cost__sum'] or 0

    # ✅ ПОЛУЧАЕМ БАЛАНС УЧЕНИКА
    student_balance = float(student.user.balance)

    context = {
        'student': student,
        'dates': dates,
        'subjects_data': subjects_data,
        'daily_totals': [float(daily_totals.get(date, 0)) for date in dates],
        'total_lessons': total_lessons,
        'total_attended_cost': float(total_attended_cost),
        'debt_lessons': debt_lessons,
        'total_debt_cost': float(total_debt_cost),
        'student_balance': student_balance,  # ✅ Добавлено
    }

    # Для отладки
    print(f"\n{'=' * 60}")
    print(f"ОТЧЕТ ПО УЧЕНИКУ: {student.user.get_full_name()}")
    print(f"Проведенных уроков: {total_lessons}")
    print(f"Сумма проведенных: {total_attended_cost}")
    print(f"Уроков в долг: {debt_lessons}")
    print(f"Сумма долга: {total_debt_cost}")
    print(f"Баланс ученика: {student_balance}")  # ✅ Добавлено
    print(f"Предметы: {list(subjects)}")
    print(f"Даты: {[d.strftime('%d.%m.%Y') for d in dates]}")
    print(f"{'=' * 60}\n")

    return render(request, 'admin/school/student/report.html', context)


@staff_member_required
def teacher_report(request, teacher_id):
    """Отчет по учителю"""
    teacher = get_object_or_404(Teacher, id=teacher_id)

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Преобразуем строки в даты
    start_date = None
    end_date = None
    if date_from:
        start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
    if date_to:
        end_date = datetime.strptime(date_to, '%Y-%m-%d').date()

    # ОТЛАДКА: смотрим все статусы уроков
    all_statuses = Lesson.objects.filter(teacher=teacher).values_list('status', flat=True).distinct()
    print(f"\n🔍 Все статусы уроков учителя: {list(all_statuses)}")

    # Получаем ТОЛЬКО ПРОВЕДЕННЫЕ уроки
    lessons = Lesson.objects.filter(
        teacher=teacher,
        status='completed'
    ).prefetch_related(
        'attendance__student__user', 'subject'
    ).order_by('date')

    # ОТЛАДКА: сколько нашлось
    print(f"🔍 Найдено проведенных уроков: {lessons.count()}")

    if start_date:
        lessons = lessons.filter(date__gte=start_date)
    if end_date:
        lessons = lessons.filter(date__lte=end_date)

    # Получаем все уникальные даты
    dates = lessons.dates('date', 'day').order_by('date')

    # ОТЛАДКА: даты
    print(f"🔍 Даты проведенных уроков: {[d.strftime('%d.%m.%Y') for d in dates]}")

    # Словари для хранения данных
    students_lessons_dict = {}  # Для стоимости уроков (ученик платит)
    students_earnings_dict = {}  # Для заработка учителя (teacher_payment_share)
    daily_totals_lessons = {date: 0 for date in dates}
    daily_totals_earnings = {date: 0 for date in dates}

    total_lessons_count = 0
    total_income_sum = 0
    total_earnings_sum = 0

    # Собираем данные по каждому уроку
    for lesson in lessons:
        total_lessons_count += 1

        for attendance in lesson.attendance.all():
            student_name = attendance.student.user.get_full_name()
            subject_name = lesson.subject.name
            key = f"{student_name} ({subject_name})"

            # Стоимость для ученика
            cost = attendance.cost
            # Заработок учителя
            earning = attendance.teacher_payment_share

            # Добавляем в словарь стоимости (ученик платит)
            if key not in students_lessons_dict:
                students_lessons_dict[key] = {date: 0 for date in dates}
            students_lessons_dict[key][lesson.date] += cost

            # Добавляем в словарь заработка учителя
            if key not in students_earnings_dict:
                students_earnings_dict[key] = {date: 0 for date in dates}
            students_earnings_dict[key][lesson.date] += earning

            # Обновляем итоги по дням
            daily_totals_lessons[lesson.date] += cost
            daily_totals_earnings[lesson.date] += earning

            # Обновляем общие итоги
            total_income_sum += cost
            total_earnings_sum += earning

    # Формируем данные для таблиц
    lessons_data = []
    earnings_data = []

    for key in students_lessons_dict.keys():
        # Данные по стоимости уроков
        daily_costs = []
        student_total = 0
        for date in dates:
            cost = students_lessons_dict[key].get(date, 0)
            daily_costs.append(float(cost))
            student_total += cost

        lessons_data.append({
            'name': key,
            'daily_costs': daily_costs,
            'total': float(student_total)
        })

        # Данные по заработку учителя
        daily_earnings = []
        earning_total = 0
        for date in dates:
            earning = students_earnings_dict[key].get(date, 0)
            daily_earnings.append(float(earning))
            earning_total += earning

        earnings_data.append({
            'name': key,
            'daily_earnings': daily_earnings,
            'total': float(earning_total)
        })

    # Сортируем данные по имени ученика
    lessons_data.sort(key=lambda x: x['name'])
    earnings_data.sort(key=lambda x: x['name'])

    # Формируем итоги по дням
    daily_totals_lessons_list = []
    daily_totals_earnings_list = []

    for date in dates:
        daily_totals_lessons_list.append(float(daily_totals_lessons.get(date, 0)))
        daily_totals_earnings_list.append(float(daily_totals_earnings.get(date, 0)))

    context = {
        'teacher': teacher,
        'dates': dates,
        'lessons_data': lessons_data,
        'earnings_data': earnings_data,
        'daily_totals_lessons': daily_totals_lessons_list,
        'daily_totals_earnings': daily_totals_earnings_list,
        'total_lessons': total_lessons_count,
        'total_income': float(total_income_sum),
        'total_earnings': float(total_earnings_sum),
    }

    # ИТОГОВАЯ ОТЛАДКА
    print(f"\n{'=' * 60}")
    print(f"ОТЧЕТ ПО УЧИТЕЛЮ: {teacher.user.get_full_name()}")
    print(f"Всего проведенных уроков в отчете: {total_lessons_count}")
    print(f"Общая стоимость: {total_income_sum}")
    print(f"Заработок: {total_earnings_sum}")
    print(f"Даты в отчете: {[d.strftime('%d.%m.%Y') for d in dates]}")
    print(f"{'=' * 60}\n")

    return render(request, 'admin/school/teacher/report.html', context)


@staff_member_required
def teacher_payments_dashboard(request):
    """Дашборд для расчета выплат учителям"""
    teachers = Teacher.objects.all().select_related('user')

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    context = {
        'teachers': teachers,
        'default_start': start_date.strftime('%Y-%m-%d'),
        'default_end': end_date.strftime('%Y-%m-%d'),
        'title': 'Расчет выплат учителям',
    }
    return render(request, 'admin/school/teacher_payments/dashboard.html', context)


@staff_member_required
def calculate_teacher_payment(request):
    """API для расчета выплат учителю за период"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)

    try:
        data = json.loads(request.body)
        teacher_id = data.get('teacher_id')
        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()

        teacher = get_object_or_404(Teacher, id=teacher_id)

        completed_lessons = Lesson.objects.filter(
            teacher=teacher,
            status='completed',
            date__gte=start_date,
            date__lte=end_date
        ).prefetch_related('attendance__student__user', 'subject')

        # ИСПОЛЬЗУЕМ PeriodFinanceCalculator
        period_calc = PeriodFinanceCalculator(completed_lessons)
        stats = period_calc.lessons_stats

        # Агрегация по предметам
        subject_stats = []
        subject_totals = {}

        for lesson in completed_lessons:
            calculator = LessonFinanceCalculator(lesson)
            subject_name = lesson.subject.name
            if subject_name not in subject_totals:
                subject_totals[subject_name] = {'count': 0, 'payment': 0}
            for attendance in calculator.get_attendance_details():
                subject_totals[subject_name]['count'] += 1
                subject_totals[subject_name]['payment'] += attendance['teacher_payment']

        for name, data in subject_totals.items():
            subject_stats.append({
                'subject__name': name,
                'lesson_count': data['count'],
                'total_payment': data['payment']
            })

        # Агрегация по ученикам
        student_stats = []
        student_totals = {}

        for lesson in completed_lessons:
            calculator = LessonFinanceCalculator(lesson)
            for attendance in calculator.get_attendance_details():
                student_name = attendance['student_name']
                if student_name not in student_totals:
                    student_totals[student_name] = {'count': 0, 'payment': 0}
                student_totals[student_name]['count'] += 1
                student_totals[student_name]['payment'] += attendance['teacher_payment']

        for name, data in student_totals.items():
            name_parts = name.split()
            student_stats.append({
                'student__user__last_name': name_parts[0] if name_parts else '',
                'student__user__first_name': name_parts[1] if len(name_parts) > 1 else '',
                'student__user__patronymic': '',
                'lesson_count': data['count'],
                'total_payment': data['payment']
            })

        # Данные для таблицы по дням
        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date.strftime('%d.%m.%Y'))
            current_date += timedelta(days=1)

        lessons_data = []
        for lesson in completed_lessons:
            calculator = LessonFinanceCalculator(lesson)
            for attendance in calculator.get_attendance_details():
                lessons_data.append({
                    'date': lesson.date.strftime('%d.%m.%Y'),
                    'student': attendance['student_name'],
                    'subject': lesson.subject.name,
                    'cost': attendance['cost'],
                    'teacher_payment': attendance['teacher_payment'],
                    'status': lesson.status
                })

        response_data = {
            'teacher': {
                'id': teacher.id,
                'name': teacher.user.get_full_name(),
            },
            'period': {
                'start': start_date.strftime('%d.%m.%Y'),
                'end': end_date.strftime('%d.%m.%Y'),
            },
            'totals': {
                'lessons': stats['completed'],
                'cost': stats['total_cost'],
                'payment': stats['teacher_payment'],
            },
            'subject_stats': subject_stats,
            'student_stats': sorted(student_stats, key=lambda x: x['total_payment'], reverse=True),
            'lessons_data': lessons_data,
            'dates': dates,
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ============================================
# ЧАСТЬ 8: ДОМАШНИЕ ЗАДАНИЯ
# ============================================

@login_required
def teacher_homeworks(request):
    """Список заданий для учителя"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    teacher = request.user.teacher_profile

    student_id = request.GET.get('student')
    status = request.GET.get('status')

    homeworks = Homework.objects.filter(teacher=teacher).select_related(
        'student__user', 'subject'
    ).prefetch_related('submission')

    if student_id:
        homeworks = homeworks.filter(student_id=student_id)

    students = Student.objects.filter(teachers=teacher)

    stats = {
        'total': homeworks.count(),
        'pending': sum(1 for h in homeworks if h.get_status() == 'pending'),
        'submitted': sum(1 for h in homeworks if h.get_status() == 'submitted'),
        'checked': sum(1 for h in homeworks if h.get_status() == 'checked'),
        'overdue': sum(1 for h in homeworks if h.get_status() == 'overdue'),
    }

    context = {
        'homeworks': homeworks.order_by('-created_at'),
        'students': students,
        'stats': stats,
        'teacher': teacher,
    }
    return render(request, 'school/teacher/homeworks.html', context)


@login_required
def teacher_homework_create(request, student_id):
    """Создание домашнего задания для конкретного ученика"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    teacher = request.user.teacher_profile
    student = get_object_or_404(Student, id=student_id, teachers=teacher)

    if request.method == 'POST':
        form = HomeworkForm(request.POST, request.FILES)
        if form.is_valid():
            homework = form.save(commit=False)
            homework.teacher = teacher
            homework.student = student
            homework.subject = teacher.subjects.first()
            homework.save()

            Notification.objects.create(
                user=student.user,
                title='📝 Новое домашнее задание',
                message=f"{teacher.user.get_full_name()} выдал задание: {homework.title}",
                notification_type='homework_assigned',
                link='/student/homeworks/'
            )

            messages.success(request, f'Задание "{homework.title}" создано')
            return redirect('teacher_homeworks')
    else:
        form = HomeworkForm()

    context = {
        'form': form,
        'student': student,
        'teacher': teacher,
    }
    return render(request, 'school/teacher/homework_form.html', context)


@login_required
def teacher_homework_detail(request, homework_id):
    """Детали задания для учителя"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    teacher = request.user.teacher_profile
    homework = get_object_or_404(Homework, id=homework_id, teacher=teacher)

    submission = None
    if hasattr(homework, 'submission'):
        submission = homework.submission

    if request.method == 'POST' and submission:
        form = HomeworkCheckForm(request.POST, instance=submission)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.status = 'checked'
            submission.checked_at = timezone.now()
            submission.save()

            Notification.objects.create(
                user=homework.student.user,
                title='✅ Задание проверено',
                message=f"Ваше задание '{homework.title}' проверено. Оценка: {submission.grade}",
                notification_type='homework_checked',
                link='/student/homeworks/'
            )

            messages.success(request, 'Задание проверено')
            return redirect('teacher_homeworks')
    else:
        form = HomeworkCheckForm(instance=submission) if submission else None

    context = {
        'homework': homework,
        'submission': submission,
        'form': form,
        'teacher': teacher,
    }
    return render(request, 'school/teacher/homework_detail.html', context)


@login_required
def student_homeworks(request):
    """Список заданий для ученика"""
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    student = request.user.student_profile
    status = request.GET.get('status')

    homeworks = Homework.objects.filter(student=student).select_related(
        'teacher__user', 'subject'
    ).prefetch_related('submission')

    if status:
        if status == 'pending':
            homeworks = [h for h in homeworks if h.get_status() == 'pending']
        elif status == 'submitted':
            homeworks = [h for h in homeworks if h.get_status() == 'submitted']
        elif status == 'checked':
            homeworks = [h for h in homeworks if h.get_status() == 'checked']
        elif status == 'overdue':
            homeworks = [h for h in homeworks if h.get_status() == 'overdue']

    all_homeworks = Homework.objects.filter(student=student)
    stats = {
        'total': all_homeworks.count(),
        'pending': sum(1 for h in all_homeworks if h.get_status() == 'pending'),
        'submitted': sum(1 for h in all_homeworks if h.get_status() == 'submitted'),
        'checked': sum(1 for h in all_homeworks if h.get_status() == 'checked'),
        'overdue': sum(1 for h in all_homeworks if h.get_status() == 'overdue'),
    }

    context = {
        'homeworks': homeworks,
        'stats': stats,
        'student': student,
    }
    return render(request, 'school/student/homeworks.html', context)


@login_required
def student_homework_detail(request, homework_id):
    """Детали задания для ученика"""
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    student = request.user.student_profile
    homework = get_object_or_404(Homework, id=homework_id, student=student)

    try:
        submission = homework.submission
        can_submit = False
    except HomeworkSubmission.DoesNotExist:
        submission = None
        can_submit = True

    if request.method == 'POST' and can_submit:
        form = HomeworkSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.homework = homework
            submission.student = student
            submission.save()

            messages.success(request, 'Задание отправлено на проверку!')
            return redirect('student_homeworks')
    else:
        form = HomeworkSubmissionForm()

    context = {
        'homework': homework,
        'submission': submission,
        'form': form if can_submit else None,
        'can_submit': can_submit,
        'student': student,
    }
    return render(request, 'school/student/homework_detail.html', context)


# ============================================
# ЧАСТЬ 9: ОТЗЫВЫ И ОЦЕНКИ
# ============================================

@login_required
def lesson_feedback(request, lesson_id):
    """Страница оценки урока"""
    lesson = get_object_or_404(Lesson, id=lesson_id)

    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    try:
        attendance = lesson.attendance.get(student__user=request.user)
    except LessonAttendance.DoesNotExist:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    if lesson.status != 'completed':
        messages.error(request, 'Можно оценивать только проведенные уроки')
        return redirect('student_dashboard')

    if hasattr(lesson, 'feedback'):
        messages.info(request, 'Вы уже оценили этот урок')
        return redirect('student_dashboard')

    if request.method == 'POST':
        form = LessonFeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.lesson = lesson
            feedback.student = attendance.student
            feedback.teacher = lesson.teacher
            feedback.save()

            messages.success(request, 'Спасибо за вашу оценку! Отзыв поможет нам стать лучше.')
            return redirect('student_dashboard')
    else:
        form = LessonFeedbackForm()

    context = {
        'lesson': lesson,
        'form': form,
    }
    return render(request, 'school/student/lesson_feedback.html', context)


@login_required
def teacher_feedbacks(request):
    """Страница с отзывами для учителя"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    teacher = request.user.teacher_profile
    feedbacks = LessonFeedback.objects.filter(teacher=teacher).select_related(
        'lesson', 'student__user', 'lesson__subject'
    ).order_by('-created_at')

    stats = feedbacks.aggregate(
        avg_rating=Avg('rating'),
        total=Count('id')
    )

    rating_distribution = {
        5: feedbacks.filter(rating=5).count(),
        4: feedbacks.filter(rating=4).count(),
        3: feedbacks.filter(rating=3).count(),
        2: feedbacks.filter(rating=2).count(),
        1: feedbacks.filter(rating=1).count(),
    }

    context = {
        'feedbacks': feedbacks,
        'stats': stats,
        'rating_distribution': rating_distribution,
        'teacher': teacher,
    }
    return render(request, 'school/teacher/feedbacks.html', context)


@login_required
def student_feedbacks(request):
    """Страница с отзывами для ученика"""
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    student = request.user.student_profile
    feedbacks = LessonFeedback.objects.filter(student=student).select_related(
        'lesson', 'teacher__user', 'lesson__subject'
    ).order_by('-created_at')

    context = {
        'feedbacks': feedbacks,
        'student': student,
    }
    return render(request, 'school/student/feedbacks.html', context)


# ============================================
# ЧАСТЬ 10: ГРУППОВЫЕ УРОКИ
# ============================================

@login_required
def teacher_group_lessons(request):
    """Список групповых уроков для учителя"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    teacher = request.user.teacher_profile
    group_lessons = GroupLesson.objects.filter(teacher=teacher).order_by('-date', '-start_time')

    context = {
        'group_lessons': group_lessons,
    }
    return render(request, 'school/teacher/group_lessons.html', context)


@login_required
def teacher_group_lesson_detail(request, lesson_id):
    """Детальная страница группового урока для учителя"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    lesson = get_object_or_404(GroupLesson, id=lesson_id)

    if lesson.teacher.user != request.user:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    enrollments = lesson.enrollments.all().select_related('student__user')

    context = {
        'lesson': lesson,
        'enrollments': enrollments,
    }
    return render(request, 'school/teacher/group_lesson_detail.html', context)


@login_required
@require_POST
def mark_group_attendance(request, lesson_id):
    """Отметить присутствие ученика на групповом уроке"""
    if request.user.role != 'teacher':
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)

    lesson = get_object_or_404(GroupLesson, id=lesson_id)

    if lesson.teacher.user != request.user:
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)

    enrollment_id = request.POST.get('enrollment_id')
    status = request.POST.get('status')

    enrollment = get_object_or_404(GroupEnrollment, id=enrollment_id, group_lesson=lesson)
    enrollment.status = status
    enrollment.save()

    return JsonResponse({'success': True})


@login_required
@require_POST
def complete_group_lesson(request, lesson_id):
    """Завершить групповой урок"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    lesson = get_object_or_404(GroupLesson, id=lesson_id)

    if lesson.teacher.user != request.user:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    if lesson.status != 'scheduled':
        messages.error(request, 'Урок уже завершен или отменен')
        return redirect('teacher_group_lesson_detail', lesson_id=lesson.id)

    lesson.mark_as_completed()

    messages.success(request, 'Групповой урок завершен')
    return redirect('teacher_group_lessons')


# ============================================
# ЧАСТЬ 11: ШАБЛОНЫ РАСПИСАНИЯ
# ============================================

@login_required
def teacher_schedule_templates(request):
    """Список шаблонов расписания учителя"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    teacher = request.user.teacher_profile
    templates = ScheduleTemplate.objects.filter(teacher=teacher).order_by('-created_at')

    context = {
        'templates': templates,
    }
    return render(request, 'school/teacher/schedule_templates.html', context)


@login_required
def teacher_schedule_template_create(request):
    """Создание шаблона расписания"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    teacher = request.user.teacher_profile

    if request.method == 'POST':
        form = ScheduleTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.teacher = teacher
            template.save()
            form.save_m2m()

            messages.success(request, 'Шаблон расписания создан')
            return redirect('teacher_schedule_templates')
    else:
        form = ScheduleTemplateForm()
        form.fields['students'].queryset = teacher.student_set.all()

    context = {
        'form': form,
        'teacher': teacher,
    }
    return render(request, 'school/teacher/schedule_template_form.html', context)


@login_required
def teacher_schedule_template_detail(request, template_id):
    """Детали шаблона и генерация уроков"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    teacher = request.user.teacher_profile
    template = get_object_or_404(ScheduleTemplate, id=template_id, teacher=teacher)

    if request.method == 'POST' and 'generate' in request.POST:
        student_ids = request.POST.getlist('students')
        students = Student.objects.filter(id__in=student_ids, teachers=teacher)

        lessons = template.generate_lessons(students)
        messages.success(request, f'Создано {len(lessons)} уроков')
        return redirect('teacher_schedule_template_detail', template_id=template.id)

    context = {
        'template': template,
        'students': teacher.student_set.all(),
    }
    return render(request, 'school/teacher/schedule_template_detail.html', context)


@login_required
def teacher_schedule_template_delete(request, template_id):
    """Удаление шаблона расписания"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    teacher = request.user.teacher_profile
    template = get_object_or_404(ScheduleTemplate, id=template_id, teacher=teacher)

    if request.method == 'POST':
        template.delete()
        messages.success(request, 'Шаблон успешно удален')
        return redirect('teacher_schedule_templates')

    context = {
        'template': template,
    }
    return render(request, 'school/teacher/schedule_template_confirm_delete.html', context)


# ============================================
# ЧАСТЬ 12: ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

@login_required
def teacher_edit_lesson(request, lesson_id):
    """Редактирование урока учителем"""
    lesson = get_object_or_404(Lesson, id=lesson_id)

    if request.user.role != 'teacher' or lesson.teacher.user != request.user:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    if request.method == 'POST':
        lesson.date = request.POST.get('date')
        lesson.start_time = request.POST.get('start_time')
        lesson.end_time = request.POST.get('end_time')
        lesson.meeting_link = request.POST.get('meeting_link')
        lesson.meeting_platform = request.POST.get('meeting_platform')
        lesson.notes = request.POST.get('notes')
        lesson.save()

        messages.success(request, 'Урок обновлен')
        return redirect('teacher_lesson_detail', lesson_id=lesson.id)

    context = {
        'lesson': lesson,
    }
    return render(request, 'school/teacher/edit_lesson.html', context)


@login_required
def teacher_create_schedule(request):
    """Создание шаблона расписания (разового или повторяющегося)"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    teacher = request.user.teacher_profile

    if request.method == 'POST':
        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')
        topic = request.POST.get('topic', '')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        repeat_type = request.POST.get('repeat_type', 'single')
        notes = request.POST.get('notes', '')

        if not student_id or not subject_id or not start_time_str:
            messages.error(request, 'Заполните все обязательные поля')
            return redirect('teacher_create_schedule')

        student = get_object_or_404(Student, id=student_id, teachers=teacher)
        subject = get_object_or_404(Subject, id=subject_id)

        cost, teacher_payment = StudentSubjectPrice.get_price_for(student, subject)

        try:
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
        except ValueError:
            messages.error(request, 'Неверный формат времени начала')
            return redirect('teacher_create_schedule')

        if not end_time_str:
            today_date = date.today()
            start_dt = datetime.combine(today_date, start_time)
            end_dt = start_dt + timedelta(hours=1)
            end_time = end_dt.time()
        else:
            try:
                end_time = datetime.strptime(end_time_str, '%H:%M').time()
            except ValueError:
                messages.error(request, 'Неверный формат времени окончания')
                return redirect('teacher_create_schedule')

        template = ScheduleTemplate(
            teacher=teacher,
            subject=subject,
            start_time=start_time,
            end_time=end_time,
            repeat_type=repeat_type,
            notes=notes,
            base_cost=cost or Decimal('1000'),
            base_teacher_payment=teacher_payment or (cost or Decimal('1000')) * Decimal('0.7')
        )

        if repeat_type == 'single':
            date_str = request.POST.get('date')
            if not date_str:
                messages.error(request, 'Укажите дату занятия')
                return redirect('teacher_create_schedule')

            template.start_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            template.end_date = None
            template.max_occurrences = 1

        else:
            weekdays = request.POST.getlist('weekdays[]')
            start_date_str = request.POST.get('start_date')
            end_date_str = request.POST.get('end_date')
            max_occurrences = request.POST.get('max_occurrences')

            if not start_date_str:
                messages.error(request, 'Укажите дату начала расписания')
                return redirect('teacher_create_schedule')

            if not weekdays:
                messages.error(request, 'Выберите хотя бы один день недели')
                return redirect('teacher_create_schedule')

            template.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            template.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
            template.max_occurrences = int(max_occurrences) if max_occurrences else None

            template.monday = '1' in weekdays
            template.tuesday = '2' in weekdays
            template.wednesday = '3' in weekdays
            template.thursday = '4' in weekdays
            template.friday = '5' in weekdays
            template.saturday = '6' in weekdays
            template.sunday = '7' in weekdays

        template.save()
        template.students.add(student)

        lessons = template.generate_lessons()

        if repeat_type == 'single':
            messages.success(request, f'Урок создан на {template.start_date} в {start_time_str}')
        else:
            messages.success(request, f'Расписание создано! Сгенерировано {len(lessons)} уроков')

        return redirect('teacher_dashboard')

    students = teacher.student_set.all()
    subjects = teacher.subjects.all()

    context = {
        'teacher': teacher,
        'students': students,
        'subjects': subjects,
        'today': timezone.now().date().strftime('%Y-%m-%d'),
    }
    return render(request, 'school/teacher/schedule_template_form.html', context)


@login_required
def profile(request):
    """Профиль пользователя"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлен')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'school/profile.html', {'form': form})


@login_required
def student_materials(request):
    """Все методические материалы для ученика"""
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    student = request.user.student_profile
    teachers = student.teachers.all()

    materials = Material.objects.filter(
        Q(students=student) | Q(is_public=True) | Q(teachers__in=teachers)
    ).distinct().order_by('-created_at')

    subject_id = request.GET.get('subject')
    if subject_id:
        materials = materials.filter(subjects__id=subject_id)

    material_type = request.GET.get('type')
    if material_type:
        materials = materials.filter(material_type=material_type)

    subjects = Subject.objects.all()

    context = {
        'materials': materials,
        'subjects': subjects,
        'student': student,
    }

    return render(request, 'school/student/materials.html', context)


@login_required
def teacher_materials(request):
    """Управление методическими материалами для учителя"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    teacher = request.user.teacher_profile
    materials = Material.objects.filter(
        Q(teachers=teacher) | Q(created_by=request.user)
    ).distinct().order_by('-created_at')

    student_id = request.GET.get('student')
    if student_id:
        materials = materials.filter(students__id=student_id)

    students = teacher.student_set.all()

    context = {
        'materials': materials,
        'students': students,
        'teacher': teacher,
    }

    return render(request, 'school/teacher/materials.html', context)


@login_required
def teacher_student_detail(request, student_id):
    """Детальная информация об ученике для учителя"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    teacher = request.user.teacher_profile
    student = get_object_or_404(Student, id=student_id, teachers=teacher)

    # ИСПОЛЬЗУЕМ StudentFinanceHelper
    finance_helper = StudentFinanceHelper(student)

    lessons = Lesson.objects.filter(
        teacher=teacher,
        attendance__student=student
    ).select_related('subject', 'format').distinct().order_by('-date')

    notes = StudentNote.objects.filter(teacher=teacher, student=student).order_by('-created_at')

    materials = Material.objects.filter(
        Q(students=student) | Q(is_public=True)
    ).distinct()

    context = {
        'student': student,
        'finance': {
            'balance': float(finance_helper.balance),
            'stats': finance_helper.get_lessons_stats(30)
        },
        'lessons': lessons[:20],
        'notes': notes,
        'materials': materials,
    }

    return render(request, 'school/teacher/student_detail.html', context)


@login_required
def student_calendar(request):
    """Календарь ученика"""
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    student = request.user.student_profile

    lessons = Lesson.objects.filter(student=student).order_by('date', 'start_time')

    calendar_events = []
    for lesson in lessons:
        calendar_events.append({
            'title': f"{lesson.subject.name} - {lesson.teacher.user.get_full_name()}",
            'start': f"{lesson.date}T{lesson.start_time}",
            'end': f"{lesson.date}T{lesson.end_time}",
            'url': f"/lessons/{lesson.id}/",
            'status': lesson.status,
        })

    context = {
        'calendar_events': calendar_events,
    }
    return render(request, 'school/student/calendar.html', context)


# ============================================
# ЧАСТЬ 13: ПОДТВЕРЖДЕНИЕ EMAIL
# ============================================

def verify_email(request, token):
    """Подтверждение email по токену"""
    print(f"\n{'=' * 50}")
    print(f"🔍 verify_email вызван с токеном: {token}")
    print(f"{'=' * 50}\n")

    try:
        verification_token = get_object_or_404(EmailVerificationToken, token=token)

        if not verification_token.is_valid():
            messages.error(
                request,
                'Срок действия ссылки истек. Запросите повторную отправку письма.'
            )
            return redirect('resend_verification')

        user = verification_token.user

        if user.is_email_verified:
            messages.info(request, 'Email уже подтвержден')
            return redirect('login')

        user.is_email_verified = True
        user.save(update_fields=['is_email_verified'])

        try:
            send_verification_success_email(user)
        except Exception as e:
            logger.error(f"Ошибка отправки письма об успехе: {e}")

        verification_token.delete()

        messages.success(
            request,
            '✅ Email успешно подтвержден! Теперь вы можете войти в систему.'
        )

    except EmailVerificationToken.DoesNotExist:
        messages.error(request, '❌ Недействительная ссылка подтверждения')
    except Exception as e:
        traceback.print_exc()
        messages.error(request, f'❌ Ошибка при подтверждении: {str(e)}')

    return redirect('login')


def resend_verification(request):
    """Повторная отправка письма подтверждения"""
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)

            if user.is_email_verified:
                messages.info(
                    request,
                    'Этот email уже подтвержден. Вы можете войти в систему.'
                )
                return redirect('login')

            if user.email_verification_sent:
                time_since = timezone.now() - user.email_verification_sent
                if time_since.total_seconds() < 300:
                    minutes_left = 5 - (time_since.total_seconds() // 60)
                    messages.error(
                        request,
                        f'Письмо уже отправлено. Повторная отправка через {int(minutes_left)} минут'
                    )
                    return redirect('login')

            if send_verification_email(user, request):
                messages.success(
                    request,
                    'Письмо с подтверждением отправлено повторно. Проверьте вашу почту.'
                )
            else:
                messages.error(
                    request,
                    'Ошибка при отправке письма. Попробуйте позже.'
                )

        except User.DoesNotExist:
            messages.success(
                request,
                'Если пользователь с таким email существует, письмо будет отправлено повторно.'
            )

    return render(request, 'school/resend_verification.html')


@login_required
@require_POST
def complete_lesson(request, lesson_id):
    """Завершение урока и создание отчета с учетом явки"""
    lesson = get_object_or_404(Lesson, id=lesson_id)

    if request.user.role != 'teacher' or lesson.teacher.user != request.user:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    if lesson.status != 'scheduled':
        messages.error(request, 'Урок уже завершен или отменен')
        return redirect('teacher_lesson_detail', lesson_id=lesson.id)

    report_data = {
        'topic': request.POST.get('topic'),
        'covered_material': request.POST.get('covered_material'),
        'homework': request.POST.get('homework'),
        'student_progress': request.POST.get('student_progress'),
        'next_lesson_plan': request.POST.get('next_lesson_plan', '')
    }

    required_fields = ['topic', 'covered_material', 'homework', 'student_progress']
    if not all([report_data.get(field) for field in required_fields]):
        messages.error(request, 'Заполните все обязательные поля')
        return redirect('teacher_lesson_detail', lesson_id=lesson.id)

    attended_students = []
    for attendance in lesson.attendance.all():
        if request.POST.get(f'attended_{attendance.id}'):
            attended_students.append(attendance.id)
            attendance.status = 'attended'
            attendance.save()
        else:
            attendance.status = 'absent'
            attendance.save()

    report = lesson.mark_as_completed(report_data, attended_students)

    if report:
        messages.success(request,
                         f'Урок завершен. Отчет #{report.id} создан. Присутствовало: {len(attended_students)} учеников.')
    else:
        messages.success(request, f'Урок завершен. Присутствовало: {len(attended_students)} учеников.')

    return redirect('teacher_lesson_detail', lesson_id=lesson.id)
