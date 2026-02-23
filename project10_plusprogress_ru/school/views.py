from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET, require_POST
from datetime import datetime, date, timedelta
from decimal import Decimal
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
import logging
from django.urls import reverse
import io
import json
import csv
import csv
import openpyxl
from django.contrib import messages
from django.http import HttpResponse
from .models import Lesson, Teacher, Student, Subject, LessonFormat, LessonAttendance
from django.template.loader import render_to_string
from weasyprint import HTML
from .models import Notification
from django.utils.timesince import timesince
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Avg, Count
from .models import Lesson, LessonFeedback, TeacherRating
from .forms import LessonFeedbackForm
from .models import Homework, HomeworkSubmission
from .forms import HomeworkForm, HomeworkSubmissionForm, HomeworkCheckForm
from django.utils import timezone
import uuid
from django.http import JsonResponse
from .forms import LessonReportForm
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
import uuid
import urllib.parse
from .models import ScheduleTemplate, ScheduleTemplateStudent
from .forms import ScheduleTemplateForm
from .models import StudentSubjectPrice
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import EmailVerificationToken
from .utils import send_verification_email, send_verification_success_email
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Lesson, Teacher, Student, Subject, ScheduleTemplate
from .models import ScheduleTemplate, ScheduleTemplateStudent
from .models import (
    User, Teacher, Student, Lesson, Subject,
    LessonReport, Payment, TrialRequest, Schedule,
    Material, Deposit, StudentNote,
    GroupLesson, GroupEnrollment,
)
from .forms import (
    UserRegistrationForm, UserLoginForm, TrialRequestForm,
    LessonReportForm, ProfileUpdateForm
)


def home(request):
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


# school/views.py

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()

                # Отправляем письмо с подтверждением
                from .utils import send_verification_email
                if send_verification_email(user, request):
                    messages.success(
                        request,
                        'Регистрация прошла успешно! '
                        'На ваш email отправлено письмо с подтверждением.'
                    )
                else:
                    messages.warning(
                        request,
                        'Регистрация прошла успешно, но не удалось отправить '
                        'письмо подтверждения. Вы сможете запросить его позже.'
                    )

                # Не логиним пользователя сразу, требуем подтверждение email
                return redirect('login')

            except Exception as e:
                messages.error(request, f'Ошибка при регистрации: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        form = UserRegistrationForm()

    return render(request, 'school/register.html', {'form': form})


# school/views.py

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        print(f"\n{'=' * 60}")
        print(f"🔍 ПОПЫТКА ВХОДА")
        print(f"{'=' * 60}")

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            print(f"📝 Данные формы:")
            print(f"   Username: {username}")
            print(f"   Password: {'*' * len(password)}")

            # 1. Проверяем, есть ли пользователь в БД
            try:
                user_from_db = User.objects.get(username=username)
                print(f"✅ Пользователь найден в БД:")
                print(f"   ID: {user_from_db.id}")
                print(f"   Email: {user_from_db.email}")
                print(f"   is_email_verified: {user_from_db.is_email_verified}")
                print(f"   Role: {user_from_db.role}")
                print(f"   Is active: {user_from_db.is_active}")
            except User.DoesNotExist:
                print(f"❌ Пользователь с username '{username}' не найден в БД")

            # 2. Пытаемся аутентифицировать
            user = authenticate(username=username, password=password)

            if user:
                print(f"✅ Аутентификация успешна!")
                print(f"   User: {user.username}")
                print(f"   is_email_verified: {user.is_email_verified}")

                # 3. Проверяем подтверждение email
                if not user.is_email_verified:
                    print(f"❌ Email НЕ подтвержден!")
                    messages.warning(
                        request,
                        'Пожалуйста, подтвердите ваш email перед входом в систему. '
                        '<a href="{}" class="alert-link">Отправить письмо повторно</a>'.format(
                            reverse('resend_verification')
                        )
                    )
                    return redirect('login')

                # 4. Входим в систему
                login(request, user)
                print(f"✅ Вход выполнен!")

                # 5. Перенаправляем по роли
                if user.role == 'student':
                    print(f"   Перенаправление на student_dashboard")
                    return redirect('student_dashboard')
                elif user.role == 'teacher':
                    print(f"   Перенаправление на teacher_dashboard")
                    return redirect('teacher_dashboard')
                else:
                    print(f"   Перенаправление на admin")
                    return redirect('admin:index')
            else:
                print(f"❌ Аутентификация失败!")
                print(f"   Неверный пароль для пользователя {username}")
                messages.error(request, 'Неверное имя пользователя или пароль')
        else:
            print(f"❌ Форма невалидна:")
            print(f"   Ошибки: {form.errors}")
    else:
        form = UserLoginForm()

    return render(request, 'school/login.html', {'form': form})


@login_required
def user_logout(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    user = request.user

    if user.role == 'student':
        return redirect('student_dashboard')
    elif user.role == 'teacher':
        return redirect('teacher_dashboard')
    else:
        return redirect('admin_dashboard')


@login_required
def student_dashboard(request):
    """Личный кабинет ученика"""
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    # ПОЛНОЕ обновление пользователя из базы данных
    user = User.objects.get(pk=request.user.pk)

    # Получаем профиль ученика
    try:
        student = user.student_profile
    except:
        student = Student.objects.create(user=user)
        messages.info(request, 'Профиль ученика был создан')

    student.refresh_from_db()

    # Получаем баланс
    balance = student.get_balance()

    # Получаем учителей ученика
    teachers = student.teachers.all()

    # Получаем последние депозиты
    recent_deposits = student.deposits.all()[:5]

    # Получаем ближайшие занятия через attendance
    upcoming_lessons = Lesson.objects.filter(
        attendance__student=student,
        date__gte=date.today(),
        status='scheduled'
    ).select_related('teacher__user', 'subject', 'format').distinct().order_by('date', 'start_time')[:10]

    # Получаем последние проведенные занятия через attendance
    past_lessons = Lesson.objects.filter(
        attendance__student=student,
        status='completed'
    ).select_related('teacher__user', 'subject').distinct().order_by('-date')[:10]

    # Получаем методические материалы
    materials = Material.objects.filter(
        Q(students=student) | Q(is_public=True) | Q(teachers__in=teachers)
    ).distinct()[:20]

    # ===== НОВЫЙ КОД: ПОЛУЧАЕМ ДОМАШНИЕ ЗАДАНИЯ =====
    from .models import Homework  # импорт внутри функции
    recent_homeworks = Homework.objects.filter(
        student=student,
        is_active=True
    ).exclude(
        submission__status='checked'
    ).select_related('teacher__user', 'subject').order_by('deadline')[:4]
    # ================================================

    context = {
        'student': student,
        'balance': balance,
        'recent_deposits': recent_deposits,
        'upcoming_lessons': upcoming_lessons,
        'past_lessons': past_lessons,
        'teachers': teachers,
        'materials': materials,
        'recent_homeworks': recent_homeworks,  # ← ДОБАВЛЯЕМ В КОНТЕКСТ
    }

    # Получаем групповые уроки ученика
    group_lessons = GroupLesson.objects.filter(
        enrollments__student=student,
        date__gte=date.today(),
        status='scheduled'
    ).select_related('teacher__user', 'subject')

    # Объединяем с обычными уроками для календаря
    calendar_events = []

    # Обычные уроки
    for lesson in upcoming_lessons:
        calendar_events.append({
            'title': f"{lesson.subject.name} - {lesson.teacher.user.last_name}",
            'start': f"{lesson.date}T{lesson.start_time}",
            'end': f"{lesson.date}T{lesson.end_time}",
            'url': f"/lesson/{lesson.id}/",
            'backgroundColor': '#007bff',
        })

    # Групповые уроки (другим цветом)
    for lesson in group_lessons:
        calendar_events.append({
            'title': f"👥 {lesson.subject.name} (группа)",
            'start': f"{lesson.date}T{lesson.start_time}",
            'end': f"{lesson.date}T{lesson.end_time}",
            'url': f"/student/group-lesson/{lesson.id}/",
            'backgroundColor': '#9b59b6',  # фиолетовый для групп
        })

    context['calendar_events'] = calendar_events

    return render(request, 'school/student/dashboard.html', context)


@login_required
def student_calendar(request):
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    student = request.user.student_profile

    # Получаем все занятия ученика
    lessons = Lesson.objects.filter(student=student).order_by('date', 'start_time')

    # Преобразуем в формат для календаря
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

    # Фильтр по предметам
    subject_id = request.GET.get('subject')
    if subject_id:
        materials = materials.filter(subjects__id=subject_id)

    # Фильтр по типу
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
def student_deposit(request):
    """Пополнение баланса ученика"""
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    if request.method == 'POST':
        amount = request.POST.get('amount')
        description = request.POST.get('description', 'Пополнение счета')

        try:
            amount = float(amount)
            if amount <= 0:
                messages.error(request, 'Сумма должна быть положительной')
                return redirect('student_dashboard')

            student = request.user.student_profile

            # Создаем депозит
            deposit = Deposit.objects.create(
                student=student,
                amount=amount,
                description=description,
                created_by=request.user
            )

            # Обновляем баланс пользователя
            request.user.balance += amount
            request.user.save()

            messages.success(request, f'Счет пополнен на {amount} ₽')

        except (ValueError, TypeError):
            messages.error(request, 'Неверная сумма')

        return redirect('student_dashboard')

    return redirect('student_dashboard')


@login_required
def teacher_dashboard(request):
    """Личный кабинет учителя"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    teacher = request.user.teacher_profile
    today = timezone.now().date()

    # Получаем всех учеников учителя
    students = teacher.student_set.all().select_related('user')

    # Получаем ближайшие занятия
    upcoming_lessons = Lesson.objects.filter(
        teacher=teacher,
        date__gte=today,
        status='scheduled'
    ).select_related('subject').order_by('date', 'start_time')[:20]

    # Получаем занятия на сегодня
    today_lessons = Lesson.objects.filter(
        teacher=teacher,
        date=today,
        status='scheduled'
    ).select_related('subject').order_by('start_time')

    # Получаем прошедшие занятия
    past_lessons = Lesson.objects.filter(
        teacher=teacher,
        status='completed'
    ).select_related('subject').order_by('-date')[:20]

    # ✅ ИСПРАВЛЕННЫЙ КОД: получаем ВСЕ уроки с учениками
    from django.db.models import Prefetch

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

    # Получаем методические материалы
    materials = Material.objects.filter(
        Q(teachers=teacher) | Q(created_by=request.user)
    ).distinct().order_by('-created_at')[:20]

    # Баланс кошелька
    wallet_balance = teacher.wallet_balance

    # Недавние выплаты
    recent_payments = Payment.objects.filter(
        user=request.user,
        payment_type='teacher_payment'
    ).order_by('-created_at')[:10]

    # Подготовка событий для календаря
    calendar_events = []

    for lesson in all_lessons:
        # Определяем цвет в зависимости от статуса
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

        # Формируем заголовок (ИМЯ И ПЕРВА БУКВА ФАМИЛИИ)
        attendance_count = lesson.attendance.count()
        if attendance_count == 0:
            title = "Нет учеников"
        elif attendance_count == 1:
            student = lesson.attendance.first().student
            first_name = student.user.first_name
            last_name_initial = student.user.last_name[0] if student.user.last_name else ''
            title = f"{first_name} {last_name_initial}." if last_name_initial else first_name
        else:
            title = f"{attendance_count} учеников"

        calendar_events.append({
            'title': title,
            'start': f"{lesson.date}T{lesson.start_time}",
            'end': f"{lesson.date}T{lesson.end_time}",
            'url': f"/teacher/lesson/{lesson.id}/",
            'backgroundColor': bg_color,
            'borderColor': bg_color,
            'textColor': 'white',
        })

    context = {
        'teacher': teacher,
        'students': students,
        'upcoming_lessons': upcoming_lessons,
        'today_lessons': today_lessons,
        'past_lessons': past_lessons,
        'all_lessons': all_lessons,  # ← передаем в шаблон
        'materials': materials,
        'wallet_balance': wallet_balance,
        'recent_payments': recent_payments,
        'calendar_events': calendar_events,
    }

    return render(request, 'school/teacher/dashboard.html', context)


@login_required
def teacher_student_detail(request, student_id):
    """Детальная информация об ученике для учителя"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    teacher = request.user.teacher_profile
    student = get_object_or_404(Student, id=student_id, teachers=teacher)

    # Получаем занятия с этим учеником
    lessons = Lesson.objects.filter(
        teacher=teacher,
        student=student
    ).select_related('subject', 'format').order_by('-date')

    # Получаем заметки учителя об этом ученике
    notes = StudentNote.objects.filter(teacher=teacher, student=student).order_by('-created_at')

    # Получаем материалы, доступные ученику
    materials = Material.objects.filter(
        Q(students=student) | Q(is_public=True)
    ).distinct()

    # Статистика
    total_lessons = lessons.count()
    completed_lessons = lessons.filter(status='completed').count()
    total_cost = lessons.filter(status='completed').aggregate(Sum('cost'))['cost__sum'] or 0

    context = {
        'student': student,
        'lessons': lessons[:20],
        'notes': notes,
        'materials': materials,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'total_cost': total_cost,
    }

    return render(request, 'school/teacher/student_detail.html', context)


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

    # Фильтр по ученикам
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
def lesson_detail(request, lesson_id):
    """Детальная страница урока для ученика"""
    lesson = get_object_or_404(Lesson, id=lesson_id)

    user = request.user

    # Проверка доступа для ученика
    if user.role == 'student':
        # Проверяем, есть ли ученик в списке участников урока
        try:
            attendance = lesson.attendance.get(student__user=user)
        except LessonAttendance.DoesNotExist:
            messages.error(request, 'Доступ запрещен')
            return redirect('dashboard')

        # Получаем ВСЕХ участников урока (для отображения группы)
        attendances = lesson.attendance.all().select_related('student__user')

    # Проверка доступа для учителя
    elif user.role == 'teacher' and lesson.teacher.user != user:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    else:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    # Получаем предыдущие уроки с этим учителем (для ученика)
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

    # Обработка POST запроса (оценка урока)
    if request.method == 'POST' and user.role == 'student' and lesson.status == 'completed' and not hasattr(lesson,
                                                                                                            'feedback'):
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')
        is_public = request.POST.get('is_public') == 'on'

        if rating and rating.isdigit():
            from .models import LessonFeedback, TeacherRating

            # Создаем оценку
            feedback = LessonFeedback.objects.create(
                lesson=lesson,
                student=attendance.student,
                teacher=lesson.teacher,
                rating=int(rating),
                comment=comment,
                is_public=is_public
            )

            # Обновляем рейтинг учителя
            teacher_rating, created = TeacherRating.objects.get_or_create(teacher=lesson.teacher)
            teacher_rating.update_stats()

            messages.success(request, 'Спасибо за вашу оценку!')
            return redirect('lesson_detail', lesson_id=lesson.id)
        else:
            messages.error(request, 'Пожалуйста, поставьте оценку')

    context = {
        'lesson': lesson,
        'attendance': attendance,  # текущий ученик
        'attendances': attendances,  # ВСЕ ученики (для отображения группы)
        'report': report,
        'previous_lessons': previous_lessons,
    }
    return render(request, 'school/student/lesson_detail.html', context)


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлен')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'school/profile.html', {'form': form})


@require_GET
def api_schedules(request):
    """API для календаря расписаний"""
    schedules = Schedule.objects.filter(is_active=True).select_related('teacher__user')

    events = []
    today = date.today()

    for schedule in schedules:
        # Генерируем события на месяц вперед
        for i in range(30):
            event_date = today + timedelta(days=i)
            if event_date.weekday() == schedule.day_of_week:
                # Проверяем, есть ли занятие в это время
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


@login_required
def overdue_report(request):
    """Отчет по просроченным занятиям"""
    if request.user.role not in ['admin', 'teacher']:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    # Обновляем статусы просроченных занятий
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

    # Фильтры
    teacher_id = request.GET.get('teacher')
    student_id = request.GET.get('student')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    lessons = Lesson.objects.filter(status='overdue').select_related(
        'teacher__user', 'student__user', 'subject'
    )

    if teacher_id:
        lessons = lessons.filter(teacher_id=teacher_id)
    if student_id:
        lessons = lessons.filter(student_id=student_id)
    if date_from:
        lessons = lessons.filter(date__gte=date_from)
    if date_to:
        lessons = lessons.filter(date__lte=date_to)

    # Статистика
    stats = {
        'total': lessons.count(),
        'by_teacher': lessons.values('teacher__user__last_name').annotate(
            count=Count('id')
        ).order_by('-count'),
        'by_subject': lessons.values('subject__name').annotate(
            count=Count('id')
        ).order_by('-count'),
    }

    context = {
        'lessons': lessons.order_by('-date', '-start_time'),
        'stats': stats,
        'teachers': Teacher.objects.all(),
        'students': Student.objects.all(),
    }

    return render(request, 'school/reports/overdue.html', context)


@staff_member_required
def schedule_calendar_data(request):
    """API для календаря расписаний"""
    schedules = Schedule.objects.filter(is_active=True).select_related('teacher__user')

    events = []
    today = date.today()

    for i in range(60):
        event_date = today + timedelta(days=i)

        # Ищем расписания на эту дату
        day_schedules = schedules.filter(date=event_date)

        for schedule in day_schedules:
            # Ищем занятие на это время
            lesson = Lesson.objects.filter(
                teacher=schedule.teacher,
                date=event_date,
                start_time=schedule.start_time
            ).first()

            start_dt = datetime.combine(event_date, schedule.start_time)
            end_dt = datetime.combine(event_date, schedule.end_time)

            # Определяем цвет
            color = '#79aec8'  # синий по умолчанию (свободно)
            if lesson:
                if lesson.status == 'completed':
                    color = '#28a745'  # зеленый
                elif lesson.status == 'overdue':
                    color = '#dc3545'  # красный
                elif lesson.status == 'scheduled':
                    color = '#007bff'  # синий
                elif lesson.status == 'cancelled':
                    color = '#fd7e14'  # оранжевый

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
                if lesson.student:
                    event['title'] += f" ({lesson.student.user.last_name})"
            else:
                event['title'] = f"{schedule.teacher.user.last_name} - свободно"

            events.append(event)

    return JsonResponse(events, safe=False)


@staff_member_required
@require_POST
def admin_complete_lesson(request, lesson_id):
    """Завершает занятие из админ-панели"""
    try:
        lesson = Lesson.objects.get(pk=lesson_id)

        if lesson.status == 'completed':
            return JsonResponse({'success': False, 'error': 'Занятие уже завершено'})

        report_data = {
            'topic': request.POST.get('topic'),
            'covered_material': request.POST.get('covered_material'),
            'homework': request.POST.get('homework'),
            'student_progress': request.POST.get('student_progress'),
            'next_lesson_plan': request.POST.get('next_lesson_plan', '')
        }

        # Проверяем обязательные поля
        if not all([report_data['topic'], report_data['covered_material'],
                    report_data['homework'], report_data['student_progress']]):
            return JsonResponse({'success': False, 'error': 'Заполните все обязательные поля'})

        report = lesson.mark_as_completed(report_data)

        return JsonResponse({
            'success': True,
            'report_id': report.id,
            'message': f'Занятие завершено. Создан отчет #{report.id}'
        })

    except Lesson.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Занятие не найдено'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@staff_member_required
def student_report(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    # Получаем параметры фильтрации
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Базовый queryset
    lessons = Lesson.objects.filter(student=student)

    # Применяем фильтры по датам
    if date_from:
        lessons = lessons.filter(date__gte=date_from)
    if date_to:
        lessons = lessons.filter(date__lte=date_to)

    # Получаем все уникальные даты занятий
    dates = lessons.dates('date', 'day').order_by('date')

    # Получаем все уникальные предметы
    subjects = lessons.values_list('subject__name', flat=True).distinct()

    # Подготавливаем данные для таблицы
    subjects_data = []
    daily_totals = {date: 0 for date in dates}

    for subject_name in subjects:
        subject_lessons = lessons.filter(subject__name=subject_name)
        daily_costs = []
        subject_total = 0

        for date in dates:
            day_lessons = subject_lessons.filter(date=date)
            day_total = day_lessons.aggregate(Sum('cost'))['cost__sum'] or 0
            daily_costs.append(day_total)
            subject_total += day_total
            daily_totals[date] += day_total

        subjects_data.append({
            'name': subject_name,
            'daily_costs': daily_costs,
            'total': subject_total
        })

    # Агрегация по предметам (для статистики)
    subject_stats = lessons.values(
        'subject__name'
    ).annotate(
        lesson_count=Count('id'),
        total_cost=Sum('cost')
    ).order_by('-total_cost')

    # Общие итоги
    total_lessons = lessons.count()
    total_cost = lessons.aggregate(Sum('cost'))['cost__sum'] or 0

    context = {
        'student': student,
        'subject_stats': subject_stats,
        'total_lessons': total_lessons,
        'total_cost': total_cost,
        'dates': dates,
        'subjects_data': subjects_data,
        'daily_totals': [daily_totals[date] for date in dates],
    }

    return render(request, 'admin/school/student/report.html', context)


@staff_member_required
def teacher_report(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)

    # Получаем параметры фильтрации
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Базовый queryset уроков учителя
    lessons = Lesson.objects.filter(teacher=teacher)

    # Применяем фильтры по датам
    if date_from:
        lessons = lessons.filter(date__gte=date_from)
    if date_to:
        lessons = lessons.filter(date__lte=date_to)

    # Получаем все уникальные даты занятий
    dates = lessons.dates('date', 'day').order_by('date')

    # Получаем всех уникальных учеников с их предметами
    students_lessons = lessons.values(
        'student', 'student__user__last_name', 'student__user__first_name', 'subject__name'
    ).distinct()

    # Подготавливаем данные для таблицы занятий (стоимость для ученика)
    students_data = []
    daily_totals_lessons = {date: Decimal('0') for date in dates}

    for item in students_lessons:
        student_id = item['student']
        student_name = f"{item['student__user__last_name']} {item['student__user__first_name']}"
        subject_name = item['subject__name']

        student_lessons = lessons.filter(
            student_id=student_id,
            subject__name=subject_name
        )

        daily_costs = []
        student_total = Decimal('0')

        for date in dates:
            day_lessons = student_lessons.filter(date=date)
            day_total = day_lessons.aggregate(Sum('cost'))['cost__sum'] or Decimal('0')
            daily_costs.append(day_total)
            student_total += day_total
            daily_totals_lessons[date] += day_total

        students_data.append({
            'name': f"{student_name} ({subject_name})",
            'daily_costs': daily_costs,
            'total': student_total
        })

    # Подготавливаем данные для таблицы выплат (БЕРЕМ ИЗ ПОЛЯ teacher_payment)
    payments_data = []
    daily_totals_payments = {date: Decimal('0') for date in dates}

    for item in students_lessons:
        student_id = item['student']
        student_name = f"{item['student__user__last_name']} {item['student__user__first_name']}"
        subject_name = item['subject__name']

        student_lessons = lessons.filter(
            student_id=student_id,
            subject__name=subject_name
        )

        daily_payments = []
        student_payment_total = Decimal('0')

        for date in dates:
            day_lessons = student_lessons.filter(date=date)
            # Берем сумму выплаты учителю из поля teacher_payment
            day_payment = day_lessons.aggregate(Sum('teacher_payment'))['teacher_payment__sum'] or Decimal('0')
            daily_payments.append(day_payment)
            student_payment_total += day_payment
            daily_totals_payments[date] += day_payment

        payments_data.append({
            'name': f"{student_name} ({subject_name})",
            'daily_payments': daily_payments,
            'total': student_payment_total
        })

    # Общие итоги
    total_lessons = lessons.count()
    total_income = lessons.aggregate(Sum('cost'))['cost__sum'] or Decimal('0')
    total_payment = lessons.aggregate(Sum('teacher_payment'))['teacher_payment__sum'] or Decimal('0')

    context = {
        'teacher': teacher,
        'total_lessons': total_lessons,
        'total_income': total_income,
        'total_payment': total_payment,
        'dates': dates,
        'students_data': students_data,
        'payments_data': payments_data,
        'daily_totals_lessons': [daily_totals_lessons[date] for date in dates],
        'daily_totals_payments': [daily_totals_payments[date] for date in dates],
    }

    return render(request, 'admin/school/teacher/report.html', context)


@staff_member_required
def teacher_payments_dashboard(request):
    """Дашборд для расчета выплат учителям"""
    teachers = Teacher.objects.all().select_related('user')

    # Период по умолчанию: последние 7 дней
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

        # Получаем все проведенные уроки за период
        completed_lessons = Lesson.objects.filter(
            teacher=teacher,
            status='completed',
            date__gte=start_date,
            date__lte=end_date
        ).select_related('student__user', 'subject').order_by('date')

        # Агрегация по предметам
        subject_stats = completed_lessons.values(
            'subject__name'
        ).annotate(
            lesson_count=Count('id'),
            total_payment=Sum('teacher_payment')
        ).order_by('-total_payment')

        # Агрегация по ученикам
        student_stats = completed_lessons.values(
            'student__user__last_name',
            'student__user__first_name',
            'student__user__patronymic'
        ).annotate(
            lesson_count=Count('id'),
            total_payment=Sum('teacher_payment')
        ).order_by('-total_payment')

        # Данные для таблицы по дням
        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date.strftime('%d.%m.%Y'))
            current_date += timedelta(days=1)

        # Собираем данные для сводной таблицы
        lessons_data = []
        for lesson in completed_lessons:
            lessons_data.append({
                'date': lesson.date.strftime('%d.%m.%Y'),
                'student': lesson.student.user.get_full_name(),
                'subject': lesson.subject.name,
                'cost': float(lesson.cost),
                'teacher_payment': float(lesson.teacher_payment),
                'status': lesson.status
            })

        # Итоги
        total_lessons = completed_lessons.count()
        total_cost = completed_lessons.aggregate(Sum('cost'))['cost__sum'] or Decimal('0')
        total_payment = completed_lessons.aggregate(Sum('teacher_payment'))['teacher_payment__sum'] or Decimal('0')

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
                'lessons': total_lessons,
                'cost': float(total_cost),
                'payment': float(total_payment),
            },
            'subject_stats': list(subject_stats),
            'student_stats': list(student_stats),
            'lessons_data': lessons_data,
            'dates': dates,
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@staff_member_required
def export_teacher_payment(request, format, teacher_id, start_date, end_date):
    """Экспорт отчета в разных форматах"""

    teacher = get_object_or_404(Teacher, id=teacher_id)
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Получаем данные
    lessons = Lesson.objects.filter(
        teacher=teacher,
        status='completed',
        date__gte=start,
        date__lte=end
    ).select_related('student__user', 'subject').order_by('date')

    total_payment = lessons.aggregate(Sum('teacher_payment'))['teacher_payment__sum'] or Decimal('0')

    if format == 'excel':
        return export_to_excel(teacher, lessons, start, end, total_payment)
    elif format == 'word':
        return export_to_word(teacher, lessons, start, end, total_payment)
    elif format == 'pdf':
        return export_to_pdf(teacher, lessons, start, end, total_payment)
    else:
        return HttpResponse('Неподдерживаемый формат', status=400)


def export_to_excel(teacher, lessons, start, end, total_payment):
    """Экспорт в Excel"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Расчет выплат"

    # Стили
    title_font = Font(name='Arial', size=14, bold=True)
    header_font = Font(name='Arial', size=11, bold=True)
    normal_font = Font(name='Arial', size=10)

    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font_white = Font(name='Arial', size=11, bold=True, color="FFFFFF")

    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Заголовок
    ws.merge_cells('A1:F1')
    cell = ws['A1']
    cell.value = f"Расчет выплат учителю: {teacher.user.get_full_name()}"
    cell.font = title_font
    cell.alignment = Alignment(horizontal='center')

    # Период
    ws.merge_cells('A2:F2')
    cell = ws['A2']
    cell.value = f"Период: {start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}"
    cell.font = normal_font
    cell.alignment = Alignment(horizontal='center')

    # Пустая строка
    ws.append([])

    # Заголовки таблицы
    headers = ['Дата', 'Ученик', 'Предмет', 'Стоимость урока', 'Выплата учителю', 'Статус']
    ws.append(headers)

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col)
        cell.value = header
        cell.font = header_font_white
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border

    # Данные
    row = 5
    for lesson in lessons:
        ws.cell(row=row, column=1, value=lesson.date.strftime('%d.%m.%Y')).border = thin_border
        ws.cell(row=row, column=2, value=lesson.student.user.get_full_name()).border = thin_border
        ws.cell(row=row, column=3, value=lesson.subject.name).border = thin_border
        ws.cell(row=row, column=4, value=float(lesson.cost)).border = thin_border
        ws.cell(row=row, column=5, value=float(lesson.teacher_payment)).border = thin_border
        ws.cell(row=row, column=6, value=lesson.get_status_display()).border = thin_border

        # Форматирование чисел
        ws.cell(row=row, column=4).number_format = '#,##0.00 ₽'
        ws.cell(row=row, column=5).number_format = '#,##0.00 ₽'
        row += 1

    # Итог
    row += 1
    ws.cell(row=row, column=4, value="ИТОГО:").font = header_font
    ws.cell(row=row, column=5, value=float(total_payment)).font = header_font
    ws.cell(row=row, column=5).number_format = '#,##0.00 ₽'

    # Настройка ширины колонок
    column_widths = [12, 30, 20, 15, 15, 15]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

    # Создаем response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="teacher_payment_{teacher.id}_{start}_{end}.xlsx"'

    wb.save(response)
    return response


def export_to_word(teacher, lessons, start, end, total_payment):
    """Экспорт в Word"""
    doc = Document()

    # Заголовок
    title = doc.add_heading('Расчет выплат учителю', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Информация об учителе
    doc.add_heading('Информация об учителе:', level=1)
    doc.add_paragraph(f'ФИО: {teacher.user.get_full_name()}')
    doc.add_paragraph(f'Email: {teacher.user.email}')
    doc.add_paragraph(f'Телефон: {teacher.user.phone}')

    # Период
    doc.add_heading('Период расчета:', level=1)
    doc.add_paragraph(f'с {start.strftime("%d.%m.%Y")} по {end.strftime("%d.%m.%Y")}')

    # Таблица с уроками
    doc.add_heading('Детализация уроков:', level=1)

    table = doc.add_table(rows=1, cols=5)
    table.style = 'Table Grid'

    # Заголовки
    header_cells = table.rows[0].cells
    headers = ['Дата', 'Ученик', 'Предмет', 'Стоимость', 'Выплата']
    for i, header in enumerate(headers):
        header_cells[i].text = header
        header_cells[i].paragraphs[0].runs[0].font.bold = True

    # Данные
    for lesson in lessons:
        row_cells = table.add_row().cells
        row_cells[0].text = lesson.date.strftime('%d.%m.%Y')
        row_cells[1].text = lesson.student.user.get_full_name()
        row_cells[2].text = lesson.subject.name
        row_cells[3].text = f"{lesson.cost:.2f} ₽"
        row_cells[4].text = f"{lesson.teacher_payment:.2f} ₽"

    # Итог
    doc.add_paragraph()
    total_para = doc.add_paragraph()
    total_para.add_run('ИТОГО К ВЫПЛАТЕ: ').bold = True
    total_para.add_run(f'{total_payment:.2f} ₽').bold = True

    # Сохраняем
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="teacher_payment_{teacher.id}_{start}_{end}.docx"'

    doc.save(response)
    return response


def export_to_pdf(teacher, lessons, start, end, total_payment):
    """Экспорт в PDF"""
    buffer = io.BytesIO()

    # Создаем PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Заголовок
    title = Paragraph(f"Расчет выплат учителю", styles['Title'])
    elements.append(title)
    elements.append(Paragraph(f"<b>{teacher.user.get_full_name()}</b>", styles['Normal']))
    elements.append(Paragraph(f"Период: {start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}", styles['Normal']))
    elements.append(Paragraph("<br/>", styles['Normal']))

    # Таблица
    data = [['Дата', 'Ученик', 'Предмет', 'Стоимость', 'Выплата']]

    for lesson in lessons:
        data.append([
            lesson.date.strftime('%d.%m.%Y'),
            lesson.student.user.get_full_name(),
            lesson.subject.name,
            f"{lesson.cost:.2f} ₽",
            f"{lesson.teacher_payment:.2f} ₽"
        ])

    # Итог
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

    # Сборка PDF
    doc.build(elements)

    # Сохраняем
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="teacher_payment_{teacher.id}_{start}_{end}.pdf"'

    return response


@staff_member_required
def admin_lesson_export(request, format):
    """Экспорт уроков из админки"""
    # Получаем все уроки с фильтрацией (как в админке)
    lessons = Lesson.objects.all().select_related(
        'teacher__user', 'student__user', 'subject', 'format'
    ).order_by('-date', 'start_time')

    # Применяем фильтры из GET-параметров (как в админке)
    teacher_id = request.GET.get('teacher__id__exact')
    student_id = request.GET.get('student__id__exact')
    subject_id = request.GET.get('subject__id__exact')
    status = request.GET.get('status__exact')
    date_from = request.GET.get('date__gte')
    date_to = request.GET.get('date__lte')

    if teacher_id:
        lessons = lessons.filter(teacher_id=teacher_id)
    if student_id:
        lessons = lessons.filter(student_id=student_id)
    if subject_id:
        lessons = lessons.filter(subject_id=subject_id)
    if status:
        lessons = lessons.filter(status=status)
    if date_from:
        lessons = lessons.filter(date__gte=date_from)
    if date_to:
        lessons = lessons.filter(date__lte=date_to)

    # Подсчет статистики
    completed_count = lessons.filter(status='completed').count()
    cancelled_count = lessons.filter(status='cancelled').count()
    overdue_count = lessons.filter(status='overdue').count()
    total_cost = lessons.aggregate(Sum('cost'))['cost__sum'] or 0
    total_payment = lessons.aggregate(Sum('teacher_payment'))['teacher_payment__sum'] or 0

    title = f"Экспорт уроков"

    # Выбор формата экспорта
    if format == 'excel':
        return export_lessons_excel(lessons, title, request, completed_count, cancelled_count, overdue_count,
                                    total_cost, total_payment)
    elif format == 'csv':
        return export_lessons_csv(lessons, title, request, completed_count, cancelled_count, overdue_count, total_cost,
                                  total_payment)
    elif format == 'html':
        return export_lessons_html(lessons, title, request, completed_count, cancelled_count, overdue_count, total_cost,
                                   total_payment)
    elif format == 'pdf':
        return export_lessons_pdf(lessons, title, request, completed_count, cancelled_count, overdue_count, total_cost,
                                  total_payment)
    else:
        messages.error(request, 'Неподдерживаемый формат')
        return redirect(request.META.get('HTTP_REFERER', 'admin:school_lesson_changelist'))


def export_lessons_excel(lessons, title, request, completed_count, cancelled_count, overdue_count, total_cost,
                         total_payment):
    """Экспорт уроков в Excel"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Уроки"

    # Стили
    title_font = Font(name='Arial', size=16, bold=True)
    header_font = Font(name='Arial', size=12, bold=True)

    header_fill = PatternFill(start_color="417690", end_color="417690", fill_type="solid")
    header_font_white = Font(name='Arial', size=12, bold=True, color="FFFFFF")

    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Заголовок
    ws.merge_cells('A1:I1')
    cell = ws['A1']
    cell.value = title
    cell.font = title_font
    cell.alignment = Alignment(horizontal='center')

    # Дата экспорта
    ws.merge_cells('A2:I2')
    cell = ws['A2']
    cell.value = f"Дата экспорта: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    cell.font = Font(italic=True)
    cell.alignment = Alignment(horizontal='center')

    # Статистика
    ws.merge_cells('A3:I3')
    cell = ws['A3']
    cell.value = f"Всего: {lessons.count()} | Проведено: {completed_count} | Отменено: {cancelled_count} | Просрочено: {overdue_count} | Сумма: {total_cost:,.2f} ₽ | Выплаты: {total_payment:,.2f} ₽"
    cell.font = Font(bold=True)
    cell.alignment = Alignment(horizontal='center')

    # Пустая строка
    ws.append([])

    # Заголовки таблицы
    headers = ['ID урока', 'Дата', 'Время', 'ID учителя', 'Учитель', 'ID ученика', 'Ученик', 'Предмет', 'Стоимость',
               'Выплата учителю', 'Статус']

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=5, column=col)
        cell.value = header
        cell.font = header_font_white
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border

    # Данные
    row = 6
    for lesson in lessons:
        ws.cell(row=row, column=1, value=lesson.id).border = thin_border
        ws.cell(row=row, column=2, value=lesson.date.strftime('%d.%m.%Y')).border = thin_border
        ws.cell(row=row, column=3,
                value=f"{lesson.start_time.strftime('%H:%M')}-{lesson.end_time.strftime('%H:%M')}").border = thin_border
        ws.cell(row=row, column=4, value=lesson.teacher.user.get_full_name()).border = thin_border
        ws.cell(row=row, column=5, value=lesson.student.user.get_full_name()).border = thin_border
        ws.cell(row=row, column=6, value=lesson.subject.name).border = thin_border
        ws.cell(row=row, column=7, value=float(lesson.cost)).border = thin_border
        ws.cell(row=row, column=8, value=float(lesson.teacher_payment)).border = thin_border
        ws.cell(row=row, column=9, value=lesson.get_status_display()).border = thin_border

        # Форматирование чисел
        ws.cell(row=row, column=7).number_format = '#,##0.00 ₽'
        ws.cell(row=row, column=8).number_format = '#,##0.00 ₽'

        # Цвет статуса
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

    # Итоговая строка
    row += 1
    ws.cell(row=row, column=6, value="ИТОГО:").font = Font(bold=True)
    ws.cell(row=row, column=7, value=float(total_cost)).font = Font(bold=True)
    ws.cell(row=row, column=7).number_format = '#,##0.00 ₽'
    ws.cell(row=row, column=8, value=float(total_payment)).font = Font(bold=True)
    ws.cell(row=row, column=8).number_format = '#,##0.00 ₽'

    # Настройка ширины колонок
    column_widths = [8, 12, 15, 25, 25, 20, 15, 18, 15]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

    # Создаем response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"lessons_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    wb.save(response)
    return response


def export_lessons_csv(lessons, title, request, completed_count, cancelled_count, overdue_count, total_cost,
                       total_payment):
    """Экспорт уроков в CSV"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    filename = f"lessons_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Добавляем BOM для корректного отображения русских букв
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';')

    # Заголовок
    writer.writerow([title])
    writer.writerow([f"Дата экспорта: {datetime.now().strftime('%d.%m.%Y %H:%M')}"])
    writer.writerow([
        f"Всего: {lessons.count()} | Проведено: {completed_count} | Отменено: {cancelled_count} | Просрочено: {overdue_count}"])
    writer.writerow([f"Общая стоимость: {total_cost:.2f} ₽ | Общая сумма выплат: {total_payment:.2f} ₽"])
    writer.writerow([])

    # Заголовки таблицы
    writer.writerow(['ID', 'Дата', 'Время', 'Учитель', 'Ученик', 'Предмет', 'Стоимость', 'Выплата учителю', 'Статус'])

    # Данные
    for lesson in lessons:
        writer.writerow([
            lesson.id,
            lesson.date.strftime('%d.%m.%Y'),
            f"{lesson.start_time.strftime('%H:%M')}-{lesson.end_time.strftime('%H:%M')}",
            lesson.teacher.user.get_full_name(),
            lesson.student.user.get_full_name(),
            lesson.subject.name,
            f"{lesson.cost:.2f}",
            f"{lesson.teacher_payment:.2f}",
            lesson.get_status_display(),
        ])

    return response


def export_lessons_html(lessons, title, request, completed_count, cancelled_count, overdue_count, total_cost,
                        total_payment):
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


def export_lessons_pdf(lessons, title, request, completed_count, cancelled_count, overdue_count, total_cost,
                       total_payment):
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

    # Генерируем PDF
    response = HttpResponse(content_type='application/pdf')
    filename = f"lessons_export_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    HTML(string=html_string).write_pdf(response)

    return response


def export_lessons(request):
    """Экспорт уроков в разных форматах"""
    export_format = request.GET.get('export')

    # Получаем отфильтрованные уроки (как в админке)
    lessons = Lesson.objects.all()

    # Применяем те же фильтры, что и в админке
    # (здесь нужно добавить фильтрацию по GET параметрам)

    if export_format == 'excel':
        return export_excel(lessons)
    elif export_format == 'csv':
        return export_csv(lessons)
    elif export_format == 'pdf':
        return export_pdf(lessons)
    else:
        return redirect(request.META.get('HTTP_REFERER', 'admin:school_lesson_changelist'))


def export_excel(lessons):
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="lessons.xlsx"'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Уроки"

    # Заголовки
    headers = ['ID', 'Дата', 'Время', 'Учитель', 'Ученик', 'Предмет', 'Стоимость', 'Статус']
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)

    # Данные
    for row, lesson in enumerate(lessons, 2):
        ws.cell(row=row, column=1, value=lesson.id)
        ws.cell(row=row, column=2, value=lesson.date.strftime('%d.%m.%Y'))
        ws.cell(row=row, column=3, value=f"{lesson.start_time}-{lesson.end_time}")
        ws.cell(row=row, column=4, value=str(lesson.teacher))
        ws.cell(row=row, column=5, value=str(lesson.student))
        ws.cell(row=row, column=6, value=lesson.subject.name)
        ws.cell(row=row, column=7, value=float(lesson.cost))
        ws.cell(row=row, column=8, value=lesson.get_status_display())

    wb.save(response)
    return response


def export_csv(lessons):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="lessons.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Дата', 'Время', 'Учитель', 'Ученик', 'Предмет', 'Стоимость', 'Статус'])

    for lesson in lessons:
        writer.writerow([
            lesson.id,
            lesson.date.strftime('%d.%m.%Y'),
            f"{lesson.start_time}-{lesson.end_time}",
            str(lesson.teacher),
            str(lesson.student),
            lesson.subject.name,
            lesson.cost,
            lesson.get_status_display()
        ])

    return response


def export_pdf(lessons):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="lessons.pdf"'

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # Заголовок
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "Экспорт уроков")

    # Таблица (упрощенно)
    p.setFont("Helvetica", 10)
    y = height - 100

    for lesson in lessons[:30]:  # Ограничим 30 записями для PDF
        p.drawString(50, y, lesson.date.strftime('%d.%m.%Y'))
        p.drawString(120, y, str(lesson.teacher))
        p.drawString(250, y, str(lesson.student))
        p.drawString(400, y, lesson.subject.name)
        p.drawString(500, y, f"{lesson.cost}₽")
        y -= 20

        if y < 50:
            p.showPage()
            y = height - 50

    p.save()
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


def import_lessons(request):
    """Импорт уроков из Excel или CSV"""
    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            messages.error(request, 'Выберите файл для импорта')
            return redirect('admin:school_lesson_changelist')

        # Определяем формат по расширению
        if file.name.endswith('.csv'):
            return import_from_csv(file, request)
        elif file.name.endswith(('.xlsx', '.xls')):
            return import_from_excel(file, request)
        else:
            messages.error(request, 'Поддерживаются только файлы CSV и Excel (.xlsx, .xls)')
            return redirect('admin:school_lesson_changelist')

    # GET запрос - показываем форму импорта
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
                # Поиск связанных объектов
                teacher = Teacher.objects.get(user__last_name=row.get('Учитель', '').strip())
                student = Student.objects.get(user__last_name=row.get('Ученик', '').strip())
                subject = Subject.objects.get(name=row.get('Предмет', '').strip())

                # Парсинг даты
                date_str = row.get('Дата', '').strip()
                if date_str:
                    date = datetime.strptime(date_str, '%d.%m.%Y').date()
                else:
                    raise ValueError("Дата не указана")

                # Парсинг времени
                start_time_str = row.get('Время начала', '').strip()
                end_time_str = row.get('Время окончания', '').strip()

                if start_time_str:
                    start_time = datetime.strptime(start_time_str, '%H:%M').time()
                else:
                    raise ValueError("Время начала не указано")

                if end_time_str:
                    end_time = datetime.strptime(end_time_str, '%H:%M').time()
                else:
                    # Если время окончания не указано, ставим +1 час
                    from datetime import timedelta
                    start_dt = datetime.combine(date, start_time)
                    end_dt = start_dt + timedelta(hours=1)
                    end_time = end_dt.time()

                # Стоимость
                cost = float(row.get('Стоимость', 0).replace(',', '.')) if row.get('Стоимость') else 0
                teacher_payment = float(row.get('Выплата учителю', 0).replace(',', '.')) if row.get(
                    'Выплата учителю') else cost * 0.5

                # Статус
                status = row.get('Статус', 'scheduled').strip().lower()
                if status not in ['scheduled', 'completed', 'cancelled', 'overdue']:
                    status = 'scheduled'

                # Создание урока
                Lesson.objects.create(
                    teacher=teacher,
                    student=student,
                    subject=subject,
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    cost=cost,
                    teacher_payment=teacher_payment,
                    status=status,
                )
                success_count += 1

            except Teacher.DoesNotExist:
                error_count += 1
                errors.append(f"Строка {row_num}: Учитель '{row.get('Учитель')}' не найден")
            except Student.DoesNotExist:
                error_count += 1
                errors.append(f"Строка {row_num}: Ученик '{row.get('Ученик')}' не найден")
            except Subject.DoesNotExist:
                error_count += 1
                errors.append(f"Строка {row_num}: Предмет '{row.get('Предмет')}' не найден")
            except Exception as e:
                error_count += 1
                errors.append(f"Строка {row_num}: {str(e)}")

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


def find_teacher_by_full_name(name):
    """Поиск учителя по полному имени (фамилия имя отчество)"""
    if not name:
        return None

    name = str(name).strip()
    if not name:
        return None

    # Разбиваем имя на части
    name_parts = name.split()
    if not name_parts:
        return None

    # Пробуем найти по фамилии (первое слово)
    last_name = name_parts[0]
    teachers = Teacher.objects.filter(user__last_name__icontains=last_name)

    if teachers.exists():
        if teachers.count() == 1:
            return teachers.first()

        # Если несколько учителей с такой фамилией, пробуем уточнить по имени
        if len(name_parts) > 1:
            first_name = name_parts[1]
            teachers = teachers.filter(user__first_name__icontains=first_name)
            if teachers.exists():
                return teachers.first()

    # Если не нашли, пробуем поиск по полному имени
    for teacher in Teacher.objects.all():
        full_name = teacher.user.get_full_name().lower()
        if name.lower() in full_name:
            return teacher

    return None


def find_student_by_full_name(name):
    """Поиск ученика по полному имени (фамилия имя отчество)"""
    if not name:
        return None

    name = str(name).strip()
    if not name:
        return None

    # Разбиваем имя на части
    name_parts = name.split()
    if not name_parts:
        return None

    # Пробуем найти по фамилии
    last_name = name_parts[0]
    students = Student.objects.filter(user__last_name__icontains=last_name)

    if students.exists():
        if students.count() == 1:
            return students.first()

        # Если несколько, уточняем по имени
        if len(name_parts) > 1:
            first_name = name_parts[1]
            students = students.filter(user__first_name__icontains=first_name)
            if students.exists():
                return students.first()

    # Поиск по полному имени
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


def import_from_excel(file, request):
    """Импорт из Excel с поддержкой ID"""
    try:
        import tempfile
        import os
        from datetime import datetime as dt

        # Сохраняем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            for chunk in file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        wb = openpyxl.load_workbook(tmp_path)
        ws = wb.active

        # Получаем заголовки (первая строка)
        headers = [cell.value for cell in ws[1] if cell.value]

        success_count = 0
        error_count = 0
        errors = []

        for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if not any(row):
                continue

            try:
                # Создаем словарь из строки
                row_dict = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        row_dict[header] = row[i]

                # Поиск учителя по ID или ФИО (для обратной совместимости)
                teacher_id = row_dict.get('ID учителя')
                teacher = None

                if teacher_id:
                    teacher = find_teacher_by_id(teacher_id)
                    if not teacher:
                        raise ValueError(f"Учитель с ID '{teacher_id}' не найден")
                else:
                    # Если ID нет, пробуем по ФИО (старый формат)
                    teacher_name = str(row_dict.get('Учитель', '')).strip()
                    teacher = find_teacher_by_full_name(teacher_name)
                    if not teacher:
                        raise ValueError(f"Учитель '{teacher_name}' не найден")

                # Поиск учеников по ID или ФИО
                students = []

                # Пробуем сначала по ID учеников
                student_ids_str = row_dict.get('ID учеников', '')
                if student_ids_str:
                    student_ids = [s.strip() for s in str(student_ids_str).split(';') if s.strip()]
                    for student_id in student_ids:
                        student = find_student_by_id(student_id)
                        if not student:
                            raise ValueError(f"Ученик с ID '{student_id}' не найден")
                        students.append(student)
                else:
                    # Если ID нет, пробуем по ФИО
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

                # ... остальной код создания урока ...

                success_count += 1

            except Exception as e:
                error_count += 1
                errors.append(f"Строка {row_num}: {str(e)}")

        # ... остальной код ...

    except Exception as e:
        messages.error(request, f'Ошибка при импорте: {str(e)}')
        return redirect('admin:school_lesson_changelist')


def download_import_template(request):
    """Скачать шаблон для импорта с поддержкой ID"""
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="import_lessons_template.xlsx"'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Импорт уроков"

    # Заголовки
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

    # Примеры данных
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

    # Настройка ширины колонок
    column_widths = [12, 15, 15, 12, 25, 15, 30, 20, 15, 15, 15]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

    wb.save(response)
    return response


@login_required
def get_notifications(request):
    """API для получения уведомлений (для AJAX)"""
    try:
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:20]
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

        notifications_data = []
        for n in notifications:
            # Вычисляем "сколько времени назад" безопасно
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

        data = {
            'unread_count': unread_count,
            'notifications': notifications_data
        }

        # Для отладки
        print(f"📨 Уведомления для {request.user}: {len(notifications_data)} шт., непрочитано: {unread_count}")

        return JsonResponse(data)

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

        # Получаем обновленное количество непрочитанных
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

        print(f"✅ Уведомление {notification_id} отмечено как прочитанное для {request.user}")

        return JsonResponse({
            'status': 'ok',
            'unread_count': unread_count,
            'message': 'Уведомление отмечено как прочитанное'
        })
    except Notification.DoesNotExist:
        print(f"❌ Уведомление {notification_id} не найдено для {request.user}")
        return JsonResponse({'status': 'error', 'message': 'Уведомление не найдено'}, status=404)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def mark_all_notifications_read(request):
    """Отметить все уведомления как прочитанные"""
    try:
        count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        print(f"✅ Отмечено {count} уведомлений как прочитанные для {request.user}")
        return JsonResponse({
            'status': 'ok',
            'count': count,
            'message': f'Отмечено {count} уведомлений'
        })
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def lesson_feedback(request, lesson_id):
    """Страница оценки урока"""
    lesson = get_object_or_404(Lesson, id=lesson_id)

    # Проверяем, что ученик имеет право оценивать
    if request.user.role != 'student' or lesson.student.user != request.user:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    # Проверяем, что урок проведен
    if lesson.status != 'completed':
        messages.error(request, 'Можно оценивать только проведенные уроки')
        return redirect('student_dashboard')

    # Проверяем, не оценивал ли уже
    if hasattr(lesson, 'feedback'):
        messages.info(request, 'Вы уже оценили этот урок')
        return redirect('student_dashboard')

    if request.method == 'POST':
        form = LessonFeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.lesson = lesson
            feedback.student = lesson.student
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

    # Статистика
    stats = feedbacks.aggregate(
        avg_rating=Avg('rating'),
        total=Count('id')
    )

    # Распределение по звездам
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


@login_required
def teacher_homeworks(request):
    """Список заданий для учителя"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    teacher = request.user.teacher_profile

    # Фильтры
    student_id = request.GET.get('student')
    status = request.GET.get('status')

    homeworks = Homework.objects.filter(teacher=teacher).select_related(
        'student__user', 'subject'
    ).prefetch_related('submission')

    if student_id:
        homeworks = homeworks.filter(student_id=student_id)

    students = Student.objects.filter(teachers=teacher)

    # Статистика
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
            homework.subject = student.subjects.first()  # Или выбрать предмет
            homework.save()

            # Уведомление ученику
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
    """Детали задания для учителя (с возможностью проверки)"""
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

            # Уведомление ученику о проверке
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

    # Фильтры
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

    # Статистика
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
    """Детали задания для ученика (с возможностью сдачи)"""
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    student = request.user.student_profile
    homework = get_object_or_404(Homework, id=homework_id, student=student)

    # Проверяем, есть ли уже сданное задание
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


from django.http import JsonResponse
import uuid


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
def complete_lesson(request, lesson_id):
    """Завершение урока и создание отчета с учетом явки"""
    lesson = get_object_or_404(Lesson, id=lesson_id)

    if request.user.role != 'teacher' or lesson.teacher.user != request.user:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    if lesson.status != 'scheduled':
        messages.error(request, 'Урок уже завершен или отменен')
        return redirect('teacher_lesson_detail', lesson_id=lesson.id)

    # Получаем данные формы
    report_data = {
        'topic': request.POST.get('topic'),
        'covered_material': request.POST.get('covered_material'),
        'homework': request.POST.get('homework'),
        'student_progress': request.POST.get('student_progress'),
        'next_lesson_plan': request.POST.get('next_lesson_plan', '')
    }

    # Проверка обязательных полей
    required_fields = ['topic', 'covered_material', 'homework', 'student_progress']
    if not all([report_data.get(field) for field in required_fields]):
        messages.error(request, 'Заполните все обязательные поля')
        return redirect('teacher_lesson_detail', lesson_id=lesson.id)

    # Обрабатываем отметки явки
    attended_students = []
    for attendance in lesson.attendance.all():
        if request.POST.get(f'attended_{attendance.id}'):
            attended_students.append(attendance.id)
            attendance.status = 'attended'
            attendance.save()
        else:
            attendance.status = 'absent'
            attendance.save()

    # Отмечаем урок как проведенный
    report = lesson.mark_as_completed(report_data, attended_students)

    if report:
        messages.success(request,
                         f'Урок завершен. Отчет #{report.id} создан. Присутствовало: {len(attended_students)} учеников.')
    else:
        messages.success(request, f'Урок завершен. Присутствовало: {len(attended_students)} учеников.')

    return redirect('teacher_lesson_detail', lesson_id=lesson.id)


@login_required
def teacher_lesson_detail(request, lesson_id):
    """Детальная страница урока для учителя"""
    lesson = get_object_or_404(Lesson, id=lesson_id)

    if request.user.role != 'teacher' or lesson.teacher.user != request.user:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    # Получаем все записи посещаемости с учениками
    attendances = lesson.attendance.all().select_related('student__user')

    # Общая стоимость (для информации)
    total_cost = sum([a.cost for a in attendances]) if attendances else 0

    # ВЫПЛАТА УЧИТЕЛЮ - считаем по ВСЕМ ученикам, независимо от статуса!
    # Учитель получает деньги за всех, кто был на уроке (attended)
    # Статус 'debt' означает, что ученик должен школе, но учитель всё равно получает
    teacher_payment = sum([a.teacher_payment_share for a in attendances]) if attendances else 0

    print(f"DEBUG: Всего учеников: {attendances.count()}")
    for a in attendances:
        print(f"  {a.student.user.get_full_name()}: статус={a.status}, выплата={a.teacher_payment_share}")
    print(f"DEBUG: total_cost = {total_cost}, teacher_payment = {teacher_payment}")

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
        'attendances': attendances,
        'total_cost': total_cost,
        'teacher_payment': teacher_payment,  # Теперь считаем всех учеников
        'report': report,
        'form': form,
        'previous_lessons': previous_lessons,
        'homeworks': homeworks,
    }
    return render(request, 'school/teacher/lesson_detail.html', context)


@login_required
@require_POST
def create_video_room(request, lesson_id):
    """Учитель создает видео-комнату для урока"""
    from .models import Lesson

    try:
        lesson = get_object_or_404(Lesson, id=lesson_id)

        # Только учитель может создать комнату
        if request.user.role != 'teacher' or lesson.teacher.user != request.user:
            return JsonResponse({'error': 'Доступ запрещен'}, status=403)

        # Проверяем статус урока
        if lesson.status != 'scheduled':
            return JsonResponse({'error': 'Урок уже проведен или отменен'}, status=400)

        # Если комната уже есть, возвращаем её
        if not lesson.video_room:
            lesson.video_room = str(uuid.uuid4())[:8]
            lesson.save()

        return JsonResponse({
            'success': True,
            'room': lesson.video_room
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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

    # Проверка, что это урок этого учителя
    if lesson.teacher.user != request.user:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    # Получаем записи учеников
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

    # Завершаем урок (списываем деньги, начисляем выплату)
    lesson.mark_as_completed()

    messages.success(request, 'Групповой урок завершен')
    return redirect('teacher_group_lessons')


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
            form.save_m2m()  # сохраняем учеников

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
        # Генерируем уроки для выбранных учеников
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
def teacher_edit_lesson(request, lesson_id):
    """Редактирование урока учителем"""
    lesson = get_object_or_404(Lesson, id=lesson_id)

    if request.user.role != 'teacher' or lesson.teacher.user != request.user:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    if request.method == 'POST':
        # Обновляем поля урока
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


def create_lesson_with_prices(teacher, student, subject, date, start_time, end_time):
    """Создание урока с автоматической подстановкой цен"""

    # Получаем цены для этого ученика и предмета
    cost, teacher_payment = StudentSubjectPrice.get_price_for(student, subject)

    # Если цены не найдены, используем стандартные
    if cost is None:
        cost = subject.default_cost or 1000  # значение по умолчанию
    if teacher_payment is None:
        teacher_payment = subject.default_teacher_payment or cost * 0.7

    lesson = Lesson.objects.create(
        teacher=teacher,
        student=student,
        subject=subject,
        date=date,
        start_time=start_time,
        end_time=end_time,
        base_cost=cost,
        base_teacher_payment=teacher_payment
    )

    return lesson


@staff_member_required
def import_students(request):
    """Импорт учеников из Excel"""
    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            messages.error(request, 'Выберите файл для импорта')
            return redirect('admin:school_student_changelist')

        try:
            import openpyxl
            wb = openpyxl.load_workbook(file)
            ws = wb.active

            success_count = 0
            error_count = 0
            errors = []

            for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if not any(row):
                    continue

                try:
                    # Ожидаемый формат: ID, Фамилия, Имя, Отчество, Email, Телефон, Родитель, Телефон родителя
                    student_id = row[0]
                    last_name = row[1]
                    first_name = row[2]
                    patronymic = row[3]
                    email = row[4]
                    phone = row[5]
                    parent_name = row[6]
                    parent_phone = row[7]

                    # Создаем или обновляем пользователя
                    if student_id:
                        # Обновляем существующего
                        user = User.objects.get(id=student_id)
                    else:
                        # Создаем нового
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

                    # Создаем или обновляем профиль ученика
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
            import openpyxl
            wb = openpyxl.load_workbook(file)
            ws = wb.active

            success_count = 0
            error_count = 0
            errors = []

            for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if not any(row):
                    continue

                try:
                    # Ожидаемый формат: ID, Фамилия, Имя, Отчество, Email, Телефон, Предметы, Опыт, Образование
                    teacher_id = row[0]
                    last_name = row[1]
                    first_name = row[2]
                    patronymic = row[3]
                    email = row[4]
                    phone = row[5]
                    subjects_str = row[6]
                    experience = row[7]
                    education = row[8]

                    # Создаем или обновляем пользователя
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

                    # Создаем или обновляем профиль учителя
                    teacher, created = Teacher.objects.get_or_create(user=user)
                    teacher.experience = experience or 0
                    teacher.education = education or ''
                    teacher.save()

                    # Добавляем предметы
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


# school/views.py


logger = logging.getLogger(__name__)


def verify_email(request, token):
    """Подтверждение email по токену"""
    print(f"\n{'=' * 50}")
    print(f"🔍 verify_email вызван с токеном: {token}")
    print(f"📝 Request path: {request.path}")
    print(f"👤 User authenticated: {request.user.is_authenticated}")
    print(f"{'=' * 50}\n")

    try:
        # Ищем токен
        print(f"🔎 Ищем токен в БД...")
        verification_token = get_object_or_404(EmailVerificationToken, token=token)

        print(f"✅ Токен найден!")
        print(f"   Пользователь: {verification_token.user.username}")
        print(f"   Email: {verification_token.user.email}")
        print(f"   Создан: {verification_token.created_at}")
        print(f"   Истекает: {verification_token.expires_at}")
        print(f"   Действителен: {verification_token.is_valid()}")
        print(f"   Email верифицирован сейчас: {verification_token.user.is_email_verified}")

        # Проверяем, не истек ли токен
        if not verification_token.is_valid():
            print(f"❌ Токен истек!")
            messages.error(
                request,
                'Срок действия ссылки истек. Запросите повторную отправку письма.'
            )
            return redirect('resend_verification')

        user = verification_token.user

        # Проверяем, не подтвержден ли уже email
        if user.is_email_verified:
            print(f"ℹ️ Email уже подтвержден")
            messages.info(request, 'Email уже подтвержден')
            return redirect('login')

        # Подтверждаем email
        print(f"🔄 Подтверждаем email...")
        user.is_email_verified = True
        user.save(update_fields=['is_email_verified'])
        print(f"✅ Email подтвержден!")

        # Отправляем письмо об успехе
        try:
            print(f"📧 Отправляем письмо об успехе...")
            from .utils import send_verification_success_email
            send_verification_success_email(user)
            print(f"✅ Письмо об успехе отправлено")
        except Exception as e:
            print(f"⚠️ Ошибка при отправке письма об успехе: {e}")
            logger.error(f"Ошибка отправки письма об успехе: {e}")

        # Удаляем использованный токен
        print(f"🗑️ Удаляем токен...")
        verification_token.delete()
        print(f"✅ Токен удален")

        messages.success(
            request,
            '✅ Email успешно подтвержден! Теперь вы можете войти в систему.'
        )
        print(f"🎉 Процесс завершен успешно!")

    except EmailVerificationToken.DoesNotExist:
        print(f"❌ Токен не найден в БД!")
        messages.error(request, '❌ Недействительная ссылка подтверждения')
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'❌ Ошибка при подтверждении: {str(e)}')

    print(f"↩️ Редирект на login\n")
    return redirect('login')


def resend_verification(request):
    """Повторная отправка письма подтверждения"""
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            # Убираем фильтр is_email_verified=False
            user = User.objects.get(email=email)

            print(f"📧 Найден пользователь: {user.username}")
            print(f"   is_email_verified: {user.is_email_verified}")

            # Если уже подтвержден
            if user.is_email_verified:
                messages.info(
                    request,
                    'Этот email уже подтвержден. Вы можете войти в систему.'
                )
                return redirect('login')

            # Проверяем, не отправляли ли письмо недавно
            if user.email_verification_sent:
                time_since = timezone.now() - user.email_verification_sent
                if time_since.total_seconds() < 300:  # 5 минут
                    minutes_left = 5 - (time_since.total_seconds() // 60)
                    messages.error(
                        request,
                        f'Письмо уже отправлено. Повторная отправка через {int(minutes_left)} минут'
                    )
                    return redirect('login')

            # Отправляем письмо повторно
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
            # Не сообщаем, существует ли пользователь (безопасность)
            messages.success(
                request,
                'Если пользователь с таким email существует, '
                'письмо будет отправлено повторно.'
            )

    return render(request, 'school/resend_verification.html')



@login_required
def teacher_create_lesson_page(request):
    """Страница создания урока"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    teacher = request.user.teacher_profile
    students = teacher.student_set.all()

    context = {
        'teacher': teacher,
        'students': students,
    }
    return render(request, 'school/teacher/create_lesson.html', context)


@login_required
def teacher_create_schedule(request):
    """Создание шаблона расписания (разового или повторяющегося)"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')

    teacher = request.user.teacher_profile

    if request.method == 'POST':
        # Основные поля
        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')
        topic = request.POST.get('topic', '')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        repeat_type = request.POST.get('repeat_type', 'single')
        notes = request.POST.get('notes', '')
        print(f"🔍 repeat_type = {repeat_type}")
        print(f"🔍 Все POST данные: {dict(request.POST)}")
        # Валидация общих полей
        if not student_id or not subject_id or not start_time_str:
            messages.error(request, 'Заполните все обязательные поля')
            return redirect('teacher_create_schedule')

        student = get_object_or_404(Student, id=student_id, teachers=teacher)
        subject = get_object_or_404(Subject, id=subject_id)

        # Конвертируем время из строки в объект time
        from datetime import datetime, timedelta, date

        try:
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
        except ValueError:
            messages.error(request, 'Неверный формат времени начала')
            return redirect('teacher_create_schedule')

        # Если время окончания не указано, ставим +1 час
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

        # Создаем шаблон
        template = ScheduleTemplate(
            teacher=teacher,
            subject=subject,
            start_time=start_time,
            end_time=end_time,
            repeat_type=repeat_type,
            notes=notes
        )

        # ПРОВЕРКА В ЗАВИСИМОСТИ ОТ ТИПА
        if repeat_type == 'single':
            # Разовый урок - проверяем только дату
            date_str = request.POST.get('date')
            if not date_str:
                messages.error(request, 'Укажите дату занятия')
                return redirect('teacher_create_schedule')

            template.start_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            template.end_date = None
            template.max_occurrences = 1

        else:
            # Повторяющееся расписание - проверяем все поля
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

            # Дни недели
            template.monday = '1' in weekdays
            template.tuesday = '2' in weekdays
            template.wednesday = '3' in weekdays
            template.thursday = '4' in weekdays
            template.friday = '5' in weekdays
            template.saturday = '6' in weekdays
            template.sunday = '7' in weekdays

        # Сохраняем шаблон
        template.save()
        template.students.add(student)

        # Генерируем уроки
        lessons = template.generate_lessons()

        if repeat_type == 'single':
            messages.success(request, f'Урок создан на {template.start_date} в {start_time_str}')
        else:
            messages.success(request, f'Расписание создано! Сгенерировано {len(lessons)} уроков')

        return redirect('teacher_dashboard')

    # GET запрос - показываем форму
    students = teacher.student_set.all()
    subjects = teacher.subjects.all()

    context = {
        'teacher': teacher,
        'students': students,
        'subjects': subjects,
        'today': timezone.now().date().strftime('%Y-%m-%d'),
    }
    return render(request, 'school/teacher/schedule_template_form.html', context)

