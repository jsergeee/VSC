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
import io
import json

from .models import (
    User, Teacher, Student, Lesson, Subject, 
    LessonReport, Payment, TrialRequest, Schedule,
    Material, Deposit, StudentNote
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


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'school/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Неверное имя пользователя или пароль')
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
    
    # Получаем ближайшие занятия
    upcoming_lessons = Lesson.objects.filter(
        student=student,
        date__gte=date.today(),
        status='scheduled'
    ).select_related('teacher__user', 'subject', 'format').order_by('date', 'start_time')[:10]
    
    # Получаем последние проведенные занятия
    past_lessons = Lesson.objects.filter(
        student=student,
        status='completed'
    ).select_related('teacher__user', 'subject').order_by('-date')[:10]
    
    # Получаем методические материалы
    materials = Material.objects.filter(
        Q(students=student) | Q(is_public=True) | Q(teachers__in=teachers)
    ).distinct()[:20]
    
    context = {
        'student': student,
        'balance': balance,
        'recent_deposits': recent_deposits,
        'upcoming_lessons': upcoming_lessons,
        'past_lessons': past_lessons,
        'teachers': teachers,
        'materials': materials,
    }
    
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
    ).select_related('student__user', 'subject').order_by('date', 'start_time')[:20]
    
    # Получаем занятия на сегодня
    today_lessons = Lesson.objects.filter(
        teacher=teacher,
        date=today,
        status='scheduled'
    ).select_related('student__user', 'subject').order_by('start_time')
    
    # Получаем методические материалы учителя
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
    
    context = {
        'teacher': teacher,
        'students': students,
        'upcoming_lessons': upcoming_lessons,
        'today_lessons': today_lessons,
        'materials': materials,
        'wallet_balance': wallet_balance,
        'recent_payments': recent_payments,
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
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    # Проверка доступа
    user = request.user
    if user.role == 'student' and lesson.student.user != user:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')
    elif user.role == 'teacher' and lesson.teacher.user != user:
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')
    
    report = None
    if hasattr(lesson, 'report'):
        report = lesson.report
    
    if request.method == 'POST' and user.role == 'teacher':
        form = LessonReportForm(request.POST, instance=report)
        if form.is_valid():
            report = form.save(commit=False)
            report.lesson = lesson
            report.save()
            
            # Обновляем статус урока
            lesson.status = 'completed'
            lesson.save()
            
            messages.success(request, 'Отчет сохранен')
            return redirect('lesson_detail', lesson_id=lesson.id)
    else:
        form = LessonReportForm(instance=report)
    
    context = {
        'lesson': lesson,
        'report': report,
        'form': form if user.role == 'teacher' and lesson.status != 'completed' else None,
    }
    return render(request, 'school/lesson_detail.html', context)


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