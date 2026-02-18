# school/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from datetime import datetime, date, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count, Q
from .models import (
    User, Teacher, Student, Lesson, Subject, 
    LessonReport, Payment, TrialRequest, Schedule
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
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')
    
    student = request.user.student_profile
    today = timezone.now().date()
    
    # Получаем расписание
    upcoming_lessons = Lesson.objects.filter(
        student=student,
        date__gte=today,
        status='scheduled'
    ).order_by('date', 'start_time')[:10]
    
    # История занятий
    past_lessons = Lesson.objects.filter(
        student=student,
        status='completed'
    ).order_by('-date', '-start_time')[:10]
    
    # Баланс
    balance = request.user.balance
    
    # Последние платежи
    recent_payments = Payment.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'student': student,
        'upcoming_lessons': upcoming_lessons,
        'past_lessons': past_lessons,
        'balance': balance,
        'recent_payments': recent_payments,
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
def teacher_dashboard(request):
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ запрещен')
        return redirect('dashboard')
    
    teacher = request.user.teacher_profile
    today = timezone.now().date()
    
    # Список учеников
    students = Student.objects.filter(teachers=teacher)
    
    # Расписание на сегодня
    today_lessons = Lesson.objects.filter(
        teacher=teacher,
        date=today
    ).order_by('start_time')
    
    # Предстоящие занятия
    upcoming_lessons = Lesson.objects.filter(
        teacher=teacher,
        date__gt=today,
        status='scheduled'
    ).order_by('date', 'start_time')[:10]
    
    # Баланс кошелька
    wallet_balance = teacher.wallet_balance
    
    # Недавние выплаты
    recent_payments = Payment.objects.filter(
        user=request.user,
        payment_type='teacher_payment'
    ).order_by('-created_at')[:5]
    
    context = {
        'teacher': teacher,
        'students': students,
        'today_lessons': today_lessons,
        'upcoming_lessons': upcoming_lessons,
        'wallet_balance': wallet_balance,
        'recent_payments': recent_payments,
    }
    return render(request, 'school/teacher/dashboard.html', context)


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
    """API для календаря расписаний с цветовой индикацией"""
    schedules = Schedule.objects.filter(is_active=True).select_related('teacher__user')
    
    events = []
    today = date.today()
    
    # Цвета для разных статусов
    colors = {
        'scheduled': '#007bff',   # Синий
        'completed': '#28a745',    # Зеленый
        'overdue': '#dc3545',      # Красный
        'cancelled': '#fd7e14',    # Оранжевый
        'no_show': '#6c757d',      # Серый
        'empty': '#79aec8',        # Голубой (свободно)
    }
    
    # Показываем на 60 дней вперед
    for i in range(60):
        event_date = today + timedelta(days=i)
        
        for schedule in schedules:
            if event_date.weekday() == schedule.day_of_week:
                # Ищем занятие на это время
                lesson = Lesson.objects.filter(
                    teacher=schedule.teacher,
                    date=event_date,
                    start_time=schedule.start_time
                ).select_related('student__user', 'subject').first()
                
                start_dt = datetime.combine(event_date, schedule.start_time)
                end_dt = datetime.combine(event_date, schedule.end_time)
                
                if lesson:
                    # Если есть занятие
                    title = f"{schedule.teacher.user.last_name} - {lesson.subject.name}"
                    if lesson.student:
                        title += f" ({lesson.student.user.last_name})"
                    
                    event = {
                        'id': f"lesson_{lesson.id}",
                        'schedule_id': schedule.id,
                        'lesson_id': lesson.id,
                        'teacher_name': schedule.teacher.user.get_full_name(),
                        'subject': lesson.subject.name,
                        'student_name': lesson.student.user.get_full_name() if lesson.student else None,
                        'status': lesson.get_status_display(),
                        'start': start_dt.isoformat(),
                        'end': end_dt.isoformat(),
                        'color': colors.get(lesson.status, colors['scheduled']),
                    }
                else:
                    # Свободное время
                    event = {
                        'id': f"schedule_{schedule.id}_{event_date}",
                        'schedule_id': schedule.id,
                        'teacher_name': schedule.teacher.user.get_full_name(),
                        'subject': None,
                        'student_name': None,
                        'status': 'Свободно',
                        'start': start_dt.isoformat(),
                        'end': end_dt.isoformat(),
                        'color': colors['empty'],
                        'lesson_id': None,
                    }
                
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
